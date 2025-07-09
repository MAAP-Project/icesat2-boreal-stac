"""Tests for STAC metadata"""

import os
from datetime import datetime, timezone

import pytest

from stactools.icesat2_boreal.stac import (
    AssetType,
    Variable,
    create_collection,
    create_item,
)

cog_key = (
    "file://"
    + os.path.dirname(__file__)
    + "/data/boreal_ht_2020_202501131736787421_0000004.tif"
)


def test_create_item(cog_key: str) -> None:
    """Test STAC item creation"""
    item = create_item(cog_key, "file://training_data.csv")
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


def test_create_item_v1_0_0(stac_v1_0_0) -> None:
    "Test STAC item creation for STAC v1.0.0"
    item = create_item(cog_key, "file://training_data.csv")
    item.validate()
    assert item.to_dict()["stac_version"] == "1.0.0"
    assert item.ext.has("raster")


@pytest.mark.parametrize("variable", list(Variable))
def test_create_collection(variable: Variable) -> None:
    """Test create_collection"""
    collection = create_collection(variable)
    collection.validate()
    assert collection.ext.render

    assert not collection.ext.has("raster")
    assert not collection.ext.has("item_assets")


def test_create_collection_v1_0_0(stac_v1_0_0) -> None:
    "Test STAC collection creation for STAC v1.0.0"
    collection = create_collection(Variable.AGB)
    collection.validate()
    assert collection.to_dict()["stac_version"] == "1.0.0"
    assert collection.ext.has("raster")
    assert collection.ext.has("item_assets")
