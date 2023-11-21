#!/usr/bin/env python3

from setuptools import setup

setup(
    name="dc_api_common",
    version="0.0.3",
    description="Common elements to the DC API",
    author="Sym Roe",
    author_email="sym.roe@democracyclub.org.uk",
    setup_requires=["wheel"],
    packages=["common"],
    package_dir={"common": "."},
    install_requires=[
        "httpx[http2]==0.23.0",
        "mangum==0.17.0",
        "starlette==0.26.1",
        "dc_logging_utils @ https://github.com/DemocracyClub/dc_logging/archive/refs/tags/1.0.2.tar.gz",
        "sentry-sdk[starlette]",
        "urllib3<2.0.0",
    ],
)
