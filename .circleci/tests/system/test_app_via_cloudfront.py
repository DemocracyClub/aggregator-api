import boto3
import os
import pytest
import requests
from tomlkit.toml_document import TOMLDocument
from tomlkit.toml_file import TOMLFile


def test_public_front_page_http_200(public_url):
    resp = requests.get(public_url)
    assert resp.status_code == 200


def test_cdn_front_page_http_200(cdn_url):
    resp = requests.get(cdn_url)
    assert resp.status_code == 200


def skip_discovery():
    return bool(os.environ.get("APP_URL"))


def cfn_output_value(stack, output_name):
    for op in stack.outputs:
        if op["OutputKey"] == output_name:
            # Cfn Outputs have unique per-stack names
            return op["OutputValue"]


@pytest.fixture(scope="session")
def public_url(deployed_cfn_stack):
    if skip_discovery():
        # FIXME: assert something about the format of PUBLIC_URL, e.g. matching 'https?://'
        return os.environ["PUBLIC_URL"]

    public_fqdn = cfn_output_value(deployed_cfn_stack, "PublicFqdn")
    assert public_fqdn
    return public_fqdn


@pytest.fixture(scope="session")
def cdn_url(deployed_cfn_stack):
    if skip_discovery():
        # FIXME: assert something about the format of CDN_URL, e.g. matching 'https?://'
        return os.environ["CDN_URL"]

    cdn_fqdn = cfn_output_value(deployed_cfn_stack, "CloudFrontDistributionFqdn")
    assert cdn_fqdn
    return f"https://{cdn_fqdn}"


@pytest.fixture(scope="session")
def deployed_cfn_stack(sam_cli_configuration):
    if skip_discovery():
        return None

    deploy = sam_cli_configuration.get("deploy")
    assert deploy
    params = deploy.get("parameters")
    assert params
    stack_name = params.get("stack_name")
    assert stack_name

    # 'region' /can/ be absent from the config file, in which case it'll
    # need to be present in the env (AWS_DEFAULT_REGION) or the user's AWS config files
    stack = boto3.resource("cloudformation", region_name=params.get("region")).Stack(
        stack_name
    )
    assert stack.stack_status  # 'assert stack' doesn't actually check stack presence!
    return stack


@pytest.fixture(scope="session")
def sam_cli_configuration():
    if skip_discovery():
        return None

    config_file_path = os.environ.get("SAM_CONFIG_FILE", "samconfig.toml")
    assert os.path.exists(config_file_path)
    config = TOMLFile(config_file_path).read()

    config_env = os.environ.get("SAM_PUBLIC_CONFIG_ENV", "default-public-access")
    assert config.get(config_env)
    return config[config_env]
