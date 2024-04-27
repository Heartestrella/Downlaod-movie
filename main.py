import json
import os
import re
import sys
import time

import requests
from requests.cookies import RequestsCookieJar
from requests.exceptions import RequestException
from requests.utils import cookiejar_from_dict
from tqdm import tqdm

from tools import login, scrape


def load_config():
    data = {
        "sleep_time": 10,
        "html_path": "",
        "sorce": 9.5,
        "save_path": "",
        "qn": 80,
        "chunk_size": 1024,
        "headers": {
            "authority": "api.vc.bilibili.com",
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://message.bilibili.com",
            "referer": "https://message.bilibili.com/",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "Windows",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.81",
        },
        "cookies": {},
    }
    config_file = "config.json"

    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            data = json.load(f)
            return data
    else:
        with open(config_file, "w") as f:
            json.dump(data, f, indent=4)
            print("配置文件初始化完毕，请手动修改某些数值")
            sys.exit()


class Downloader:
    def __init__(self, config, cookie):
        self.config = config
        cookie_jar = RequestsCookieJar()
        cookie_jar.update(cookie)
        self.session = requests.Session()
        self.session.cookies = cookie_jar

    def get_epid_video(self, ep_id, name):
        url = f"https://api.bilibili.com/pgc/player/web/playurl?ep_id={ep_id[2:]}&qn={self.config['qn']}"
        response = self.session.get(url, headers=self.config["headers"])
        video_url = response.json()["result"]["durl"][0]["url"]
        if self.download_video(video_url, name):
            return True

    def download_video(self, url, name):
        print("开始下载 MP4，请耐心等待...")
        full_path = os.path.join(self.config["save_path"], f"{name}.mp4")
        if os.path.exists(full_path):
            print(f"电影 {name} 已经存在")
            return True
        else:
            try:
                response = self.session.get(
                    url, headers=self.config["headers"], stream=True
                )
                if response.status_code == 200:
                    content_length = int(response.headers.get("Content-Length", 0))
                    with tqdm(
                        total=content_length,
                        unit="B",
                        unit_scale=True,
                        desc=name,
                        file=sys.stdout,
                    ) as pbar:

                        with open(full_path, "wb") as file:
                            for chunk in response.iter_content(
                                chunk_size=self.config["chunk_size"]
                            ):
                                file.write(chunk)
                                pbar.update(len(chunk))
                    print("\n下载完成")
                    return True
                else:
                    print(name, "下载失败")
                    return False
            except RequestException as e:
                print(f"出现错误 : {e} 1分钟后再次尝试!")
                time.sleep(60)
                self.download_video(url, name)


if __name__ == "__main__":
    config = load_config()
    if not config["cookies"]:
        cookies = login.Login()
        cookies = cookies.get_cookies()
        config["cookies"] = cookies
        with open("config.json", "w") as f:
            json.dump(config, f, indent=4)
    movies = scrape.BilibiliMovieScraper("https://www.bilibili.com/movie/", config)
    movies = movies.get_moive()
    Downloader_ = Downloader(config, config["cookies"])
    sleep_time = config["sleep_time"]
    for movie in movies:
        for name, values in movie.items():
            match = re.search(r"/ep(\d+)", values[0])
            if match:
                target = match.group(1)
                id = f"ep{target}"
                if Downloader_.get_epid_video(id, name):
                    print(
                        f"电影 {name} 下载完成! 休眠：{sleep_time} 后继续下载下一部电影"
                    )
                    time.sleep(sleep_time)
            else:
                print("没匹配到id")
