"""STAC metadata methods for icesat2-boreal collections"""

import os
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, Optional, Set

import boto3
import rasterio
import rio_stac
from botocore.exceptions import ClientError
from dateutil.relativedelta import relativedelta
from pystac import (
    Collection,
    Extent,
    Item,
    ItemAssetDefinition,
    Link,
    MediaType,
    SpatialExtent,
    TemporalExtent,
)
from pystac.extensions.render import Render, RenderExtension
from pystac.extensions.version import VersionRelType
from rio_stac.stac import get_raster_info

from icesat2_boreal_stac.constants import (
    BBOX,
    COLLECTION_ID_FORMAT,
    CSV_MEDIA_TYPE,
    RASTER_SIZE,
    TEMPORAL_INTERVALS,
    VERSION,
    AssetType,
    Variable,
)
from icesat2_boreal_stac.s3 import cog_key_to_asset_keys

# specific text fields for each variable/asset
COLLECTION_DESCRIPTIONS = {
    Variable.AGB: {
        "title": "Icesat2 Boreal v2.1: Gridded Aboveground Biomass Density",
        "description": "Gridded predictions of aboveground biomass (Mg/ha) "
        "for the boreal region built from ICESat-2/ATL08 observations at 30m segment "
        "lengths, 30m HLS multispectral data, 30m Copernicus GLO30 topography, and 30m "
        "ESA Worldcover 2020 v1.0 land cover data.",
    },
    Variable.HT: {
        "title": "Icesat2 Boreal v2.1: Vegetation Height",
        "description": "Gridded predictions of vegetation height (m) "
        "for the boreal region built from ICESat-2/ATL08 observations at 30m segment "
        "lengths, 30m HLS multispectral data, 30m Copernicus GLO30 topography, and 30m "
        "ESA Worldcover 2020 v1.0 land cover data.",
    },
}

TEXT = {
    Variable.AGB: {
        AssetType.COG: {
            "title": "Gridded predictions of aboveground biomass (Mg/ha)",
            "description": "Gridded predictions of aboveground biomass (Mg/ha)",
        },
        AssetType.TRAINING_DATA_CSV: {
            "description": "Tabular training data with latitude, longitude, and "
            "biomass observations",
        },
    },
    Variable.HT: {
        AssetType.COG: {
            "title": "Gridded predictions of vegetation height (m)",
            "description": "Gridded predictions of vegetation height (m)",
        },
        AssetType.TRAINING_DATA_CSV: {
            "description": "Tabular training data with latitude, longitude, and "
            "height observations",
        },
    },
}

RENDERS = {
    Variable.AGB: {
        "agb_viridis": Render(
            {
                "title": "Aboveground biomass (Mg/ha)",
                "expression": "cog_b1",
                "rescale": [[0, 125]],
                "colormap_name": "viridis",
                "minmax_zoom": [6, 18],
            }
        ),
        "agb_gist_earth_r": Render(
            {
                "title": "Aboveground biomass (Mg/ha)",
                "expression": "cog_b1",
                "rescale": [[0, 400]],
                "colormap_name": "gist_earth_r",
                "color_formula": "gamma r 1.05",
                "minmax_zoom": [6, 18],
            }
        ),
    },
    Variable.HT: {
        "ht_inferno": Render(
            {
                "title": "Vegetation height (m)",
                "expression": "cog_b1",
                "rescale": [[0, 30]],
                "colormap_name": "inferno",
                "minmax_zoom": [6, 18],
            }
        )
    },
}


ITEM_ASSET_PROPERTIES = {
    AssetType.COG: {
        "type": MediaType.COG,
        "roles": ["data"],
    },
    AssetType.TRAINING_DATA_CSV: {
        "type": CSV_MEDIA_TYPE,
        "roles": ["data"],
        "title": "Tabular training data",
    },
    # AssetType.MODEL: {
    #     "type": RDS_MEDIA_TYPE,
    #     "roles": ["model"],
    #     "title": "Prediction model",
    #     "description": "Random forest model used to generate predictions for this "
    #     "item, stored as an .Rds",
    # },
}

ITEM_ASSETS = {
    variable: {
        asset_type: ItemAssetDefinition(
            {
                **properties,
                **TEXT[variable].get(asset_type, {}),
            }
        )
        for asset_type, properties in ITEM_ASSET_PROPERTIES.items()
    }
    for variable in Variable
}


def create_collection(variable: Variable) -> Collection:
    """Create STAC collection object"""
    collection_id = COLLECTION_ID_FORMAT.format(
        version=VERSION, variable=variable.value
    )

    collection = Collection(
        id=collection_id,
        title=COLLECTION_DESCRIPTIONS[variable]["title"],
        description=COLLECTION_DESCRIPTIONS[variable]["description"],
        extent=Extent(
            spatial=SpatialExtent(bboxes=[BBOX]),
            temporal=TemporalExtent(intervals=TEMPORAL_INTERVALS),
        ),
        license="CC-BY-NC-SA-4.0",
    )

    collection.item_assets = {
        item_asset.value: asset for item_asset, asset in ITEM_ASSETS[variable].items()
    }

    # add version extension
    collection.ext.add("version")
    collection.ext.version.version = VERSION
    collection.ext.version.deprecated = False

    collection.add_link(
        Link(
            rel=VersionRelType.PREDECESSOR,
            target="https://stac.maap-project.org/collections/icesat2-boreal",
            title="Previous version",
        )
    )

    # add render extension
    collection.ext.add("render")
    RenderExtension.ext(collection).apply(RENDERS[variable])

    return collection


def create_item(cog_key: str, copy_to: Optional[str] = None) -> Item:
    """Create a STAC item given the S3 key for a COG"""
    asset_keys = cog_key_to_asset_keys(cog_key, copy_to)
    cog_key = asset_keys[AssetType.COG]

    item_id = os.path.splitext(os.path.basename(cog_key))[0]

    # parse id into properties
    id_parts = item_id.split("_")

    variable = Variable(id_parts[1])
    collection_id = COLLECTION_ID_FORMAT.format(
        version=VERSION, variable=variable.value
    )
    created_datetime = datetime.strptime(id_parts[3][:8], "%Y%M%d")
    item_start_datetime = datetime.strptime(id_parts[2], "%Y")
    item_end_datetime = (
        item_start_datetime + relativedelta(years=1) - timedelta(seconds=1)
    )

    # generate dictionary of assets
    item_assets = {
        asset: ITEM_ASSETS[variable][asset].create_asset(key)
        for asset, key in asset_keys.items()
    }

    item = rio_stac.create_stac_item(
        source=asset_keys[AssetType.COG],
        collection=collection_id,
        id=item_id,
        input_datetime=(
            item_start_datetime + (item_end_datetime - item_start_datetime) / 2
        ),
        properties={
            "start_datetime": item_start_datetime.replace(
                tzinfo=timezone.utc
            ).isoformat(),
            "end_datetime": item_end_datetime.replace(tzinfo=timezone.utc).isoformat(),
            "created_datetime": created_datetime.replace(
                tzinfo=timezone.utc
            ).isoformat(),
        },
        assets=item_assets,
        # skip with_raster because when assets is specified, raster info does not get
        # attached to the asset
        with_raster=False,
        with_proj=True,
    )

    # retrieve the raster info separately
    with rasterio.open(cog_key) as src:
        raster_info = {"raster:bands": get_raster_info(src, max_size=RASTER_SIZE)}

    item.assets[AssetType.COG].extra_fields.update(**raster_info)
    item.stac_extensions.append(
        "https://stac-extensions.github.io/raster/v1.1.0/schema.json"
    )

    item.validate()

    return item
