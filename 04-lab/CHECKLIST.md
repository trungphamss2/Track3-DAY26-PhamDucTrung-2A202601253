# Checklist kiểm tra kết quả

Ngày kiểm tra: 2026-08-28

## Bài Dễ

- [x] MCP Server khởi động được tại `http://localhost:8085/mcp`.
- [x] Có hai tool nghiệp vụ tự xây: `get_current_weather` và `get_forecast`.
- [x] Tool giải quyết việc tra cứu thời tiết trước khi di chuyển.
- [x] Tool gọi WeatherAPI và trả dữ liệu thật, không hard-code kết quả.
- [x] `claude mcp list` nhận ra `weather-personal` và báo `Connected`.
- [ ] Xác nhận danh sách tools bên trong phiên Claude Code.
- [ ] Gọi tool bằng câu hỏi tự nhiên bên trong Claude Code.
- [x] Tool nhận đúng arguments: đã test `city="Hanoi", days=2`.
- [x] Tool trả dữ liệu dự báo thật đúng cấu trúc.

Hai mục chưa đánh dấu cần tài khoản có quyền chạy Claude Code. Tài khoản Claude
Free vẫn đăng ký/kiểm tra kết nối MCP được nhưng không chạy được model trong CLI.

Câu hỏi tự nhiên đã được kiểm thử thành công bằng Google ADK (không nói tên tool):

```text
Cuối tuần này tôi định đi Hà Nội. Hãy cho tôi biết thời tiết hai ngày tới để chuẩn bị.
```

Agent tự chọn:

```text
get_forecast(city="Hanoi", days=2)
```

Khi có tài khoản Claude Code phù hợp, dùng chính câu hỏi trên để hoàn thành hai ô
còn lại.

## Bài Trung bình

- [x] Server chạy bằng Streamable HTTP.
- [x] Client kết nối qua HTTP.
- [x] Authentication được bật bằng `TokenVerifier` và `AuthSettings`.
- [x] Token hợp lệ list/call tools thành công.
- [x] Thiếu token bị từ chối bằng HTTP 401.
- [x] Token sai bị từ chối bằng HTTP 401.
- [ ] Truy cập từ máy khác trong LAN (phần tùy điều kiện).

Lệnh kiểm tra trong Git Bash, khi server đang chạy:

```bash
cd /d/LABS_TRACK3/Day26-MCP-Tools-Integration
source ./activate.sh
cd 04-lab/mcp-client
.venv/Scripts/python secure_weather_client.py
```

Kết quả chính:

```text
Missing token: HTTP 401
Invalid token: HTTP 401
Authorized: weather-personal v2.0.0 (streamable-http)
Forecast arguments city=Hanoi, days=2: OK
```

## Bài Khó

- [x] `get_current_weather_v2` thay đổi response từ chuỗi sang JSON có version.
- [x] Client cũ tiếp tục gọi `get_current_weather` và nhận chuỗi cũ.
- [x] Client mới dùng được v2 và tham số optional `units`.
- [x] Có resource `server://info`.
- [x] Resource chứa server version, capabilities, tool version và deprecation.
- [x] Client mới đọc metadata trước, chọn v2 nếu có và fallback về v1 nếu cần.

## Lỗi thường gặp

| Lỗi | Cách kiểm tra |
|-----|---------------|
| Claude không thấy server | Chạy `claude mcp list`; kiểm tra URL, server và đúng thư mục project |
| Server thấy nhưng không có tool | Kiểm tra `@mcp.tool()`, exception lúc import và Python environment |
| Tool gọi bị lỗi | Kiểm tra kiểu input, tên thành phố, `WEATHERAPI_KEY` và response API |
| HTTP không kết nối | Kiểm tra port 8085, firewall, endpoint `/mcp`; server bind `0.0.0.0` |
| Token nào cũng gọi được | Kiểm tra `TokenVerifier`, `AuthSettings` và required scope |
| Token đúng vẫn 401 | Header phải là `Authorization: Bearer <TOKEN>` và hai phía dùng cùng token |
| Client cũ bị hỏng | Không xóa v1; không đổi kiểu output v1; tạo v2 song song |
| Secret bị push | Rotate key, cập nhật `.env`, kiểm tra `.gitignore` và Git history |

Không ghi API key hoặc bearer token vào ảnh chụp, log nộp bài hay GitHub.
