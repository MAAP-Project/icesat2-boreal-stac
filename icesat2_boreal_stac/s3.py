"""Utilities for parsing/copying S3 keys"""

import os
from typing import Dict, Optional

import boto3
from botocore.exceptions import ClientError

from icesat2_boreal_stac.constants import AssetType


def _parse_s3_path(s3_path: str) -> tuple[str, str]:
    """Parse an S3 path into bucket and key components"""
    if not s3_path.startswith("s3://"):
        raise ValueError(f"{s3_path} is not a valid s3 key")

    _, _, bucket, key = s3_path.split("/", 3)
    return bucket, key


def _should_copy_object(
    s3_client,
    source_bucket: str,
    source_key: str,
    dest_bucket: str,
    dest_key: str,
) -> bool:
    """Check if object needs to be copied based on metadata comparison"""
    source_metadata = s3_client.head_object(Bucket=source_bucket, Key=source_key)
    source_etag = source_metadata["ETag"]
    source_size = source_metadata["ContentLength"]

    try:
        dest_metadata = s3_client.head_object(Bucket=dest_bucket, Key=dest_key)
        dest_etag = dest_metadata["ETag"]
        dest_size = dest_metadata["ContentLength"]

        return not (source_etag == dest_etag and source_size == dest_size)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "404":
            return True

        raise


def cog_key_to_asset_keys(
    cog_key: str, copy_to: Optional[str] = None
) -> Dict[AssetType, str]:
    """Given an S3 key to a cog asset, return a dictionary of all associated assets and
    their storage keys"""
    source_bucket, input_key = _parse_s3_path(cog_key)

    s3_client = boto3.client("s3")
    s3_client.head_object(Bucket=source_bucket, Key=input_key)

    s3_dir = os.path.dirname(input_key)
    asset_keys = {}

    dir_contents = s3_client.list_objects_v2(Bucket=source_bucket, Prefix=s3_dir + "/")

    for obj in dir_contents.get("Contents", []):
        obj_key = obj["Key"]
        filename = os.path.basename(obj_key)
        full_s3_path = f"s3://{source_bucket}/{obj_key}"

        for asset_type in AssetType:
            if asset_type.matches_file(filename):
                if copy_to:
                    dest_bucket, dest_dir = _parse_s3_path(copy_to)
                    dest_key = f"{dest_dir.strip('/')}/{filename}"

                    if _should_copy_object(
                        s3_client, source_bucket, obj_key, dest_bucket, dest_key
                    ):
                        s3_client.copy_object(
                            CopySource={"Bucket": source_bucket, "Key": obj_key},
                            Bucket=dest_bucket,
                            Key=dest_key,
                            MetadataDirective="COPY",
                        )

                    full_s3_path = f"s3://{dest_bucket}/{dest_key}"

                asset_keys[asset_type] = full_s3_path

    # verify all required assets were found
    missing_assets = AssetType.required_assets() - set(asset_keys.keys())
    if missing_assets:
        raise ValueError(f"Missing required assets: {missing_assets}")

    return asset_keys
