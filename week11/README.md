API Design Patterns — Tuần 11

Mục tiêu kiến thức
- Các mẫu thiết kế API: CRUD, Query, HATEOAS, Event-driven, Webhook — khái niệm và ví dụ ngắn.
- Hiểu khi nào dùng REST, khi nào dùng gRPC hoặc GraphQL.

Kỹ năng thực hành
- Thiết kế API kết hợp nhiều patterns (ví dụ CRUD + Query, REST cho truy vấn tài nguyên + Event-driven cho xử lý bất đồng bộ).
- Triển khai webhook để tích hợp hệ thống (ví dụ: hệ thống A gửi sự kiện tới hệ thống B).

Tóm tắt các mẫu
- CRUD: Create/Read/Update/Delete — phù hợp cho tài nguyên trực tiếp, thường dùng REST endpoints chuẩn.
- Query: Tối ưu cho các truy vấn phức tạp (filter, sort, paging). Có thể triển khai dưới dạng endpoint `/items?filter=...` hoặc GraphQL cho truy vấn linh hoạt.
- HATEOAS: Hypermedia as the Engine — response chứa các liên kết (links) để dẫn client qua trạng thái ứng dụng; hữu ích cho API hướng tài nguyên, giúp client khám phá API.
- Event-driven: Hệ thống phát ra events (message broker: Kafka, RabbitMQ) — phù hợp cho xử lý bất đồng bộ, hệ thống phân tán, CQRS.
- Webhook: HTTP callback — hệ thống nhận sự kiện bằng endpoint HTTP công khai; đơn giản, dễ tích hợp giữa dịch vụ.

Khi chọn REST vs gRPC vs GraphQL
- REST: Tốt cho tài nguyên CRUD, tương thích rộng, caching HTTP, dễ dùng với HTTP/JSON.
- gRPC: Tốt cho giao tiếp dịch vụ đến dịch vụ (service-to-service), cần hiệu năng cao, streaming, hẹp băng thông, strong-typing (protobuf).
- GraphQL: Tốt khi client cần truy vấn linh hoạt, tránh over/under-fetching; quản lý schema trung tâm, nhưng phức tạp hơn về caching và authorization.

Thiết kế kết hợp patterns (ví dụ)
- Dùng REST cho thao tác CRUD trên tài nguyên chính.
- Thêm endpoint Query (hoặc GraphQL) cho các truy vấn phức tạp.
- Dùng Event-driven cho xử lý bất đồng bộ (ví dụ: khi user tạo order -> publish event `order.created` -> worker xử lý tồn kho).
- Dùng Webhook để thông báo service bên ngoài (ví dụ: notify payment gateway, CRM).

Webhook example (trong repository)
- week11/webhook-server : server Node/Express nhận webhook POST JSON.
- week11/webhook-client : script Node gửi POST tới server (dùng Node built-in http).

API server demo (CRUD / Query / HATEOAS / Event-driven / Webhook)
- Thư mục: `week11/api-server` — server Express cung cấp CRUD cho `items`, hỗ trợ query/filter/sort/paging, trả HATEOAS links trong response.
- Event-driven: khi `item` được tạo server emit sự kiện `item.created` và worker nội bộ sẽ gửi payload đến các webhooks đã đăng ký.
- Webhook registration: POST `/webhooks/register` với JSON `{ "url": "http://..." }` để đăng ký.

Chạy API server
```bash
cd week11/api-server
npm install
node index.js
```

Ví dụ endpoints
- `GET /items` — list, hỗ trợ `name`, `minPrice`, `maxPrice`, `sort`, `order`, `page`, `limit`.
- `GET /items/:id` — get single item (response có HATEOAS links).
- `POST /items` — create item `{ name, price }` (sẽ phát `item.created` và gửi đến webhooks).
- `PUT /items/:id` — update item.
- `DELETE /items/:id` — delete item.
- `POST /webhooks/register` — register a webhook `{ url }`.
- `GET /webhooks` — list registered webhooks.
- `POST /webhooks/test` — send a test payload to registered webhooks.
 - `POST /webhooks/test` — send a test payload to registered webhooks.

HMAC signature (bảo mật webhook)
- Ví dụ trong repo sử dụng HMAC-SHA256 để chứng thực nguồn webhook. Thiết lập biến môi trường `WEBHOOK_SECRET` cho cả `webhook-server` và `webhook-client` để chia sẻ secret.

Ví dụ chạy với HMAC
1. Mở terminal, chạy webhook receiver (port 4000):
```bash
cd week11/webhook-server
# Linux/macOS
export WEBHOOK_SECRET=mysecret
# Windows PowerShell
$env:WEBHOOK_SECRET="mysecret"
npm install
node index.js
```
2. Mở terminal khác, chạy API server (port 4100) và đăng ký webhook:
```bash
cd week11/api-server
# Linux/macOS
export WEBHOOK_SECRET=mysecret
# Windows PowerShell
$env:WEBHOOK_SECRET="mysecret"
npm install
node index.js

# Register the webhook so API server will deliver events to receiver
curl -X POST http://localhost:4100/webhooks/register -H "Content-Type: application/json" -d '{"url":"http://localhost:4000/webhook"}'

# Create item to trigger event delivery
curl -X POST http://localhost:4100/items -H "Content-Type: application/json" -d '{"name":"Example","price":9.99}'
```

Chạy ví dụ
1. Mở terminal, chạy server:
```bash
cd week11/webhook-server
npm install
node index.js
```
2. Ở terminal khác, gửi event từ client:
```bash
node week11/webhook-client/client.js
```

Gợi ý nâng cao
- Thêm xác thực signature (HMAC) cho webhook để xác minh nguồn gửi.
- Sử dụng retry/circuit-breaker cho webhook delivery.
- Dùng queue (e.g., Redis, RabbitMQ) để xử lý webhook đầu vào không gây blocking.

Tài liệu tham khảo ngắn
- Roy Fielding, REST architecture
- gRPC docs
- GraphQL docs

Thêm trợ giúp? Nếu bạn muốn, tôi có thể: cung cấp ví dụ GraphQL, demo gRPC, hoặc mở rộng webhook với HMAC verification và retry.
