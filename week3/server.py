from flask import Flask, jsonify, make_response, request
import hashlib
import json

app = Flask(__name__)

# Demo data (resource state)
tasks = [
    {"id": 1, "title": "Học REST basics", "done": False},
    {"id": 2, "title": "Làm demo cacheable", "done": True},
    {"id": 3, "title": "Ôn naming conventions", "done": False},
]
next_id = 4

# ---- Stateless auth demo ----
API_TOKEN = "demo-token"


def require_bearer_token():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return False
    token = auth.removeprefix("Bearer ").strip()
    return token == API_TOKEN


# ---- Consistent representation ----
def task_representation(task):
    return {"id": task["id"], "title": task["title"], "done": task["done"]}


# ---- Cacheable demo (ETag + If-None-Match) ----
def compute_etag(data) -> str:
    payload = json.dumps(
        data, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def cacheable_json(data, *, max_age_seconds: int = 30):
    """
    Demo cacheable theo HTTP:
    - Response: ETag + Cache-Control
    - Request: If-None-Match -> 304 Not Modified nếu nội dung chưa đổi
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


# -----------------------------
# Naming conventions demo:
# - plural nouns: /tasks
# - lowercase: /api/v1/...
# - hyphens: /task-items (ví dụ alias)
# - versioning: /v1
# -----------------------------


@app.get("/api/ping")
def ping():
    return jsonify({"ok": True}), 200


@app.get("/api/v1/tasks")
def v1_list_tasks():
    """
    Consistency:
    - Query params: done, q, sort, order, limit, offset
    - Response: tasks + meta + status
    Clarity:
    - Filter done=true/false, search q=..., sort=..., order=...
    Extensibility:
    - meta mở rộng dễ, versioning /v1, pagination chuẩn
    """
    if not require_bearer_token():
        return jsonify({"error": "Unauthorized"}), 401

    items = [task_representation(t) for t in tasks]

    # done=true|false
    done = request.args.get("done")
    if done is not None:
        done_norm = done.strip().lower()
        if done_norm not in ("true", "false"):
            return jsonify({"error": "Invalid query: done must be true/false"}), 400
        want = done_norm == "true"
        items = [t for t in items if t["done"] is want]

    # q=keyword
    q = request.args.get("q")
    if q:
        qn = q.strip().lower()
        items = [t for t in items if qn in t["title"].lower()]

    # sort=id|title, order=asc|desc
    sort = (request.args.get("sort") or "id").strip().lower()
    order = (request.args.get("order") or "asc").strip().lower()
    if sort not in ("id", "title"):
        return jsonify({"error": "Invalid query: sort must be id/title"}), 400
    if order not in ("asc", "desc"):
        return jsonify({"error": "Invalid query: order must be asc/desc"}), 400
    items.sort(key=lambda t: t[sort])
    if order == "desc":
        items.reverse()

    # limit/offset
    try:
        limit = int(request.args.get("limit") or 50)
        offset = int(request.args.get("offset") or 0)
    except ValueError:
        return jsonify({"error": "Invalid query: limit/offset must be integers"}), 400
    if limit < 0 or offset < 0:
        return jsonify({"error": "Invalid query: limit/offset must be >= 0"}), 400

    total = len(items)
    paged = items[offset : offset + limit]

    body = {
        "tasks": paged,
        "status": "success",
        "meta": {
            "version": "v1",
            "total": total,
            "limit": limit,
            "offset": offset,
            "done": done,
            "q": q,
            "sort": sort,
            "order": order,
        },
    }
    return cacheable_json(body, max_age_seconds=30)


@app.get("/api/v1/tasks/<int:task_id>")
def v1_get_task(task_id: int):
    if not require_bearer_token():
        return jsonify({"error": "Unauthorized"}), 401
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        return jsonify({"error": "Not found"}), 404
    return cacheable_json({"task": task_representation(task), "status": "success"}, max_age_seconds=30)


@app.post("/api/v1/tasks")
def v1_create_task():
    global next_id
    if not require_bearer_token():
        return jsonify({"error": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or {}
    title = payload.get("title")
    if not isinstance(title, str) or not title.strip():
        return jsonify({"error": "Invalid payload: 'title' is required"}), 400

    new_task = {"id": next_id, "title": title.strip(), "done": False}
    next_id += 1
    tasks.append(new_task)
    return jsonify({"task": task_representation(new_task), "status": "success"}), 201


@app.put("/api/v1/tasks/<int:task_id>")
def v1_update_task(task_id: int):
    if not require_bearer_token():
        return jsonify({"error": "Unauthorized"}), 401

    task = next((t for t in tasks if t["id"] == task_id), None)
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

    return jsonify({"task": task_representation(task), "status": "success"}), 200


@app.delete("/api/v1/tasks/<int:task_id>")
def v1_delete_task(task_id: int):
    if not require_bearer_token():
        return jsonify({"error": "Unauthorized"}), 401

    idx = next((i for i, t in enumerate(tasks) if t["id"] == task_id), None)
    if idx is None:
        return jsonify({"error": "Not found"}), 404
    tasks.pop(idx)
    return "", 204


@app.get("/api/v1/task-items")
def v1_task_items_alias():
    # Demo hyphen: alias để minh họa naming (plural + hyphen)
    return v1_list_tasks()


if __name__ == "__main__":
    app.run(port=5000, debug=True)
