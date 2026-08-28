from typing import Any
import httpx
import json
import logging
import os
import secrets
from datetime import datetime, timezone

from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP

port = int(os.getenv("PORT", 8085))
SERVER_VERSION = "2.0.0"
AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN")
if not AUTH_TOKEN:
    raise RuntimeError("MCP_AUTH_TOKEN is required. Set it in the root .env file.")


class StaticTokenVerifier(TokenVerifier):
    """Verify the bearer token used by Claude Code and other MCP clients."""

    async def verify_token(self, token: str) -> AccessToken | None:
        if not secrets.compare_digest(token, AUTH_TOKEN):
            return None
        return AccessToken(
            token=token,
            client_id="weather-client",
            scopes=["weather:read"],
        )


mcp = FastMCP(
    "weather-personal",
    instructions=(
        "Personal weather server with real WeatherAPI data. "
        "Use get_current_weather_v2 for new clients; get_current_weather is kept for compatibility."
    ),
    host="0.0.0.0",
    port=port,
    auth=AuthSettings(
        issuer_url=f"http://localhost:{port}",
        resource_server_url=f"http://localhost:{port}",
        required_scopes=["weather:read"],
    ),
    token_verifier=StaticTokenVerifier(),
)

# Do not log WeatherAPI query strings because they contain the API key.
logging.getLogger("httpx").setLevel(logging.WARNING)

# Constants
WEATHERAPI_BASE = "https://api.weatherapi.com/v1"
USER_AGENT = "weather-app/1.0"

# Get API key from environment variable
API_KEY = os.getenv("WEATHERAPI_KEY")

