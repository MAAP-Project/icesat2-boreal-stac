# icesat2-boreal-stac

![GitHub Workflow Status (with event)](https://img.shields.io/github/actions/workflow/status/MAAP-project/icesat2-boreal-stac/ci.yml?style=for-the-badge)

- Name: icesat2-boreal-stac
- Package: `icesat2_boreal_stac`
- Owner: @hrodmn
- STAC extensions used:
  - [proj](https://github.com/stac-extensions/projection/)
  - [render](https://github.com/stac-extensions/render/)
- [Browse an example in human-readable form](https://radiantearth.github.io/stac-browser/#/external/raw.githubusercontent.com/MAAP-project/icesat2-boreal-stac/main/examples/agb/collection.json)

A short description of the package and its usage.

## STAC examples

### Aboveground biomass

- [Collection](./examples/agb/collection.json)
- [Item](./examples/agb/boreal_agb_2020_202411251732556086_0000004/boreal_agb_2020_202411251732556086_0000004.json)

### Vegetation height

- [Collection](./examples/ht/collection.json)
- [Item](./examples/ht/boreal_ht_2020_202501131736787421_0000004/boreal_ht_2020_202501131736787421_0000004.json)

## Installation

```shell
pip install git+https://github.com/MAAP-project/icesat2-boreal-stac.git@main
```

## Usage
>
> [!WARNING]
> By default, this package will create STAC v1.1.0 collections and items!
>
> Use `pystac.set_stac_version` or the `PYSTAC_STAC_VERSION_OVERRIDE` environment variable to set it to version 1.0.0 if you need that for your catalog.

To create collections:

```python
from pystac import set_stac_version
from icesat2_boreal_stac.stac import create_collection, Variable

# optional: set STAC version to 1.0.0
# set_stac_version("1.0.0")

agb_collection = create_collection(Variable.AGB)
ht_collection = create_collection(Variable.HT)
```

To create items, specify the key to the COG asset for this item. The package assumes that the other asset(s) (e.g. train_data.csv) are located alongside the COG asset in a folder in S3.

> [!NOTE]
> You need to be authenticated with MAAP SMCE AWS credentials to access the files in these buckets:

```python
from icesat2_boreal_stac.stac import create_item

agb_item = create_item(
    cog_key="s3://maap-ops-workspace/aliz237/dps_output/run_boreal_biomass_map/dev_v1.5/AGB_H30_2020/full_run/2024/11/25/09/38/51/560230/boreal_agb_2020_202411251732556086_0000004.tif"
)
ht_item = create_item(
    cog_key="s3://maap-ops-workspace/aliz237/dps_output/run_boreal_biomass_map/dev_v1.5/Ht_H30_2020/full_run/2025/01/13/09/01/49/694207/boreal_ht_2020_202501131736787421_0000004.tif"
)
```

You can also specify an S3 directory into which the assets should be copied before generating the metadata:

```python
from icesat2_boreal_stac.stac import create_item

agb_item_copied = create_item(
    cog_key="s3://maap-ops-workspace/aliz237/dps_output/run_boreal_biomass_map/dev_v1.5/AGB_H30_2020/full_run/2024/11/25/09/38/51/560230/boreal_agb_2020_202411251732556086_0000004.tif",
    copy_to="s3://nasa-maap-data-store/file-staging/nasa-map/icesat2-boreal-v2.1/0000004/agb",
)
```

Before generating the metadata, the assets that will be included in the item will be copied from the folder where `cog_key` is located into the `copy_to` folder.
Files will retain the same basename.

At this time the package is only usable from Python.

## Contributing

We use [pre-commit](https://pre-commit.com/) to check any changes.
To set up your development environment:

```shell
uv sync
uv run pre-commit install
```

To check all files:

```shell
uv run pre-commit run --all-files
```

To run the tests:

```shell
uv run pytest
```

If you've updated the STAC metadata output, update the examples:
> [!NOTE]
> You need to be authenticated with MAAP SMCE credentials to run this

```shell
uv run scripts/update-examples
```
