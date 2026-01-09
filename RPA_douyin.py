import re
import time
from pathlib import Path
from typing import Optional, Dict
from base_rpa import BaseRPA
from config import Config_Douyin
from playwright.sync_api import Page, Locator

class DouyinRPA(BaseRPA):
    def __init__(self, config: Config_Douyin):
        super().__init__(config, "抖音")

    def _check_error_states(self, page: Page) -> Optional[str]:
        if page.get_by_text("你要观看的图文不存在").count() > 0 or page.get_by_text("视频不存在").count() > 0:
            return "PAGE_NOT_FOUND"
        return None

    def _download(self, page: Page, title: str, author: str, download_media: bool, locator_video: Optional[Locator], close_btn_selector: str) -> str:
        if locator_video:
            save_path = Path(self.save_dir) / f"{self._safe_filename(title or 'unnamed')}-{self._safe_filename(author or 'unnamed')}.mp4"
            save_path.parent.mkdir(parents=True, exist_ok=True)
            self._close_login_popup(page, close_btn_selector)
            
            video_url = None
            try:
                # 优先通过浏览器性能记录(Performance API)查找包含 mime_type=video_mp4 的网络请求
                # 这种方式可以捕获到在此函数调用前已经发生的网络请求
                video_url = page.evaluate("""
                    () => {
                        const entries = performance.getEntriesByType('resource');
                        const videoEntry = entries.find(e => e.name.includes('mime_type=video_mp4'));
                        return videoEntry ? videoEntry.name : null;
                    }
                """)
                
                # 如果性能记录中没有，尝试监听后续可能发生的请求（如自动播放或触发加载）
                if not video_url:
                    try:
                        with page.expect_response(lambda res: "mime_type=video_mp4" in res.url, timeout=3000) as response_info:
                            video_url = response_info.value.url
                    except:
                        pass
            except Exception as e:
                print(f"Error intercepting video URL: {e}")

            try:
                if download_media and video_url and video_url.startswith("http"):
                    # 使用 page.request.get 确保使用当前页面的 cookies 和 context
                    response = page.request.get(video_url)
                    if response.ok:
                        with open(save_path, "wb") as f:
                            f.write(response.body())
                    else:
                        print(f"Download failed with status: {response.status}")
                return video_url or None
            except Exception as e:
                print(f"Error during video download: {e}")
                return None
        else:
            save_path = Path(self.save_dir) / f"{self._safe_filename(author or 'unnamed')}.jpg"
            save_path.parent.mkdir(parents=True, exist_ok=True)
            self._close_login_popup(page, close_btn_selector)
            time.sleep(0.3)
            page.screenshot(path=str(save_path))
            return "screenshot"

    def extract_info(self, page: Page, url: str, download_media: bool) -> str:
        if "douyin.com/video" in page.url:
            return self._extract_video(page, download_media)
        elif "douyin.com/note" in page.url:
            return self._extract_note(page, download_media)
        else:
            return self._convent_json(400)

    def _extract_video(self, page: Page, download_media: bool) -> str:
        v_xpaths = self.xpaths["video_xpaths"]
        v_wait_list = self.config.wait_list["video_wait_list"]
        locators = {k: page.locator(v) for k, v in v_xpaths.items()}

        status = self._poll_until_ready(page, locators, v_wait_list, v_xpaths["video_close_btn"])
        if status == "ALL_READY":
            title = self._safe_get_text(locators["video_title"], "video_title")
            author = self._safe_get_text(locators["video_author"], "video_author")
            like  = self._safe_get_text(locators["video_likes"], "video_likes")
            comments = self._safe_get_text(locators["video_comments"], "video_comments")
            shares = self._safe_get_text(locators["video_shares"], "video_shares")
            fans = self._safe_get_text(locators["video_fans"], "video_fans")
            publish_time = self._safe_get_text(locators["video_publish_time"], "video_publish_time")
            url_long = page.url

            video_url = self._download(page, title, author, download_media, locators["video_video"], v_xpaths["video_close_btn"])

            data = {
                "title": title,
                "author": author,
                "content": None,
                "likes": like,
                "comments": comments,
                "shares": shares,
                "fans": fans,
                "publish_time": publish_time,
                "url": url_long,
                "media_url": video_url
            }
            return self._convent_json(200, data, message="SUCCESS: 抖音数据提取成功")
        
        if status == "PAGE_NOT_FOUND":
            data = {"url": page.url}
            return self._convent_json(404, data=data, message="PAGE_NOT_FOUND: 作品已下架")

        else:
            data = {"url": page.url}
            return self._convent_json(502, data=data, message="ERROR: 抓取数据失败")

    def _extract_note(self, page: Page, download_media: bool) -> str:
        n_xpaths = self.xpaths["note_xpaths"]
        n_wait_list = self.config.wait_list["note_wait_list"]
        locators = {k: page.locator(v) for k, v in n_xpaths.items()}

        status = self._poll_until_ready(page, locators, n_wait_list, n_xpaths["note_close_btn"])
        if status == "ALL_READY":

            title_raw = self._safe_get_text(locators["note_title"], "note_title")
            title = re.split(r"发布时间：", title_raw.replace("\n", "").strip())[0].strip() if title_raw else None
            author = self._safe_get_text(locators["note_author"], "note_author")
            # Douyin note stats are often combined in one element, need custom parsing if necessary
            # but original code had some specific logic:

            # self._close_login_popup(page, n_xpaths["note_close_btn"])
            likes_comments_favorites_shares = locators["note_likes"].first.inner_text(timeout=1000)
            likes, comments, favorites, shares = None, None, None, None
            if likes_comments_favorites_shares:
                parts = likes_comments_favorites_shares.split("\n")
                if len(parts) >= 1: likes = parts[0].strip()
                if len(parts) >= 2: comments = parts[1].strip()
                if len(parts) >= 3: favorites = parts[2].strip()
                if len(parts) >= 4: shares = parts[3].strip()

            media_url = self._download(page, title, author, download_media, None, n_xpaths["note_close_btn"])

            data = {
                "title": None,
                "author": author,
                "content": title, # Use title as content for notes
                "likes": likes,
                "comments": comments,
                "shares": shares,
                "fans": self._safe_get_text(locators["note_fans"], "note_fans"),
                "publish_time": self._safe_get_text(locators["note_publish_time"], "note_publish_time"),
                "url": page.url,
                "media_url": media_url
            }
            return self._convent_json(200, data, message="SUCCESS: 抖音数据提取成功")
        
        if status == "PAGE_NOT_FOUND":
            data = {"url": page.url}
            return self._convent_json(404, data=data, message="PAGE_NOT_FOUND: 作品已下架")

        else:
            data = {"url": page.url}
            return self._convent_json(502, data=data, message="ERROR: 抓取数据失败")

def get_douyin_short_video_info(url, xpaths, wait_list, save_dir, download_video=False, user_data_dir: Optional[str] = None, headless: bool = False, user_agent: Optional[str] = None, viewport: Optional[Dict[str, int]] = None, timezone_id: Optional[str] = None):
    config = Config_Douyin()
    rpa = DouyinRPA(config)
    return rpa.run(url, download_media=download_video, user_data_dir=user_data_dir, headless=headless, user_agent=user_agent, viewport=viewport, timezone_id=timezone_id)

if __name__ == "__main__":
    url = "https://v.douyin.com/CpcD7JUpYEk/"
    config = Config_Douyin()
    rpa = DouyinRPA(config)
    result = rpa.run(url, download_media=False, headless=False)
    print(result)
