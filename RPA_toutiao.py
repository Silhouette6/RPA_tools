import re
from playwright.sync_api import sync_playwright
from pathlib import Path
import time
import json
from datetime import datetime
from urllib3.util import url
from config import Config_Toutiao
from typing import Optional

"""
头条RPA，基于层级结构提取内容
"""

def convent_json(code: int, title: str, url_long: str, content: str, final_media_url: str, publish_time: str, web_name: str, likes: str, comments: str, shares: str, author: str, fans: str):
    def parse_publish_time(text: str) -> datetime | None:
        """
        将形如：
        - '发布时间：2025-11-06 20:27:40'
        - '发布时间：2025-12-17 15:30'
        的字符串解析为 datetime 对象

        解析失败返回 None
        """
        if not text:
            return text

        # 去掉前缀
        text = text.strip()
        if "：" in text:
            text = text.split("：", 1)[1].strip()

        # 尝试多种时间格式
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
        ]

        for fmt in formats:
            try:
                return str(datetime.strptime(text, fmt))
            except ValueError:
                continue

        return text

    def media_type(url: str) -> str:
        """
        根据URL判断媒体类型
        """
        try:
            if "video" in url:
                return "video"
            elif "image" in url:
                return "image"
            elif "screenshot" in url:
                return "screenshot"
            else:
                return "unknown"
        except Exception:
            return "unknown"

    def convert_counts(text: str) -> int | None:
        """
        将字符串形式的数量转换为整数
        解析失败返回 None
        """
        if not text:
            return None

        text = text.strip()

        try:
            if "千" in text:
                num = re.findall(r"[\d.]+", text)
                if not num:
                    return None
                return int(float(num[0]) * 1000)

            elif "万" in text:
                num = re.findall(r"[\d.]+", text)
                if not num:
                    return None
                return int(float(num[0]) * 10000)

            else:
                # 纯数字情况
                num = re.findall(r"\d+", text)
                if not num:
                    return None
                return int(num[0])

        except Exception:
            return None


    if code == 200:
        publish_time = parse_publish_time(publish_time)
        likes = convert_counts(likes)
        comments = convert_counts(comments)
        shares = convert_counts(shares)
        fans = convert_counts(fans)
        
        result = json.dumps({
            "code": code,
            "message": "success",
            "data": {
                "title": title,
                "url": url_long,
                "content": content,
                "media_type": media_type(final_media_url),  # 区分媒体类型
                "publish_time": publish_time,
                "web_name": web_name,
                "praise_count": likes,
                "forward_count": shares,  # 抖音无转发数则设为null
                "visit_count": None,
                "reply_count": comments,
                "author": author,
                "author_nickname": None,  # 未获取则设为null
                "author_fans_count": fans,
                "author_statuses_count": None,
                "ip_region": None,
                "user_id": author,  # 复用author
                "author_avatar_url": None,
                "media_urls": final_media_url,  # 无图片则设为空列表
            }
            }, ensure_ascii=False)

    if code == 404:
        result = json.dumps({
            "code": 404,
            "message": "PAGE_NOT_FOUND: 作品已下架",
            "data": {
                "title": None,
                "url": url_long,
                "content": None,
                "media_type": None,
                "publish_time": None,
                "web_name": web_name,
                "praise_count": None,
                "forward_count": None,
                "visit_count": None,
                "reply_count": None,
                "author": None,
                "author_nickname": None,
                "author_fans_count": None,
                "author_statuses_count": None,
                "ip_region": None,
                "user_id": None,
                "author_avatar_url": None,
                "img_urls": None,
                "video_urls": None,
            }
        }, ensure_ascii=False)

    if code == 403:
        result = json.dumps({
            "code": 403,
            "message": "ERROR: 需要 APP 扫码授权",
            "data": {
                "title": None,
                "url": url_long,
                "content": None,
                "media_type": None,
                "publish_time": None,
                "web_name": web_name,
                "praise_count": None,
                "forward_count": None,
                "visit_count": None,
                "reply_count": None,
                "author": None,
                "author_nickname": None,
                "author_fans_count": None,
                "author_statuses_count": None,
                "ip_region": None,
                "user_id": None,
                "author_avatar_url": None,
                "img_urls": None,
                "video_urls": None,
            }
        }, ensure_ascii=False)

    if code == 502:
        result = json.dumps({
            "code": 502,
            "message": "ERROR: 抓取数据失败",
            "data": {
                "title": None,
                "url": url_long,
                "content": None,
                "media_type": None,
                "publish_time": None,
                "web_name": web_name,
                "praise_count": None,
                "forward_count": None,
                "visit_count": None,
                "reply_count": None,
                "author": None,
                "author_nickname": None,
                "author_fans_count": None,
                "author_statuses_count": None,
                "ip_region": None,
                "user_id": None,
                "author_avatar_url": None,
                "img_urls": None,
                "video_urls": None,
            }
        }, ensure_ascii=False)
    
    if code == 400:
        result = json.dumps({
            "code": 400,
            "message": "ERROR: 不支持的链接",
            "data": {
                "title": None,
                "url": None,
                "content": None,
                "media_type": None,
                "publish_time": None,
                "web_name": web_name,
                "praise_count": None,
                "forward_count": None,
                "visit_count": None,
                "reply_count": None,
                "author": None,
                "author_nickname": None,
                "author_fans_count": None,
                "author_statuses_count": None,
                "ip_region": None,
                "user_id": None,
                "author_avatar_url": None,
                "img_urls": None,
                "video_urls": None,
            }
        }, ensure_ascii=False)

    return result

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

            if "toutiao.com/w" in page.url:
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

                    result = convent_json(
                        code=200,
                        title=None, # 微头条没有显式标题
                        url_long=url_long,
                        content=content,
                        final_media_url=None, # 微头条目前未处理媒体下载
                        publish_time=publish_time,
                        web_name="微头条",
                        likes=likes,
                        comments=None,
                        shares=None,
                        author=author,
                        fans=None
                    )
                
                elif status == "PAGE_NOT_FOUND":
                    result = convent_json(
                        code=404,
                        title=None,
                        url_long=page.url,
                        content=None,
                        final_media_url=None,
                        publish_time=None,
                        web_name="微头条",
                        likes=None,
                        comments=None,
                        shares=None,
                        author=None,
                        fans=None
                    )
                    return result

                else:
                    result = convent_json(
                        code=502,
                        title=None,
                        url_long=page.url,
                        content=None,
                        final_media_url=None,
                        publish_time=None,
                        web_name="微头条",
                        likes=None,
                        comments=None,
                        shares=None,
                        author=None,
                        fans=None
                    )
                    print("未找到对应元素，请检查路径或页面加载状态。")
                    return result
            
            elif "toutiao.com/video" in page.url:
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

                    result = convent_json(
                        code=200,
                        title=content, # 头条视频目前提取的是内容，没有显式标题
                        url_long=url_long,
                        content=None,
                        final_media_url=video_url,
                        publish_time=publish_time,
                        web_name="头条视频",
                        likes=likes,
                        comments=None, # 原始逻辑未提取评论数
                        shares=None,
                        author=author,
                        fans=None
                    )
                
                elif status == "PAGE_NOT_FOUND":
                    result = convent_json(
                        code=404,
                        title=None,
                        url_long=page.url,
                        content=None,
                        final_media_url=None,
                        publish_time=None,
                        web_name="头条视频",
                        likes=None,
                        comments=None,
                        shares=None,
                        author=None,
                        fans=None
                    )
                    return result

                else:
                    result = convent_json(
                        code=502,
                        title=None,
                        url_long=page.url,
                        content=None,
                        final_media_url=None,
                        publish_time=None,
                        web_name="头条视频",
                        likes=None,
                        comments=None,
                        shares=None,
                        author=None,
                        fans=None
                    )
                    print("未找到对应元素，请检查路径或页面加载状态。")
                    return result
            else:
                result = convent_json(
                    code=400,
                    title=None,
                    url_long=page.url,
                    content=None,
                    final_media_url=None,
                    publish_time=None,
                    web_name="头条",
                    likes=None,
                    comments=None,
                    shares=None,
                    author=None,
                    fans=None
                )
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
    url = "https://weitoutiao.zjurl.cn/ugc/share/wap/comment/7532665415143686975/#412c2b86822dc1697524f403d5fb32b0"
    
    config = Config_Toutiao() 
    # XPath路径
    xpaths = config.xpaths
    # 创建等待列表，等待元素可见
    wait_list = config.wait_list
    save_dir = config.save_dir

    result = get_toutiao_info(url, xpaths, wait_list, save_dir, download_video=False, headless=False)
    print(result)


