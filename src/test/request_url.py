from curl_cffi import requests

url = 'https://search.bilibili.com/all?keyword={}&from_source=banner_search'.format("南京")
url = 'https://www.zhipin.com/web/geek/job?query={}&city=101190100&experience=104,105&scale=306&jobType=1901&salary=407'.format(
    "文档工程师")
url = "https://mp.weixin.qq.com/s?__biz=MzUyMzUyNzM4Ng==&mid=2247504247&idx=2&sn=41bdfc75f19e70ac168362e510ea7b3b&chksm=fa39a4c2cd4e2dd459a6ae4afb90a404f5dc77a0012be79206eb09394b51eb8557725ab254df&scene=127#wechat_redirect"

# print("请求地址:", url)

headers = {
    "Host": "kimi.moonshot.cn",
    "Connection": "keep-alive",
    "Content-Length": "123",
    "x-msh-session-id": "1730129924829253384",
    "sec-ch-ua-platform": "Windows",
    "Authorization": "Bearer eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ1c2VyLWNlbnRlciIsImV4cCI6MTc0MzIzNDAzNywiaWF0IjoxNzM1NDU4MDM3LCJqdGkiOiJjdG9mcHRiZHVxYjNlczFpZGdtMCIsInR5cCI6ImFjY2VzcyIsImFwcF9pZCI6ImtpbWkiLCJzdWIiOiJjbzk2OXZrdWR1NmM1am9hY3FiZyIsInNwYWNlX2lkIjoiY285Njl2a3VkdTZjNWpvYWNxYjAiLCJhYnN0cmFjdF91c2VyX2lkIjoiY285Njl2a3VkdTZjNWpvYWNxYWcifQ.93-XmF-gNj8MoaYlyOB-_3oWZPplKsKa5YlnOCdiOu4CWbu2jRRI_cMkXkJN5nJUh-XVQ_OtjjmJLK2b6LmWvA",
    "x-msh-platform": "web",
    "x-msh-device-id": "7409278258769860109",
    "sec-ch-ua": "Microsoft Edge;v=131, Chromium;v=131, Not_A Brand;v=24",
    "sec-ch-ua-mobile": "?0",
    "R-Timezone": "Asia/Shanghai",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    "Content-Type": "application/json",
    "X-Traffic-Id": "co969vkudu6c5joacqbg",
    "Accept": "*/*",
    "Origin": "https://kimi.moonshot.cn",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://kimi.moonshot.cn/chat/cu1i45kr4djrsk3joj20",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Cookie": "_ga=GA1.1.511310081.1725107027; _gcl_au=1.1.1037238185.1735458036; kimi-auth=eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ1c2VyLWNlbnRlciIsImV4cCI6MTc0MzIzNDAzNywiaWF0IjoxNzM1NDU4MDM3LCJqdGkiOiJjdG9mcHRiZHVxYjNlczFpZGdtMCIsInR5cCI6ImFjY2VzcyIsImFwcF9pZCI6ImtpbWkiLCJzdWIiOiJjbzk2OXZrdWR1NmM1am9hY3FiZyIsInNwYWNlX2lkIjoiY285Njl2a3VkdTZjNWpvYWNxYjAiLCJhYnN0cmFjdF91c2VyX2lkIjoiY285Njl2a3VkdTZjNWpvYWNxYWcifQ.93-XmF-gNj8MoaYlyOB-_3oWZPplKsKa5YlnOCdiOu4CWbu2jRRI_cMkXkJN5nJUh-XVQ_OtjjmJLK2b6LmWvA; ntes_utid=tid._.y0VQTS8VIXdAFkRFRVKSJEdDbU63nadu._.0; _ga_YXD8W70SZP=GS1.1.1736647192.33.0.1736647192.0.0.0"
}

response = requests.post("https://kimi.moonshot.cn/api/pre-sign-url", headers=headers,
                         data={"action": "file",
                               "name": "【东盟十国07丨老挝】东南亚最穷国，被美法轮流伺候，如何借东风？.txt"})
content = response.text
print(content)
