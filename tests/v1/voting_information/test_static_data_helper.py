import polars as pl
import pytest
from starlette.datastructures import Headers
from starlette.requests import Request
from static_data_helper import (
    DuplicateUPRNError,
    MultipleAddressbaseSourceError,
    StaticDataHelper,
)


class MockStaticDataHelper(StaticDataHelper):
    def get_file_path(self):
        return "test/path.parquet"

    def get_bucket_name(self):
        return "test-bucket"

    def query_to_dict(self, query_data):
        return query_data.to_dicts()


@pytest.fixture
def mock_request():
    return Request(
        {
            "type": "http",
            "path": "/test",
            "server": ("example.com", 443),
            "scheme": "https",
            "headers": Headers().raw,
        }
    )


@pytest.fixture
def mock_static_data_helper(mock_request):
    return MockStaticDataHelper(mock_request, postcode="AA1 1AA")


class TestDataQualityCheck:
    def test_valid_data(self, mock_static_data_helper):
        df = pl.DataFrame(
            {
                "uprn": ["100", "200", "300"],
                "address": ["1 Test St", "2 Test St", "3 Test St"],
                "postcode": ["AA1 1AA", "AA1 1AA", "AA1 1AA"],
                "addressbase_source": [
                    "s3://test/",
                    "s3://test/",
                    "s3://test/",
                ],
            }
        )

        # Should not raise any exception
        mock_static_data_helper.data_quality_check(df)

    def test_raises_duplicate_uprn_error(self, mock_static_data_helper):
        df = pl.DataFrame(
            {
                "uprn": ["100", "100", "200"],
                "address": ["1 Test St", "1 Test St", "2 Test St"],
                "postcode": ["AA1 1AA", "AA1 1AA", "AA1 1AA"],
                "addressbase_source": [
                    "s3://test/",
                    "s3://test/",
                    "s3://test/",
                ],
            }
        )

        with pytest.raises(DuplicateUPRNError) as exc_info:
            mock_static_data_helper.data_quality_check(df)

        error_message = str(exc_info.value)
        assert (
            error_message
            == "Duplicate UPRNs found for postcode AA1 1AA: ['100']"
        )

    def test_duplicate_uprn_error_lists_all_duplicates(
        self, mock_static_data_helper
    ):
        # What happens when we have more than one duplicate uprn
        df = pl.DataFrame(
            {
                "uprn": ["100", "100", "200", "200", "300"],
                "address": [
                    "1 Test St",
                    "1 Test St",
                    "2 Test St",
                    "2 Test St",
                    "3 Test St",
                ],
                "postcode": [
                    "AA1 1AA",
                    "AA1 1AA",
                    "AA1 1AA",
                    "AA1 1AA",
                    "AA1 1AA",
                ],
                "addressbase_source": [
                    "s3://test/",
                    "s3://test/",
                    "s3://test/",
                    "s3://test/",
                    "s3://test/",
                ],
            }
        )

        with pytest.raises(DuplicateUPRNError) as exc_info:
            mock_static_data_helper.data_quality_check(df)

        error_message = str(exc_info.value)
        assert (
            error_message
            == "Duplicate UPRNs found for postcode AA1 1AA: ['100', '200']"
        )

    def test_raises_multiple_addressbase_source_error(
        self, mock_static_data_helper
    ):
        df = pl.DataFrame(
            {
                "uprn": ["100", "200", "300"],
                "address": ["1 Test St", "2 Test St", "3 Test St"],
                "postcode": ["AA1 1AA", "AA1 1AA", "AA1 1AA"],
                "addressbase_source": [
                    "s3://source1/",
                    "s3://source2/",
                    "s3://source1/",
                ],
            }
        )

        with pytest.raises(MultipleAddressbaseSourceError) as exc_info:
            mock_static_data_helper.data_quality_check(df)

        error_message = str(exc_info.value)
        assert (
            error_message
            == "Multiple addressbase sources found for postcode AA1 1AA: ['s3://source1/', 's3://source2/']"
        )

    def test_duplicate_uprn_checked_before_addressbase_source(
        self, mock_static_data_helper
    ):
        df = pl.DataFrame(
            {
                "uprn": ["100", "100", "200"],
                "address": ["1 Test St", "1 Test St Dup", "2 Test St"],
                "postcode": ["AA1 1AA", "AA1 1AA", "AA1 1AA"],
                "addressbase_source": [
                    "s3://source1/",
                    "s3://source2/",
                    "s3://source1/",
                ],
            }
        )

        with pytest.raises(DuplicateUPRNError) as exc_info:
            mock_static_data_helper.data_quality_check(df)

        error_message = str(exc_info.value)
        assert (
            error_message
            == "Duplicate UPRNs found for postcode AA1 1AA: ['100']"
        )

    def test_passes_for_empty_dataframe(self, mock_static_data_helper):
        df = pl.DataFrame(
            {
                "uprn": [],
                "address": [],
                "postcode": [],
                "addressbase_source": [],
            }
        )
        # Doesn't raise an exception
        mock_static_data_helper.data_quality_check(df)
