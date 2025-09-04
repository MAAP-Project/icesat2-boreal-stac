"""Constants for icesat2_boreal_stac"""

from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Any, Dict, List, Set

from pystac import (
    Asset,
    ItemAssetDefinition,
    Link,
    MediaType,
    Provider,
    ProviderRole,
    Summaries,
)
from pystac.extensions.render import Render


class Variable(StrEnum):
    """Enumeration of the different variables"""

    AGB = "agb"
    HT = "ht"


class AssetType(StrEnum):
    """Enumeration of all possible asset types that should be present"""

    COG = "cog"
    # MODEL = "model"
    TRAINING_DATA_PARQUET = "training_data_parquet"

    def get_file_pattern(self) -> str:
        """Returns the file pattern for this asset type"""
        patterns = {
            self.COG: ".tif",
            self.TRAINING_DATA_PARQUET: "_train.parquet",
        }
        return patterns[self]

    def matches_file(self, filename: str) -> bool:
        """Check if the given filename matches this asset type's pattern"""
        return filename.endswith(self.get_file_pattern())

    @classmethod
    def required_assets(cls) -> Set[str]:
        """Returns set of all required asset types"""
        return {member.value for member in cls}


VERSION = "v3.1"
COLLECTION_ID_FORMAT = "icesat2-boreal-{version}-{variable}"


RESOLUTION = 30
BBOX = [-180, 51.6, 180, 78]
TEMPORAL_INTERVALS = [
    [
        datetime(2020, 1, 1, tzinfo=timezone.utc),
        datetime(2021, 1, 1, tzinfo=timezone.utc) - timedelta(seconds=1),
    ]
]

LICENSE = "CC-BY"

COLLECTION_DESCRIPTION = """This dataset provides predictions of woody aboveground
biomass density (AGBD) and vegetation height for high northern latitude forests at 30 m
spatial resolution for the year 2020, accounting for >30% of global forest area.

Maps of woody AGBD and height are essential for understanding patterns of forest
structure, including the mass of forest vegetation, its carbon content, and its vertical
and horizontal arrangement across managed and unmanaged landscapes. These maps are
optimized to visualize these patterns, monitor forest conditions, and manage forest
carbon stocks and their changes. The information contained in these maps provides
insights into the current conditions and shifts in a global biome that is shaped by
natural processes that play out across decades to millennia, as well as human decisions,
and whose status and functioning affects wildlife, the climate, economies, and the
wellbeing of public and private sector stakeholders both within and outside of the
north.

These maps are built with state-of-the-art earth observation datasets collected from
space, including lidar observations from NASA’s ICESat-2 and imagery from NASA’s
Harmonized Landsat/Sentinel-2 project. They are designed for circumpolar boreal-wide
mapping from local to global scales and provide the northern component of global forest
structure estimates, to which complementary estimates from NASA's Global Ecosystem
Dynamics Investigation (GEDI) mission contribute temperate and tropical portions. The
AGBD and height predictions cover the extent of high latitude boreal forests and
shrublands, and while they extend southward outside the boreal domain nominally to ~50°N
they are intended to contribute to global estimates northward from 51.6°N.

The compilation of these maps is a final value-added step made possible by decades of
investment coupled with world-class expertise from the US Government into engineering,
space, and earth science. With this long-term investment, NASA and its federal (USGS,
NOAA), international, and private sector partners have conceived of, tested, built,
launched, collected and processed data from, and maintained a constellation of, earth
observation satellites that provide the fundamental measurements used to build these
maps.

These maps are compiled on a platform built for geoscience algorithm development and
data processing that uses Amazon Web Services. This platform (the Multi-mission
Algorithm and Analysis Platform; www.maap-project.org) is the result of an international
partnership between NASA and the European Space Agency to promote and support science
that is accessible, reproducible, and well-documented. This work is the result of a
collaboration of a team of scientists and engineers from the University of
Maryland-College Park, NASA Goddard Space Flight Center, the University of Texas-Austin,
NASA Jet Propulsion Lab, and Development Seed. The primary funding source for this work
came through NASA Terrestrial Ecology Program grants associated with NASA’s decade-long
Arctic/Boreal Vulnerability Experiment (http://above.nasa.gov)"""

