import requests
import json

# BASE_URL = "http://127.0.0.1:8000"

BASE_URL= "http://192.168.30.137:8000"

def test_xhs():
    print("\n--- Testing 小红书 ---", BASE_URL)
    payload = {
        "url": "http://xhslink.com/o/8PdviBz0NBi",
        "download_img": False,
        "headless": False 
    }
    try:
        response = requests.post(f"{BASE_URL}/xhs", json=payload, timeout=60)
        print(f"Status Code: {response.status_code}")
        print(json.dumps(response.json(), indent=4, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")

def test_douyin():
    print("\n--- Testing 抖音 ---", BASE_URL)
    payload = {
        "url": "https://v.douyin.com/1YdDJg98DWs/",
        "download_video": False,
        "headless": False
    }
    try:
        response = requests.post(f"{BASE_URL}/douyin", json=payload, timeout=60)
        print(f"Status Code: {response.status_code}")
        print(json.dumps(response.json(), indent=4, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")

def test_toutiao():
    print("\n--- Testing 今日头条 ---", BASE_URL)
    payload = {
        "url": "https://weitoutiao.zjurl.cn/ugc/share/wap/comment/7532665415143686975/#412c2b86822dc1697524f403d5fb32b0",
        "download_video": False,
        "headless": False
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
    # test_xhs()
    test_douyin()
    
    '''
    for i in range(5):
        test_xhs()
        test_xhs()
        test_xhs()
        test_douyin()
        test_douyin()
        test_douyin()
        test_toutiao()
        test_toutiao()
        test_toutiao()
    '''