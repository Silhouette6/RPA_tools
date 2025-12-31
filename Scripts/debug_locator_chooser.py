from playwright.sync_api import sync_playwright
from pathlib import Path

with sync_playwright() as p:
    user_data_dir = str(Path(__file__).parent.parent / "chrome-profile")
    print("Using user data dir:", user_data_dir)
    context = p.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        channel="chrome",
        headless=False,
    )
    page = context.new_page()
    page.goto("https://m.toutiao.com/article/7530199854962786851/?app=news_article&category_new=__search__&module_name=Android_tt_others&share_did=MS4wLjACAAAAxMTOW9OFmwO1BIKhPg2st-nicYPfGJux1scZxlFuIZNwhHscB0hTHhBTYjVZYwN-&share_uid=MS4wLjABAAAAxMTOW9OFmwO1BIKhPg2st-nicYPfGJux1scZxlFuIZNwhHscB0hTHhBTYjVZYwN-&timestamp=1767146425&tt_from=wechat&upstream_biz=Android_wechat&utm_campaign=client_share&utm_medium=toutiao_android&utm_source=wechat&share_token=a89b783a-d49b-4d47-9ea9-f0db9c0a5ad5")
    
    xpath_file = Path(__file__).parent / "xpath.txt"
    print(f"Ready. Press 'x' to read xpath from {xpath_file.name}, or other key to exit.")
    
    while True:
        user_input = input("Enter command (x/exit): ").strip().lower()
        if user_input == 'x':
            if not xpath_file.exists():
                print(f"Error: {xpath_file} not found")
                continue
            
            xpath = xpath_file.read_text(encoding='utf-8').strip()
            if not xpath:
                print("xpath.txt is empty")
                continue
            
            print(f"Constructing locator for: {xpath}")
            try:
                # 使用 locator(f"xpath={xpath}") 确保使用 xpath 构造
                locator = page.locator(f"xpath={xpath}")
                if locator.count() > 0:
                    print("Inner Text result:")
                    lis = locator.first.inner_text().split("\n")
                    print(lis)
                else:
                    print("Element not found with this xpath")
            except Exception as e:
                print(f"Error: {e}")
        else:
            print("Exiting...")
            break

    context.close()