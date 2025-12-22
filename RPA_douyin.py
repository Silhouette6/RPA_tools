import re
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

def safe_filename(name, max_len=100):
    """
    文件名合法性审查
    """
    name = re.sub(r'[\\/:*?"<>|]', "_", name)
    name = name.strip()
    if not name:
        name = "unnamed"
    return name[:max_len]

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
     
def download(page, save_dir, title, author, close_btn ,locator_video = None):

    
    if locator_video:
        # 路径保护与文件名合法性处理
        save_path = f"{save_dir}/{title}-{author}.mp4"
        path_obj = Path(save_path)
        directory = path_obj.parent
        # 对文件名（不含后缀）进行合法性审查并重新拼接
        safe_name = f"{safe_filename(path_obj.stem)}{path_obj.suffix}"
        safe_save_path = str(directory / safe_name)
        close_login_popup(close_btn)
        video_url = locator_video.get_attribute("src")
        print('下载视频中...')   
        
        # 确保目录存在（路径保护）
        directory.mkdir(parents=True, exist_ok=True)

        response = page.request.get(video_url)
        with open(safe_save_path, "wb") as f:
            f.write(response.body()) 
        print(f"视频已保存至: {safe_save_path}")
    else:
        # ===== 兜底策略：截屏 （处理note）=====
        
        # 路径保护与文件名合法性处理
        save_path = f"{save_dir}/{title}-{author}.jpg"
        path_obj = Path(save_path)
        directory = path_obj.parent
        # 对文件名（不含后缀）进行合法性审查并重新拼接
        safe_name = f"{safe_filename(path_obj.stem)}{path_obj.suffix}"
        safe_save_path = str(directory / safe_name)
        print(f"解析视频失败，采用截屏策略保存至 {safe_save_path}")
        
        close_login_popup(close_btn)
        time.sleep(0.3)
        page.screenshot(path=safe_save_path)

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

        if "douyin.com/video" in page.url:
            video_xpaths = xpaths["video_xpaths"]
            video_wait_list = wait_list["video_wait_list"]

            close_btn = page.locator(video_xpaths["video_close_btn"])
            # 统一构建locator
            locators = {k: page.locator(v) for k, v in video_xpaths.items()}

            # 3️⃣ 等待正文就绪
            status = poll_until_ready(page=page, close_btn=close_btn, locators=locators, wait_list=video_wait_list)
            
            if status == "ALL_READY":
                def safe_get_text(key):
                    """
                    安全获取元素文本，处理可能的异常
                    """

                    start_time = time.time()
                    try:
                        r = locators[key].first.inner_text(timeout=1000)
                        if time.time() - start_time > 0.5:
                            print(f"warning: {key} 耗时 {time.time() - start_time} 秒")
                        return r
                    except Exception:
                        '''
                        # example: title 元素排版有时候很怪出现异常，导致获取失败，这里添加异常处理
                        if key == "title":
                            try:
                                r = locators["title_bak1"].first.inner_text(timeout=1000)
                                if time.time() - start_time > 0.5:
                                    print(f"warning: {key} 耗时 {time.time() - start_time} 秒")
                                return r
                            except Exception:
                                if time.time() - start_time > 0.5:
                                    print(f"error: {key} 耗时 {time.time() - start_time} 秒，title_bak1也不存在，获取title失败")
                                return None

                        else:
                            '''
                        if time.time() - start_time > 0.5:
                            print(f"warning: {key} 耗时 {time.time() - start_time} 秒，且进入了异常处理（是否因为该元素不存在？）")
                        return None

                title = safe_get_text("video_title")
                author = safe_get_text("video_author")
                result = json.dumps({
                    "code": 200,
                    "message": "success",
                    "data": {
                            "source": "抖音",
                            "status": "200",
                            "title": title, 
                            "author": author, 
                            "likes": safe_get_text("video_likes"), 
                            "comments": safe_get_text("video_comments"), 
                            "shares": safe_get_text("video_shares"), 
                            "fans": safe_get_text("video_fans"),
                            "publish_time": safe_get_text("video_publish_time"),
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
                download(page=page, save_dir=save_dir, title=title, author=author, close_btn=close_btn, locator_video=locators["video_video"])
        
        if "douyin.com/note" in page.url:
            note_xpaths = xpaths["note_xpaths"]
            note_wait_list = wait_list["note_wait_list"]

            close_btn = page.locator(note_xpaths["note_close_btn"])
            # 统一构建locator
            locators = {k: page.locator(v) for k, v in note_xpaths.items()}

            # 3️⃣ 等待正文就绪
            status = poll_until_ready(page=page, close_btn=close_btn, locators=locators, wait_list=note_wait_list)
            
            if status == "ALL_READY":
                def safe_get_text(key):
                    """
                    安全获取元素文本，处理可能的异常
                    """

                    start_time = time.time()
                    try:
                        r = locators[key].first.inner_text(timeout=1000)
                        if time.time() - start_time > 0.5:
                            print(f"warning: {key} 耗时 {time.time() - start_time} 秒")
                        return r
                    except Exception:
                        '''
                        # example: title 元素排版有时候很怪出现异常，导致获取失败，这里添加异常处理
                        if key == "title":
                            try:
                                r = locators["title_bak1"].first.inner_text(timeout=1000)
                                if time.time() - start_time > 0.5:
                                    print(f"warning: {key} 耗时 {time.time() - start_time} 秒")
                                return r
                            except Exception:
                                if time.time() - start_time > 0.5:
                                    print(f"error: {key} 耗时 {time.time() - start_time} 秒，title_bak1也不存在，获取title失败")
                                return None

                        else:
                            '''
                        if time.time() - start_time > 0.5:
                            print(f"warning: {key} 耗时 {time.time() - start_time} 秒，且进入了异常处理（是否因为该元素不存在？）")
                        return None

                title = safe_get_text("note_title")
                author = safe_get_text("note_author")
                result = json.dumps({
                    "code": 200,
                    "message": "success",
                    "data": {
                            "source": "抖音",
                            "status": "200",
                            "title": title, 
                            "author": author, 
                            "likes": safe_get_text("note_likes"), 
                            "comments": safe_get_text("note_comments"), 
                            "favorites": safe_get_text("note_favorites"),
                            "shares": safe_get_text("note_shares"), 
                            "fans": safe_get_text("note_fans"),
                            "publish_time": safe_get_text("note_publish_time"),
                            "url_long": page.url
                            }
                }, ensure_ascii=False)
                # print(result)

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
                download(page=page, save_dir=save_dir, title=title, author=author, close_btn=close_btn, locator_video = None)

        return result


if __name__ == "__main__":
    # https://v.douyin.com/CpcD7JUpYEk/ 已下架
    # https://v.douyin.com/WogUSRW-pzM/ 短链接
    # https://www.iesdouyin.com/share/video/7568635678734328811 长link

    
    url = "http://xhslink.com/o/6sk7iUPYhxj"
    
    config = Config_Douyin() 
    # XPath路径
    xpaths = config.xpaths
    # 创建等待列表，等待元素可见
    wait_list = config.wait_list
    save_dir = config.save_dir

    result = get_douyin_short_video_info(url, xpaths, wait_list, save_dir, download_video=True)
    print(result)
