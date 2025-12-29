class Config_Douyin:
    def __init__(self):
        self.xpaths = {
            "video_xpaths" : {
                "video_author": '//div[@data-e2e="video-detail"]/div/div/div/div/a/div[@data-click-from="title"]/span/span/span/span/span/span',
                "video_title": '//*[local-name()="h1"]/span/span/span/span/span/span/span',
                "video_likes": '//*[@id="douyin-right-container"]/div[2]/div/div/div[1]/div[3]/div/div[2]/div[1]/div[1]/span',
                "video_comments": '//*[@id="douyin-right-container"]/div[2]/div/div/div[1]/div[3]/div/div[2]/div[1]/div[2]/span',
                "video_shares": '//*[@id="douyin-right-container"]/div[2]/div/div/div[1]/div[3]/div/div[2]/div[1]/div[4]/span',
                "video_fans": '//*[@id="douyin-right-container"]/div[2]/div/div/div[2]/div/div[1]/div[2]/p/span[2]',
                "video_publish_time": '//*[@id="douyin-right-container"]/div[2]/div/div/div[1]/div[3]/div/div[2]/div[2]/span',
                "video_video": '//*[@id="douyin-right-container"]/div[2]/div/div/div[1]/div[2]/div/div[1]/xg-video-container/video/source[1]',
                "video_close_btn": '//article/div/div/div/*[local-name()="svg"]'
                },
            "note_xpaths" : {
                "note_title": '//*[@id="douyin-right-container"]/div[2]/main/div[2]/div[2]',
                "note_author": '//*[@id="douyin-right-container"]/div[2]/main/div[2]/div[1]/div[2]/a/div/span/span/span/span/span/span',
                "note_likes": '//*[@id="douyin-right-container"]/div[2]/main/div[1]/div[2]/div/div[2]',
                "note_comments": '//*[@id="douyin-right-container"]/div[2]/main/div[1]/div[2]/div/div[2]',
                "note_favourites": '//*[@id="douyin-right-container"]/div[2]/main/div[1]/div[2]/div/div[2]',
                "note_shares": '//*[@id="douyin-right-container"]/div[2]/main/div[1]/div[2]/div/div[2]',
                "note_fans": '//*[@id="douyin-right-container"]/div[2]/main/div[2]/div[1]/div[2]/p/span[2]',
                "note_publish_time": '//*[@id="douyin-right-container"]/div[2]/main/div[2]/div[2]/div/div[2]/span',
                "note_close_btn": '//article/div/div/div/*[local-name()="svg"]'
            }
        }
        self.wait_list = {
            "video_wait_list": ["video_author", "video_likes", "video_comments", "video_shares", "video_fans", "video_publish_time"],
            "note_wait_list": ["note_title"],
        }
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

class ServerConfig:
    def __init__(self):
        self.host = "0.0.0.0"
        self.port = 8000