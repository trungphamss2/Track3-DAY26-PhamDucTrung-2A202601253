# Lab 04 — Weather Agent with Remote MCP Server

A weather agent built with Google ADK that connects to an MCP server via Streamable HTTP transport.

## Architecture

```
┌─────────────────┐  HTTP + Bearer token ┌─────────────────┐      REST       ┌─────────────────┐
│ ADK/Claude Code │ ──────────────────── │   MCP Server    │ ─────────────── │  WeatherAPI.com │
│  (MCP clients)  │   localhost:8085/mcp │ + TokenVerifier │                 │                 │
└─────────────────┘                      └─────────────────┘                 └─────────────────┘
```

## Tools

| Tool | Description |
|------|-------------|
| `get_current_weather(city)` | v1 string response, kept for old clients |
| `get_current_weather_v2(city, units)` | v2 versioned JSON response for new clients |
| `get_forecast(city, days)` | Get weather forecast (1–3 days) |
| `health_check()` | Verify server is running |

The same server also exposes `server://info`, which publishes the server version,
capabilities, and the migration path from the deprecated v1 tool to v2.

## Assignment mapping (Easy → Medium → Hard)

This lab evolves one real Weather MCP Server instead of using unrelated demos:

1. **Easy — real tools:** `get_current_weather` and `get_forecast` call WeatherAPI.com.
2. **Medium — authentication:** the same server uses Streamable HTTP and a
   `TokenVerifier`. Missing or invalid bearer tokens are rejected with HTTP 401/403.
3. **Hard — versioning:** the v1 tool remains available, v2 returns a new JSON
   format, and `server://info` lets a new client select the replacement tool.

### Verify auth and versioning

Start the server in terminal 1 (Git Bash):

```bash
cd /d/LABS_TRACK3/Day26-MCP-Tools-Integration
source ./activate.sh
cd 04-lab/mcp-server
.venv/Scripts/python weather.py
```

Run the verification client in terminal 2:

```bash
cd /d/LABS_TRACK3/Day26-MCP-Tools-Integration
source ./activate.sh
cd 04-lab/mcp-client
.venv/Scripts/python secure_weather_client.py
```

The client verifies missing token, invalid token, valid token, the legacy v1
tool, `server://info`, and automatic selection of the v2 tool.

### Register in Claude Code

Keep the server running, then register it locally from Git Bash:

```bash
claude mcp add --transport http --scope local weather-personal \
  http://localhost:8085/mcp \
  --header "Authorization: Bearer $MCP_AUTH_TOKEN"

claude mcp get weather-personal
```

If Claude Code has not been authenticated on this machine, run `claude` and use
`/login` once. Then open Claude Code and ask:

```text
Use the weather-personal MCP tools to get the current weather and
3-day forecast for Hanoi.
```

The local Claude configuration contains the bearer header, while `.env` and API
keys remain ignored by Git.

## ADK làm gì trong Lab này?

ADK (Agent Development Kit) đóng vai trò **MCP Client** 
```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  1. KẾT NỐI tới MCP Server qua Streamable HTTP                  │
│     StreamableHTTPConnectionParams(url="localhost:8085/mcp")    │
│                                                                 │
│  2. KHÁM PHÁ tools tự động (list_tools)                         │
│     McpToolset → tự hỏi server "anh có tool gì?"                │
│     → nhận về: weather v1, weather v2, forecast, health_check   │
│                                                                 │
│  3. TRUYỀN tools cho LLM (Gemini)                               │
│     Agent(model="gemini-3.6-flash", tools=[weather_tools])      │
│     → Gemini biết nó có thể gọi 4 tools trên                    │
│                                                                 │
│  4. ĐIỀU PHỐI vòng lặp Function Calling                         │
│     User hỏi → Gemini chọn tool → ADK gọi MCP Server            │
│     → nhận kết quả → đưa lại cho Gemini tổng hợp                │
│                                                                 │
│  5. CUNG CẤP giao diện web (adk web)                            │
│     → http://localhost:8000 để chat với agent                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

So với bài 02 (viết client thủ công bằng `mcp.ClientSession`), ADK giúp bạn **không phải viết vòng lặp function calling thủ công** nữa. Toàn bộ luồng list_tools → model quyết định → call_tool → model tổng hợp được ADK xử lý tự động.

## Setup

### 1. MCP Server

```bash
cd mcp-server
uv sync

# Set your WeatherAPI key (get one free at https://weatherapi.com)
export WEATHERAPI_KEY="your_weatherapi_key"
export MCP_AUTH_TOKEN="choose_a_private_token"

# Start the server (runs on port 8085 by default)
uv run python weather.py
```

The server will be available at `http://localhost:8085/mcp`.

### 2. ADK Agent (Client)

```bash
cd mcp-client
uv sync

# Load GOOGLE_API_KEY, WEATHERAPI_KEY, and MCP_AUTH_TOKEN from the root .env
source ../../activate.sh

# Start ADK web interface
uv run adk web
```

Open http://localhost:8000 in your browser, select `weather_agent`, and ask about the weather.

## Configuration

| Variable | Where | Description |
|----------|-------|-------------|
| `WEATHERAPI_KEY` | mcp-server | API key from weatherapi.com |
| `GOOGLE_API_KEY` | mcp-client/.env | Gemini API key |
| `PORT` | mcp-server (env) | Override server port (default: 8085) |
| `MCP_AUTH_TOKEN` | server + clients | Bearer token (default: `dev-token-abc123`) |
| `MCP_SERVER_URL` | clients | Override MCP URL (default: `http://localhost:8085/mcp`) |
