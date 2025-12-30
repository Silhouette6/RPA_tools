from pathlib import Path
from typing import Optional
from base_rpa import BaseRPA
from config import Config_Toutiao
from playwright.sync_api import Page

class ToutiaoRPA(BaseRPA):
    def __init__(self, config: Config_Toutiao):
        super().__init__(config, "头条")

    def _check_error_states(self, page: Page) -> Optional[str]:
        if page.get_by_text("内容不存在").count() > 0:
            return "PAGE_NOT_FOUND"
        return None

    def _download_video(self, page: Page, author: str, download_media: bool, video_selector: str) -> Optional[str]:
        save_path = Path(self.save_dir) / f"{self._safe_filename(author)}.mp4"
        save_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            loc = page.locator(video_selector).first
            loc.wait_for(state="attached", timeout=5000)
            video_url = loc.get_attribute("src")
            if not video_url: return None
            
            if video_url.startswith("//"):
                video_url = "https:" + video_url
            
            if download_media:
                headers = {"Referer": "https://www.toutiao.com/", "User-Agent": page.evaluate("navigator.userAgent")}
                response = page.request.get(video_url, headers=headers, timeout=10000)
                if response.ok:
                    with open(save_path, "wb") as f:
                        f.write(response.body())
            return video_url
        except Exception:
            return None

    def extract_info(self, page: Page, url: str, download_media: bool) -> str:
        if "toutiao.com/w" in page.url:
            return self._extract_weitoutiao(page, download_media)
        elif "toutiao.com/video" in page.url:
            return self._extract_video(page, download_media)
        else:
            return self._convent_json(400, message="URL_NOT_SUPPORTED: 不支持的今日头条URL格式")

    def _extract_weitoutiao(self, page: Page, download_media: bool) -> str:
        w_xpaths = self.xpaths["w_xpaths"]
        w_wait_list = self.config.wait_list["w_wait_list"]
        locators = {k: page.locator(v) for k, v in w_xpaths.items()}

        status = self._poll_until_ready(page, locators, w_wait_list)
        if status == "ALL_READY":
            data = {
                "title": None,
                "author": self._safe_get_text(locators["w_author"], "w_author"),
                "content": self._safe_get_text(locators["w_content"], "w_content"),
                "likes": self._safe_get_text(locators["w_likes"], "w_likes"),
                "publish_time": self._safe_get_text(locators["w_publish_time"], "w_publish_time"),
                "web_name": "微头条",
                "url": page.url,
                "media_url": None,
                "comments": None,
                "shares": None,
                "fans": None
            }
            return self._convent_json(200, data)
        if status == "PAGE_NOT_FOUND":
            return self._convent_json(404, data={"url": page.url}, message="PAGE_NOT_FOUND: 作品已下架")
        else:
            return self._convent_json(502, data={"url": page.url}, message="ERROR: 抓取数据失败")

    def _extract_video(self, page: Page, download_media: bool) -> str:
        v_xpaths = self.xpaths["video_xpaths"]
        v_wait_list = self.config.wait_list["video_wait_list"]
        locators = {k: page.locator(v) for k, v in v_xpaths.items()}

        status = self._poll_until_ready(page, locators, v_wait_list)
        if status == "ALL_READY":
            author = self._safe_get_text(locators["video_author"], "video_author")
            video_url = self._download_video(page, author or "unnamed", download_media, v_xpaths["video_video"])
            
            data = {
                "title": self._safe_get_text(locators["video_content"], "video_content"),
                "author": author,
                "content": None,
                "likes": self._safe_get_text(locators["video_likes"], "video_likes"),
                "publish_time": self._safe_get_text(locators["video_publish_time"], "video_publish_time"),
                "url": page.url,
                "media_url": video_url,
                "comments": None,
                "shares": None,
                "fans": None
            }
            return self._convent_json(200, data)
        
        if status == "PAGE_NOT_FOUND":
            data = {"url": page.url}
            return self._convent_json(404, data=data, message="PAGE_NOT_FOUND: 作品已下架")
        elif status == "MOBILE_LINK":
            data = {"url": page.url}
            return self._convent_json(403, data=data, message="ERROR: 需要 APP 扫码授权")
        else:
            data = {"url": page.url}
            return self._convent_json(502, data=data, message="ERROR: 抓取数据失败")

def get_toutiao_info(url, xpaths, wait_list, save_dir, download_video=False, user_data_dir: Optional[str] = None, headless: bool = False):
    config = Config_Toutiao()
    rpa = ToutiaoRPA(config)
    return rpa.run(url, download_media=download_video, user_data_dir=user_data_dir, headless=headless)

if __name__ == "__main__":
    url = "https://www.toutiao.com/w/1848052368845833/"
    config = Config_Toutiao()
    rpa = ToutiaoRPA(config)
    result = rpa.run(url, download_media=False, headless=False)
    print(result)
