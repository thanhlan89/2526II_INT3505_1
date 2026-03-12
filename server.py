from flask import Flask, jsonify, request, make_response
import hashlib
import json

app = Flask(__name__)

tasks = [
    {"id": 1, "title": "Học Flask", "done": False},
    {"id": 2, "title": "Xây dựng REST API", "done": False},
]
next_id = 3

API_TOKEN = "demo-token"

def task_representation(task):
    return {
        "id": task["id"],
        "title": task["title"],
        "done": task["done"],
    }


def require_bearer_token():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return False
    token = auth.removeprefix("Bearer ").strip()
    return token == API_TOKEN


def get_request_identity():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth.removeprefix("Bearer ").strip()
    if token != API_TOKEN:
        return None
    return {"sub": "demo-user", "scopes": ["tasks:read", "tasks:write"]}


def compute_etag(data) -> str:
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def cacheable_json(data, *, max_age_seconds: int = 30):
    """
    Demo "cacheable" theo HTTP:
    - Server trả ETag + Cache-Control
    - Client có thể gửi If-None-Match để nhận 304 Not Modified

    Lưu ý: có Authorization nên dùng private + Vary: Authorization.
    """
    etag = compute_etag(data)
    inm = (request.headers.get("If-None-Match") or "").strip().strip('"')

    if inm and inm == etag:
        resp = make_response("", 304)
        resp.headers["ETag"] = f"\"{etag}\""
        resp.headers["Cache-Control"] = f"private, max-age={max_age_seconds}"
        resp.headers["Vary"] = "Authorization"
        return resp

    resp = make_response(jsonify(data), 200)
    resp.headers["ETag"] = f"\"{etag}\""
    resp.headers["Cache-Control"] = f"private, max-age={max_age_seconds}"
    resp.headers["Vary"] = "Authorization"
    return resp


@app.get("/api/ping")
def ping():
    return jsonify({"ok": True, "stateless": True}), 200


@app.get("/api/me")
def me():
    ident = get_request_identity()
    if not ident:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"me": ident}), 200

@app.get('/api/tasks')
def list_tasks():
    if not require_bearer_token():
        return jsonify({"error": "Unauthorized"}), 401
    # Giữ style demo cũ: có thêm "status"
    body = {"tasks": [task_representation(t) for t in tasks], "status": "success"}
    return cacheable_json(body, max_age_seconds=30)


@app.get("/api/tasks-legacy")
def list_tasks_legacy():
    if not require_bearer_token():
        return jsonify({"error": "Unauthorized"}), 401
    body = {"tasks": tasks, "status": "success"}
    return cacheable_json(body, max_age_seconds=30)

@app.get("/api/tasks/<int:task_id>")
def get_task(task_id):
    if not require_bearer_token():
        return jsonify({"error": "Unauthorized"}), 401
    task = next((t for t in tasks if t['id'] == task_id), None)
    if not task:
        return jsonify({"error": "Not found"}), 404
    body = task_representation(task)
    return cacheable_json(body, max_age_seconds=30)

@app.post('/api/tasks')
def create_task():
    global next_id
    if not require_bearer_token():
        return jsonify({"error": "Unauthorized"}), 401
    payload = request.get_json(silent=True) or {}
    title = payload.get("title")
    if not isinstance(title, str) or not title.strip():
        return jsonify({"error": "Invalid payload: 'title' is required"}), 400
    new_task = {
        "id": next_id,
        "title": title.strip(),
        "done": False
    }
    next_id += 1
    tasks.append(new_task)
    return jsonify(task_representation(new_task)), 201


@app.post("/api/add_task")
def add_task():
    if not require_bearer_token():
        return jsonify({"error": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or {}
    title = payload.get("title")
    if not isinstance(title, str) or not title.strip():
        return jsonify({"error": "Thiếu dữ liệu"}), 400

    global next_id
    new_task = {
        "id": next_id,
        "title": title.strip(),
        "done": False,
    }
    next_id += 1
    tasks.append(new_task)
    return jsonify(new_task), 201

@app.put('/api/tasks/<int:task_id>')
def update_task(task_id):
    if not require_bearer_token():
        return jsonify({"error": "Unauthorized"}), 401
    task = next((t for t in tasks if t['id'] == task_id), None)
    if not task:
        return jsonify({"error": "Not found"}), 404

    payload = request.get_json(silent=True) or {}
    if "title" in payload:
        if not isinstance(payload["title"], str) or not payload["title"].strip():
            return jsonify({"error": "Invalid payload: 'title' must be non-empty string"}), 400
        task["title"] = payload["title"].strip()
    if "done" in payload:
        if not isinstance(payload["done"], bool):
            return jsonify({"error": "Invalid payload: 'done' must be boolean"}), 400
        task["done"] = payload["done"]

    return jsonify(task_representation(task)), 200

@app.delete('/api/tasks/<int:task_id>')
def delete_task(task_id):
    if not require_bearer_token():
        return jsonify({"error": "Unauthorized"}), 401
    idx = next((i for i, t in enumerate(tasks) if t["id"] == task_id), None)
    if idx is None:
        return jsonify({"error": "Not found"}), 404
    tasks.pop(idx)
    return "", 204

if __name__ == '__main__':
    app.run(port=5000, debug=True)