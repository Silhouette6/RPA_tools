import http.client
import json
import requests
from typing import Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
'''
这个脚本用于从数据库服务器获取需要更新的数据，并调用内网RPA服务获取需要更新的数据，然后将数据发送回数据库服务器。
'''

# 配置
REMOTE_SERVER = "192.168.30.165:8501"
RPA_SERVER = "http://127.0.0.1:8000"

# 平台映射到API端点
PLATFORM_ENDPOINT_MAP = {
    "今日头条": "/toutiao",
    "抖音": "/douyin",
    "小红书": "/xhs"
}

def get_token():

    url = "http://192.168.30.165/api/admin/login/token"

    payload = {
        "username": "zhangyidian",
        "password": "hSiVVdxQU3AJKTrCr3Q6GmWU/dsL6NvcqvW1hgSJXRZqDAJCKOVbCPMnDbr8fm9ncaxxv6WzGMyH84KJZ8XswyjqSZ5xxSIS+3TAxA+y6F3VHMi15d2/e/6+Zo25U3X5khxMlQnK2zzqCooZqdOyXrmp2pvD7+UuIPBmtGTY73k="
    }

    # 使用 form data 格式而不是 JSON
    resp = requests.post(url, data=payload, timeout=5)

    # print("status:", resp.status_code)
    # print("response:", resp.text)

    data = resp.json()

    # 响应格式：{"code": 0, "message": "...", "data": {"access_token": "..."}}
    # token 在 data.data 中
    if data.get("code") == 0:
        token = data.get("data", {}).get("access_token")
        print("成功获取token! 准备从服务器获取需要更新的数据...")
        print("token:", token)
        return token
    else:
        print("获取 token 失败:", data.get("message"))
        return None

def get_update_data_from_server(token: str) -> Dict[str, Any]:
    """
    从服务器获取需要更新的数据
    """
    print("正在从服务器获取需要更新的数据...")
    try:
        conn = http.client.HTTPConnection(REMOTE_SERVER)
        payload = ''
        headers = {
            'Content-Type': 'text/plain',
            'Authorization': 'Bearer ' + token
        }
        conn.request("GET", "/api/platform/getAllUpdateData", payload, headers)
        res = conn.getresponse()
        data = res.read()
        result = json.loads(data.decode("utf-8"))
        conn.close()
        
        if result.get("code") == 0:
            print(f"成功获取数据: {result.get('message')}")
            return result
        else:
            print(f"获取数据失败: {result}")
            return None
    except Exception as e:
        print(f"获取数据时发生错误: {e}")
        return None


