from curl_cffi import requests

req = {"url": [
    "https://mp.weixin.qq.com/s?__biz=MzIwNTU2ODMwNg==&mid=2247493230&idx=1&sn=13ac189a8aee34cc9197b3f6db6d4a3c&scene=21#wechat_redirect",
    "https://mp.weixin.qq.com/s?__biz=MzIwNTU2ODMwNg==&mid=2247493067&idx=2&sn=8bf0af91342a9a837a725cd557ba959f&scene=21#wechat_redirect",
    "https://mp.weixin.qq.com/s?__biz=MzIwNTU2ODMwNg==&mid=2247492943&idx=3&sn=bd1c9d06af45c711efb16c3af301cb5e&scene=21#wechat_redirect",
    "https://mp.weixin.qq.com/s?__biz=MzIwNTU2ODMwNg==&mid=2247492857&idx=2&sn=75f17d30e2b93fecdbe6bc752a9a0b92&scene=21#wechat_redirect",
    "https://mp.weixin.qq.com/s?__biz=MzIwNTU2ODMwNg==&mid=2247492987&idx=1&sn=539ed6801ba3cc28f61f1f99a6fd72f0&scene=21#wechat_redirect",
    "https://mp.weixin.qq.com/s?__biz=MzIwNTU2ODMwNg==&mid=2247493190&idx=1&sn=7a948f904a75d10353564493601ace65&scene=21#wechat_redirect",
    "https://mp.weixin.qq.com/s?__biz=MzIwNTU2ODMwNg==&mid=2247493203&idx=1&sn=426eb085ec91eee486d624abee37bb4b&scene=21#wechat_redirect"]}

req = {"url": [
    "https://mp.weixin.qq.com/s?__biz=MzIwNTU2ODMwNg==&mid=2247493230&idx=1&sn=13ac189a8aee34cc9197b3f6db6d4a3c&scene=21#wechat_redirect",
    "https://mp.weixin.qq.com/s?__biz=MzIwNTU2ODMwNg==&mid=2247493067&idx=2&sn=8bf0af91342a9a837a725cd557ba959f&scene=21#wechat_redirect",
    "https://mp.weixin.qq.com/s?__biz=MzIwNTU2ODMwNg==&mid=2247492943&idx=3&sn=bd1c9d06af45c711efb16c3af301cb5e&scene=21#wechat_redirect",
    "https://mp.weixin.qq.com/s?__biz=MzIwNTU2ODMwNg==&mid=2247492857&idx=2&sn=75f17d30e2b93fecdbe6bc752a9a0b92&scene=21#wechat_redirect",
    "https://mp.weixin.qq.com/s?__biz=MzIwNTU2ODMwNg==&mid=2247492987&idx=1&sn=539ed6801ba3cc28f61f1f99a6fd72f0&scene=21#wechat_redirect",
    "https://mp.weixin.qq.com/s?__biz=MzIwNTU2ODMwNg==&mid=2247493190&idx=1&sn=7a948f904a75d10353564493601ace65&scene=21#wechat_redirect",
    "https://mp.weixin.qq.com/s?__biz=MzIwNTU2ODMwNg==&mid=2247493203&idx=1&sn=426eb085ec91eee486d624abee37bb4b&scene=21#wechat_redirect"]}

for i in req["url"]:
    response = requests.get(i)
    print(response.text)
