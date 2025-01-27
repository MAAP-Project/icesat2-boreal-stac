"""STAC metadata methods for icesat2-boreal collections"""

import os
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, Set

import boto3
import rasterio
import rio_stac
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

VERSION = "v2.1"
COLLECTION_ID_FORMAT = "icesat2-boreal-{version}-{variable}"

RDS_MEDIA_TYPE = "application/x-rds"
CSV_MEDIA_TYPE = "text/csv"

RASTER_SIZE = 3000
BBOX = [-180, 51.6, 180, 78]
TEMPORAL_INTERVALS = [
    [
        datetime(2020, 1, 1, tzinfo=timezone.utc),
        datetime(2021, 1, 1, tzinfo=timezone.utc) - timedelta(seconds=1),
    ]
]


class Variable(str, Enum):
    """Enumeration of the different variables"""

    AGB = "agb"
    HT = "ht"


class AssetType(str, Enum):
    """Enumeration of all possible asset types that should be present"""

    COG = "cog"
    # MODEL = "model"
    TRAINING_DATA_CSV = "training_data_csv"

    def get_file_pattern(self) -> str:
        """Returns the file pattern for this asset type"""
        patterns = {
            self.COG: ".tif",
            # self.MODEL: "_model.Rds",
            self.TRAINING_DATA_CSV: "_train_data.csv",
        }
        return patterns[self]

    def matches_file(self, filename: str) -> bool:
        """Check if the given filename matches this asset type's pattern"""
        return filename.endswith(self.get_file_pattern())

    @classmethod
    def required_assets(cls) -> Set[str]:
        """Returns set of all required asset types"""
        return {member.value for member in cls}


# specific text fields for each variable/asset
COLLECTION_DESCRIPTIONS = {
    Variable.AGB: {
        "title": "Icesat2 Boreal v2.1: Gridded Aboveground Biomass Density",
        "description": "Gridded predictions of aboveground biomass (Mg/ha) "
        "for boreal region derived from ICESat-2 and Harmonized Landsat Sentinel 2 "
        "data.",
    },
    Variable.HT: {
        "title": "Icesat2 Boreal v2.1: Vegetation Height",
        "description": "Gridded predictions of vegetation height (m) "
        "for boreal region derived from ICESat-2 and Harmonized Landsat Sentinel 2 "
        "data.",
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
        "agb": Render(
            {
                "title": "Aboveground biomass (Mg/ha)",
                "assets": [AssetType.COG],
                "expression": "cog_b1",
                "rescale": [[0, 125]],
                "colormap_name": "viridis",
                "minmax_zoom": [6, 18],
            }
        )
    },
    Variable.HT: {
        "ht": Render(
            {
                "title": "Vegetation height (m)",
                "assets": [AssetType.COG],
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


def cog_key_to_asset_keys(cog_key: str) -> Dict[AssetType, str]:
    """Given an S3 key to a cog asset, return a dictionary of all associated assets and
    their storage keys"""
    if not cog_key.startswith("s3://"):
        raise ValueError(f"{cog_key} is not a valid s3 key")

    s3_client = boto3.client("s3")
    _, _, bucket, input_key = cog_key.split("/", 3)

    s3_client.head_object(Bucket=bucket, Key=input_key)

    s3_dir = os.path.dirname(input_key)

    asset_keys = {}

    dir_contents = s3_client.list_objects_v2(Bucket=bucket, Prefix=s3_dir + "/")

    for obj in dir_contents.get("Contents", []):
        obj_key = obj["Key"]
        filename = os.path.basename(obj_key)
        full_s3_path = f"s3://{bucket}/{obj_key}"

        # check each asset type for a match
        for asset_type in AssetType:
            if asset_type.matches_file(filename):
                asset_keys[asset_type] = full_s3_path

    # verify all required assets were found
    missing_assets = AssetType.required_assets() - set(asset_keys.keys())
    if missing_assets:
        raise ValueError(f"Missing required assets: {missing_assets}")

    return asset_keys


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
        license="CC-BY",
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


def create_item(cog_key: str) -> Item:
    """Create a STAC item given the S3 key for a COG"""
    asset_keys = cog_key_to_asset_keys(cog_key)

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
