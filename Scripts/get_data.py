import requests
import time
import json
import os

URL = "http://192.168.30.238/api/bpm/bizDef/execByCode/bz.opinion.system.event.manage.list"

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer 13e606df-cce6-4bf7-bfcb-33cd20579b30"
}

PAGE_SIZE = 20
SLEEP_SECONDS = 1
OUTPUT_DIR = "data"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def normalize_webname(name):
    if not isinstance(name, str):
        return ""
    return name.strip()


def fetch_page(current: int):
    payload = {
        "handleStatus": "0",
        "current": current,
        "pageSize": PAGE_SIZE
    }
    resp = requests.post(URL, json=payload, headers=HEADERS, timeout=10)
    data = resp.json()

    if data.get("code") == 2012:
        raise RuntimeError("Token 已失效，需要重新登录")

    if data.get("code") != 0:
        raise RuntimeError(f"接口异常: {data}")

    return data["data"]


def main():
    # Use dictionaries for deduplication (simulating sets)
    toutiao_data = {}
    xiaohongshu_data = {}
    douyin_data = {}
    other_data = {}

    current = 1
    total_pages = None

    while True:
        page_data = fetch_page(current)

        records = page_data.get("records", [])
        response_current = int(page_data.get("current", current))
        pages = int(page_data.get("pages", 0))

        if total_pages is None:
            total_pages = pages
            print(f"Total pages reported by server: {total_pages}")

        print(
            f"[PAGE] request={current} "
            f"response={response_current} "
            f"records={len(records)}"
        )

        if not records:
            print("No records returned, stopping.")
            break

        for record in records:
            record_id = record.get("id")
            # Fallback ID if missing
            if not record_id:
                record_id = str(record)

            webname = normalize_webname(record.get("webName", ""))

            if "今日头条" in webname:
                toutiao_data[record_id] = record
            elif "小红书" in webname:
                xiaohongshu_data[record_id] = record
            elif "抖音" in webname:
                douyin_data[record_id] = record
            else:
                other_data[record_id] = record

        if current >= total_pages:
            print("Reached last page.")
            break

        current += 1
        time.sleep(SLEEP_SECONDS)

    save_json("toutiao.json", list(toutiao_data.values()))
    save_json("xiaohongshu.json", list(xiaohongshu_data.values()))
    save_json("douyin.json", list(douyin_data.values()))
    save_json("other.json", list(other_data.values()))

    print("Done.")
    print(
        f"toutiao={len(toutiao_data)}, "
        f"xiaohongshu={len(xiaohongshu_data)}, "
        f"douyin={len(douyin_data)}, "
        f"other={len(other_data)}"
    )


def save_json(filename, data):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(data)} records -> {path}")


if __name__ == "__main__":
    main()
