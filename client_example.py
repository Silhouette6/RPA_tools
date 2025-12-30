import requests
import json

BASE_URL_LOCAL = "http://127.0.0.1:8000"

BASE_URL_REMOTE = "http://192.168.30.137:8000"

def test_xhs(BASE_URL):
    print("\n--- Testing 小红书 ---", BASE_URL)
    payload = {
        "url": "https://www.xiaohongshu.com/discovery/item/6911a4c30000000004005418",
        "download_img": False,
        "headless": False 
    }
    try:
        response = requests.post(f"{BASE_URL}/xhs", json=payload, timeout=60)
        print(f"Status Code: {response.status_code}")
        print(json.dumps(response.json(), indent=4, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")

def test_douyin(BASE_URL):
    print("\n--- Testing 抖音 ---", BASE_URL)
    payload = {
        "url": "https://v.douyin.com/SbTeoPlxMP0/",
        "download_video": False,
        "headless": False
    }
    try:
        response = requests.post(f"{BASE_URL}/douyin", json=payload, timeout=60)
        print(f"Status Code: {response.status_code}")
        print(json.dumps(response.json(), indent=4, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")

def test_toutiao(BASE_URL):
    print("\n--- Testing 今日头条 ---", BASE_URL)
    payload = {
        "url": "https://www.toutiao.com/video/7571303297971060770/#ocr",
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
    # test_xhs(BASE_URL_LOCAL)
    # test_xhs(BASE_URL_REMOTE)
    # test_douyin(BASE_URL_LOCAL)
    # test_douyin(BASE_URL_REMOTE)
    test_toutiao(BASE_URL_LOCAL)
    test_toutiao(BASE_URL_REMOTE)
    
    '''
    for i in range(5):
        test_xhs(BASE_URL_LOCAL)
    '''
