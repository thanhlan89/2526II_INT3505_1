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


# -----------------------------
# API versioning demo (v1)
# Naming conventions:
# - plural nouns: /tasks
# - lowercase: /api/v1/...
# - hyphens: /task-items (ví dụ)
# -----------------------------

@app.get("/api/v1/tasks")
def v1_list_tasks():
    """
    Demo consistency/clarity/extensibility:
    - Resource plural: /tasks
    - Query params rõ ràng: done, q, sort, order, limit, offset
    - Response giữ key "tasks" để tương thích, thêm "meta" để dễ mở rộng
    """
    if not require_bearer_token():
        return jsonify({"error": "Unauthorized"}), 401

    items = [task_representation(t) for t in tasks]

    # Filtering (clarity): done=true/false
    done = request.args.get("done")
    if done is not None:
        done_norm = done.strip().lower()
        if done_norm not in ("true", "false"):
            return jsonify({"error": "Invalid query: done must be true/false"}), 400
        want = done_norm == "true"
        items = [t for t in items if t["done"] is want]

    # Search (extensibility): q=keyword
    q = request.args.get("q")
    if q:
        qn = q.strip().lower()
        items = [t for t in items if qn in t["title"].lower()]

    # Sorting (consistency): sort=id|title, order=asc|desc
    sort = (request.args.get("sort") or "id").strip().lower()
    order = (request.args.get("order") or "asc").strip().lower()
    if sort not in ("id", "title"):
        return jsonify({"error": "Invalid query: sort must be id/title"}), 400
    if order not in ("asc", "desc"):
        return jsonify({"error": "Invalid query: order must be asc/desc"}), 400
    items.sort(key=lambda t: t[sort])
    if order == "desc":
        items.reverse()

    # Pagination (extensibility): limit/offset
    try:
        limit = int(request.args.get("limit") or 50)
        offset = int(request.args.get("offset") or 0)
    except ValueError:
        return jsonify({"error": "Invalid query: limit/offset must be integers"}), 400
    if limit < 0 or offset < 0:
        return jsonify({"error": "Invalid query: limit/offset must be >= 0"}), 400

    total = len(items)
    paged = items[offset: offset + limit]

    body = {
        "tasks": paged,
        "status": "success",
        "meta": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "sort": sort,
            "order": order,
            "done": done,
            "q": q,
            "version": "v1",
        },
    }
    return cacheable_json(body, max_age_seconds=30)


@app.post("/api/v1/tasks")
def v1_create_task():
    return create_task()


@app.get("/api/v1/tasks/<int:task_id>")
def v1_get_task(task_id):
    return get_task(task_id)


@app.put("/api/v1/tasks/<int:task_id>")
def v1_update_task(task_id):
    return update_task(task_id)


@app.delete("/api/v1/tasks/<int:task_id>")
def v1_delete_task(task_id):
    return delete_task(task_id)


@app.get("/api/v1/task-items")
def v1_task_items_alias():
    # Demo hyphen: alias cho /tasks (không khuyến khích có 2 đường dẫn thật trong hệ thống lớn,
    # nhưng dùng để minh họa naming convention)
    return v1_list_tasks()

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