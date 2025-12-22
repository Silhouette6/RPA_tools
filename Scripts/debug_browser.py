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
    input("Press anything to exit...")