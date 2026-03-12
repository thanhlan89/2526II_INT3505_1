import requests
import time

# Địa chỉ duy nhất để Client tìm thấy Server
SERVER_URL = "http://127.0.0.1:5000/api/tasks"

def call_server():
    print("--- CLIENT: Đang gửi yêu cầu GET để lấy thực đơn ---")
    try:
        response = requests.get(SERVER_URL)
        if response.status_code == 200:
            data = response.json()
            print("SERVER TRẢ VỀ:", data['tasks'])
    except Exception as e:
        print("Lỗi: Không kết nối được tới Server!", e)
        return

    time.sleep(1) # Nghỉ 1 giây để dễ quan sát

    print("\n--- CLIENT: Đang gửi yêu cầu POST để đặt món mới ---")
    new_data = {"title": "Học về Uniform Interface"}
    post_response = requests.post(SERVER_URL, json=new_data)
    
    if post_response.status_code == 201:
        print("SERVER XÁC NHẬN ĐÃ THÊM:", post_response.json())

if __name__ == "__main__":
    call_server()