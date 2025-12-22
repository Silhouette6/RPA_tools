
from playwright.sync_api import sync_playwright
from pathlib import Path
import time
import json
import re
from urllib3.util import url
from config import Config_Xhs

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
        print("trying")
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

def download(page, img_xpath, save_dir, close_btn):
    """
    通用图片下载器：
    - 支持 <img src / data-src / data-original>
    - 兜底策略：截屏当前页面图片
    
    :param page: Playwright Page 对象
    :param img_xpath: XPath 列表（按优先级）
    :param img_name: 保存文件名
    :return: img_url 或 "screenshot"
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
            img = page.locator(xp).first
            img.wait_for(state="attached", timeout=500)
            img_url = None

            # ===== 1️⃣ 普通 img 标签 =====
            img_url = (
                img.get_attribute("src")
                or img.get_attribute("data-src")
                or img.get_attribute("data-original")
            )

            if not img_url:
                continue

            # ===== 2️⃣ // URL 修正 =====
            if img_url.startswith("//"):
                img_url = "https:" + img_url

            print("img url:", img_url)

            # ===== 3️⃣ 下载 =====
            response = page.request.get(img_url)
            with open(safe_save_path, "wb") as f:
                f.write(response.body())

            return img_url

        except Exception as e:
            continue

    # ===== 4️⃣ 兜底策略：截屏 =====
    print(f"解析图片失败，采用截屏策略保存至 {safe_save_path}")
    close_login_popup(close_btn)
    time.sleep(0.3)
    page.screenshot(path=safe_save_path)
    return "screenshot"

def get_xhs_info(url, xpaths, wait_list, save_dir, download_img = True):

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

        close_btn = page.locator(xpaths["close_btn"])
        # 统一构建locator
        locators = {k: page.locator(v) for k, v in xpaths.items()}
        
        # 3️⃣ 等待正文就绪
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
            
            result = json.dumps({
                "code": 200,
                "message": "success",
                "data": {
                        "source": "小红书",
                        "status": "200",
                        "title": title, 
                        "content": content,
                        "author": author, 
                        "likes": safe_get_text("likes"), 
                        "favours": safe_get_text("favours"),
                        "comments": safe_get_text("comments"), 
                        "publish_time": safe_get_text("publish_time"),
                        "url_long": page.url
                        }
            }, ensure_ascii=False)
            # print(result)
        
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

        # 4️⃣ 尝试下载图片
        if status == "ALL_READY" and download_img:
            try:
                download(page, [xpaths["img_live"], xpaths["img"], xpaths["cover"]], f"{save_dir}/{title}-{author}.jpg" , close_btn)
            except:
                print("未找到图片元素，请检查路径或页面加载状态。")
        
        return result


if __name__ == "__main__":
    # 五种情况
    # http://xhslink.com/o/8PdviBz0NBi live_img
    # http://xhslink.com/o/9B1KLuSUesI img
    # http://xhslink.com/o/6kZ7NPjrUJa video_cover
    # http://xhslink.com/o/3C2UqEN1jIz 已下架
    # https://www.xiaohongshu.com/discovery/item/6911a4c30000000004005418 移动端扫码链接
    
    url = "http://xhslink.com/o/3C2UqEN1jIz"
    
    config = Config_Xhs()

    # XPath路径
    xpaths= config.xpaths
    wait_list = config.wait_list
    save_dir = config.save_dir

    result = get_xhs_info(url, xpaths, wait_list, save_dir, download_img=True)
    print(result)
