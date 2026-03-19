from __future__ import annotations

from pathlib import Path

from flask import Flask, Response, redirect

APP_DIR = Path(__file__).resolve().parent
OPENAPI_PATH = APP_DIR / "openapi.yaml"

app = Flask(__name__)


@app.get("/")
def root():
    return redirect("/docs", code=302)


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


if __name__ == "__main__":
    # Swagger UI server (docs). API server của bạn chạy riêng (ví dụ port 5000).
    # Mặc định chạy docs ở port 8000 để không trùng port.
    app.run(host="127.0.0.1", port=8000, debug=True)

