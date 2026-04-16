from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/books', methods=['GET'])
def get_books():
    # Trả về đúng dữ liệu mà API Blueprint yêu cầu
    return jsonify([
        {
            "id": "1",
            "title": "Clean Code",
            "author": "Robert C. Martin"
        }
    ]), 200

@app.route('/books', methods=['POST'])
def create_book():
    # Trả về HTTP Status 201 như tài liệu yêu cầu
    return jsonify({}), 201

if __name__ == '__main__':
    # Cho server chạy ở port 3000 để Dredd gọi vào
    app.run(port=3000)