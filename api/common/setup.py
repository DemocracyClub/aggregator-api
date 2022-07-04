#!/usr/bin/env python3

from setuptools import setup

setup(
    name="dc_api_common",
    version="0.0.1",
    description="Common elements to the DC API",
    author="Sym Roe",
    author_email="sym.roe@democracyclub.org.uk",
    setup_requires=["wheel"],
<<<<<<< HEAD
    packages=["common"],
    package_dir={"common": "."},
=======
    packages=["."],
>>>>>>> 90caa5a (New Starlette based APIs)
    install_requires=[
        "httpx==0.23.0",
        "mangum==0.15.0",
        "starlette==0.19.1",
    ],
)
