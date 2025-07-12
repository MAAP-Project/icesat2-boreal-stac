"""stactools-icesat2-boreal"""

import stactools.core
from stactools.cli.registry import Registry
from stactools.icesat2_boreal.stac import create_collection, create_item

__all__ = ["create_collection", "create_item"]

stactools.core.use_fsspec()


def register_plugin(registry: Registry) -> None:
    from stactools.icesat2_boreal import commands

    registry.register_subcommand(commands.create_icesat2boreal_command)
