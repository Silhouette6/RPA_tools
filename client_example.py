import requests
import json

BASE_URL_LOCAL = "http://127.0.0.1:8000"

BASE_URL_REMOTE = "http://192.168.30.137:8000"

def test_xhs(BASE_URL):
    print("\n--- Testing 小红书 ---", BASE_URL)
    payload = {
        "url": "http://xhslink.com/o/5oh1Qa9WztU",
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
        "url": "https://m.toutiao.com/article/7567667244877070899/?app=news_article&category_new=__search__&module_name=Android_tt_others&share_did=MS4wLjACAAAAxMTOW9OFmwO1BIKhPg2st-nicYPfGJux1scZxlFuIZNwhHscB0hTHhBTYjVZYwN-&share_uid=MS4wLjABAAAAxMTOW9OFmwO1BIKhPg2st-nicYPfGJux1scZxlFuIZNwhHscB0hTHhBTYjVZYwN-&timestamp=1767146460&tt_from=wechat&upstream_biz=Android_wechat&utm_campaign=client_share&utm_medium=toutiao_android&utm_source=wechat&share_token=d9054977-011f-48ab-8050-4140a845d88d",
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
    test_douyin(BASE_URL_LOCAL)
    # test_douyin(BASE_URL_REMOTE)
    test_toutiao(BASE_URL_LOCAL)
    # test_toutiao(BASE_URL_REMOTE)
    
    # for i in range(3):
    #     test_xhs(BASE_URL_LOCAL)

