"""Tests for STAC metadata"""

import os
from datetime import datetime, timezone

import pytest

from icesat2_boreal_stac.stac import (
    AssetType,
    Variable,
    create_collection,
    create_item,
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
