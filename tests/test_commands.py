"""Tests for cli commands"""

from pathlib import Path

from click import Group
from click.testing import CliRunner
from pystac import Collection, Item

from icesat2_boreal_stac.commands import create_icesat2boreal_command

command = create_icesat2boreal_command(Group())


def test_create_collection(tmp_path: Path) -> None:
    """Test create collection cli"""
    path = str(tmp_path / "collection.json")
    runner = CliRunner()
    result = runner.invoke(command, ["create-collection", "agb", path])
    assert result.exit_code == 0, "\n{}".format(result.output)
    collection = Collection.from_file(path)
    collection.validate()


def test_create_item(tmp_path: Path, cog_key: str, mock_cog_key_to_asset_keys) -> None:
    """Test create item cli"""
    # Smoke test for the command line create-item command
    #
    # Most checks should be done in test_stac.py::test_create_item
    path = str(tmp_path / "item.json")
    runner = CliRunner()
    result = runner.invoke(command, ["create-item", cog_key, path])
    assert result.exit_code == 0, "\n{}".format(result.output)
    item = Item.from_file(path)
    item.validate()
