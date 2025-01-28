"""Tests for STAC metadata"""

import os
from datetime import datetime, timezone

import pytest
from botocore.errorfactory import ClientError
from rasterio.session import boto3

from icesat2_boreal_stac.stac import (
    AssetType,
    Variable,
    cog_key_to_asset_keys,
    create_collection,
    create_item,
)


def test_cog_key_to_asset_keys(
    test_cog_key, test_bad_cog_key, test_bucket, test_copy_bucket
) -> None:
    """Test function that takes a COG key and returns an asset dict"""
    asset_keys = cog_key_to_asset_keys(f"s3://{test_bucket}/{test_cog_key}")

    assert all(asset_type in asset_keys for asset_type in AssetType)

    # no such key
    with pytest.raises(ClientError):
        cog_key_to_asset_keys(f"s3://{test_bucket}/no/such/file.tif")

    # no such bucket
    with pytest.raises(ClientError):
        cog_key_to_asset_keys(f"s3://nope/{test_cog_key}")

    # bad key format
    with pytest.raises(ValueError):
        cog_key_to_asset_keys("file/test/file.tif")

    # COG in a folder with none of the other required assets
    with pytest.raises(ValueError, match="Missing required assets:*"):
        cog_key_to_asset_keys(f"s3://{test_bucket}/{test_bad_cog_key}")

    # copy to new bucket
    s3_client = boto3.client("s3")
    for copy_to in [f"s3://{test_copy_bucket}/new/", f"s3://{test_copy_bucket}/new"]:
        copied_asset_keys = cog_key_to_asset_keys(
            f"s3://{test_bucket}/{test_cog_key}", copy_to=copy_to
        )
        assert all(asset_type in copied_asset_keys for asset_type in AssetType)
        for asset_key in copied_asset_keys.values():
            _, _, bucket, key = asset_key.split("/", 3)
            _ = s3_client.head_object(Bucket=bucket, Key=key)

    # copy to bucket that doesn't exist
    with pytest.raises(ClientError):
        cog_key_to_asset_keys(
            f"s3://{test_bucket}/{test_cog_key}",
            copy_to=f"s3://nope/new/",
        )


def test_create_item(mock_cog_key_to_asset_keys) -> None:
    """Test STAC item creation"""
    cog_key = (
        "file://"
        + os.path.dirname(__file__)
        + "/data/boreal_ht_2020_202501131736787421_0000004.tif"
    )
    item = create_item(cog_key)

    assert item.id == "boreal_ht_2020_202501131736787421_0000004"
    assert (
        item.properties["start_datetime"]
        == datetime(2020, 1, 1, tzinfo=timezone.utc).isoformat()
    )

    assert all(asset_type.value in item.assets for asset_type in AssetType)


@pytest.mark.parametrize("variable", list(Variable))
def test_create_collection(variable: Variable) -> None:
    """Test create_collection"""
    collection = create_collection(variable)
    assert collection.ext.render
