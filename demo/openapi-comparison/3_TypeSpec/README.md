# TypeSpec Demo

## Cách cài đặt và chạy
1. Cài đặt TypeSpec compiler và thư viện:
   `npm install`
   `npm install -g @typespec/compiler`
2. Biên dịch TypeSpec sang OpenAPI 3:
   `tsp compile main.tsp --emit @typespec/openapi3`
3. File kết quả sẽ nằm trong thư mục `tsp-output/`.