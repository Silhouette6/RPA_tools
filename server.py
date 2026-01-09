import asyncio
import json
import os
import shutil
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI
from pydantic import BaseModel

from config import Config_Douyin, Config_Toutiao, Config_Xhs, ServerConfig
from RPA_douyin import get_douyin_short_video_info
from RPA_toutiao import get_toutiao_info
from RPA_xhs_sharelk import get_xhs_info

app = FastAPI()

# 定义 8 个固定的 Profile 目录
BASE_DIR = Path(__file__).parent
PROFILE_PATHS = [
    str(BASE_DIR / "profiles" / f"worker_{i}") for i in range(1, 9)
]

# 定义固定的 DeviceProfiles (符合中国大陆真实设备分布)
DEVICE_PROFILES = [
    # 1️⃣ Windows Chrome（主力，常见笔记本）
    {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "viewport": {"width": 1366, "height": 768},
        "timezone_id": "Asia/Shanghai"
    },

    # 2️⃣ Windows Chrome（中分辨率，真实存在）
    {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "viewport": {"width": 1536, "height": 864},
        "timezone_id": "Asia/Shanghai"
    },

    # 3️⃣ Windows Chrome（非最新版本，真实用户）
    {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "viewport": {"width": 1600, "height": 900},
        "timezone_id": "Asia/Shanghai"
    },

    # 4️⃣ Windows Edge（少量存在，控制比例）
    {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "viewport": {"width": 1536, "height": 864},
        "timezone_id": "Asia/Shanghai"
    },

    # 5️⃣ Mac Safari（非常重要，高权重）
    {
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "viewport": {"width": 1440, "height": 900},
        "timezone_id": "Asia/Shanghai"
    },

    # 6️⃣ Mac Safari（稍高分辨率，真实老款 MBP）
    {
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "viewport": {"width": 1680, "height": 1050},
        "timezone_id": "Asia/Shanghai"
    },

    # 7️⃣ Mac Chrome（少量存在）
    {
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "viewport": {"width": 1440, "height": 900},
        "timezone_id": "Asia/Shanghai"
    },

    # 8️⃣ Windows Chrome（备用，稳定组合）
    {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "viewport": {"width": 1366, "height": 768},
        "timezone_id": "Asia/Shanghai"
    },
]


# 并发控制
MAX_CONCURRENCY = 3
_concurrency_sem = None  # 在 startup 中初始化
_worker_index = 0
_worker_lock = None      # 在 startup 中初始化
_worker_queues = []      # 每个 worker 的状态队列 (长度 3)

@app.on_event("startup")
async def startup_event():
    global _concurrency_sem, _worker_lock, _worker_queues
    _concurrency_sem = asyncio.Semaphore(MAX_CONCURRENCY)
    _worker_lock = asyncio.Lock()
    _worker_queues = [deque(maxlen=3) for _ in range(len(PROFILE_PATHS))]
    
    # 确保目录存在
    for path in PROFILE_PATHS:
        os.makedirs(path, exist_ok=True)
    print(f"INFO: Profile pool initialized with {len(PROFILE_PATHS)} workers. Max concurrency: {MAX_CONCURRENCY}")

async def get_next_worker_info():
    global _worker_index
    async with _worker_lock:
        idx = _worker_index
        path = PROFILE_PATHS[idx]
        profile = DEVICE_PROFILES[idx]
        _worker_index = (_worker_index + 1) % len(PROFILE_PATHS)
        return idx, path, profile

class XhsRequest(BaseModel):
    url: str
    download_img: bool = True
    headless: bool = True

class DouyinRequest(BaseModel):
    url: str
    download_video: bool = True
    headless: bool = True

class ToutiaoRequest(BaseModel):
    url: str
    download_video: bool = True
    headless: bool = True

def _safe_parse_json(text: Any) -> Dict[str, Any]:
    if isinstance(text, dict):
        return text
    if isinstance(text, str):
        try:
            return json.loads(text)
        except Exception:
            return {
                "code": 500,
                "message": "invalid_json_response",
                "data": {"raw": text},
            }
    return {"code": 500, "message": "invalid_response_type", "data": {"type": str(type(text))}}

@app.get("/health")
async def health() -> Dict[str, Any]:
    available_slots = _concurrency_sem._value if _concurrency_sem else 0
    return {
        "status": "ok", 
        "total_workers": len(PROFILE_PATHS),
        "max_concurrency": MAX_CONCURRENCY,
        "available_concurrency_slots": available_slots
    }

