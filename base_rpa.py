import re
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Any, Dict, List
from playwright.sync_api import sync_playwright, Page, BrowserContext, Locator

class BaseRPA:
    """
    RPA 爬虫基类，提供 Playwright 环境管理、数据清洗、统一输出格式等公共功能。
    所有特定平台的 RPA 脚本（如抖音、小红书）应继承此类并实现 extract_info 方法。
    """
    def __init__(self, config: Any, web_name: str):
        """
        初始化 RPA 基础配置。
        
        :param config: 平台相关的配置对象（需包含 save_dir, xpaths, wait_list 等属性）
        :param web_name: 网站名称（用于日志和 JSON 输出中的 web_name 字段）
        """
        self.config = config
        self.web_name = web_name
        self.save_dir = getattr(config, "save_dir", "data/default")
        self.xpaths = getattr(config, "xpaths", {})
        self.wait_list = getattr(config, "wait_list", [])

    def _safe_filename(self, name: str, max_len: int = 100) -> str:
        """
        处理文件名，去除 Windows/Linux 系统不支持的特殊字符，并限制长度。
        """
        name = re.sub(r'[\\/:*?"<>|]', "_", name)
        name = name.strip()
        if not name:
            name = "unnamed"
        return name[:max_len]

    def _parse_publish_time(self, text: str) -> Optional[str]:
        """
        解析各种格式的发布时间字符串。
        支持格式：
        - "X天前"
        - "发布时间：2023-01-01 12:00:00"
        - "12-17 北京" (月-日 地区)
        - 标准日期格式 "%Y-%m-%d %H:%M:%S" 等
        """
        if not text:
            return None
        text = text.strip()
        
        # 1. 处理 “X天前”
        match = re.search(r"(\d+)\s*天前", text)
        if match:
            days = int(match.group(1))
            return str(datetime.now() - timedelta(days=days))

        # 2. 去掉“发布时间：”、“发布于”等前缀
        if "：" in text:
            text = text.split("：", 1)[1].strip()
        elif text.startswith("发布于"):
            text = text[len("发布于"):].strip()

        # 3. 处理带地区的情况，如 "12-17 北京" 或 "2023-12-17 广东"
        # 提取前面的日期部分 (匹配数字、破折号、冒号、空格组成的日期时间部分)
        time_part_match = re.match(r"^(\d{2,4}-\d{1,2}-\d{1,2}(\s\d{1,2}:\d{1,2}(:\d{1,2})?)?|\d{1,2}-\d{1,2}(\s\d{1,2}:\d{1,2})?)", text)
        if time_part_match:
            text = time_part_match.group(1).strip()

        # 4. 尝试多种绝对时间格式
        formats_with_year = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
        ]
        
        for fmt in formats_with_year:
            try:
                return str(datetime.strptime(text, fmt))
            except ValueError:
                continue

        # 5. 处理不带年份的格式，如 "12-17"，默认为当前年份
        formats_without_year = [
            "%m-%d %H:%M",
            "%m-%d",
        ]
        current_year = datetime.now().year
        for fmt in formats_without_year:
            try:
                dt = datetime.strptime(text, fmt)
                dt = dt.replace(year=current_year)
                return str(dt)
            except ValueError:
                continue
        
        print(f"[Warining]:无法解析时间格式: {text}")
        return None

    def _convert_counts(self, text: Any) -> Optional[int]:
        """
        将字符串形式的数量（如 "1.2万", "3千"）转换为整数。
        """
        if text is None:
            return None
        if isinstance(text, (int, float)):
            return int(text)
        
        text = str(text).strip()
        if not text:
            return None
        
        if not any(ch.isdigit() for ch in text):
            # 处理非数字字符串，默认返 0
            return 0
        try:
            if "千" in text:
                num = re.findall(r"[\d.]+", text)
                return int(float(num[0]) * 1000) if num else None
            elif "万" in text:
                num = re.findall(r"[\d.]+", text)
                return int(float(num[0]) * 10000) if num else None
            else:
                num = re.findall(r"\d+", text)
                return int(num[0]) if num else None
        except Exception:
            return None

    def _get_media_type(self, url: str) -> str:
        """
        根据媒体 URL 判断类型（video/image/screenshot/None）。
        """
        if not url: return None
        url = url.lower()
        if "video" in url: return "video"
        if any(x in url for x in ["image", "blob", "webp", ".jpg", ".png", ".jpeg"]): return "image"
        if "screenshot" in url: return "screenshot"
        return None

    def _convent_json(self, code: int, data: Dict[str, Any] = None, message: str = "success") -> str:
        """
        统一构建返回的 JSON 响应。
        
        :param code: 状态码（200: 成功, 404: 下架, 403: 需扫码, 502: 抓取失败, 400: 不支持链接）
        :param data: 抓取到的数据字典
        :param message: 响应消息描述
        :return: JSON 字符串
        若需要写额外的逻辑更新某个值，可以在_extract方法内写然后通过data对象传入_convent以更新
        """
        web_name = self.web_name
        if data and data.get("web_name"):
            web_name = data.get("web_name")

        res_data = {
            "title": None, "url": None, "content": None, "media_type": None,
            "publish_time": None, "web_name": web_name, "praise_count": None,
            "forward_count": None, "visit_count": None, "reply_count": None,
            "author": None, "author_nickname": None, "author_fans_count": None,
            "author_statuses_count": None, "ip_region": None, "user_id": None,
            "author_avatar_url": None, "media_urls": None
        }
        
        if code == 200 and data:
            res_data.update({
                "title": data.get("title"),
                "url": data.get("url"),
                "content": data.get("content"),
                "media_type": self._get_media_type(data.get("media_url")),
                "publish_time": self._parse_publish_time(data.get("publish_time")),
                "praise_count": self._convert_counts(data.get("likes")),
                "forward_count": self._convert_counts(data.get("shares")),
                "reply_count": self._convert_counts(data.get("comments")),
                "author": data.get("author"),
                "author_fans_count": self._convert_counts(data.get("fans")),
                "media_urls": data.get("media_url"),
            })
        elif code == 404 and data:
            res_data.update({
                "url": data.get("url")
            })
            # message = "PAGE_NOT_FOUND: 作品已下架"
        elif code == 403 and data:
            res_data.update({
                "url": data.get("url")
            })
            # message = "ERROR: 需要 APP 扫码授权"
        elif code == 502 and data:
            res_data.update({
                "url": data.get("url")
            })
            # message = "ERROR: 抓取数据失败"
        elif code == 400:
            pass
            # message = "ERROR: 不支持的链接"

        return json.dumps({"code": code, "message": message, "data": res_data}, ensure_ascii=False)

    def _close_login_popup(self, page: Page, selector: str):
        """
        检测并关闭可能出现的登录弹窗。
        """
        try:
            btn = page.locator(selector)
            if btn.count() > 0 and btn.is_visible():
                btn.click(timeout=1000)
                print(f"INFO: [{self.web_name}] login popup closed")
        except Exception:
            pass

    def _poll_until_ready(self, page: Page, locators: Dict[str, Locator], wait_keys: List[str], 
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

            all_ready = True
            for key in wait_keys:
                if locators[key].count() == 0:
                    all_ready = False
                    break
            
            if all_ready:
                return "ALL_READY"
            time.sleep(0.5)
        
        return "TIMEOUT"

    def _check_error_states(self, page: Page) -> Optional[str]:
        """
        检查页面轮询时是否进入错误状态（如404，403等）。需在子类中重写实现。
        """
        return None

    def _safe_get_text(self, locator: Locator, key: str) -> Optional[str]:
        """
        安全获取元素文本，处理可能的异常，亦可以在此重写异常处理逻辑（但目前尚未
        """
        start_time = time.time()
        try:
            r = locator.first.inner_text(timeout=1000)
            if time.time() - start_time > 0.5:
                print(f"warning: {key} 耗时 {time.time() - start_time} 秒")
            return r
        except Exception:
            if time.time() - start_time > 0.5:
                print(f"warning: {key} 耗时 {time.time() - start_time} 秒，且进入了异常处理（是否因为该元素不存在？）")
            return None

    def _get_browser_context(self, p: Any, user_data_dir: Optional[str], headless: bool, user_agent: Optional[str] = None, viewport: Optional[Dict[str, int]] = None, timezone_id: Optional[str] = None) -> BrowserContext:
        """
        启动并获取持久化浏览器上下文（支持缓存和 Chrome 渠道）。
        """
        if user_data_dir is None:
            user_data_dir = str(Path(__file__).parent / "chrome-profile")
        
        launch_kwargs = {
            "user_data_dir": user_data_dir,
            "channel": "chrome",
            "headless": headless,
        }
        if user_agent:
            launch_kwargs["user_agent"] = user_agent
        if viewport:
            launch_kwargs["viewport"] = viewport
        if timezone_id:
            launch_kwargs["timezone_id"] = timezone_id
            
        return p.chromium.launch_persistent_context(**launch_kwargs)

    def run(self, url: str, download_media: bool = False, user_data_dir: Optional[str] = None, headless: bool = False, user_agent: Optional[str] = None, viewport: Optional[Dict[str, int]] = None, timezone_id: Optional[str] = None) -> str:
        """
        执行 RPA 任务的主入口。
        
        :param url: 目标页面 URL
        :param download_media: 是否下载媒体文件
        :param user_data_dir: 浏览器用户数据目录
        :param headless: 是否使用无头模式
        :param user_agent: 用户代理字符串
        :param viewport: 视口大小 {"width": 1920, "height": 1080}
        :param timezone_id: 时区 ID，如 "Asia/Shanghai"
        :return: JSON 结果字符串
        """
        with sync_playwright() as p:
            browser_context = self._get_browser_context(p, user_data_dir, headless, user_agent, viewport, timezone_id)
            try:
                page = browser_context.new_page()
                print(f"Opening {url} ...")
                page.goto(url, wait_until="domcontentloaded")
                
                return self.extract_info(page, url, download_media)
            except Exception as e:
                print(f"Error: {str(e)}")
                return self._convent_json(502, data={"url": page.url}, message="ERROR: 抓取数据失败")
            finally:
                browser_context.close()

    def extract_info(self, page: Page, url: str, download_media: bool) -> str:
        """
        具体的页面信息提取逻辑。必须在子类中实现。
        """
        raise NotImplementedError
