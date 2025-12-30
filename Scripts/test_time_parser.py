from base_rpa import BaseRPA
from datetime import datetime

class TestRPA(BaseRPA):
    def extract_info(self, page, url, download_media):
        pass

def test_time_parsing():
    rpa = TestRPA(None, "Test")
    test_cases = [
        "12-17 北京",
        "2023-12-17 广东",
        "12-17 14:30 上海",
        "发布时间：2023-01-01 12:00:00",
        "2 天前",
        "2023-05-01",
        "无法解析的时间格式",
        "",
        None
    ]
    
    print(f"Current Year: {datetime.now().year}")
    print("-" * 50)
    for case in test_cases:
        result = rpa._parse_publish_time(case)
        print(f"Input: {str(case):30} -> Output: {result}")

if __name__ == "__main__":
    test_time_parsing()
