from re import L
from playwright.sync_api import sync_playwright
from pathlib import Path
import time
import json
from urllib3.util import url
from config import Config_Toutiao

"""
头条RPA，基于层级结构提取内容
TODO:
toutiao/w
toutiao/video
"""
def download(page, video_locator, save_path):
    try:
        # 等 video 出现在 DOM 中即可，不用等播放
        video_locator.wait_for(state="attached", timeout=10000)

        video_url = video_locator.get_attribute("src")
        if not video_url:
            raise RuntimeError("video src not found")

        if video_url.startswith("//"):
            video_url = "https:" + video_url

        print("video url:", video_url)

        # 增加 Referer 头部，头条视频 CDN 通常会校验来源
        headers = {
            "Referer": "https://www.toutiao.com/",
            "User-Agent": page.evaluate("navigator.userAgent")
        }

        # timeout 单位是毫秒，增加到 10 秒以应对大视频
        response = page.request.get(video_url, headers=headers, timeout=10000)
        
        if not response.ok:
            raise RuntimeError(f"download failed: {response.status} {response.status_text}")

        with open(save_path, "wb") as f:
            f.write(response.body())

        print("video saved to:", save_path)
        return "video"

    except Exception as e:
        print(f"download video failed: {str(e)}")
        return "download_video_failed"

def poll_until_ready(
    page,
    locators,
    wait_list,
    timeout=12,
    interval=0.5):
    """
    :param page: Playwright Page 对象
    :param locators: dict[str, Locator]，所有元素定位器
    :param wait_list: list[str]，必须就绪的键名列表
    :param timeout: 总超时（秒）
    :param interval: 轮询间隔
    """
    start = time.time()
    not_ready = None

    while time.time() - start < timeout:
        print("tring")

        # 2️⃣ 检查特殊页面状态
        if page.get_by_text("内容不存在").count() > 0:
            print("Detected: Content not found (404)")
            return "PAGE_NOT_FOUND"

        # 3️⃣ 判断正文是否就绪
        all_ready = True
        for key in wait_list:
            loc = locators[key]
            if loc.count() == 0:
                not_ready = key
                all_ready = False
                break

        if all_ready:
            print("content ready")
            return "ALL_READY"

        time.sleep(interval)

    if not_ready:
        print(f"not ready locator: {not_ready}")
    raise TimeoutError("page not ready within timeout")

def get_toutiao_info(url, xpaths, wait_list, save_dir, download_video = True):

    with sync_playwright() as p:
        user_data_dir = str(Path(__file__).parent / "chrome-profile")
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            channel="chrome",
            headless=False,
        )
        page = context.new_page()

        print(f"Opening {url} ...")
        page.goto(url, wait_until="domcontentloaded")

        if "toutiao.com/w" in url: # 处理微头条
            w_xpaths = xpaths["w_xpaths"]
            w_wait_list = wait_list["w_wait_list"]
            # 统一构建locator
            locators = {k: page.locator(v) for k, v in w_xpaths.items()}

            # 3️⃣ 等待正文就绪
            status = poll_until_ready(page=page, locators=locators, wait_list=w_wait_list)
        
            if status == "ALL_READY":
                def safe_get_text(key):
                    try:
                        return locators[key].first.inner_text()
                    except Exception:
                        return None

                content = safe_get_text("w_content")
                author = safe_get_text("w_author")
                result = json.dumps({
                    "code": 200,
                    "message": "success",
                    "data": {
                            "source": "微头条",
                            "status": "200",
                            "content": content, 
                            "author": author, 
                            "likes": safe_get_text("w_likes"), 
                            "publish_time": safe_get_text("w_publish_time"),
                            "url_long": page.url
                            }
                }, ensure_ascii=False)
            
            elif status == "PAGE_NOT_FOUND":
                result = json.dumps({
                    "code": 200,
                    "message": "PAGE_NOT_FOUND已下架",
                    "data": {
                            "source": "微头条",
                            "status": "PAGE_NOT_FOUND",
                            "message": "检查到作品已下架"
                            }
                }, ensure_ascii=False)
                return result

            else:
                result = json.dumps({
                    "code": 400,
                    "message": "400未找到对应元素，请检查路径或页面加载状态。",
                    "data": {
                            "source": "微头条",
                            "status": "400",
                            "message": "未找到对应元素，请检查路径或页面加载状态。",
                            "url_long": page.url
                            }
                }, ensure_ascii=False)
                print("未找到对应元素，请检查路径或页面加载状态。")
                return result
        
        if "toutiao.com/video" in url: # 处理视频
            video_xpaths = xpaths["video_xpaths"]
            video_wait_list = wait_list["video_wait_list"]
            # 统一构建locator
            locators = {k: page.locator(v) for k, v in video_xpaths.items()}

            # 3️⃣ 等待正文就绪
            status = poll_until_ready(page=page, locators=locators, wait_list=video_wait_list)
        
            if status == "ALL_READY":
                def safe_get_text(key):
                    try:
                        return locators[key].first.inner_text()
                    except Exception:
                        return None

                content = safe_get_text("video_content")
                author = safe_get_text("video_author")    
                result = json.dumps({
                    "code": 200,
                    "message": "success",
                    "data": {
                            "source": "头条视频",
                            "status": "200",
                            "content": content, 
                            "author": author, 
                            "views": safe_get_text("video_views"), 
                            "likes": safe_get_text("video_likes"), 
                            "publish_time": safe_get_text("video_publish_time"),
                            "url_long": page.url
                            }
                }, ensure_ascii=False)

                if download_video:
                    download(page, locators["video_video"].first, f"{save_dir}/{author}.mp4")
            
            elif status == "PAGE_NOT_FOUND":
                result = json.dumps({
                    "code": 200,
                    "message": "PAGE_NOT_FOUND已下架",
                    "data": {
                            "source": "头条视频",
                            "status": "PAGE_NOT_FOUND",
                            "message": "检查到作品已下架"
                            }
                }, ensure_ascii=False)
                return result

            else:
                result = json.dumps({
                    "code": 400,
                    "message": "400未找到对应元素，请检查路径或页面加载状态。",
                    "data": {
                            "source": "头条视频",
                            "status": "400",
                            "message": "未找到对应元素，请检查路径或页面加载状态。",
                            "url_long": page.url
                            }
                }, ensure_ascii=False)
                print("未找到对应元素，请检查路径或页面加载状态。")
                return result
        
        return result


if __name__ == "__main__":
    # https://www.toutiao.com/w/1850041869600772/#ocr 
    # https://www.toutiao.com/w/1850641232900096/
    # https://www.toutiao.com/w/1848052368845833/ 已下架
    # https://www.toutiao.com/video/7523088690436898851/#ocr 视频
    # https://www.toutiao.com/video/7571580926610636841/ 视频2
    # https://www.toutiao.com/video/7571303297971060770/#ocr 视频已下架
    url = "https://www.toutiao.com/video/7571303297971060770/#ocr"
    
    config = Config_Toutiao() 
    # XPath路径
    xpaths = config.xpaths
    # 创建等待列表，等待元素可见
    wait_list = config.wait_list
    save_dir = config.save_dir

    result = get_toutiao_info(url, xpaths, wait_list, save_dir, download_video=True)
    print(result)
