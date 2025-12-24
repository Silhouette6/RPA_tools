import requests
import json

# BASE_URL = "http://127.0.0.1:8000"

BASE_URL= "http://192.168.30.137:8000"

def test_xhs():
    print("\n--- Testing 小红书 ---")
    payload = {
        "url": "http://xhslink.com/o/6kZ7NPjrUJa",
        "download_img": True,
        "headless": False
    }
    try:
        response = requests.post(f"{BASE_URL}/xhs", json=payload, timeout=60)
        print(f"Status Code: {response.status_code}")
        print(json.dumps(response.json(), indent=4, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")

def test_douyin():
    print("\n--- Testing 抖音 ---")
    payload = {
        "url": "https://v.douyin.com/WogUSRW-pzM/",
        "download_video": False,
        "headless": True
    }
    try:
        response = requests.post(f"{BASE_URL}/douyin", json=payload, timeout=60)
        print(f"Status Code: {response.status_code}")
        print(json.dumps(response.json(), indent=4, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")

def test_toutiao():
    print("\n--- Testing 今日头条 ---")
    payload = {
        "url": "https://www.toutiao.com/w/1850641232900096/",
        "download_video": False,
        "headless": True
    }
    try:
        response = requests.post(f"{BASE_URL}/toutiao", json=payload, timeout=60)
        print(f"Status Code: {response.status_code}")
        print(json.dumps(response.json(), indent=4, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # 请确保 server.py 已经启动 (python server.py)
    # 也可以在不同终端同时运行此脚本测试并发排队
    for i in range(10):
        test_xhs()
        # test_douyin()
        # test_toutiao()
