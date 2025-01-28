"""Tests for S3 utility functions"""

import os
import time

import pytest
from botocore.errorfactory import ClientError
from rasterio.session import boto3

from icesat2_boreal_stac.stac import (
    AssetType,
    cog_key_to_asset_keys,
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

    copied_asset_keys = cog_key_to_asset_keys(
        f"s3://{test_bucket}/{test_cog_key}", copy_to=f"s3://{test_copy_bucket}/new"
    )

    # copy to bucket that doesn't exist
    with pytest.raises(ClientError):
        cog_key_to_asset_keys(
            f"s3://{test_bucket}/{test_cog_key}",
            copy_to=f"s3://nope/new/",
        )


def test_cog_key_to_asset_keys_copy_behavior(
    test_cog_key, test_bucket, test_copy_bucket
) -> None:
    """Test that files are only copied when necessary"""
    s3_client = boto3.client("s3")
    source_path = f"s3://{test_bucket}/{test_cog_key}"
    copy_to = f"s3://{test_copy_bucket}/new"

    # First copy - should copy all files
    copied_asset_keys = cog_key_to_asset_keys(source_path, copy_to=copy_to)

    # Get initial timestamps of copied files
    initial_timestamps = {}
    for asset_key in copied_asset_keys.values():
        _, _, bucket, key = asset_key.split("/", 3)
        response = s3_client.head_object(Bucket=bucket, Key=key)
        initial_timestamps[key] = response["LastModified"]

    # Wait a moment to ensure any new timestamps would be different
    time.sleep(1)

    # Second copy - should skip all files
    copied_asset_keys = cog_key_to_asset_keys(source_path, copy_to=copy_to)

    # Verify timestamps haven't changed
    for asset_key in copied_asset_keys.values():
        _, _, bucket, key = asset_key.split("/", 3)
        response = s3_client.head_object(Bucket=bucket, Key=key)
        assert response["LastModified"] == initial_timestamps[key], (
            f"File {key} was unnecessarily copied"
        )

    # Modify source file
    _, _, src_bucket, src_key = source_path.split("/", 3)
    print(f"modifying {src_key} and copying to {src_bucket}")
    s3_client.put_object(Bucket=src_bucket, Key=src_key, Body=b"modified content")

    # Third copy - should copy the modified file
    copied_asset_keys = cog_key_to_asset_keys(source_path, copy_to=copy_to)

    # Verify the modified file was copied
    for asset_key in copied_asset_keys.values():
        _, _, bucket, key = asset_key.split("/", 3)
        response = s3_client.head_object(Bucket=bucket, Key=key)
        if os.path.basename(key) == os.path.basename(src_key):  # the modified file
            assert response["LastModified"] > initial_timestamps[key], (
                f"Modified file {key} was not copied"
            )
        else:  # unmodified files
            assert response["LastModified"] == initial_timestamps[key], (
                f"Unmodified file {key} was unnecessarily copied"
            )