COLLECTION_CITATION = """Duncanson, L., P.M. Montesano, A. Neuenschwander, A.
Zarringhalam, N. Thomas, A. Mandel, D. Minor, E. Guenther, S. Hancock, T. Feng, A.
Barciauskas, G.W. Chang, S. Shah, and B.P. Satorius. Circumpolar boreal aboveground
biomass mapping with ICESat-2. (in prep.)"""

PROCESSING_LEVEL = "L4"

PROVIDERS = [
    Provider(
        name="UMD/GEOG",
        description="Department of Geographical Sciences, University of Maryland",
        url="https://geog.umd.edu/",
        roles=[ProviderRole.PRODUCER, ProviderRole.LICENSOR],
    ),
    Provider(
        name="NASA/GSFC",
        description="Goddard Space Flight Center, NASA",
        url="https://gsfc.nasa.gov",
        roles=[ProviderRole.PRODUCER, ProviderRole.LICENSOR],
    ),
    Provider(
        name="UTX-AUSTIN/CSR",
        description="Center for Space Research, University of Texas at Austin",
        url="http://www.csr.utexas.edu/",
        roles=[ProviderRole.PRODUCER, ProviderRole.LICENSOR],
    ),
    Provider(
        name="NASA/MAAP",
        description="The ESA-NASA Multi-Mission Algorithm and Analysis Platform",
        roles=[
            ProviderRole.PROCESSOR,
            ProviderRole.HOST,
        ],
        extra_fields={"processing:level": PROCESSING_LEVEL},
    ),
]

SUMMARIES = Summaries(
    summaries={
        "platform": [
            # list out platforms included in HLS
            "LANDSAT-8",
            "LANDSAT-9",
            "SENTINEL-2A",
            "SENTINEL-2B",
            # others
            "ICESat-2",
        ],
        "instruments": [
            "Advanced Topographic Laser Altimeter System",
            "Operational Land Imager",
            "Operational Land Imager 2",
            "Sentinel-2 Multispectral Imager",
        ],
        "mission": [
            "ABoVE",
        ],
        "gsd": {
            "minimum": 30,
            "maximum": 30,
        },
        "processing:level": [PROCESSING_LEVEL],
    }
)

KEYWORDS = ["BIOMASS", "VEGETATION HEIGHT"]


def format_year_range(temporal_interval: List[datetime]) -> str:
    """
    Format a year range string from temporal intervals.

    Args:
        temporal_intervals: List of [start_datetime, end_datetime] pairs

    Returns:
        str: Year range string (e.g., "2020" or "2020-2024")
    """

    start_date, end_date = temporal_interval

    start_year = start_date.year
    end_year = end_date.year

    if start_year == end_year:
        return str(start_year)
    else:
        return f"{start_year}-{end_year}"


COLLECTION_TITLE_PREFIX = (
    "Circumpolar boreal forest structure from ICESat-2 & HLS "
    f"({format_year_range(TEMPORAL_INTERVALS[0])} {VERSION})"
)
COLLECTION_TITLES = {
    Variable.AGB: f"{COLLECTION_TITLE_PREFIX}: 30m aboveground woody biomass density",
    Variable.HT: f"{COLLECTION_TITLE_PREFIX}: 30m vegetation height",
}

TILE_GPKG_BUCKET = "nasa-maap-data-store"
TILE_GPKG_KEY = "file-staging/nasa-map/boreal_tiles_v004.gpkg"
TILE_GPKG_HREF = f"s3://{TILE_GPKG_BUCKET}/{TILE_GPKG_KEY}"

THUMBNAIL_HREF_FORMAT = "https://raw.githubusercontent.com/MAAP-Project/icesat2-boreal-stac/refs/heads/main/assets/{variable}.png"

COLLECTION_ASSETS = {
    Variable.AGB: {
        "thumbnail": Asset(
            href=THUMBNAIL_HREF_FORMAT.format(variable=Variable.AGB),
            media_type=MediaType.PNG,
            roles=["thumbnail"],
            title="Thumbnail",
            description="Circumpolar view of model predictions",
        ),
        "tiles": Asset(
            href=TILE_GPKG_HREF,
            title="Processing tiles",
            description="90 km tile geometries for processing AGB predictions",
            media_type=MediaType.GEOPACKAGE,
            roles=["metadata"],
        ),
    },
    Variable.HT: {
        "thumbnail": Asset(
            href=THUMBNAIL_HREF_FORMAT.format(variable=Variable.HT),
            media_type=MediaType.PNG,
            roles=["thumbnail"],
            title="Thumbnail",
            description="Circumpolar view of model predictions",
        ),
        "tiles": Asset(
            href=TILE_GPKG_HREF,
            title="Processing tiles",
            description="90 km tile geometries for processing vegetation height "
            "predictions",
            media_type=MediaType.GEOPACKAGE,
            roles=["metadata"],
        ),
    },
}


