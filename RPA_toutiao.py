import re
from playwright.sync_api import sync_playwright
from pathlib import Path
import time
import json
from urllib3.util import url
from config import Config_Toutiao
from typing import Optional

"""
头条RPA，基于层级结构提取内容
TODO:
toutiao/w
toutiao/video
"""
def safe_filename(name, max_len=100):
    """
    文件名合法性审查
    """
    name = re.sub(r'[\\/:*?"<>|]', "_", name)
    name = name.strip()
    if not name:
        name = "unnamed"
    return name[:max_len]

def download(page, video_locator, save_path, download_img: bool = True):
    """
    下载视频并应用路径保护与文件名合法性审查
    """
    # 路径保护与文件名合法性处理
    path_obj = Path(save_path)
    directory = path_obj.parent
    # 对文件名（不含后缀）进行合法性审查并重新拼接
    safe_name = f"{safe_filename(path_obj.stem)}{path_obj.suffix}"
    safe_save_path = str(directory / safe_name)
    
    # 确保目录存在（路径保护）
    directory.mkdir(parents=True, exist_ok=True)

    try:
        # 等 video 出现在 DOM 中即可，不用等播放
        video_locator.wait_for(state="attached", timeout=10000)

        video_url = video_locator.get_attribute("src")
        if not video_url:
            return None
        if video_url.startswith("//"):
            video_url = "https:" + video_url
        headers = {
            "Referer": "https://www.toutiao.com/",
            "User-Agent": page.evaluate("navigator.userAgent")
        }
        if download_img:
            response = page.request.get(video_url, headers=headers, timeout=10000)
            if not response.ok:
                return video_url
            with open(safe_save_path, "wb") as f:
                f.write(response.body())
        return video_url
    except Exception:
        return None

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
        # print("tring")

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

def get_toutiao_info(url, xpaths, wait_list, save_dir, download_video = False, user_data_dir: Optional[str] = None, headless: bool = False):

    with sync_playwright() as p:
        if user_data_dir is None:
            user_data_dir = str(Path(__file__).parent / "chrome-profile")
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            channel="chrome",
            headless=headless,
        )
        try:
            page = context.new_page()

            print(f"Opening {url} ...")
            page.goto(url, wait_until="domcontentloaded")

            if "toutiao.com/w" in url:
                w_xpaths = xpaths["w_xpaths"]
                w_wait_list = wait_list["w_wait_list"]
                locators = {k: page.locator(v) for k, v in w_xpaths.items()}

                status = poll_until_ready(page=page, locators=locators, wait_list=w_wait_list)
            
                if status == "ALL_READY":
                    def safe_get_text(key):
                        try:
                            return locators[key].first.inner_text()
                        except Exception:
                            return None

                    content = safe_get_text("w_content")
                    author = safe_get_text("w_author")
                    likes = safe_get_text("w_likes")
                    publish_time = safe_get_text("w_publish_time")
                    url_long = page.url

                    result = json.dumps({
                        "code": 200,
                        "message": "success",
                        "data": {
                                "web_name": "微头条",
                                "status": "200",
                                "content": content, 
                                "author": author, 
                                "praise_count": likes, 
                                "publish_time": publish_time,
                                "url": url_long,
                                "video_urls": None
                                }
                    }, ensure_ascii=False)
                
                elif status == "PAGE_NOT_FOUND":
                    result = json.dumps({
                        "code": 200,
                        "message": "PAGE_NOT_FOUND已下架",
                        "data": {
                                "web_name": "微头条",
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
                                "web_name": "微头条",
                                "status": "400",
                                "message": "未找到对应元素，请检查路径或页面加载状态。",
                                "url": page.url
                                }
                    }, ensure_ascii=False)
                    print("未找到对应元素，请检查路径或页面加载状态。")
                    return result
            
            elif "toutiao.com/video" in url:
                video_xpaths = xpaths["video_xpaths"]
                video_wait_list = wait_list["video_wait_list"]
                locators = {k: page.locator(v) for k, v in video_xpaths.items()}

                status = poll_until_ready(page=page, locators=locators, wait_list=video_wait_list)
            
                if status == "ALL_READY":
                    def safe_get_text(key):
                        try:
                            return locators[key].first.inner_text()
                        except Exception:
                            return None

                    content = safe_get_text("video_content")
                    author = safe_get_text("video_author")
                    views = safe_get_text("video_views")
                    likes = safe_get_text("video_likes")
                    publish_time = safe_get_text("video_publish_time")
                    url_long = page.url
                    
                    video_url = download(page, locators["video_video"].first, f"{save_dir}/{author}.mp4", download_img=download_video)

                    result = json.dumps({
                        "code": 200,
                        "message": "success",
                        "data": {
                                "web_name": "头条视频",
                                "status": "200",
                                "content": content, 
                                "author": author, 
                                "views": views, 
                                "praise_count": likes, 
                                "publish_time": publish_time,
                                "url": url_long,
                                "video_urls": video_url
                                }
                    }, ensure_ascii=False)
                
                elif status == "PAGE_NOT_FOUND":
                    result = json.dumps({
                        "code": 200,
                        "message": "PAGE_NOT_FOUND已下架",
                        "data": {
                                "web_name": "头条视频",
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
                                "web_name": "头条视频",
                                "status": "400",
                                "message": "未找到对应元素，请检查路径或页面加载状态。",
                                "url": page.url
                                }
                    }, ensure_ascii=False)
                    print("未找到对应元素，请检查路径或页面加载状态。")
                    return result
            else:
                result = json.dumps({
                    "code": 400,
                    "message": "400不支持的url类型",
                    "data": {
                            "web_name": "头条",
                            "status": "400",
                            "message": "不支持的url类型",
                            "url": page.url
                            }
                }, ensure_ascii=False)
                return result

            return result
        finally:
            context.close()


if __name__ == "__main__":
    # https://www.toutiao.com/w/1850041869600772/#ocr 
    # https://www.toutiao.com/w/1850641232900096/
    # https://www.toutiao.com/w/1848052368845833/ 已下架
    # https://www.toutiao.com/video/7523088690436898851/#ocr 视频
    # https://www.toutiao.com/video/7571580926610636841/ 视频2
    # https://www.toutiao.com/video/7571303297971060770/#ocr 视频已下架
    url = "https://www.toutiao.com/video/7523088690436898851/#ocr"
    
    config = Config_Toutiao() 
    # XPath路径
    xpaths = config.xpaths
    # 创建等待列表，等待元素可见
    wait_list = config.wait_list
    save_dir = config.save_dir

    result = get_toutiao_info(url, xpaths, wait_list, save_dir, download_video=False)
    print(result)
