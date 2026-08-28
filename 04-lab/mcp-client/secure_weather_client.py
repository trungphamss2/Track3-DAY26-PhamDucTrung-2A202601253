"""Verify auth, version metadata, and backward compatibility of the Weather MCP server."""

from __future__ import annotations

import asyncio
import json
import os

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8085/mcp")
VALID_TOKEN = os.getenv("MCP_AUTH_TOKEN")
if not VALID_TOKEN:
    raise RuntimeError("MCP_AUTH_TOKEN is required. Load the root .env with activate.sh.")


async def auth_status(token: str | None) -> int:
    """Return the HTTP status for an MCP endpoint request with optional auth."""
    headers = {"Accept": "application/json, text/event-stream"}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    async with httpx.AsyncClient() as client:
        response = await client.get(SERVER_URL, headers=headers, timeout=10.0)
        return response.status_code


async def verify_authorization() -> None:
    missing_status = await auth_status(None)
    invalid_status = await auth_status("invalid-token")
    print(f"Missing token: HTTP {missing_status}")
    print(f"Invalid token: HTTP {invalid_status}")
    if missing_status not in {401, 403} or invalid_status not in {401, 403}:
        raise RuntimeError("Missing and invalid tokens must be rejected with HTTP 401/403")


async def verify_valid_client() -> None:
    http_client = httpx.AsyncClient(
        headers={"Authorization": f"Bearer {VALID_TOKEN}"},
    )
    async with http_client:
        async with streamable_http_client(
            SERVER_URL,
            http_client=http_client,
        ) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()

                info = await session.read_resource("server://info")
                metadata = json.loads(info.contents[0].text)
                print(
                    f"Authorized: weather-personal v{metadata['server_version']} "
                    f"({metadata['transport']})"
                )

                tools = await session.list_tools()
                tool_names = {tool.name for tool in tools.tools}
                print("Tools:", ", ".join(sorted(tool_names)))

                # Old clients keep using the unchanged v1 tool.
                legacy = await session.call_tool(
                    "get_current_weather",
                    {"city": "Hanoi"},
                )
                if "Current Weather" not in legacy.content[0].text:
                    raise RuntimeError("Legacy v1 client no longer receives its expected string format")
                print("Legacy v1 client: OK")

                forecast = await session.call_tool(
                    "get_forecast",
                    {"city": "Hanoi", "days": 2},
                )
                if "Weather Forecast for Hanoi" not in forecast.content[0].text:
                    raise RuntimeError("Forecast tool returned an unexpected result")
                print("Forecast arguments city=Hanoi, days=2: OK")

                # New clients inspect metadata and select the replacement tool.
                v1_metadata = metadata["tools"]["get_current_weather"]
                replacement = v1_metadata.get("replacement")
                selected_tool = (
                    replacement
                    if v1_metadata.get("deprecated") and replacement in tool_names
                    else "get_current_weather"
                )

                modern = await session.call_tool(
                    selected_tool,
                    (
                        {"city": "Hanoi", "units": "celsius"}
                        if selected_tool == "get_current_weather_v2"
                        else {"city": "Hanoi"}
                    ),
                )
                if selected_tool == "get_current_weather_v2":
                    result = json.loads(modern.content[0].text)
                    if result.get("api_version") != "2.0":
                        raise RuntimeError("v2 tool did not return the expected API version")
                    print(f"Modern client selected {selected_tool}: API v{result['api_version']} OK")
                elif "Current Weather" in modern.content[0].text:
                    print("Modern client fell back to get_current_weather v1: OK")
                else:
                    raise RuntimeError("Fallback v1 tool returned an unexpected result")


async def main() -> None:
    await verify_authorization()
    await verify_valid_client()
    print("All secure Weather MCP checks passed.")


if __name__ == "__main__":
    asyncio.run(main())
