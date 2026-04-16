import os
from flask import Flask, jsonify, request
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "demo_db")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]
tasks_collection = db["tasks"]


def serialize_task(task):
    return {
        "id": str(task["_id"]),
        "title": task.get("title", ""),
        "completed": bool(task.get("completed", False)),
    }


@app.get("/api/v1/task-id")
def list_task_id():
    first_task = tasks_collection.find_one({}, {"_id": 1})
    task_id = str(first_task["_id"]) if first_task else None
    return jsonify({"task_id": task_id}), 200


@app.get("/api/v1/tasks")
def list_tasks():
    q = (request.args.get("q") or "").strip()
    query = {}
    if q:
        query = {"title": {"$regex": q, "$options": "i"}}

    tasks = [serialize_task(task) for task in tasks_collection.find(query)]
    return jsonify({"tasks": tasks, "status": {"version": "v1"}}), 200


@app.post("/api/v1/tasks")
def create_task():
    payload = request.get_json(silent=True) or {}
    title = (payload.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title is required"}), 400

    doc = {"title": title, "completed": bool(payload.get("completed", False))}
    result = tasks_collection.insert_one(doc)
    created = tasks_collection.find_one({"_id": ObjectId(result.inserted_id)})
    return jsonify({"task": serialize_task(created)}), 201


if __name__ == "__main__":
    app.run(debug=True)