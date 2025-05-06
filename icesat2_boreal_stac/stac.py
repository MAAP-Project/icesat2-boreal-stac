"""STAC metadata methods for icesat2-boreal collections"""

import os
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

import rasterio
import rio_stac
import semver
from dateutil.relativedelta import relativedelta
from pystac import (
    Collection,
    Extent,
    Item,
    Link,
    SpatialExtent,
    TemporalExtent,
    get_stac_version,
)
from pystac.extensions.render import RenderExtension
from pystac.extensions.version import VersionRelType
from rio_stac.stac import get_raster_info

from icesat2_boreal_stac.constants import (
    BBOX,
    COLLECTION_ASSETS,
    COLLECTION_CITATION,
    COLLECTION_DESCRIPTION,
    COLLECTION_ID_FORMAT,
    COLLECTION_TITLES,
    ITEM_ASSETS,
    LICENSE,
    PROVIDERS,
    RENDERS,
    REPOSITORY_LINK,
    SUMMARIES,
    TEMPORAL_INTERVALS,
    VERSION,
    AssetType,
    Variable,
)
from icesat2_boreal_stac.s3 import cog_key_to_asset_keys

# specific text fields for each variable/asset


def format_multiline_string(string: str) -> str:
    """Format a multi-line string for use in metadata fields"""
    return re.sub(r" +", " ", re.sub(r"(?<!\n)\n(?!\n)", " ", string))


def create_collection(variable: Variable) -> Collection:
    """Create STAC collection object"""
    collection_id = COLLECTION_ID_FORMAT.format(
        version=VERSION, variable=variable.value
    )

    collection = Collection(
        id=collection_id,
        title=COLLECTION_TITLES[variable],
        description=format_multiline_string(COLLECTION_DESCRIPTION),
        extent=Extent(
            spatial=SpatialExtent(bboxes=[BBOX]),
            temporal=TemporalExtent(intervals=TEMPORAL_INTERVALS),
        ),
        license=LICENSE,
        providers=PROVIDERS,
        summaries=SUMMARIES,
        assets=COLLECTION_ASSETS[variable],
    )

    collection.add_link(REPOSITORY_LINK)

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

    # add processing extension
    collection.stac_extensions.append(
        "https://stac-extensions.github.io/processing/v1.2.0/schema.json"
    )

    # if using STAC v1.0.0, add raster and item-assets extensions
    if semver.Version.parse(get_stac_version()) <= semver.Version.parse("1.0.0"):
        collection.ext.add("raster")
        collection.ext.add("item_assets")

    # add render extension
    collection.ext.add("render")
    RenderExtension.ext(collection).apply(RENDERS[variable])

    # add scientific extension
    collection.ext.add("sci")
    collection.ext.sci.apply(
        citation=format_multiline_string(COLLECTION_CITATION),
    )

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
    if semver.Version.parse(get_stac_version()) <= semver.Version.parse("1.0.0"):
        item.stac_extensions.append(
            "https://stac-extensions.github.io/raster/v1.1.0/schema.json"
        )
        band_property = "raster:bands"
    else:
        band_property = "bands"

    with rasterio.open(cog_key) as src:
        raster_info = {band_property: get_raster_info(src, max_size=3000)}

    item.assets[AssetType.COG].extra_fields.update(**raster_info)

    item.validate()

    return item
