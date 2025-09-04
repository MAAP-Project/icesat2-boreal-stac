"""Tests for STAC metadata"""

from datetime import datetime, timezone

import pytest

from stactools.icesat2_boreal.stac import (
    AssetType,
    Variable,
    create_collection,
    create_item,
)


def test_create_item_in_daac(cog_key_in_daac: str) -> None:
    """Test STAC item creation"""
    item = create_item(cog_key_in_daac, "file://training_data.parquet")
    item.validate()
    assert item.id == "boreal_ht_2020_202501131736787421_0000004"
    assert (
        item.properties["start_datetime"]
        == datetime(2020, 1, 1, tzinfo=timezone.utc).isoformat()
    )

    assert all(asset_type.value in item.assets for asset_type in AssetType)

    # check STAC v1.1.0 things
    assert item.to_dict()["stac_version"] == "1.1.0"
    assert not item.ext.has("raster")

    assert item.assets.get("cog")


def test_create_item_not_in_daac(cog_key_not_in_daac: str) -> None:
    """Test STAC item creation"""
    item = create_item(cog_key_not_in_daac, "file://training_data.parquet")
    item.validate()
    assert item.id == "boreal_ht_2020_202501131736787421_0000003"
    assert not item.properties["icesat2-boreal:in_daac"]


@pytest.mark.parametrize("variable", list(Variable))
def test_create_collection(variable: Variable) -> None:
    """Test create_collection"""
    collection = create_collection(variable)
    collection.validate()
    assert collection.ext.render

    assert not collection.ext.has("raster")
    assert not collection.ext.has("item_assets")
