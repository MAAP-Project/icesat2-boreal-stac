"""Constants for icesat2_boreal_stac"""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, Set

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


class Variable(str, Enum):
    """Enumeration of the different variables"""

    AGB = "agb"
    HT = "ht"


class AssetType(str, Enum):
    """Enumeration of all possible asset types that should be present"""

    COG = "cog"
    # MODEL = "model"
    TRAINING_DATA_CSV = "training_data_csv"

    def get_file_pattern(self) -> str:
        """Returns the file pattern for this asset type"""
        patterns = {
            self.COG: ".tif",
            self.TRAINING_DATA_CSV: "_train_data.csv",
        }
        return patterns[self]

    def matches_file(self, filename: str) -> bool:
        """Check if the given filename matches this asset type's pattern"""
        return filename.endswith(self.get_file_pattern())

    @classmethod
    def required_assets(cls) -> Set[str]:
        """Returns set of all required asset types"""
        return {member.value for member in cls}


VERSION = "v2.1"
COLLECTION_ID_FORMAT = "icesat2-boreal-{version}-{variable}"

CSV_MEDIA_TYPE = "text/csv"

RESOLUTION = 30
BBOX = [-180, 51.6, 180, 78]
TEMPORAL_INTERVALS = [
    [
        datetime(2020, 1, 1, tzinfo=timezone.utc),
        datetime(2021, 1, 1, tzinfo=timezone.utc) - timedelta(seconds=1),
    ]
]

LICENSE = "CC-BY"

COLLECTION_DESCRIPTION = """This dataset provides predictions of woody Aboveground
Biomass Density (AGBD) and vegetation height for high northern latitude forests at a
30-m spatial resolution. It is designed both for circumpolar boreal-wide mapping and
filling the northern spatial data gap from NASA's Global Ecosystem Dynamics
Investigation (GEDI) mission. Mapping woody AGBD and height is essential for
understanding, monitoring, and managing forest carbon stocks and fluxes. The
AGBD and height predictions cover the extent of high latitude boreal forests and
shrublands, and extend southward outside the boreal domain to 51.6°N. These maps
represent conditions in 2020.

ICESat-2 ATL08 represented the training data for these mapped products, with
ATL08’s maximum height (h_canopy) used to train the height product, and
estimates of 30-m AGBD from ATL08 used to train the AGBD product. AGBD and
vegetation models were developed using local moving window models, with models
produced for a suite of 90 km tiles.

Prediction of AGBD involved two modeling steps: (1) regression with ordinary
least squares (OLS) to relate field plot measurements of AGBD to NASA's ICESat-2
30-m ATL08 lidar samples, and (2) machine learning modeling with random forest
to extend estimates beyond the field plots by relating ICESat-2 AGBD predictions
to wall-to-wall gridded covariate stacks from Harmonized Landsat/Sentinel-2
(HLS) and the Copernicus GLO30 DEM. Per-pixel uncertainties are estimated from
bootstrapping both models.

Prediction of vegetation height used the second of the two steps for AGBD, since
what would otherwise be the dependent variable (height) is a direct measurement
from ICESat-2 ATL08. Uncertainty was therefore estimated from bootstrapping the
random forest model, with no propagation of any uncertainties from the ICESat-2
height measurements.

Uncertainties were estimated using bootstrapping of training data to produce a
suite of models and maps, which were then summarized to produce pixel-level
standard error estimates. Models were re-fit for each 90 km tile until the
variance of the 90 km AGBD total stabilized (less than 5% change in the variance
of tile total AGBD). The pixel-level SD is calculated as the SD of the set of
pixel predictions from these iterations.

This dataset features predictions for landcovers that are associated with the
full woody structure gradient according to the European Space Agency’s
Worldcover v1.0 2020 dataset. This primarily includes forests, shrubs, and grass
extents in which woody vegetation is present. Importantly, predictions were also
made for the ‘moss/lichen’ land cover. The decision to include these pixels
considered the broad domain of this study, where areas from the far north down
to southern portions featured this classification, but represented very
different apparent land uses. In northern portions, this classification occurs
frequently across tundra extents (eg, the Brooks Range), whereas in the south it
appears at sites of recent forest clearing. Non-vegetated land covers (e.g.
built up, water, rock, ice) were masked out of our predictions.

HLS composites and ICESat-2 data were from 2020 to produce a single-year 2020
map. ICESat-2 data were filtered to include only strong beams, growing seasons
(June through September), solar elevations less than 5 degrees, snow free land
(snow flag set to 1), and "msw_flag" equal to 0 (clear skies and no observed
atmospheric scattering). ICESat-2's ATL08 product was resampled to a 30-m
spatial resolution to better match both the field plots and mapped pixels, which
involved reprocessing the nominal 100-m segments to 30-m segments. HLS data
(both the L30 and S30 products) were used to create a harmonized (HLSH30)
greenest pixel composite of growing season multispectral data, which was then
used to compute a suite of vegetation indices: NDVI, NDWI, NBR, NBR2, TCW, TCG.
These were then used, in combination with a suite of topographic information
(elevation, slope, topographic solar radiation index, topographic position
index, and a binary slope mask indicating flat pixels) from the Copernicus DEM
product, to predict 30-m AGBD per 90-km tile. Estimates of mean AGBD and mean
vegetation height with standard deviation are provided in cloud-optimized
GeoTIFF (CoG) format. The product consists of a set of raster grids and tabular
(CSV) files referenced to a set of 90-km tiles that cover the circumpolar boreal
domain and south to 51.6°N (Figure 1). Each raster grid is a 2-band file where
the first and second band represent the mean and standard deviation pixel values
that result from the bootstrapped prediction. The CSV files feature the ICESat-2
ATL08 30 m segment centroids that were used as training data in the prediction
of each raster. A polygon map of these data tiles is included as a GeoPackage
file and a Shapefile. This product was generated on the NASA-ESA Multi-Mission
Algorithm and Analysis Platform (MAAP, https://scimaap.net), an open science
platform. All code and input files are publicly available:
[https://github.com/lauraduncanson/icesat2_boreal.git](https://repo.ops.maap-project.org/icesat2_boreal/icesat2_boreal.git).

For each product (AGB and height) there are 3902 cloud-optimized GeoTIFFs, 3902 tables
in comma-separated values (CSV) format, and 1 geopackage tile index."""

