import json
import os
import platform
import re
import sys
import time

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


def load_config():
    data = {
        "sorce": 9.5,
        "save_path": "",
        "qn": 80,
        "chunk_size": 1024,
        "headers": {
            "Referer": "https://www.bilibili.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0",
            "cookies": "",
        },
    }
    config_file = "config.json"
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            return json.load(f)
    else:
        with open(config_file, "w") as f:
            json.dump(data, f, indent=4)
            print("请手动修改配置文件后再次启动")
            sys.exit()


class get_full_page:
    def __init__(self, url) -> None:
        self.url = url

    def main(self) -> str:
        if platform.system() == "Windows":
            from selenium import webdriver

            self.driver = webdriver.Edge()
            self.driver.get(self.url)
            for i in range(5):
                self.driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(5)

            page_content = self.driver.page_source
            self.driver.quit()

            return page_content
        if platform.system() == "Linux":
            Warning("Linux系统暂不支持使用webdriver库模拟请求以获取更多资源")
            resp = requests.get(url=self.url, headers=config["headers"])
            if resp.status_code == 200:
                page_content = resp.text
                return page_content
            else:
                raise KeyError("无法获取到页面，请检查网络")


class BilibiliMovieScraper:
    def __init__(self, url, headers):
        """{
            "240P 极速": 6,
            "360P 流畅": 16,
            "480P 清晰": 32,
            "720P 高清": 64,
            "720P60 高帧率": 74,
            "1080P 高清": 80,
            "1080P+ 高码率": 112,
            "1080P60 高帧率": 116,
            "4K 超清": 120
        }
        """
        self.url = url
        #  self.headers = headers
        self.movie_info = []
        full_page = get_full_page(url)
        self.page_content = full_page.main()
        open("full_page.html", encoding="utf-8", mode="a").write(self.page_content)

    def scrape_movie_info(self):
        # response = httpx.get(self.url, headers=self.headers)

        # soup = BeautifulSoup(response.text, "html.parser")
        soup = BeautifulSoup(self.page_content, "html.parser")

        target_divs = soup.find_all("div", class_="module inner-c web_feed_v2")

        for div in target_divs:
            hover_c_divs = div.find_all("div", class_="hover-c")

            for hover_c_div in hover_c_divs:
                title_div = hover_c_div.find("div", class_="title")
                if title_div:
                    movie_name = title_div.get_text(strip=True)

                    a_tag = hover_c_div.find("a", {"target": "_blank"})

                    if a_tag:
                        a_href = a_tag["href"]
                    else:
                        a_href = "N/A"

                    img_tags = hover_c_div.find_all("img")
                    if img_tags:
                        img_src = img_tags[0]["src"]
                    else:
                        img_src = "N/A"

                    score_tags = hover_c_div.find_all("div", class_="score")
                    if score_tags:
                        for score_tag in score_tags:
                            score = score_tag.get_text(strip=True)
                    else:
                        score = "N/A"

                    self.movie_info.append(
                        {
                            movie_name: [a_href, img_src, score]
                        },  # 电影名 : 电影播放地址 图片地址 分数
                    )

    def get_moive(self):
        print("所有电影:\n")
        self.wait_download_moives = []
        for info in self.movie_info:
            sorce = list(info.values())[-1][-1]
            if sorce == "N/A":
                print(f"电影{list(info.keys())[0]},无法获取到分数")
            elif float(sorce) >= float(config["sorce"]):  # 只下载高分电影
                self.wait_download_moives.append(info)
        print("将要下载的电影:\n")
        for movie_info in self.wait_download_moives:
            movie_name = list(movie_info.keys())[0]
            print(f"{movie_name}\n")
        result = input(f"确定下载吗？ Y/YES : ").upper()
        print(f"{config['save_path']} 电影将保存到此")
        if result == "Y" or result == "YES":
            print(
                """分辨率参照表: {
                "240P 极速": 6,
                "360P 流畅": 16,
                "480P 清晰": 32,
                "720P 高清": 64,
                "720P60 高帧率": 74,
                "1080P 高清": 80,
                "1080P+ 高码率": 112,
                "1080P60 高帧率": 116,
                "4K 超清": 120
            }
            """
            )
            qn = input(
                "请输入要下载的电影的分辨率所对应的数字，大会员推荐4K(120),为空时使用配置文件中的："
            )
            print("开始下载")

            if qn == "":
                print(f"将使用配置文件的中的：{config['qn']}")
                qn = config["qn"]
            elif qn not in [6, 16, 32, 64, 74, 80, 112, 116, 120]:
                raise Warning("输入不合法")
            config["qn"] = int(qn)
            downlaod = Downloader(config)
            for data in self.wait_download_moives:
                for name, values in data.items():
                    match = re.search(r"/ep(\d+)", values[0])
                    if match:
                        target = match.group(1)
                        id = f"ep{target}"
                        if downlaod.get_epid_video(id, name):
                            print(f"已经完成 {name}的下载 30s后自动下载")
                            time.sleep(30)
                    else:
                        print("没匹配到id")


class Downloader:
    def __init__(self, config):
        self.config = config

    def get_epid_video(self, ep_id, name):
        url = f"https://api.bilibili.com/pgc/player/web/playurl?ep_id={ep_id[2:]}&qn={self.config['qn']}"
        response = requests.get(url, headers=self.config["headers"])
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
            response = requests.get(url, headers=self.config["headers"], stream=True)
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


if __name__ == "__main__":
    config = load_config()
    BilibiliMovieScraper_ = BilibiliMovieScraper(
        "https://www.bilibili.com/movie/", config["headers"]
    )
    BilibiliMovieScraper_.scrape_movie_info()
    BilibiliMovieScraper_.get_moive()
