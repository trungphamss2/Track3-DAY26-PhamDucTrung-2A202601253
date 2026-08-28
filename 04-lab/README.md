# Lab 04 — Weather Agent with Remote MCP Server

A weather agent built with Google ADK that connects to an MCP server via Streamable HTTP transport.

## Bước 1 — Use case thực tế

**Công việc hiện tại:** tra cứu thời tiết hiện tại và dự báo trước khi đi học,
đi làm hoặc lên lịch di chuyển.

**Tôi đang làm thủ công như thế nào:** mở website/app thời tiết, nhập từng thành
phố, đọc nhiệt độ, độ ẩm, gió và dự báo rồi tự tổng hợp.

**Input:** tên thành phố; số ngày dự báo; đơn vị nhiệt độ nếu dùng API v2.

**Output:** dữ liệu thời tiết thật lấy từ WeatherAPI.com, gồm địa điểm, nhiệt độ,
tình trạng, độ ẩm, gió và dự báo 1–3 ngày.

## Bước 2 — Tools đã xây

Hai tác vụ chính là:

| Tool | Input | Output | Tác vụ thật |
|------|-------|--------|-------------|
| `get_current_weather(city)` | `city: str` | Chuỗi thời tiết v1 | Gọi `current.json` của WeatherAPI |
| `get_forecast(city, days=3)` | `city: str`, `days: int` | Dự báo 1–3 ngày | Gọi `forecast.json` của WeatherAPI |

Phần versioning bổ sung `get_current_weather_v2(city, units="celsius")`; đây là
phiên bản mới của tool đầu tiên chứ không phải một use case hard-code khác. Tool
`health_check()` chỉ là tiện ích vận hành server.

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

## Đối chiếu yêu cầu (Dễ → Trung bình → Khó)

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

> Claude Code CLI có thể kiểm tra server và liệt kê trạng thái kết nối mà chưa
> đăng nhập. Để model Claude tự chọn và gọi tool, tài khoản cần có quyền Claude
> Code (Pro/Max, Team/Enterprise hoặc Anthropic API có billing). Tài khoản Claude
> Free không cung cấp lượt gọi model trong CLI.

## Kết quả kiểm thử

Chạy `secure_weather_client.py` đã xác nhận:

```text
Missing token: HTTP 401
Invalid token: HTTP 401
Authorized: weather-personal v2.0.0 (streamable-http)
Legacy v1 client: OK
Modern client selected get_current_weather_v2: API v2.0 OK
All secure Weather MCP checks passed.
```

Google ADK cũng đã kết nối bằng Bearer token, gọi
`get_current_weather_v2(city="Hanoi", units="celsius")` và trả về dữ liệu thật.

Checklist chi tiết theo đúng mục kiểm tra của bài: [CHECKLIST.md](CHECKLIST.md).

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
| `MCP_AUTH_TOKEN` | server + clients | Bearer token bắt buộc, lưu trong `.env` |
| `MCP_SERVER_URL` | clients | Override MCP URL (default: `http://localhost:8085/mcp`) |
