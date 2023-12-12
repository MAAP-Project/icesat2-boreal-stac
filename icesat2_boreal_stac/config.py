import tempfile

from pydantic_settings import BaseSettings, SettingsConfigDict


class IceSatBaseSettings(BaseSettings):
    """Base settings for icesat stac module"""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="ICESAT_")
    item_output_dir: str = '/tmp'
    COLLECTION_ID: str = "icesat2-boreal"
