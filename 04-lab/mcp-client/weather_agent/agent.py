"""Google ADK agent that consumes the authenticated local Weather MCP server."""
from google.adk import Agent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StreamableHTTPConnectionParams
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8085/mcp")
MCP_AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN")
if not MCP_AUTH_TOKEN:
    raise RuntimeError("MCP_AUTH_TOKEN is required. Load the root .env with activate.sh.")

logger.info("🌐 Initializing weather agent with MCP server: %s", MCP_SERVER_URL)

connection_params = StreamableHTTPConnectionParams(
    url=MCP_SERVER_URL,
    headers={"Authorization": f"Bearer {MCP_AUTH_TOKEN}"},
    timeout=30.0,
)

weather_tools = McpToolset(connection_params=connection_params)

# Fail loudly when MCP is unavailable; silently running without tools would not
# satisfy this lab's end-to-end requirement.
root_agent = Agent(
    name="weather_agent",
    model="gemini-3.6-flash",
    tools=[weather_tools],
)

logger.info(
    "✅ Weather MCP tools configured: v1, v2, forecast, and health_check"
)

