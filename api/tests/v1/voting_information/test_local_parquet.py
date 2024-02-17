from parl_boundary_changes.client import ParlBoundaryChangeApiClient


def test_parquet(vi_app_client):
    client = ParlBoundaryChangeApiClient(vi_app_client, postcode="GL5 1NA")
    client.postcode_response()

    client = ParlBoundaryChangeApiClient(vi_app_client, postcode="SE22 8DJ")
    client.postcode_response()

    client = ParlBoundaryChangeApiClient(
        vi_app_client, postcode="GL5 1NA", uprn=100120527685
    )
    client.uprn_response()
