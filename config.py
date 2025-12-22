class Config_Douyin:
    def __init__(self):
        self.xpaths = {
            "author": '//div[@data-e2e="video-detail"]/div/div/div/div/a/div[@data-click-from="title"]/span/span/span/span/span/span',
            "title": '//*[local-name()="h1"]/span/span/span/span/span/span/span',
            "title_bak1": '//span[3]/span[1]/span[1]/span[1]',
            "likes": '//*[@id="douyin-right-container"]/div[2]/div/div/div[1]/div[3]/div/div[2]/div[1]/div[1]/span',
            "comments": '//*[@id="douyin-right-container"]/div[2]/div/div/div[1]/div[3]/div/div[2]/div[1]/div[2]/span',
            "shares": '//*[@id="douyin-right-container"]/div[2]/div/div/div[1]/div[3]/div/div[2]/div[1]/div[4]/span',
            "fans": '//*[@id="douyin-right-container"]/div[2]/div/div/div[2]/div/div[1]/div[2]/p/span[2]',
            "publish_time": '//*[@id="douyin-right-container"]/div[2]/div/div/div[1]/div[3]/div/div[2]/div[2]/span',
            "video": '//*[@id="douyin-right-container"]/div[2]/div/div/div[1]/div[2]/div/div[1]/xg-video-container/video/source[1]',
            "close_btn": '//article/div/div/div/*[local-name()="svg"]'
            }
        self.wait_list = ["author", "likes", "comments", "shares", "fans", "publish_time"]
        self.save_dir = "data/douyin"

class Config_Xhs:
    def __init__(self):
        self.xpaths= {
            "title": '//*[@id="detail-title"]',
            "author": '//div[@class="author-container"]//a/span[contains(@class, "username")]',
            "content": '//div[@id="detail-desc"]/span[@class="note-text"]/span',
            "likes": '//div[@class="left"]/span[contains(@class, "like-wrapper")]/span[@class="count"]',
            "favours": '//span[@id="note-page-collect-board-guide"]/span[@class="count"]',
            "comments": '//span[contains(@class, "chat-wrapper")]/span[@class="count"]',
            "publish_time": '//span[@class="date"]',
            "img_live": '//img[contains(@class, "live-img")]', 
            "img": '//div[contains(@class, "swiper-slide-visible")]//img[@decoding="sync"]',
            "cover": '//*[local-name()="xg-poster"]',
            "close_btn": '.icon-btn-wrapper',
            }
        self.wait_list = ["title", "author", "likes", "favours", "comments", "publish_time"]
        self.save_dir = "data/xhs"

class Config_Toutiao:
    def __init__(self):
        # w 为weitoutiao的xpath
        # video 为视频xpath
        self.xpaths = {
            "w_xpaths" : {
                "w_author": '//a[@class="name"]',
                "w_content": '//div[@class="weitoutiao-html"]',
                "w_publish_time": '//span[@class="time"]',
                "w_likes": '//div[@class="detail-like"]/span',
            }, 
            "video_xpaths" : {
                "video_author": '//a[@class="author-name"]',
                "video_content": '//*[local-name()="h1"]',
                "video_publish_time": '//span[@class="publish-time"]',
                "video_views": '//span[@class="views-count"]',
                "video_likes": '//ul/li/button/span[contains(@class, "like-count")]',
                "video_video": '//ul/li//video[@mediatype="video"]'
            }
        }
        self.wait_list = {
            "w_wait_list" : ["w_author", "w_content", "w_publish_time", "w_likes"],
            "video_wait_list" : ["video_author", "video_content", "video_publish_time", "video_views", "video_likes"]
            }

        self.save_dir = "data/toutiao"
