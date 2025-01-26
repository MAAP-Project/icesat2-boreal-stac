import os
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, Set

import boto3
import rasterio
import rio_stac
from dateutil.relativedelta import relativedelta
from pystac import Item, MediaType
from pystac.extensions.item_assets import AssetDefinition
from rio_stac.stac import get_raster_info

VERSION = "v2.1"
COLLECTION_ID_FORMAT = "icesat2-boreal-{version}-{variable}"

RDS_MEDIA_TYPE = "application/x-rds"
CSV_MEDIA_TYPE = "text/csv"

RASTER_SIZE = 3000


class Variable(str, Enum):
    """Enumeration of the different variables"""

    AGB = "agb"
    HT = "ht"


class AssetType(str, Enum):
    """Enumeration of all possible asset types that should be present"""

    COG = "cog"
    MODEL = "model"
    TRAINING_DATA_CSV = "training_data_csv"
    CONTEXT_JSON = "context_json"
    DATASET_JSON = "dataset_json"
    MET_JSON = "met_json"

    def get_file_pattern(self) -> str:
        """Returns the file pattern for this asset type"""
        patterns = {
            self.COG: ".tif",
            self.MODEL: "_model.Rds",
            self.TRAINING_DATA_CSV: "_train_data.csv",
            self.CONTEXT_JSON: ".context.json",
            self.DATASET_JSON: ".dataset.json",
            self.MET_JSON: ".met.json",
        }
        return patterns[self]

    def matches_file(self, filename: str) -> bool:
        """Check if the given filename matches this asset type's pattern"""
        return filename.endswith(self.get_file_pattern())

    @classmethod
    def required_assets(cls) -> Set[str]:
        """Returns set of all required asset types"""
        return {member.value for member in cls}


ITEM_ASSET_PROPERTIES = {
    AssetType.COG: {
        "type": MediaType.COG,
        "roles": ["data"],
        "title": "Gridded estimates of {variable}",
        "description": "Gridded estimates of {variable}",
    },
    AssetType.MODEL: {
        "type": RDS_MEDIA_TYPE,
        "roles": ["model"],
        "title": "Prediction model",
        "description": "Random forest model used to generate predictions for this item, stored as an .Rds",
    },
    AssetType.TRAINING_DATA_CSV: {
        "type": CSV_MEDIA_TYPE,
        "roles": ["data"],
        "title": "Model training data for {variable}",
        "description": "Observed values of {variable} with geographic coordinates used for training models",
    },
    AssetType.CONTEXT_JSON: {
        "type": MediaType.JSON,
        "roles": ["metadata"],
        "title": "Context JSON",
        "description": "Context JSON",
    },
    AssetType.DATASET_JSON: {
        "type": MediaType.JSON,
        "roles": ["metadata"],
        "title": "Dataset JSON",
        "description": "Dataset JSON",
    },
    AssetType.MET_JSON: {
        "type": MediaType.JSON,
        "roles": ["metadata"],
        "title": "Met JSON",
        "description": "Met JSON",
    },
}

ITEM_ASSETS = {
    variable: {
        asset_type: AssetDefinition(
            {
                key: value.format(variable=variable.value)
                if isinstance(value, str)
                else value
                for key, value in properties.items()
            }
        )
        for asset_type, properties in ITEM_ASSET_PROPERTIES.items()
    }
    for variable in Variable
}


def cog_key_to_asset_keys(cog_key: str) -> Dict[AssetType, str]:
    """Given an S3 key to a cog asset, return a dictionary of all associated assets and their storage keys"""
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
                asset_keys[asset_type.value] = full_s3_path

    # verify all required assets were found
    missing_assets = AssetType.required_assets() - set(asset_keys.keys())
    if missing_assets:
        raise ValueError(f"Missing required assets: {missing_assets}")

    return asset_keys


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

    # generate dictionary of expected assets
    item_assets = {
        asset: ITEM_ASSETS[variable][asset].create_asset(key)
        for asset, key in asset_keys.items()
    }

    item = rio_stac.create_stac_item(
        source=asset_keys[AssetType.COG],
        collection=collection_id,
        id=item_id,
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
        with_raster=False,
        with_proj=True,
    )

    with rasterio.open(cog_key) as src:
        raster_info = {"raster:bands": get_raster_info(src, max_size=RASTER_SIZE)}

    item.assets[AssetType.COG].extra_fields.update(**raster_info)
    item.stac_extensions.append(
        "https://stac-extensions.github.io/raster/v1.1.0/schema.json"
    )

    item.validate()

    return item
