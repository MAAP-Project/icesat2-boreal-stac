import os

import boto3
import pytest
from moto import mock_aws


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
    return "test/path/example.tif"


@pytest.fixture
def test_bucket(aws_credentials, test_cog_key):
    """Fixture that creates a mock S3 bucket with test data"""
    with mock_aws():
        s3 = boto3.client("s3")
        bucket_name = "test-bucket"
        s3.create_bucket(Bucket=bucket_name)

        # Create test files
        test_files = {
            test_cog_key: b"fake tif content",
            "test/path/example_model.Rds": b"fake model content",
            "test/path/example_train_data.csv": b"fake training data",
            "test/path/output.context.json": b"{}",
            "test/path/output.dataset.json": b"{}",
            "test/path/output.met.json": b"{}",
        }

        for key, content in test_files.items():
            s3.put_object(Bucket=bucket_name, Key=key, Body=content)

        yield bucket_name
