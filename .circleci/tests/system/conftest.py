import os
import secrets

import boto3
import pytest
from tomlkit.toml_file import TOMLFile

from common.auth_models import User


@pytest.fixture(scope="function")
def tmp_api_user():
    api_key = secrets.token_urlsafe(16)
    user_id = secrets.token_urlsafe(16)
    user = User(api_key=api_key, user_id=user_id, key_type="development")
    user.save()
    yield user
    user.delete()


def skip_discovery():
    return bool(os.environ.get("APP_URL"))


def cfn_output_value(stack, output_name):
    for op in stack.outputs:
        if op["OutputKey"] == output_name:
            # Cfn Outputs have unique per-stack names
            return op["OutputValue"]
    return None


@pytest.fixture(scope="session")
def frontend_url(deployed_api_gateway_stack):
    if skip_discovery():
        # FIXME: assert something about the format of APP_URL, e.g. matching 'https?://'
        return os.environ["APP_URL"]

    app_fqdn = cfn_output_value(
        deployed_api_gateway_stack, "AggregatorApiFrontendFqdn"
    )
    assert app_fqdn
    return f"https://{app_fqdn}/Prod/"


@pytest.fixture(scope="session")
def api_url(deployed_api_gateway_stack):
    if skip_discovery():
        # FIXME: assert something about the format of APP_URL, e.g. matching 'https?://'
        return os.environ["APP_URL"]

    app_fqdn = cfn_output_value(deployed_api_gateway_stack, "AggregatorApiFqdn")
    assert app_fqdn
    return f"https://{app_fqdn}/Prod/"


@pytest.fixture(scope="session")
def deployed_public_cfn_stack(sam_cli_public_access_configuration):
    if skip_discovery():
        return None

    deploy = sam_cli_public_access_configuration.get("deploy")
    assert deploy
    params = deploy.get("parameters")
    assert params
    stack_name = params.get("stack_name")
    assert stack_name

    # 'region' /can/ be absent from the config file, in which case it'll
    # need to be present in the env (AWS_DEFAULT_REGION) or the user's AWS config files
    stack = boto3.resource(
        "cloudformation", region_name=params.get("region")
    ).Stack(stack_name)
    assert (
        stack.stack_status
    )  # 'assert stack' doesn't actually check stack presence!
    return stack


@pytest.fixture(scope="session")
def deployed_api_gateway_stack(sam_cli_api_gateway_configuration):
    if skip_discovery():
        return None

    deploy = sam_cli_api_gateway_configuration.get("deploy")
    assert deploy
    params = deploy.get("parameters")
    assert params
    stack_name = params.get("stack_name")
    assert stack_name

    # 'region' /can/ be absent from the config file, in which case it'll
    # need to be present in the env (AWS_DEFAULT_REGION) or the user's AWS config files
    stack = boto3.resource(
        "cloudformation", region_name=params.get("region")
    ).Stack(stack_name)
    assert (
        stack.stack_status
    )  # 'assert stack' doesn't actually check stack presence!
    return stack


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

    cdn_fqdn = cfn_output_value(
        deployed_cfn_stack, "CloudFrontDistributionFqdn"
    )
    assert cdn_fqdn
    return f"https://{cdn_fqdn}"


@pytest.fixture(scope="session")
def deployed_cfn_stack(sam_cli_public_access_configuration):
    if skip_discovery():
        return None

    deploy = sam_cli_public_access_configuration.get("deploy")
    assert deploy
    params = deploy.get("parameters")
    assert params
    stack_name = params.get("stack_name")
    assert stack_name

    # 'region' /can/ be absent from the config file, in which case it'll
    # need to be present in the env (AWS_DEFAULT_REGION) or the user's AWS config files
    stack = boto3.resource(
        "cloudformation", region_name=params.get("region")
    ).Stack(stack_name)
    assert (
        stack.stack_status
    )  # 'assert stack' doesn't actually check stack presence!
    return stack


@pytest.fixture(scope="session")
def sam_cli_public_access_configuration():
    if skip_discovery():
        return None

    config_file_path = os.environ.get("SAM_CONFIG_FILE", "samconfig.toml")
    assert os.path.exists(config_file_path)
    config = TOMLFile(config_file_path).read()

    config_env = os.environ.get(
        "SAM_PUBLIC_CONFIG_ENV", "default-public-access"
    )
    return config[config_env]


@pytest.fixture(scope="session")
def sam_cli_api_gateway_configuration():
    if skip_discovery():
        return None

    config_file_path = os.environ.get("SAM_CONFIG_FILE", "samconfig.toml")
    assert os.path.exists(config_file_path)
    config = TOMLFile(config_file_path).read()

    config_env = os.environ.get("SAM_LAMBDA_CONFIG_ENV", "default")
    return config[config_env]
