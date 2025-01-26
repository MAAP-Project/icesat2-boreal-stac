import pytest
from botocore.errorfactory import ClientError

from icesat2_boreal_stac.stac import cog_key_to_asset_keys


def test_cog_key_to_asset_keys(test_cog_key, test_bucket):
    asset_keys = cog_key_to_asset_keys(f"s3://{test_bucket}/{test_cog_key}")

    assert asset_keys

    # no such key
    with pytest.raises(ClientError):
        cog_key_to_asset_keys(f"s3://{test_bucket}/no/such/file.tif")

    # no such bucket
    with pytest.raises(ClientError):
        cog_key_to_asset_keys(f"s3://nope/{test_cog_key}")

    # bad key format
    with pytest.raises(ValueError):
        cog_key_to_asset_keys("file/test/file.tif")
