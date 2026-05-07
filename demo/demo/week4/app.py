from __future__ import annotations

from pathlib import Path

from flask import Flask, Response, jsonify, redirect

APP_DIR = Path(__file__).resolve().parent
OPENAPI_PATH = APP_DIR / "openapi.yaml"
MIGRATION_DOC_URL = "/docs/migration-api-v2"
SUNSET_DATE = "Wed, 31 Dec 2026 23:59:59 GMT"

V1_USERS = [
    {"id": 1, "name": "Alice"},
    {"id": 2, "name": "Bob"},
]

V2_USERS = [
    {"id": "usr_1", "full_name": "Alice", "status": "active"},
    {"id": "usr_2", "full_name": "Bob", "status": "active"},
]

app = Flask(__name__)


def add_v1_deprecation_headers(response: Response) -> Response:
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = SUNSET_DATE
    response.headers["Link"] = f'<{MIGRATION_DOC_URL}>; rel="deprecation"'
    return response


@app.get("/")
def root():
    return redirect("/docs", code=302)


@app.get("/api/v1/users")
def list_users_v1():
    response = jsonify({"users": V1_USERS, "status": "success", "api_version": "v1"})
    return add_v1_deprecation_headers(response)


@app.get("/api/v2/users")
def list_users_v2():
    return jsonify(
        {
            "users": V2_USERS,
            "status": "success",
            "api_version": "v2",
            "meta": {"count": len(V2_USERS)},
        }
    )


@app.get("/openapi.yaml")
def openapi_yaml():
    if not OPENAPI_PATH.exists():
        return {"error": "openapi.yaml not found"}, 404
    return Response(OPENAPI_PATH.read_text(encoding="utf-8"), mimetype="text/yaml")


@app.get("/docs")
def swagger_ui():
    # Serve Swagger UI từ CDN (không cần cài thêm package).
    # Swagger UI sẽ load spec từ /openapi.yaml do chính Flask serve.
    html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Swagger UI</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist/swagger-ui.css" />
  </head>
  <body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist/swagger-ui-bundle.js"></script>
    <script>
      window.onload = () => {{
        window.ui = SwaggerUIBundle({{
          url: "/openapi.yaml",
          dom_id: "#swagger-ui",
          deepLinking: true,
          presets: [SwaggerUIBundle.presets.apis],
          layout: "BaseLayout"
        }});
      }};
    </script>
  </body>
</html>"""
    return Response(html, mimetype="text/html")


@app.get("/docs/migration-api-v2")
def migration_api_v2():
    markdown = """# API v1 to v2 migration

- Base path mới: `/api/v2`
- Endpoint mới: `GET /api/v2/users`
- Các thay đổi chính:
  - `name` -> `full_name`
  - `id` kiểu số -> chuỗi định danh (`usr_*`)
  - Bổ sung `status` và `meta.count`

## Deadline

`/api/v1/users` sẽ sunset vào: Wed, 31 Dec 2026 23:59:59 GMT
"""
    return Response(markdown, mimetype="text/markdown")


if __name__ == "__main__":
    # Swagger UI server (docs). API server của bạn chạy riêng (ví dụ port 5000).
    # Mặc định chạy docs ở port 8000 để không trùng port.
    app.run(host="127.0.0.1", port=8000, debug=True)

