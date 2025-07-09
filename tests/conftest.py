"""Test configuration"""

import os

import pytest


@pytest.fixture()
def cog_key():
    """Local cog key"""
    return (
        "file://"
        + os.path.dirname(__file__)
        + "/data/boreal_ht_2020_202501131736787421_0000004.tif"
    )


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture()
def test_cog_key():
    """A fake S3 key for a COG"""
    return "test/path/example.tif"


@pytest.fixture()
def test_bad_cog_key():
    """A fake S3 key for a COG without the other required assets"""
    return "test/badpath/example.tif"


@pytest.fixture(scope="function")
def stac_v1_0_0():
    """Set a custom environment variable for testing."""
    var = "PYSTAC_STAC_VERSION_OVERRIDE"
    original_value = os.getenv(var)

    os.environ[var] = "1.0.0"

    yield

    if original_value is not None:
        os.environ[var] = original_value
    else:
        del os.environ[var]
