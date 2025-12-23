
from playwright.sync_api import sync_playwright
from pathlib import Path
import time
import json
import re
from urllib3.util import url
from config import Config_Xhs
from typing import Optional

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

def poll_until_ready(
    page,
    close_btn,
    locators,
    wait_list,
    timeout=12,
    interval=0.5):
    """
    :param page: Playwright Page 对象
    :param close_btn: 可能出现的关闭按钮
    :param locators: dict[str, Locator]，所有元素定位器
    :param wait_list: list[str]，必须就绪的键名列表
    :param timeout: 总超时（秒）
    :param interval: 轮询间隔
    """
    start = time.time()
    not_ready = None

    while time.time() - start < timeout:
        # print("trying")
        # 1️⃣ 如果 close 按钮出现，立刻点掉
        close_login_popup(close_btn)

        # 2️⃣ 检查特殊页面状态
        if page.get_by_text("你访问的页面不见了").count() > 0:
            print("Detected: Page not found (404)")
            return "PAGE_NOT_FOUND"
        
        if page.get_by_text("请打开小红书App扫码查看").count() > 0:
            print("Detected: Mobile QR code requirement (MOBILE_LINK)")
            return "MOBILE_LINK"

        # 3️⃣ 判断正文是否就绪（你定义的“整体”）
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

def download(page, img_xpath, save_dir, close_btn, download_img):
    """
    通用媒体下载器：
    - 支持 <img/video src / data-src / data-original>
    - 兜底策略：截屏当前页面
    
    :param page: Playwright Page 对象
    :param img_xpath: XPath/Selector 列表（按优先级）
    :param save_dir: 保存文件的完整路径
    :param close_btn: 登录弹窗关闭按钮定位器
    :param download_img: 是否执行实际的下载操作
    :return: 找到的媒体 URL 或 "screenshot"
    """

    # 路径保护与文件名合法性处理
    path_obj = Path(save_dir)
    directory = path_obj.parent
    # 对文件名（不含后缀）进行合法性审查并重新拼接
    safe_name = f"{safe_filename(path_obj.stem)}{path_obj.suffix}"
    safe_save_path = str(directory / safe_name)
    
    # 确保目录存在（路径保护）
    directory.mkdir(parents=True, exist_ok=True)

    for xp in img_xpath:
        try:
            loc = page.locator(xp).first
            loc.wait_for(state="attached", timeout=500)
            media_url = None

            # ===== 1️⃣ 多属性兼容提取 =====
            media_url = (
                loc.get_attribute("src")
                or loc.get_attribute("data-src")
                or loc.get_attribute("data-original")
            )

            if not media_url:
                continue

            # ===== 2️⃣ // URL 修正 =====
            if media_url.startswith("//"):
                media_url = "https:" + media_url

            print(f"found media url: {media_url}")

            # ===== 3️⃣ 执行下载 (可选) =====
            if download_img:
                response = page.request.get(media_url)
                with open(safe_save_path, "wb") as f:
                    f.write(response.body())
                print(f"saved to: {safe_save_path}")

            return media_url

        except Exception:
            continue

    # ===== 4️⃣ 兜底策略：截屏 =====
    print(f"无法解析媒体元素，采用截屏策略保存至 {safe_save_path}")
    close_login_popup(close_btn)
    time.sleep(0.3)
    page.screenshot(path=safe_save_path)
    return "screenshot"

def get_xhs_info(url, xpaths, wait_list, save_dir, download_img = False, user_data_dir: Optional[str] = None, headless: bool = False):

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

            close_btn = page.locator(xpaths["close_btn"])
            locators = {k: page.locator(v) for k, v in xpaths.items()}
            
            status = poll_until_ready(page=page, close_btn=close_btn, locators=locators, wait_list=wait_list)
            
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
                        if time.time() - start_time > 0.5:
                            print(f"warning: {key} 耗时 {time.time() - start_time} 秒，且进入了异常处理（是否因为该元素不存在？）")
                        return None

                title = safe_get_text("title")
                author = safe_get_text("author")
                content = safe_get_text("content")
                likes = safe_get_text("likes")
                favours = safe_get_text("favours")
                comments = safe_get_text("comments")
                publish_time = safe_get_text("publish_time")
                url_long = page.url

                # 让 download 统一处理媒体 URL 提取与下载（包括截屏兜底）
                # 优先级：视频 -> 图片直播 -> 普通图片 -> 封面图
                media_selectors = ["video", "video source", xpaths["img_live"], xpaths["img"], xpaths["cover"]]
                final_media_url = download(
                    page=page, 
                    img_xpath=media_selectors, 
                    save_dir=f"{save_dir}/{safe_filename(title)}-{safe_filename(author)}.jpg", 
                    close_btn=close_btn, 
                    download_img=download_img
                )

                result = json.dumps({
                    "code": 200,
                    "message": "success",
                    "data": {
                            "source": "小红书",
                            "status": "200",
                            "title": title, 
                            "content": content,
                            "author": author, 
                            "likes": likes, 
                            "favours": favours,
                            "comments": comments, 
                            "publish_time": publish_time,
                            "url_long": url_long,
                            "video_url": final_media_url # 这里返回最终确定的媒体地址或 "screenshot"
                            }
                }, ensure_ascii=False)

            
            elif status == "PAGE_NOT_FOUND":
                result = json.dumps({
                    "code": 200,
                    "message": "PAGE_NOT_FOUND已下架",
                    "data": {
                            "source": "小红书",
                            "status": "PAGE_NOT_FOUND",
                            "message": "检查到作品已下架",
                            "url_long": page.url
                            }
                }, ensure_ascii=False)
                return result

            elif status == "MOBILE_LINK":
                result = json.dumps({
                    "code": 200,
                    "message": "MOBILE_LINK移动端链接无法直接访问",
                    "data": {
                            "source": "小红书",
                            "status": "MOBILE_LINK",
                            "message": "该网页为移动端链接，需要app扫描授权",
                            "url_long": page.url
                            }
                }, ensure_ascii=False)
                return result
            else:
                result = json.dumps({
                    "code": 400,
                    "message": "400未找到对应元素，请检查路径或页面加载状态。",
                    "data": {
                            "source": "小红书",
                            "status": "400",
                            "message": "未找到对应元素，请检查路径或页面加载状态。",
                            "url_long": page.url
                            }
                }, ensure_ascii=False)
                print("未找到对应元素，请检查路径或页面加载状态。")
                return result

            
            return result
        finally:
            context.close()


if __name__ == "__main__":
    # 五种情况
    # http://xhslink.com/o/8PdviBz0NBi live_img
    # http://xhslink.com/o/9B1KLuSUesI img
    # http://xhslink.com/o/6kZ7NPjrUJa video_cover
    # http://xhslink.com/o/3C2UqEN1jIz 已下架
    # https://www.xiaohongshu.com/discovery/item/6911a4c30000000004005418 移动端扫码链接
    
    url = "https://www.xiaohongshu.com/discovery/item/6911a4c30000000004005418"
    
    config = Config_Xhs()

    # XPath路径
    xpaths= config.xpaths
    wait_list = config.wait_list
    save_dir = config.save_dir

    result = get_xhs_info(url, xpaths, wait_list, save_dir, download_img=False)
    print(result)
