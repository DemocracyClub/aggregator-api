#!/usr/bin/env python3

from setuptools import setup

setup(
    name="dc_api_common",
    version="0.0.2",
    description="Common elements to the DC API",
    author="Sym Roe",
    author_email="sym.roe@democracyclub.org.uk",
    setup_requires=["wheel"],
    packages=["common"],
    package_dir={"common": "."},
    install_requires=[
        "httpx[http2]==0.23.0",
        "mangum==0.17.0",
        "starlette==0.27.0",
        "dc_logging_utils@https://github.com/DemocracyClub/dc_logging/archive/refs/tags/0.0.10.tar.gz",
        "sentry-sdk[starlette]",
        "urllib3<2.0.0",
    ],
)
