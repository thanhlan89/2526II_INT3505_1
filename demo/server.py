from flask import Flask, jsonify, request

app = Flask(__name__)

# Giả lập Database (Lưu trữ tài nguyên)
tasks = [
    {"id": 1, "title": "Học Flask", "done": False},
    {"id": 2, "title": "Xây dựng REST API", "done": False}
]

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    # Nguyên tắc REST: Trả về trạng thái của tài nguyên dưới dạng JSON
    return jsonify({"tasks": tasks, "status": "success"})

@app.route('/api/tasks', methods=['POST'])
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