import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI
from pydantic import BaseModel

from config import Config_Douyin, Config_Toutiao, Config_Xhs
from RPA_douyin import get_douyin_short_video_info
from RPA_toutiao import get_toutiao_info
from RPA_xhs_sharelk import get_xhs_info

app = FastAPI()

# 定义 3 个固定的 Profile 目录
BASE_DIR = Path(__file__).parent
PROFILE_PATHS = [
    str(BASE_DIR / "profiles" / "worker_1"),
    str(BASE_DIR / "profiles" / "worker_2"),
    str(BASE_DIR / "profiles" / "worker_3"),
]

# 初始化资源池
_profile_pool = asyncio.Queue()

@app.on_event("startup")
async def startup_event():
    # 确保目录存在并加入队列
    for path in PROFILE_PATHS:
        os.makedirs(path, exist_ok=True)
        _profile_pool.put_nowait(path)
    print(f"INFO: Profile pool initialized with {len(PROFILE_PATHS)} workers.")

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
    return {
        "status": "ok", 
        "max_concurrency": len(PROFILE_PATHS),
        "available_workers": _profile_pool.qsize()
    }

@app.post("/xhs")
async def xhs(req: XhsRequest) -> Dict[str, Any]:
    start = time.perf_counter()
    profile_dir = await _profile_pool.get()
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
        )
        return _safe_parse_json(result_text)
    except Exception as e:
        return {
            "code": 500,
            "message": "internal_error",
            "data": {"source": "小红书", "error": str(e), "url": req.url},
        }
    finally:
        cost = time.perf_counter() - start
        print(f"[xhs] cost={cost:.2f}s url={req.url} worker={profile_dir}")
        _profile_pool.put_nowait(profile_dir)

@app.post("/douyin")
async def douyin(req: DouyinRequest) -> Dict[str, Any]:
    start = time.perf_counter()
    profile_dir = await _profile_pool.get()
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
        )
        return _safe_parse_json(result_text)
    except Exception as e:
        return {
            "code": 500,
            "message": "internal_error",
            "data": {"source": "抖音", "error": str(e), "url": req.url},
        }
    finally:
        cost = time.perf_counter() - start
        print(f"[douyin] cost={cost:.2f}s url={req.url} worker={profile_dir}")
        _profile_pool.put_nowait(profile_dir)

@app.post("/toutiao")
async def toutiao(req: ToutiaoRequest) -> Dict[str, Any]:
    start = time.perf_counter()
    profile_dir = await _profile_pool.get()
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
        )
        return _safe_parse_json(result_text)
    except Exception as e:
        return {
            "code": 500,
            "message": "internal_error",
            "data": {"source": "头条", "error": str(e), "url": req.url},
        }
    finally:
        cost = time.perf_counter() - start
        print(f"[toutiao] cost={cost:.2f}s url={req.url} worker={profile_dir}")
        _profile_pool.put_nowait(profile_dir)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
