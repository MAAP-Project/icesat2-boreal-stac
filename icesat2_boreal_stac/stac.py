import datetime
import json
import tempfile

import fsspec
import pystac
from config import IceSatBaseSettings

from rio_stac.scripts.cli import stac

ACQUISITION_DATETIME = datetime.datetime(2019, 1, 1).strftime("%Y-%m-%dT%H:%M:%SZ")

s3_fs = fsspec.filesystem("s3")
icesat_base_settings = IceSatBaseSettings()


def create_item(s3_path: str) -> pystac.Item:
    print(f"Creating item for {s3_path}")

    s3_path_csv = s3_path.replace(".tif", "_train_data.csv")

    assert s3_fs.exists(s3_path), f"{s3_path} does not exist"
    assert s3_fs.exists(s3_path_csv), f"{s3_path_csv} does not exist"

    item_id = s3_path.split("/")[-1].replace(".tif", "")

    created_datetime = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    with tempfile.NamedTemporaryFile(suffix=".json") as tmp:
        stac(
            [
                s3_path,
                "--output",
                tmp.name,
                "--collection",
                icesat_base_settings.COLLECTION_ID,
                "--id",
                item_id,
                "--datetime",
                ACQUISITION_DATETIME,
                "--property",
                f"created={created_datetime}",
            ],
            standalone_mode=False,
        )
        item = pystac.read_file(tmp.name)

    csv_asset = pystac.Asset(
        href=s3_path.replace(".tif", "_train_data.csv"),
        media_type="text/csv",
        roles=["data"],
        title="CSV",
        description="CSV of training data",
    )

    item.add_asset("csv", csv_asset)

    item.validate()

    print(f"Created item for {s3_path}")

    return item


def save_item(item: pystac.Item):
    """Save STAC item
    """
    item = item.to_dict()
    print(f"Saving item {item['id']} to {icesat_base_settings.item_output_dir}")
    id = item["id"]
    with open(f"{icesat_base_settings.item_output_dir}/{id}.json", "w") as f:
        json.dump(item, f)
    print(f"Saved item {item['id']} to {icesat_base_settings.item_output_dir}")
