from curl_cffi import requests
import time
import pandas as pd
from tqdm import tqdm
import re
import json
import sys 
sys.path.append("..")
from src.tools_data_process.engine_excel import save_and_append_xlsx
from src.tools_data_process.utils_path import get_root_media_save_path


def get_home_page_url(sub_page_urls):
    home_page_url_list = []
    home_page_parse_url_dict = {
        # "微信": ("https://v4.api.link3.cc:5678/api/others/get_weixin_gongzhonghao_homeurl", "weixin_article_url"),# ttps://link3.cc/weixin
    }

    for [platform, url] in tqdm(sub_page_urls):
        time.sleep(2)
        if platform == "微信":
            if True:
                headers = {
                    "Xweb_Xhr": "1",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090c2d)XWEB/11581",
                    "Content-Type": "application/json",
                    "Accept": "*/*",
                    "Sec-Fetch-Site": "cross-site",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Dest": "empty",
                    "Referer": "https://servicewechat.com/wx7eb4f244d6fc6536/16/page-frame.html",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                }
                response = requests.post("https://mlink.cc/api/wechat/linkextractor",
                                         data=json.dumps({"article_url": url}),
                                         proxies={}, headers=headers)
                data = response.content
                print(data)
                data_dict = eval(data.decode("utf-8"))
            if response.status_code != 200:
                print("请求失败，状态码：", response.content)
                raise Exception()
        else:
            raise Exception()

        # 打印响应内容
        print(data_dict)
        home_page_url_dict = {}
        home_page_url_dict["主页名称"] = data_dict["nickname"]
        home_page_url_dict["__biz"] = re.search(r'__biz=(.*)==&scene=', data_dict["result"]).group(1)
        home_page_url_dict["主页链接"] = data_dict["result"]
        home_page_url_dict["是否已经爬取"] = 0
        home_page_url_list.append(home_page_url_dict)
    print(home_page_url_list)
    result_df = pd.DataFrame(home_page_url_list)
    result_df = result_df.drop_duplicates(subset=["__biz"])
    return result_df


if __name__ == '__main__':
    sheet_name = "量化"
    sub_page_urls = [
        ["微信", "https://mp.weixin.qq.com/s/SamwiYj7WYwjWOMek1b8qw"],
        # ["微信", "https://mp.weixin.qq.com/s/vfUsJ6jwdFkGav99auUKLA"],
        # ["微信", "https://mp.weixin.qq.com/s/LoSdPVmBjbEILX0T2Spc6Q"],
        # ["微信", "https://mp.weixin.qq.com/s/wqaNJru6U3VZihJo4YCaGQ"],
        # ["微信", "https://mp.weixin.qq.com/s/XzVmnWGaOAYNDTkYYa_lbw"],
    ]
    result_df = get_home_page_url(sub_page_urls)
    save_and_append_xlsx(result_df, sheet_name, overwrite_col="__biz",
                         output_path=os.path.join(get_root_media_save_path("homepage_url", None)[1], "home_page_url.xlsx"))


