# Product Backend

Backend demo triển khai từ OpenAPI spec và kết nối MongoDB/Mongoose.

## Các tính năng
- OpenAPI spec `openapi.yaml` mô tả resource `Product`
- CRUD endpoints: `GET /products`, `POST /products`, `GET /products/{id}`, `PUT /products/{id}`, `DELETE /products/{id}`
- Validates request/response theo spec bằng `express-openapi-validator`
- MongoDB persistence bằng `mongoose`
- Swagger UI tại `/api-docs`

## Cài đặt
1. Mở terminal tại `product-backend`
2. Chạy:
   ```bash
   npm install
   ```
3. Tạo file `.env` nếu cần và đặt `MONGODB_URI`
   ```env
   MONGODB_URI=mongodb://127.0.0.1:27017/product-backend
   PORT=3000
   ```
4. Khởi động server:
   ```bash
   npm start
   ```

## Sử dụng API
- Swagger UI: `http://localhost:3000/api-docs`
- CRUD Product:
  - `GET  /products`
  - `POST /products`
  - `GET  /products/{id}`
  - `PUT  /products/{id}`
  - `DELETE /products/{id}`

## Lưu ý
- Nếu muốn dùng Swagger Codegen: có thể generate skeleton bằng OpenAPI spec `openapi.yaml` và sau đó tích hợp `controllers` với Mongoose.
