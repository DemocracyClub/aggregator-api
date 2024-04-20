#!/usr/bin/env python3

from setuptools import setup

setup(
    name="dc_api_common",
    version="0.0.4",
    description="Common elements to the DC API",
    author="Sym Roe",
    author_email="sym.roe@democracyclub.org.uk",
    setup_requires=["wheel"],
    packages=["common"],
    package_dir={"common": "."},
    install_requires=[
        "httpx[http2]==0.26.0",
        "mangum==0.17.0",
        "starlette==0.36.2",
        "dc-logging-utils @ git+https://github.com/DemocracyClub/dc_logging.git@1.0.2",
        "sentry-sdk[starlette]",
        "urllib3<2.0.0",
        "polars==0.20.21",
    ],
)
