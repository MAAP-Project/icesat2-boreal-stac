"""Constants for icesat2_boreal_stac"""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Set

VERSION = "v2.1"
COLLECTION_ID_FORMAT = "icesat2-boreal-{version}-{variable}"

RDS_MEDIA_TYPE = "application/x-rds"
CSV_MEDIA_TYPE = "text/csv"

RASTER_SIZE = 3000
BBOX = [-180, 51.6, 180, 78]
TEMPORAL_INTERVALS = [
    [
        datetime(2020, 1, 1, tzinfo=timezone.utc),
        datetime(2021, 1, 1, tzinfo=timezone.utc) - timedelta(seconds=1),
    ]
]


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
            # self.MODEL: "_model.Rds",
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
