import requests
import time

SERVER_URL = "http://127.0.0.1:5000/api/v1/tasks"
TOKEN = "demo-token"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

BASE_URL = "http://127.0.0.1:5000"

def print_cache_headers(resp: requests.Response):
    etag = resp.headers.get("ETag")
    cache_control = resp.headers.get("Cache-Control")
    vary = resp.headers.get("Vary")
    print("  ETag:", etag)
    print("  Cache-Control:", cache_control)
    print("  Vary:", vary)

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

    print("--- CLIENT: GET /api/v1/tasks (plural + lowercase + versioning) ---")
    try:
        response = requests.get(SERVER_URL, headers=HEADERS, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("SERVER TRẢ VỀ:", data['tasks'])
            print("META:", data.get("meta"))
            print_cache_headers(response)
        else:
            print("SERVER TRẢ VỀ:", response.status_code, response.text)
    except Exception as e:
        print("Lỗi: Không kết nối được tới Server!", e)
        return

    time.sleep(1) 

    print("\n--- CLIENT: GET /api/v1/tasks?done=false&sort=title&order=asc&limit=1&offset=0 (clarity + extensibility) ---")
    r_query = requests.get(
        SERVER_URL,
        params={"done": "false", "sort": "title", "order": "asc", "limit": 1, "offset": 0},
        headers=HEADERS,
        timeout=5,
    )
    print("SERVER TRẢ VỀ:", r_query.status_code)
    if r_query.status_code == 200:
        print("TASKS:", r_query.json().get("tasks"))
        print("META:", r_query.json().get("meta"))
        print_cache_headers(r_query)
    else:
        print("BODY:", r_query.text)

    print("\n--- CLIENT: GET /api/tasks với If-None-Match (kỳ vọng 304 nếu chưa đổi) ---")
    etag = response.headers.get("ETag")
    cache_headers = dict(HEADERS)
    if etag:
        cache_headers["If-None-Match"] = etag

    r2 = requests.get(SERVER_URL, headers=cache_headers, timeout=5)
    print("SERVER TRẢ VỀ:", r2.status_code)
    print_cache_headers(r2)
    if r2.status_code == 200:
        print("BODY:", r2.json())
    else:
        print("BODY:", r2.text)

    time.sleep(1)

    print("\n--- CLIENT: POST /api/tasks ---")
    new_data = {"title": "Học về Uniform Interface"}
    post_response = requests.post(SERVER_URL, json=new_data, headers=HEADERS, timeout=5)
    
    if post_response.status_code == 201:
        print("SERVER XÁC NHẬN ĐÃ THÊM:", post_response.json())
    else:
        print("SERVER TRẢ VỀ:", post_response.status_code, post_response.text)

    time.sleep(1)

    print("\n--- CLIENT: GET /api/tasks lại với ETag cũ (kỳ vọng 200 + ETag mới) ---")
    r3 = requests.get(SERVER_URL, headers=cache_headers, timeout=5)
    print("SERVER TRẢ VỀ:", r3.status_code)
    print_cache_headers(r3)
    if r3.status_code == 200:
        print("TASKS:", r3.json().get("tasks"))

if __name__ == "__main__":
    call_server()