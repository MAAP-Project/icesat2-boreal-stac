import fsspec
import stac as icesat_stac
from config import IceSatBaseSettings

s3_fs = fsspec.filesystem("s3")
icesat_base_settings = IceSatBaseSettings()


def icesat_stac_service(s3_path: str):
    """Create and submit STAC item ingestion for icesat COG stored in S3.

    Args:
        s3_path (str): S3 path to COG
    """
    item = icesat_stac.create_item(s3_path)
    icesat_stac.save_item(item)
