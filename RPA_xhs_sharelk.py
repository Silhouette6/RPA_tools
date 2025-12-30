import time
from pathlib import Path
from typing import Optional
from base_rpa import BaseRPA
from config import Config_Xhs
from playwright.sync_api import Page

class XhsRPA(BaseRPA):
    def __init__(self, config: Config_Xhs):
        super().__init__(config, "小红书")

    def _check_error_states(self, page: Page) -> Optional[str]:
        if page.get_by_text("你访问的页面不见了").count() > 0:
            return "PAGE_NOT_FOUND"
        if page.get_by_text("请打开小红书App扫码查看").count() > 0:
            return "MOBILE_LINK"
        return None

    def _download(self, page: Page, title: str, author: str, download_media: bool) -> str:
        # 优先级：视频 -> 图片直播 -> 普通图片 -> 封面图
        media_selectors = ["video", "video source", self.xpaths["img_live"], self.xpaths["img"], self.xpaths["cover"]]
        
        save_path = Path(self.save_dir) / f"{self._safe_filename(title)}-{self._safe_filename(author)}.jpg"
        save_path.parent.mkdir(parents=True, exist_ok=True)

        for selector in media_selectors:
            try:
                loc = page.locator(selector).first
                if loc.count() == 0: continue
                
                media_url = loc.get_attribute("src") or loc.get_attribute("data-src") or loc.get_attribute("data-original")
                if not media_url: continue

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
            return self._convent_json(200, data)
        
        elif status == "PAGE_NOT_FOUND":

            data = {"url": page.url}
            return self._convent_json(404, data=data, message="PAGE_NOT_FOUND: 作品已下架")
        elif status == "MOBILE_LINK":
            data = {"url": page.url}
            return self._convent_json(403, data=data, message="ERROR: 需要 APP 扫码授权")
        else:
            data = {"url": page.url}
            return self._convent_json(502, data=data, message="ERROR: 抓取数据失败")

def get_xhs_info(url, xpaths, wait_list, save_dir, download_img=False, user_data_dir: Optional[str] = None, headless: bool = False):
    config = Config_Xhs()
    # 兼容旧接口
    rpa = XhsRPA(config)
    return rpa.run(url, download_media=download_img, user_data_dir=user_data_dir, headless=headless)

if __name__ == "__main__":
    url = "http://xhslink.com/o/3C2UqEN1jIz"
    config = Config_Xhs()
    rpa = XhsRPA(config)
    result = rpa.run(url, download_media=False, headless=False)
    print(result)