REPOSITORY_LINK = Link(
    target="https://github.com/lauraduncanson/icesat2_boreal",
    rel="about",
    media_type=MediaType.HTML,
    title="icesat2_boreal GitHub repository",
)


TEXT = {
    Variable.AGB: {
        AssetType.COG: {
            "title": "Gridded predictions of aboveground biomass (Mg/ha)",
            "description": "Gridded predictions of aboveground biomass (Mg/ha)",
        },
        AssetType.TRAINING_DATA_PARQUET: {
            "description": "Tabular training data with latitude, longitude, and "
            "biomass observations",
        },
    },
    Variable.HT: {
        AssetType.COG: {
            "title": "Gridded predictions of vegetation height (m)",
            "description": "Gridded predictions of vegetation height (m)",
        },
        AssetType.TRAINING_DATA_PARQUET: {
            "description": "Tabular training data with latitude, longitude, and "
            "height observations",
        },
    },
}

RENDERS = {
    Variable.AGB: {
        "agb_viridis": Render(
            {
                "assets": [AssetType.COG],
                "title": "Aboveground biomass (Mg/ha)",
                "expression": "cog_b1",
                "rescale": [[0, 125]],
                "colormap_name": "viridis",
                "minmax_zoom": [6, 18],
            }
        ),
        "agb_gist_earth_r": Render(
            {
                "assets": [AssetType.COG],
                "title": "Aboveground biomass (Mg/ha)",
                "expression": "cog_b1",
                "rescale": [[0, 400]],
                "colormap_name": "gist_earth_r",
                "color_formula": "gamma r 1.05",
                "minmax_zoom": [6, 18],
            }
        ),
    },
    Variable.HT: {
        "ht_inferno": Render(
            {
                "assets": [AssetType.COG],
                "title": "Vegetation height (m)",
                "expression": "cog_b1",
                "rescale": [[0, 30]],
                "colormap_name": "inferno",
                "minmax_zoom": [6, 18],
            }
        )
    },
}


UNITS = {
    Variable.AGB: "Mg ha-1",
    Variable.HT: "m",
}

LAYER_NAME_SUFFIXES = {
    Variable.AGB: "agbd",
    Variable.HT: "ht",
}

ITEM_ASSET_PROPERTIES: Dict[AssetType, Dict[str, Any]] = {
    AssetType.COG: {
        "type": MediaType.COG,
        "roles": ["data"],
        "gsd": RESOLUTION,
        "processing:level": PROCESSING_LEVEL,
        "bands": [
            {
                "sampling": "area",
                "nodata": "nan",
                "scale": 1,
                "offset": 0,
                "data_type": "float32",
                "spatial_resolution": RESOLUTION,
            },
            {
                "sampling": "area",
                "nodata": "nan",
                "scale": 1,
                "offset": 0,
                "data_type": "float32",
                "spatial_resolution": RESOLUTION,
            },
        ],
    },
    AssetType.TRAINING_DATA_PARQUET: {
        "type": MediaType.PARQUET,
        "roles": ["data"],
        "title": "Tabular training data",
    },
}

LAYER_NAMES = ["mean_{label}", "std_{label}"]

ITEM_ASSETS = {
    variable: {
        asset_type: ItemAssetDefinition(
            {
                **ITEM_ASSET_PROPERTIES[asset_type],
                **TEXT[variable][asset_type],
                **(
                    {
                        "bands": [
                            {
                                "name": layer_name.format(
                                    label=LAYER_NAME_SUFFIXES[variable]
                                ),
                                "unit": UNITS[variable],
                                **band,
                            }
                            for band, layer_name in zip(
                                ITEM_ASSET_PROPERTIES[asset_type]["bands"],
                                LAYER_NAMES,
                                strict=False,
                            )
                        ]
                    }
                    if asset_type == AssetType.COG
                    else {}
                ),
            }
        )
        for asset_type in AssetType
    }
    for variable in Variable
}
