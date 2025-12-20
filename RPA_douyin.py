from playwright.sync_api import sync_playwright
from pathlib import Path
import time
import json
from urllib3.util import url
from config import Config_Douyin

"""
抖音RPA，基于层级结构提取内容
TODO
解析两个不同的前端工程...
www.douyin.com
www.iesdouyin.com
"""

def close_login_popup(close_btn):
    start_time = time.time()
    try:
        if close_btn.count() > 0 and close_btn.is_visible():
            close_btn.click(timeout=0)
            print("INFO: login popup closed")
            end_time = time.time()
            print(f"close login popup cost time: {end_time - start_time}")
    except:
        end_time = time.time()
        print(f"close login popup cost time: {end_time - start_time}")
        pass
     
    

def poll_until_ready(
    page,
    close_btn,
    locators,
    wait_list,
    timeout=12,
    interval=0.5
):
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
        # 1️⃣ 如果 close 按钮出现，立刻点掉
        close_login_popup(close_btn)
        
        # 2️⃣ 检查特殊页面状态
        if page.get_by_text("你要观看的图文不存在").count() > 0:
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

def get_douyin_short_video_info(url, xpaths, wait_list, save_dir, download_video = True):

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
        print(page.url)

        close_btn = page.locator(xpaths["close_btn"])
        # 统一构建locator
        locators = {k: page.locator(v) for k, v in xpaths.items()}

        # 3️⃣ 等待正文就绪
        status = poll_until_ready(page=page, close_btn=close_btn, locators=locators, wait_list=wait_list)
        
        if status == "ALL_READY":
            def safe_get_text(key):
                """安全获取元素文本，处理可能的异常"""
                try:
                    return locators[key].first.inner_text()
                except Exception:
                    return None

            title = safe_get_text("title")
            author = safe_get_text("author")
            result = json.dumps({
                "code": 200,
                "message": "success",
                "data": {
                        "source": "抖音",
                        "status": "200",
                        "title": title, 
                        "author": author, 
                        "likes": safe_get_text("likes"), 
                        "comments": safe_get_text("comments"), 
                        "shares": safe_get_text("shares"), 
                        "fans": safe_get_text("fans"),
                        "publish_time": safe_get_text("publish_time"),
                        "url_long": page.url
                        }
            }, ensure_ascii=False)
        
        elif status == "PAGE_NOT_FOUND":
            result = json.dumps({
                "code": 200,
                "message": "PAGE_NOT_FOUND已下架",
                "data": {
                        "source": "抖音",
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
                        "source": "抖音",
                        "status": "400",
                        "message": "未找到对应元素，请检查路径或页面加载状态。",
                        "url_long": page.url
                        }
            }, ensure_ascii=False)
            print("未找到对应元素，请检查路径或页面加载状态。")
            return result
        
        # 尝试下载视频
        if status == "ALL_READY" and download_video:
            close_login_popup(close_btn)
            video_url = locators["video"].get_attribute("src")
            print('下载视频中...')   
            response = page.request.get(video_url)
            with open(f"{save_dir}/{title}-{author}.mp4", "wb") as f:
                f.write(response.body()) 
        
        return result


if __name__ == "__main__":
    # https://v.douyin.com/CpcD7JUpYEk/ 已下架
    # https://v.douyin.com/WogUSRW-pzM/ 短链接
    # https://www.iesdouyin.com/share/video/7568635678734328811 长link
    url = "https://v.douyin.com/WogUSRW-pzM/"
    
    config = Config_Douyin() 
    # XPath路径
    xpaths = config.xpaths
    # 创建等待列表，等待元素可见
    wait_list = config.wait_list
    save_dir = config.save_dir

    result = get_douyin_short_video_info(url, xpaths, wait_list, save_dir, download_video=True)
    print(result)
