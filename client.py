import requests
import time

# Địa chỉ duy nhất để Client tìm thấy Server
SERVER_URL = "http://127.0.0.1:5000/api/tasks"
TOKEN = "demo-token"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

BASE_URL = "http://127.0.0.1:5000"

def call_server():
    print("--- CLIENT: GET /api/ping ---")
    r = requests.get(f"{BASE_URL}/api/ping", timeout=5)
    print("SERVER TRẢ VỀ:", r.status_code, r.json())

    time.sleep(1)

    print("\n--- CLIENT: GET /api/me (không gửi token -> 401) ---")
    r = requests.get(f"{BASE_URL}/api/me", timeout=5)
    print("SERVER TRẢ VỀ:", r.status_code, r.text)

    time.sleep(1)

    print("\n--- CLIENT: GET /api/me (gửi token trong header) ---")
    r = requests.get(f"{BASE_URL}/api/me", headers=HEADERS, timeout=5)
    print("SERVER TRẢ VỀ:", r.status_code, r.json())

    time.sleep(1)

    print("--- CLIENT: GET /api/tasks (stateless qua Authorization header) ---")
    try:
        response = requests.get(SERVER_URL, headers=HEADERS, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("SERVER TRẢ VỀ:", data['tasks'])
        else:
            print("SERVER TRẢ VỀ:", response.status_code, response.text)
    except Exception as e:
        print("Lỗi: Không kết nối được tới Server!", e)
        return

    time.sleep(1) # Nghỉ 1 giây để dễ quan sát

    print("\n--- CLIENT: POST /api/tasks ---")
    new_data = {"title": "Học về Uniform Interface"}
    post_response = requests.post(SERVER_URL, json=new_data, headers=HEADERS, timeout=5)
    
    if post_response.status_code == 201:
        print("SERVER XÁC NHẬN ĐÃ THÊM:", post_response.json())
    else:
        print("SERVER TRẢ VỀ:", post_response.status_code, post_response.text)

if __name__ == "__main__":
    call_server()