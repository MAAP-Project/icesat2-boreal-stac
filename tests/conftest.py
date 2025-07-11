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