async def make_weather_request(endpoint: str, params: dict[str, str]) -> dict[str, Any] | None:
    """Make a request to the WeatherAPI with proper error handling."""
    # Check if API key is set
    if not API_KEY:
        print("ERROR: WeatherAPI key not set. Please set WEATHERAPI_KEY environment variable.")
        return None
        
    headers = {
        "User-Agent": USER_AGENT,
    }
    # Add API key to parameters
    params["key"] = API_KEY
    
    url = f"{WEATHERAPI_BASE}/{endpoint}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error {e.response.status_code}: {e.response.text}")
            return None
        except httpx.RequestError as e:
            print(f"Request Error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

@mcp.tool()
async def get_current_weather(city: str) -> str:
    """[v1, deprecated] Get current weather as a human-readable string.

    Args:
        city: City name (e.g., "Hanoi", "Haiphong", "Danang", "Brisbane", "Sydney")
    """
    params = {
        "q": city,
        "aqi": "no"
    }
    
    data = await make_weather_request("current.json", params)

    if not data:
        if not API_KEY:
            return f"❌ WeatherAPI key not configured. Please set WEATHERAPI_KEY environment variable with your API key from weatherapi.com"
        return f"Unable to fetch current weather data for {city}. Please check the city name and API key configuration."

    current = data["current"]
    location = data["location"]
    
    return f"""
Current Weather for {location['name']}, {location['region']}, {location['country']}:

Temperature: {current['temp_c']}°C ({current['temp_f']}°F)
Feels like: {current['feelslike_c']}°C ({current['feelslike_f']}°F)
Condition: {current['condition']['text']}
Humidity: {current['humidity']}%
Wind: {current['wind_kph']} km/h ({current['wind_mph']} mph) {current['wind_dir']}
Pressure: {current['pressure_mb']} mb
UV Index: {current['uv']}
Visibility: {current['vis_km']} km

Last updated: {current['last_updated']}
"""


@mcp.tool()
async def get_current_weather_v2(
    city: str,
    units: str = "celsius",
) -> str:
    """[v2] Get current weather as versioned JSON without breaking v1 clients.

    Args:
        city: City name (for example, Hanoi or Danang).
        units: Temperature unit: "celsius" or "fahrenheit".
    """
    normalized_units = units.lower()
    if normalized_units not in {"celsius", "fahrenheit"}:
        return json.dumps(
            {
                "api_version": "2.0",
                "city": city,
                "error": "units must be 'celsius' or 'fahrenheit'",
            }
        )

    data = await make_weather_request("current.json", {"q": city, "aqi": "no"})
    if not data:
        return json.dumps(
            {
                "api_version": "2.0",
                "city": city,
                "error": "Unable to fetch weather data",
            }
        )

    current = data["current"]
    location = data["location"]
    use_fahrenheit = normalized_units == "fahrenheit"
    result = {
        "api_version": "2.0",
        "server_version": SERVER_VERSION,
        "location": {
            "name": location["name"],
            "region": location["region"],
            "country": location["country"],
            "localtime": location["localtime"],
        },
        "weather": {
            "temperature": current["temp_f"] if use_fahrenheit else current["temp_c"],
            "temperature_unit": "fahrenheit" if use_fahrenheit else "celsius",
            "feels_like": current["feelslike_f"] if use_fahrenheit else current["feelslike_c"],
            "condition": current["condition"]["text"],
            "humidity_percent": current["humidity"],
            "wind_kph": current["wind_kph"],
            "wind_direction": current["wind_dir"],
            "pressure_mb": current["pressure_mb"],
            "uv_index": current["uv"],
            "visibility_km": current["vis_km"],
        },
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }
    return json.dumps(result, ensure_ascii=False)

@mcp.tool()
async def get_forecast(city: str, days: int = 3) -> str:
    """Get weather forecast for a city.

    Args:
        city: City name (e.g., "Hanoi", "Haiphong", "Danang", "Brisbane", "Sydney", "Melbourne")
        days: Number of days to forecast (1-3 for free tier, max 10 for paid)
    """
    # Limit days to 3 for free tier
    days = min(days, 3)
    
    params = {
        "q": city,
        "days": str(days),
        "aqi": "no",
        "alerts": "no"
    }
    
    data = await make_weather_request("forecast.json", params)

    if not data:
        if not API_KEY:
            return f"❌ WeatherAPI key not configured. Please set WEATHERAPI_KEY environment variable with your API key from weatherapi.com"
        return f"Unable to fetch forecast data for {city}. Please check the city name and API key configuration."

    location = data["location"]
    forecast_days = data["forecast"]["forecastday"]
    
    forecasts = []
    forecasts.append(f"Weather Forecast for {location['name']}, {location['region']}, {location['country']}:")
    
    for day in forecast_days:
        day_data = day["day"]
        date = day["date"]
        
        forecast = f"""
{date}:
High: {day_data['maxtemp_c']}°C ({day_data['maxtemp_f']}°F)
Low: {day_data['mintemp_c']}°C ({day_data['mintemp_f']}°F)
Condition: {day_data['condition']['text']}
Chance of Rain: {day_data['daily_chance_of_rain']}%
Max Wind: {day_data['maxwind_kph']} km/h
UV Index: {day_data['uv']}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)

@mcp.tool()
async def health_check() -> str:
    """Health check endpoint for deployment verification."""
    return f"✅ Weather MCP Server v{SERVER_VERSION} is running with authentication."


@mcp.resource("server://info")
def server_info() -> str:
    """Publish server version, capabilities, and migration metadata."""
    return json.dumps(
        {
            "name": "weather-personal",
            "server_version": SERVER_VERSION,
            "transport": "streamable-http",
            "authentication": "bearer-token",
            "required_scopes": ["weather:read"],
            "capabilities": [
                "current-weather",
                "forecast-1-to-3-days",
                "versioned-json-response",
            ],
            "tools": {
                "get_current_weather": {
                    "version": "1.0",
                    "deprecated": True,
                    "replacement": "get_current_weather_v2",
                },
                "get_current_weather_v2": {
                    "version": "2.0",
                    "deprecated": False,
                },
                "get_forecast": {
                    "version": "1.0",
                    "deprecated": False,
                },
            },
        },
        ensure_ascii=False,
    )

print("✅ Secure Weather MCP server initialized with Streamable HTTP transport")
print("🔧 Available tools: get_current_weather, get_current_weather_v2, get_forecast, health_check")

if __name__ == "__main__":
    print(f"🚀 Starting MCP server on http://0.0.0.0:{port}/mcp")
    mcp.run(transport="streamable-http")
