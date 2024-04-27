import re
import time

import requests
from qrcode import QRCode


class Login:
    def __init__(
        self,
    ) -> None:
        self.session = requests.session()
        self.headers = {
            "authority": "api.vc.bilibili.com",
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://message.bilibili.com",
            "referer": "https://message.bilibili.com/",
            "sec-ch-ua": '"Chromium";v="116", "Not)A;Brand";v="24", "Microsoft Edge";v="116"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.81",
        }
        if self.is_login():
            return True
        else:
            self.cookies_dict = self.scan_code()
            if self.verification():
                self.cookie_bool = True

    def get_cookies(self):
        if self.cookie_bool:
            return self.cookies_dict

    def is_login(self):
        try:
            self.session.cookies.load(ignore_discard=True)
        except Exception as e:
            print(e)
        login_url = self.session.get(
            "https://api.bilibili.com/x/web-interface/nav",
            verify=False,
            headers=self.headers,
        ).json()
        if login_url["code"] == 0:
            print(f"Cookies值有效, {login_url['data']['uname']}, 已登录！")
            return True
        else:
            print("Cookies值已经失效，请重新扫码登录！")
            return False

    def scan_code(self):

        get_login = self.session.get(
            "https://passport.bilibili.com/x/passport-login/web/qrcode/generate?source=main-fe-header",
            headers=self.headers,
        ).json()
        qrcode_key = get_login["data"]["qrcode_key"]
        token_url = f"https://passport.bilibili.com/x/passport-login/web/qrcode/poll?qrcode_key={qrcode_key}&source=main-fe-header"
        qr = QRCode()
        qr.add_data(get_login["data"]["url"])
        qr.print_ascii(invert=True)
        print("等待扫码...")
        while 1:
            qrcode_data = self.session.get(token_url, headers=self.headers).json()
            if qrcode_data["data"]["code"] == 0:
                print("扫码成功")
                self.session.get(qrcode_data["data"]["url"], headers=self.headers)
                break
            time.sleep(1)
        cookies_dict = requests.utils.dict_from_cookiejar(self.session.cookies)
        return cookies_dict

    def verification(self):
        url = "https://api.bilibili.com/x/web-interface/nav"
        resp1 = self.session.get(url=url, headers=self.headers).json()
        global tk_image
        if resp1["data"]["isLogin"]:
            print("cookie有效！登录成功！")
            return True


if __name__ == "__main__":
    test = Login()
