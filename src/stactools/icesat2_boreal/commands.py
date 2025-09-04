"""CLI commands for icesat2-boreal-stac"""

import logging

import click
from click import Command, Group

from stactools.icesat2_boreal import stac
from stactools.icesat2_boreal.constants import Variable

logger = logging.getLogger(__name__)


def create_icesat2boreal_command(cli: Group) -> Command:
    """Creates the icesat2-boreal-stac command line utility."""

    @cli.group(
        "icesat2boreal",
        short_help=("Commands for working with icesat2-boreal-stac"),
    )
    def icesat2boreal() -> None:
        pass

    @icesat2boreal.command(
        "create-collection",
        short_help="Creates a STAC collection",
    )
    @click.argument("variable")
    @click.argument("destination")
    def create_collection_command(variable: str, destination: str) -> None:
        """Creates a STAC Collection

        Args:
            destination: An HREF for the Collection JSON
        """
        collection = stac.create_collection(variable=Variable(variable))
        collection.set_self_href(destination)
        collection.save_object()

    @icesat2boreal.command("create-item", short_help="Create a STAC item")
    @click.argument("cog_source")
    @click.argument("parquet_source")
    @click.argument("destination")
    def create_item_command(
        cog_source: str, parquet_source: str, destination: str
    ) -> None:
        """Creates a STAC Item

        Args:
            source: HREF of the Asset associated with the Item
            destination: An HREF for the STAC Item
        """
        item = stac.create_item(cog_source, parquet_source)
        item.save_object(dest_href=destination)

    return icesat2boreal