@app.post("/xhs")
async def xhs(req: XhsRequest) -> Dict[str, Any]:
    start = time.perf_counter()
    
    # 使用信号量限制并发
    async with _concurrency_sem:
        # 获取下一个 worker (Round-Robin)
        idx, profile_dir, profile = await get_next_worker_info()
        
        status_code = 200
        try:
            cfg = Config_Xhs()
            result_text = await asyncio.to_thread(
                get_xhs_info,
                req.url,
                cfg.xpaths,
                cfg.wait_list,
                cfg.save_dir,
                req.download_img,
                profile_dir,
                req.headless,
                profile["user_agent"],
                profile["viewport"],
                profile["timezone_id"]
            )
            resp = _safe_parse_json(result_text)
            status_code = resp.get("code", 200)
            message = resp.get("message", "")

            # --- 小红书健康检查机制 ---
            if "可能被重定向到登录页" in message:
                _worker_queues[idx].append("warning")
                print(f"小红书 Worker_{idx+1} 警告: {message}")
            elif message == "SUCCESS: 小红书数据提取成功":
                print(f"小红书 Worker_{idx+1} 正常: {message}")
                _worker_queues[idx].append("normal")
            
            # 检查是否连续 3 次警告
            if len(_worker_queues[idx]) == 3 and all(s == "warning" for s in _worker_queues[idx]):
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{now_str}] [xhs] Worker_{idx+1} is dead (3 consecutive warnings). Destroying and re-initializing...")
                
                # 销毁 (删除目录)
                if os.path.exists(profile_dir):
                    shutil.rmtree(profile_dir)
                
                # 重新初始化 (创建目录)
                os.makedirs(profile_dir, exist_ok=True)
                
                # 重置队列
                _worker_queues[idx].clear()
            # ------------------------

            return resp
        except Exception as e:
            status_code = 500
            return {
                "code": 500,
                "message": "internal_error",
                "data": {"source": "小红书", "error": str(e), "url": req.url},
            }
        finally:
            cost = time.perf_counter() - start
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{now}] [xhs] code={status_code} cost={cost:.2f}s url={req.url} worker={profile_dir}")

@app.post("/douyin")
async def douyin(req: DouyinRequest) -> Dict[str, Any]:
    start = time.perf_counter()
    
    async with _concurrency_sem:
        idx, profile_dir, profile = await get_next_worker_info()
        
        status_code = 200
        try:
            cfg = Config_Douyin()
            result_text = await asyncio.to_thread(
                get_douyin_short_video_info,
                req.url,
                cfg.xpaths,
                cfg.wait_list,
                cfg.save_dir,
                req.download_video,
                profile_dir,
                req.headless,
                profile["user_agent"],
                profile["viewport"],
                profile["timezone_id"]
            )
            resp = _safe_parse_json(result_text)
            status_code = resp.get("code", 200)
            return resp
        except Exception as e:
            status_code = 500
            return {
                "code": 500,
                "message": "internal_error",
                "data": {"source": "抖音", "error": str(e), "url": req.url},
            }
        finally:
            cost = time.perf_counter() - start
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{now}] [douyin] code={status_code} cost={cost:.2f}s url={req.url} worker={profile_dir}")

@app.post("/toutiao")
async def toutiao(req: ToutiaoRequest) -> Dict[str, Any]:
    start = time.perf_counter()
    
    async with _concurrency_sem:
        idx, profile_dir, profile = await get_next_worker_info()
        
        status_code = 200
        try:
            cfg = Config_Toutiao()
            result_text = await asyncio.to_thread(
                get_toutiao_info,
                req.url,
                cfg.xpaths,
                cfg.wait_list,
                cfg.save_dir,
                req.download_video,
                profile_dir,
                req.headless,
                profile["user_agent"],
                profile["viewport"],
                profile["timezone_id"]
            )
            resp = _safe_parse_json(result_text)
            status_code = resp.get("code", 200)
            return resp
        except Exception as e:
            status_code = 500
            return {
                "code": 500,
                "message": "internal_error",
                "data": {"source": "头条", "error": str(e), "url": req.url},
            }
        finally:
            cost = time.perf_counter() - start
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{now}] [toutiao] code={status_code} cost={cost:.2f}s url={req.url} worker={profile_dir}")

if __name__ == "__main__":
    import uvicorn
    cfg = ServerConfig()
    uvicorn.run("server:app", host=cfg.host, port=cfg.port, reload=False)