def call_rpa_api(platform: str, url: str, download_media: bool = False, headless: bool = False) -> Dict[str, Any]:
    """
    调用本地RPA API获取数据
    
    Args:
        platform: 平台名称（如"今日头条"）
        url: 需要爬取的URL
        download_media: 是否下载媒体文件（视频/图片）
        headless: 是否使用无头模式
    
    Returns:
        API返回的数据
    """
    endpoint = PLATFORM_ENDPOINT_MAP.get(platform)
    if not endpoint:
        print(f"不支持的平台: {platform}")
        return None
    
    # 根据平台类型设置payload
    if platform == "今日头条":
        payload = {
            "url": url,
            "download_video": download_media,
            "headless": headless
        }
    elif platform == "抖音":
        payload = {
            "url": url,
            "download_video": download_media,
            "headless": headless
        }
    elif platform == "小红书":
        payload = {
            "url": url,
            "download_img": download_media,
            "headless": headless
        }
    else:
        payload = {
            "url": url,
            "headless": headless
        }
    
    try:
        print(f"正在调用 {platform} RPA API: {url}")
        response = requests.post(f"{RPA_SERVER}{endpoint}", json=payload, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            code = result.get("code")
            if code == 200 or code == 404:
                print(f"RPA API 调用成功: {platform}")
                return result
            else:
                print(f"RPA 执行获取失败: {platform}, 错误代码: {code}")
                return None
        else:
            print(f"RPA API 网络调用失败: {platform}, 网络链接HTTP状态码: {response.status_code}")
            return None

    except requests.exceptions.Timeout:
        print(f"RPA API 调用超时: {platform} - {url}")
        return None
    except Exception as e:
        print(f"RPA API 调用时发生错误: {e}")
        return None


def send_update_to_server(record_id: str, table_type: str, rpa_data: Dict[str, Any], is_offline: int = 0, token: str = None) -> bool:
    """
    将更新后的数据发送回服务器
    
    Args:
        record_id: 记录ID
        table_type: 表类型（如"event"）
        rpa_data: RPA返回的数据
        is_offline: 是否下架（0-未下架，1-已下架）
    
    Returns:
        是否发送成功
    """
    update_payload = {
        "code": 200,
        "message": "success",
        "tableType": table_type,
        "id": record_id,
        "is_offline": is_offline,
        "rpa_data": rpa_data
    }
    
    try:
        print(f"正在发送更新数据到服务器, ID: {record_id}")

        # 使用 requests 发送POST请求
        response = requests.post(
            f"http://{REMOTE_SERVER}/api/platform/receiveSingleUpdate",
            json=update_payload,
            headers={'Content-Type': 'application/json',
                     'Authorization': 'Bearer ' + token
            },
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"数据更新成功, ID: {record_id}")
            return True
        else:
            print(f"数据更新失败, ID: {record_id}, 状态码: {response.status_code}")
            return False

    except Exception as e:
        print(f"发送更新数据时发生错误, ID: {record_id}, 错误: {e}")
        return False

def process_single_item(platform: str, item: Dict[str, Any], idx: int, total: int, headless: bool = False, token: str = None) -> Tuple[bool, str]:
    """
    处理单条记录
    
    Args:
        platform: 平台名称
        item: 单条记录数据
        idx: 记录索引
        total: 总记录数
        headless: 是否使用无头模式
    
    Returns:
        (是否成功, 记录ID)
    """
    record_id = item.get("id")
    table_type = item.get("table_type")
    url = item.get("url")
    
    print(f"\n[{idx}/{total}] 处理记录 ID: {record_id}")
    print(f"URL: {url}")
    
    if not all([record_id, table_type, url]):
        print("数据不完整，跳过此记录")
        return (False, record_id)
    
    # 调用RPA API获取数据
    rpa_result = call_rpa_api(platform, url, download_media=False, headless=headless)
    
    success = True
    if rpa_result:
        # 判断是否下架（根据RPA返回的code判断）
        is_offline = 0 
        code = rpa_result.get("code")
        if code == 404:
            is_offline = 1
        if code == 403 or code == 502 or code == 400:   # 如果code为403、502、400，则认为RPA调用失败
            success = False
        
        # 发送更新数据到服务器
        success_send = send_update_to_server(record_id, table_type, rpa_result, is_offline, token)
        
        # 如果发送更新数据失败
        if not success_send:
            success = False
        
        # 更新统计信息
        if success:
            return (True, record_id)
        else:
            return (False, record_id)
    else:
        # RPA调用失败
        print("RPA调用失败")
        return (False, record_id)



def process_platform_data(platform: str, platform_data: Dict[str, Any], headless: bool = False, max_workers: int = 3, token: str = None) -> Dict[str, int]:
    """
    处理单个平台的数据（使用并发）
    
    Args:
        platform: 平台名称
        platform_data: 平台数据
        headless: 是否使用无头模式
        max_workers: 最大并发数
    
    Returns:
        处理统计信息 {success: 成功数, failed: 失败数, total: 总数}
    """
    count = platform_data.get("count", 0)
    data_list = platform_data.get("data", [])
    
    print(f"\n{'='*50}")
    print(f"开始处理平台: {platform}, 总数: {count}, 最大并发数: {max_workers}")
    print(f"{'='*50}")
    
    stats = {"success": 0, "failed": 0, "total": len(data_list)}
    
    # 使用线程池并发处理
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_item = {
            executor.submit(process_single_item, platform, item, idx, len(data_list), headless, token): item
            for idx, item in enumerate(data_list, 1)
        }
        
        # 处理完成的任务
        for future in as_completed(future_to_item):
            try:
                success, record_id = future.result()
                if success:
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
            except Exception as e:
                print(f"处理任务时发生异常: {e}")
                stats["failed"] += 1
    
    return stats


def main(headless: bool = False):
    """
    主函数
    
    Args:
        headless: 是否使用无头模式运行浏览器
    """
    print("=" * 60)
    print("数据更新脚本启动")
    print("=" * 60)
    
    # 0. 获取token
    token = get_token()
    if not token:
        print("获取 token 失败，退出程序")
        return
    
    # 1. 从服务器获取需要更新的数据
    server_response = get_update_data_from_server(token)
    
    # 将服务器响应写入文件
    if server_response:
        try:
            with open("server_response.json", "w", encoding="utf-8") as f:
                json.dump(server_response, f, ensure_ascii=False, indent=4)
            print("服务器响应已保存到 server_response.json")
        except Exception as e:
            print(f"保存服务器响应失败: {e}")
    
    if not server_response or server_response.get("code") != 0:
        print("无法获取更新数据，退出程序")
        return

    # 2. 解析数据
    platform_data = server_response.get("data", {}).get("platformData", {})
    
    if not platform_data:
        print("没有需要更新的数据")
        return
    
    # 3. 统计信息
    total_stats = {"success": 0, "failed": 0, "total": 0}
    
    # 4. 处理每个平台的数据
    for platform, data in platform_data.items():
        stats = process_platform_data(platform, data, headless=headless, token=token)
        
        # 汇总统计
        total_stats["success"] += stats["success"]
        total_stats["failed"] += stats["failed"]
        total_stats["total"] += stats["total"]
        
        print(f"\n{platform} 处理完成:")
        print(f"  成功: {stats['success']}")
        print(f"  失败: {stats['failed']}")
        print(f"  总计: {stats['total']}")
    
    # 5. 输出总体统计
    print("\n" + "=" * 60)
    print("所有平台处理完成")
    print("=" * 60)
    print(f"总成功: {total_stats['success']}")
    print(f"总失败: {total_stats['failed']}")
    print(f"总计: {total_stats['total']}")
    print(f"成功率: {total_stats['success'] / total_stats['total'] * 100:.2f}%" if total_stats['total'] > 0 else "N/A")


if __name__ == "__main__":
    # 设置 headless=True 可以使用无头模式运行，不显示浏览器窗口
    # 设置 headless=False 可以看到浏览器运行过程（方便调试）
    main(headless=False)

