from flask import Flask, jsonify, request

app = Flask(__name__)

# Giả lập Database (Lưu trữ tài nguyên)
tasks = [
    {"id": 1, "title": "Học Flask", "done": False},
    {"id": 2, "title": "Xây dựng REST API", "done": False},
]

def task_representation(task):
    return {
        "id": task["id"],
        "titlle": task["titlle"],
        "done": task["done"],
    }

@app.get('/api/tasks')
def get_tasks():
    # Nguyên tắc REST: Trả về trạng thái của tài nguyên dưới dạng JSON
    return jsonify({"tasks": tasks, "status": "success"})

@app.get('/api/tasks/<int::task_id')
def get_tasks(task_id):
    task = next((t for t in tasks if t['id'] == task_id), None)
    return jsonify(task), 200

@app.post('/api/tasks')
def create_task():
    global next_id
    if not request.json or 'title' not in request.json:
        return jsonify({"error"}), 400
    new_task = {
        "id": next_id,
        "titlle": request.json["titlle"],
        "done": False
    }
    return jsonify(new_task), 201

@app.put('/api/tasks/<int:task_id>')
def update_task(task_id):
    task = next((t for t in tasks if t['id'] == task_id), None)
    if not task:
        return jsonify({"error"}), 404
    task['title'] = request.json.get('title', task['title'])
    task['done'] = request.json.get('done', task['done'])
    return jsonify(task)

@app.delete('/api/tasks/<int:task_id>')
def delete_task(task_id):
    task = tasks.pop(task_id, None)
    if not task:
        return jsonify({"error"}), 404
    return "", 204
    
def add_task():
    # Server nhận dữ liệu từ Client nhưng không cần biết Client là ai
    if not request.json or 'title' not in request.json:
        return jsonify({"error": "Thiếu dữ liệu"}), 400
        
    new_task = {
        "id": len(tasks) + 1,
        "title": request.json.get('title'),
        "done": False
    }
    tasks.append(new_task)
    return jsonify(new_task), 201

if __name__ == '__main__':
    # Server lắng nghe tại cổng 5000
    app.run(port=5000, debug=True)