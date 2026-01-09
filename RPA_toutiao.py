from pathlib import Path
from typing import Optional
from base_rpa import BaseRPA
from config import Config_Toutiao
from playwright.sync_api import Page, Locator
import time
from typing import Optional, Any, Dict, List

class ToutiaoRPA(BaseRPA):
    def __init__(self, config: Config_Toutiao):
        super().__init__(config, "头条")

    def _check_error_states(self, page: Page) -> Optional[str]:
        if page.get_by_text("内容不存在").count() > 0:
            return "PAGE_NOT_FOUND"
        if page.get_by_text("当前内容无法展示").count() > 0:
            return "PAGE_NOT_FOUND"
        return None
    def check_404(self, page: Page, locators: Dict[str, Locator], wait_keys: List[str], 
                          close_btn_selector: Optional[str] = None, timeout: float = 12.0) -> str:
        """
        循环检测页面元素是否就绪，或是否进入错误状态（下架/需扫码等）。
        
        :param page: Playwright Page 对象
        :param locators: 元素定位器字典
        :param wait_keys: 必须出现的元素键名列表
        :param close_btn_selector: 登录弹窗关闭按钮的 CSS/XPath
        :param timeout: 超时时间（秒）
        :return: 状态字符串（"ALL_READY", "TIMEOUT", 或自定义错误状态）
        """
        start = time.time()
        while time.time() - start < timeout:
            if close_btn_selector:
                self._close_login_popup(page, close_btn_selector)
            
            # 检查特定平台的错误状态（如 404、需扫码403）
            error_state = self._check_error_states(page)
            if error_state:
                return error_state

            time.sleep(0.5)
        
        return "TIMEOUT"
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
        elif "toutiao.com/article" in page.url:
            return self._extract_article(page, download_media)
        elif "toutiao.com/login" in page.url:
            return self._convent_json(403, message="LOGIN_REQUIRED: 需登录后访问")
        else:   # 对其他链接先404检查，否则才抛出400
            start = time.time()
            while time.time() - start < 1:  # 设置1s超时
                # 检查特定平台的错误状态（如 404、需扫码403）
                error_state = self._check_error_states(page)
                if error_state == "PAGE_NOT_FOUND":
                    return self._convent_json(404, data={"url": page.url}, message="PAGE_NOT_FOUND: 作品已下架")
                time.sleep(0.3)
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
            return self._convent_json(200, data, message="SUCCESS: 微头条数据提取成功")
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
            return self._convent_json(200, data, message="SUCCESS: 抖音数据提取成功")
        
        if status == "PAGE_NOT_FOUND":
            data = {"url": page.url}
            return self._convent_json(404, data=data, message="PAGE_NOT_FOUND: 作品已下架")
        elif status == "MOBILE_LINK":
            data = {"url": page.url}
            return self._convent_json(403, data=data, message="ERROR: 需要 APP 扫码授权")
        else:
            data = {"url": page.url}
            return self._convent_json(502, data=data, message="ERROR: 抓取数据失败")

    def _extract_article(self, page: Page, download_media: bool) -> str:
        a_xpaths = self.xpaths["a_xpaths"]
        a_wait_list = self.config.wait_list["a_wait_list"]
        locators = {k: page.locator(v) for k, v in a_xpaths.items()}

        status = self._poll_until_ready(page, locators, a_wait_list)
        if status == "ALL_READY":
            data = {
                "title": self._safe_get_text(locators["a_title"], "a_title"),
                "author": self._safe_get_text(locators["a_author"], "a_author"),
                "content": self._safe_get_text(locators["a_article"], "a_article"),
                "likes": self._safe_get_text(locators["a_likes"], "a_likes"),
                "comments": self._safe_get_text(locators["a_comments"], "a_comments"),
                "publish_time": self._safe_get_text(locators["a_publish_time"], "a_publish_time"),
                "web_name": "头条文章",
                "url": page.url,
                "media_url": None,
                "shares": None,
                "fans": None
            }
            return self._convent_json(200, data, message="SUCCESS: 微头条数据提取成功")
        if status == "PAGE_NOT_FOUND":
            return self._convent_json(404, data={"url": page.url}, message="PAGE_NOT_FOUND: 作品已下架")
        else:
            return self._convent_json(502, data={"url": page.url}, message="ERROR: 抓取数据失败")

def get_toutiao_info(url, xpaths, wait_list, save_dir, download_video=False, user_data_dir: Optional[str] = None, headless: bool = False, user_agent: Optional[str] = None, viewport: Optional[Dict[str, int]] = None, timezone_id: Optional[str] = None):
    config = Config_Toutiao()
    rpa = ToutiaoRPA(config)
    return rpa.run(url, download_media=download_video, user_data_dir=user_data_dir, headless=headless, user_agent=user_agent, viewport=viewport, timezone_id=timezone_id)

if __name__ == "__main__":
    url = "https://m.toutiao.com/article/7555347911730676233/?app=news_article&category_new=__search__&module_name=Android_tt_others&share_did=MS4wLjACAAAAxMTOW9OFmwO1BIKhPg2st-nicYPfGJux1scZxlFuIZNwhHscB0hTHhBTYjVZYwN-&share_uid=MS4wLjABAAAAxMTOW9OFmwO1BIKhPg2st-nicYPfGJux1scZxlFuIZNwhHscB0hTHhBTYjVZYwN-&timestamp=1767146449&tt_from=wechat&upstream_biz=Android_wechat&utm_campaign=client_share&utm_medium=toutiao_android&utm_source=wechat&share_token=ca74277c-e0a9-488f-9ba5-7ab68681a519"
    config = Config_Toutiao()
    rpa = ToutiaoRPA(config)
    result = rpa.run(url, download_media=False, headless=False)
    print(result)
