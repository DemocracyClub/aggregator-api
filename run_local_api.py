import argparse
import asyncio
import sys
from pathlib import Path

import uvicorn

COMMON_ROOT = "api/"
ENDPOINTS_ROOT = "api/endpoints/v1"
sys.path.insert(0, COMMON_ROOT)


async def create_webserver(app, options):
    server = uvicorn.run(app, **options)
    await server.serve()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Run a single API app",
        description="Wraps Uvicorn to run single functions",
    )
    functions = {
        path.name: path
        for path in Path(ENDPOINTS_ROOT).glob("*")
        if path.is_dir() and not path.name.startswith("_")
    }

    parser.add_argument(
        "--function",
        choices=functions,
        action="store",
        help="Name of the function to run",
        required=True,
    )
    parser.add_argument(
        "--port", action="store", help="Port to run on", default=8000, type=int
    )

    args = parser.parse_args()
    path = str(functions[args.function])
    sys.path.insert(0, path)
    python_path = path.replace("/", ".")
    options = {
        "port": args.port,
        "log_level": "debug",
        "reload": True,
        "reload_dirs": [path, COMMON_ROOT],
    }
    app = f"{python_path}.app:app"
    asyncio.run(create_webserver(app, options))
