#!/usr/bin/env python3
"""Check the local Weather ADK/MCP environment without printing secrets."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path


REQUIRED_ENV = ("GOOGLE_API_KEY", "WEATHERAPI_KEY", "MCP_AUTH_TOKEN")
REQUIRED_PACKAGES = ("google.adk", "mcp", "fastmcp", "httpx", "dotenv")
REQUIRED_FILES = (
    Path("weather_agent/agent.py"),
    Path("weather_agent/__init__.py"),
    Path("secure_weather_client.py"),
)


def main() -> int:
    ok = True
    print("Weather Agent setup check")

    for name in REQUIRED_ENV:
        configured = bool(os.getenv(name))
        print(f"{'OK' if configured else 'MISSING'} env: {name}")
        ok &= configured

    for package in REQUIRED_PACKAGES:
        installed = importlib.util.find_spec(package) is not None
        print(f"{'OK' if installed else 'MISSING'} package: {package}")
        ok &= installed

    for path in REQUIRED_FILES:
        exists = path.is_file()
        print(f"{'OK' if exists else 'MISSING'} file: {path}")
        ok &= exists

    if ok:
        print("Setup is ready. Run secure_weather_client.py while the MCP server is active.")
        return 0

    print("Setup is incomplete. From Git Bash, run: source ../../activate.sh")
    return 1


if __name__ == "__main__":
    sys.exit(main())
