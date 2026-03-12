from flask import Flask, jsonify

app = Flask(__name__)

@app.get("/api/v1/task-id")
def list_task_id():
    return jsonify({"task_id": task_id}), 200

@app.get("/api/v1/tasks")
def list_tasks():
    return jsonify({"tasks": [], "status": {"version": "v1"}}), 200