COLLECTION_CITATION = """Duncanson, L., P.M. Montesano, A. Neuenschwander, A.
Zarringhalam, N. Thomas, A. Mandel, D. Minor, E. Guenther, S. Hancock, T. Feng, A.
Barciauskas, G.W. Chang, S. Shah, and B.P. Satorius. Circumpolar boreal aboveground
biomass mapping with ICESat-2. (in prep.)"""

PROVIDERS = [
    Provider(
        name="MAAP",
        description="The MAAP platform is designed to combine data, algorithms, and "
        "computational abilities for the processing and sharing of data related to "
        "NASA’s GEDI, ESA’s BIOMASS, and NASA/ISRO’s NISAR missions",
        url="https://maap-project.org",
        roles=[ProviderRole.PROCESSOR, ProviderRole.PRODUCER],
        extra_fields={"processing:level": "L4"},
    )
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
    }
)

KEYWORDS = ["BIOMASS", "VEGETATION HEIGHT"]

COLLECTION_TITLES = {
    Variable.AGB: "Icesat2 Boreal v2.1: Gridded Aboveground Biomass Density",
    Variable.HT: "Icesat2 Boreal v2.1: Vegetation Height",
}

COLLECTION_ASSETS = {
    Variable.AGB: {
        "tiles": Asset(
            href="s3://nasa-maap-data-store/file-staging/nasa-map/icesat2-boreal-v2.1/agb/boreal_tiles_v004_AGB_H30_2020_ORNLDAAC.gpkg",
            title="Processing tiles",
            description="90 km tile geometries for processing AGB predictions",
            media_type=MediaType.GEOPACKAGE,
            roles=["metadata"],
        )
    },
    Variable.HT: {
        "tiles": Asset(
            href="s3://nasa-maap-data-store/file-staging/nasa-map/icesat2-boreal-v2.1/ht/boreal_tiles_v004_HT_H30_2020_ORNLDAAC.gpkg",
            title="Processing tiles",
            description="90 km tile geometries for processing vegetation height "
            "predictions",
            media_type=MediaType.GEOPACKAGE,
            roles=["metadata"],
        )
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
        AssetType.TRAINING_DATA_CSV: {
            "description": "Tabular training data with latitude, longitude, and "
            "biomass observations",
        },
    },
    Variable.HT: {
        AssetType.COG: {
            "title": "Gridded predictions of vegetation height (m)",
            "description": "Gridded predictions of vegetation height (m)",
        },
        AssetType.TRAINING_DATA_CSV: {
            "description": "Tabular training data with latitude, longitude, and "
            "height observations",
        },
    },
}

RENDERS = {
    Variable.AGB: {
        "agb_viridis": Render(
            {
                "title": "Aboveground biomass (Mg/ha)",
                "expression": "cog_b1",
                "rescale": [[0, 125]],
                "colormap_name": "viridis",
                "minmax_zoom": [6, 18],
            }
        ),
        "agb_gist_earth_r": Render(
            {
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
                "title": "Vegetation height (m)",
                "expression": "cog_b1",
                "rescale": [[0, 30]],
                "colormap_name": "inferno",
                "minmax_zoom": [6, 18],
            }
        )
    },
}


ITEM_ASSET_PROPERTIES: Dict[AssetType, Dict[str, Any]] = {
    AssetType.COG: {
        "type": MediaType.COG,
        "roles": ["data"],
        "gsd": RESOLUTION,
    },
    AssetType.TRAINING_DATA_CSV: {
        "type": CSV_MEDIA_TYPE,
        "roles": ["data"],
        "title": "Tabular training data",
    },
}

ITEM_ASSETS = {
    variable: {
        asset_type: ItemAssetDefinition(
            {
                **ITEM_ASSET_PROPERTIES[asset_type],
                **TEXT[variable][asset_type],
            }
        )
        for asset_type in AssetType
    }
    for variable in Variable
}
