import time
from pathlib import Path
from typing import Optional, Dict
from base_rpa import BaseRPA
from config import Config_Xhs
from playwright.sync_api import Page, sync_playwright

class XhsRPA(BaseRPA):
    def __init__(self, config: Config_Xhs):
        super().__init__(config, "小红书")
        self.xhs_homepage = "https://www.xiaohongshu.com"

    def _is_first_visit(self, user_data_dir: str) -> bool:
        """检查当前 context 是否是首次访问小红书"""
        marker_file = Path(user_data_dir) / ".xhs_initialized"
        return not marker_file.exists()
    
    def _mark_as_visited(self, user_data_dir: str):
        """标记当前 context 已经访问过小红书主页"""
        marker_file = Path(user_data_dir) / ".xhs_initialized"
        marker_file.parent.mkdir(parents=True, exist_ok=True)
        marker_file.touch()

    def _check_error_states(self, page: Page) -> Optional[str]:
        if page.get_by_text("你访问的页面不见了").count() > 0:
            return "PAGE_NOT_FOUND"
        if page.get_by_text("请打开小红书App扫码查看").count() > 0:
            return "MOBILE_LINK"
        if "com/login" in page.url:
            return "REDIRECT_WARNING"
        return None

    def _download(self, page: Page, title: str, author: str, download_media: bool) -> str:
        # 优先级：视频 -> 图片直播 -> 普通图片 -> 封面图
        media_selectors = ["video", "video source", self.xpaths["img_live"], self.xpaths["img"], self.xpaths["cover"]]
        
        save_path = Path(self.save_dir) / f"{self._safe_filename(title)}-{self._safe_filename(author)}.jpg"
        save_path.parent.mkdir(parents=True, exist_ok=True)

        for selector in media_selectors:
            try:
                loc = page.locator(selector).first
                if loc.count() == 0:
                    continue
                
                media_url = loc.get_attribute("src") or loc.get_attribute("data-src") or loc.get_attribute("data-original")
                if not media_url:
                    continue

                if media_url.startswith("//"):
                    media_url = "https:" + media_url

                if download_media:
                    response = page.request.get(media_url)
                    with open(save_path, "wb") as f:
                        f.write(response.body())
                return media_url
            except Exception:
                continue

        # 兜底截屏
        self._close_login_popup(page, self.xpaths["close_btn"])
        time.sleep(0.1)
        page.screenshot(path=str(save_path))
        return "screenshot"

    def run(self, url: str, download_media: bool = False, user_data_dir: Optional[str] = None, headless: bool = False, user_agent: Optional[str] = None, viewport: Optional[Dict[str, int]] = None, timezone_id: Optional[str] = None) -> str:
        """
        重写 run 方法，添加首次访问小红书主页的逻辑（用于反爬）。
        
        :param url: 目标页面 URL
        :param download_media: 是否下载媒体文件
        :param user_data_dir: 浏览器用户数据目录
        :param headless: 是否使用无头模式
        :param user_agent: 用户代理字符串
        :param viewport: 视口大小 {"width": 1920, "height": 1080}
        :param timezone_id: 时区 ID，如 "Asia/Shanghai"
        :return: JSON 结果字符串
        """
        # 如果未指定 user_data_dir，使用默认路径
        if user_data_dir is None:
            user_data_dir = str(Path(__file__).parent / "chrome-profile")
        
        # 检查是否需要首次访问主页
        is_first_visit = self._is_first_visit(user_data_dir)
        
        with sync_playwright() as p:
            browser_context = self._get_browser_context(p, user_data_dir, headless, user_agent, viewport, timezone_id)
            try:
                page = browser_context.new_page()
                
                # 如果是首次访问，先访问小红书主页
                if is_first_visit:
                    print(f"[INFO] 检测到新的 context，首次访问小红书主页: {self.xhs_homepage}")
                    page.goto(self.xhs_homepage, wait_until="domcontentloaded")
                    print("[INFO] 小红书主页加载完成，等待 2 秒...")
                    time.sleep(1)  # 额外等待一下，让页面完全加载
                    self._mark_as_visited(user_data_dir)
                    print("[INFO] 已标记为已访问，后续访问将跳过主页")
                
                # 访问目标 URL
                print(f"Opening {url} ...")
                page.goto(url, wait_until="domcontentloaded")
                time.sleep(1)
                return self.extract_info(page, url, download_media)
            except Exception as e:
                print(f"Error: {str(e)}")
                return self._convent_json(502, data={"url": page.url if 'page' in locals() else url}, message="ERROR: 抓取数据失败")
            finally:
                browser_context.close()

    def extract_info(self, page: Page, url: str, download_media: bool) -> str:
        locators = {k: page.locator(v) for k, v in self.xpaths.items()}
        status = self._poll_until_ready(page, locators, self.wait_list, self.xpaths["close_btn"])

        if status == "ALL_READY":
            title = self._safe_get_text(locators["title"], "title")
            author = self._safe_get_text(locators["author"], "author")
            media_url = self._download(page, title or "unnamed", author or "unnamed", download_media)

            data = {
                "title": title,
                "author": author,
                "content": self._safe_get_text(locators["content"], "content"),
                "likes": self._safe_get_text(locators["likes"], "likes"),
                "comments": self._safe_get_text(locators["comments"], "comments"),
                "publish_time": self._safe_get_text(locators["publish_time"], "publish_time"),
                "url": page.url,
                "media_url": media_url,
                "shares": None,
                "fans": None
            }
            return self._convent_json(200, data, message="SUCCESS: 小红书数据提取成功")
        
        elif status == "PAGE_NOT_FOUND":

            data = {"url": page.url}
            return self._convent_json(404, data=data, message="PAGE_NOT_FOUND: 作品已下架")
        elif status == "MOBILE_LINK":
            data = {"url": page.url}
            return self._convent_json(403, data=data, message="ERROR: 需要 APP 扫码授权")
        elif status == "REDIRECT_WARNING":
            data = {"url": page.url}
            return self._convent_json(502, data=data, message="ERROR: 可能被重定向到登录页")
        else:
            data = {"url": page.url}
            return self._convent_json(502, data=data, message="ERROR: 抓取数据失败")

def get_xhs_info(url, xpaths, wait_list, save_dir, download_img=False, user_data_dir: Optional[str] = None, headless: bool = False, user_agent: Optional[str] = None, viewport: Optional[Dict[str, int]] = None, timezone_id: Optional[str] = None):
    config = Config_Xhs()
    # 兼容旧接口
    rpa = XhsRPA(config)
    return rpa.run(url, download_media=download_img, user_data_dir=user_data_dir, headless=headless, user_agent=user_agent, viewport=viewport, timezone_id=timezone_id)

if __name__ == "__main__":
    url = "http://xhslink.com/o/3C2UqEN1jIz"
    config = Config_Xhs()
    rpa = XhsRPA(config)
    result = rpa.run(url, download_media=False, headless=False)
    print(result)
