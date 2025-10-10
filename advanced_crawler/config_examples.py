#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置示例文件

这个文件包含了各种常见场景下的爬虫配置示例，
用户可以根据自己的需求选择合适的配置。
"""

from proxy_crawler import CrawlerConfig
from typing import List


def get_ecommerce_config() -> CrawlerConfig:
    """电商网站配置示例"""
    return CrawlerConfig(
        # 代理配置
        proxy_type="mitmproxy",
        proxy_host="127.0.0.1",
        proxy_port=8080,
        
        # 目标配置 - 电商API
        target_domains=[
            "api.taobao.com",
            "api.tmall.com",
            "api.jd.com",
            "api.pinduoduo.com",
            "search.suning.com",
            "api.vip.com"
        ],
        target_apis=[
            "/api/search",
            "/api/product",
            "/api/item",
            "/search",
            "/goods",
            "/commodity",
            "/mtop",  # 淘宝API前缀
            "/api/v",  # 通用API版本前缀
        ],
        
        # 浏览器配置
        headless=False,  # 显示浏览器便于调试
        browser_type="chromium",
        
        # 数据存储
        output_dir="./ecommerce_data",
        save_raw_data=True,
        save_parsed_data=True,
        
        # 性能配置 - 电商网站通常有反爬措施，需要降低频率
        max_concurrent=2,
        request_delay=3.0,  # 3秒间隔
        timeout=60  # 增加超时时间
    )


def get_social_media_config() -> CrawlerConfig:
    """社交媒体配置示例"""
    return CrawlerConfig(
        # 代理配置
        proxy_type="mitmproxy",
        proxy_host="127.0.0.1",
        proxy_port=8081,  # 使用不同端口避免冲突
        
        # 目标配置 - 社交媒体API
        target_domains=[
            "api.weibo.com",
            "api.twitter.com",
            "graph.facebook.com",
            "api.instagram.com",
            "api.tiktok.com",
            "api.douyin.com",
            "api.xiaohongshu.com"
        ],
        target_apis=[
            "/api/posts",
            "/api/feed",
            "/api/timeline",
            "/api/comments",
            "/api/user",
            "/v1/",
            "/v2/",
            "/graphql",  # Facebook/Instagram GraphQL
            "/2/tweets",  # Twitter API v2
        ],
        
        # 浏览器配置
        headless=False,
        browser_type="chromium",
        
        # 数据存储
        output_dir="./social_media_data",
        save_raw_data=True,
        save_parsed_data=True,
        
        # 性能配置
        max_concurrent=3,
        request_delay=2.0,
        timeout=45
    )


def get_news_config() -> CrawlerConfig:
    """新闻资讯配置示例"""
    return CrawlerConfig(
        # 代理配置
        proxy_type="mitmproxy",
        proxy_host="127.0.0.1",
        proxy_port=8082,
        
        # 目标配置 - 新闻API
        target_domains=[
            "api.sina.com.cn",
            "api.163.com",
            "api.sohu.com",
            "api.toutiao.com",
            "api.qq.com",
            "api.people.com.cn",
            "api.xinhuanet.com"
        ],
        target_apis=[
            "/api/news",
            "/api/article",
            "/api/content",
            "/api/list",
            "/news",
            "/article",
            "/feed",
            "/recommend"
        ],
        
        # 浏览器配置
        headless=True,  # 新闻网站可以使用无头模式
        browser_type="chromium",
        
        # 数据存储
        output_dir="./news_data",
        save_raw_data=True,
        save_parsed_data=True,
        
        # 性能配置 - 新闻网站通常限制较少
        max_concurrent=5,
        request_delay=1.0,
        timeout=30
    )


def get_financial_config() -> CrawlerConfig:
    """金融数据配置示例"""
    return CrawlerConfig(
        # 代理配置
        proxy_type="mitmproxy",
        proxy_host="127.0.0.1",
        proxy_port=8083,
        
        # 目标配置 - 金融API
        target_domains=[
            "api.eastmoney.com",
            "api.sina.com.cn",  # 新浪财经
            "api.163.com",      # 网易财经
            "api.10jqka.com.cn", # 同花顺
            "api.hexun.com",    # 和讯
            "api.cnstock.com",  # 中国证券网
            "quote.eastmoney.com",
            "push2.eastmoney.com"
        ],
        target_apis=[
            "/api/qt",      # 东财行情API
            "/api/stock",
            "/api/fund",
            "/api/bond",
            "/api/futures",
            "/api/forex",
            "/api/crypto",
            "/quote",
            "/market",
            "/realtime",
            "/kline",
            "/finance"
        ],
        
        # 浏览器配置
        headless=True,
        browser_type="chromium",
        
        # 数据存储
        output_dir="./financial_data",
        save_raw_data=True,
        save_parsed_data=True,
        
        # 性能配置 - 金融数据更新频繁，可以适当提高频率
        max_concurrent=4,
        request_delay=0.5,  # 较短间隔
        timeout=20
    )


def get_job_search_config() -> CrawlerConfig:
    """招聘网站配置示例"""
    return CrawlerConfig(
        # 代理配置
        proxy_type="mitmproxy",
        proxy_host="127.0.0.1",
        proxy_port=8084,
        
        # 目标配置 - 招聘API
        target_domains=[
            "api.zhipin.com",     # Boss直聘
            "api.51job.com",      # 前程无忧
            "api.liepin.com",     # 猎聘
            "api.lagou.com",      # 拉勾
            "api.zhaopin.com",    # 智联招聘
            "api.jobui.com",      # 职友集
            "www.zhipin.com",
            "www.lagou.com"
        ],
        target_apis=[
            "/api/job",
            "/api/search",
            "/api/position",
            "/api/company",
            "/api/salary",
            "/wapi/",  # 微信小程序API
            "/c/",     # Boss直聘API
            "/jobs/",
            "/position"
        ],
        
        # 浏览器配置
        headless=False,
        browser_type="chromium",
        
        # 数据存储
        output_dir="./job_data",
        save_raw_data=True,
        save_parsed_data=True,
        
        # 性能配置
        max_concurrent=3,
        request_delay=2.0,
        timeout=40
    )


def get_real_estate_config() -> CrawlerConfig:
    """房产网站配置示例"""
    return CrawlerConfig(
        # 代理配置
        proxy_type="mitmproxy",
        proxy_host="127.0.0.1",
        proxy_port=8085,
        
        # 目标配置 - 房产API
        target_domains=[
            "api.lianjia.com",    # 链家
            "api.anjuke.com",     # 安居客
            "api.fang.com",       # 搜房网
            "api.ke.com",         # 贝壳
            "api.58.com",         # 58同城
            "api.ganji.com",      # 赶集网
            "m.lianjia.com",
            "m.ke.com"
        ],
        target_apis=[
            "/api/house",
            "/api/rent",
            "/api/sale",
            "/api/community",
            "/api/price",
            "/api/search",
            "/ershoufang",
            "/zufang",
            "/loupan",
            "/xiaoqu"
        ],
        
        # 浏览器配置
        headless=False,
        browser_type="chromium",
        
        # 数据存储
        output_dir="./real_estate_data",
        save_raw_data=True,
        save_parsed_data=True,
        
        # 性能配置
        max_concurrent=2,
        request_delay=3.0,  # 房产网站通常有较严格的限制
        timeout=50
    )


def get_travel_config() -> CrawlerConfig:
    """旅游网站配置示例"""
    return CrawlerConfig(
        # 代理配置
        proxy_type="mitmproxy",
        proxy_host="127.0.0.1",
        proxy_port=8086,
        
        # 目标配置 - 旅游API
        target_domains=[
            "api.ctrip.com",      # 携程
            "api.qunar.com",      # 去哪儿
            "api.tuniu.com",      # 途牛
            "api.lvmama.com",     # 驴妈妈
            "api.mafengwo.cn",    # 马蜂窝
            "api.dianping.com",   # 大众点评
            "m.ctrip.com",
            "touch.qunar.com"
        ],
        target_apis=[
            "/api/flight",
            "/api/hotel",
            "/api/train",
            "/api/scenic",
            "/api/restaurant",
            "/api/search",
            "/api/price",
            "/restapi/",
            "/webapp/",
            "/h5/"
        ],
        
        # 浏览器配置
        headless=False,
        browser_type="chromium",
        
        # 数据存储
        output_dir="./travel_data",
        save_raw_data=True,
        save_parsed_data=True,
        
        # 性能配置
        max_concurrent=3,
        request_delay=2.0,
        timeout=45
    )


def get_test_config() -> CrawlerConfig:
    """测试配置 - 用于开发和调试"""
    return CrawlerConfig(
        # 代理配置
        proxy_type="mitmproxy",
        proxy_host="127.0.0.1",
        proxy_port=8080,
        
        # 目标配置 - 测试API
        target_domains=[
            "jsonplaceholder.typicode.com",
            "httpbin.org",
            "api.github.com",
            "reqres.in",
            "api.coindesk.com"
        ],
        target_apis=[
            "/posts",
            "/users",
            "/comments",
            "/json",
            "/get",
            "/api/",
            "/v1/"
        ],
        
        # 浏览器配置
        headless=False,  # 测试时显示浏览器
        browser_type="chromium",
        
        # 数据存储
        output_dir="./test_data",
        save_raw_data=True,
        save_parsed_data=True,
        
        # 性能配置 - 测试时可以更快
        max_concurrent=5,
        request_delay=0.5,
        timeout=15
    )


def get_high_performance_config() -> CrawlerConfig:
    """高性能配置 - 适用于大规模数据采集"""
    return CrawlerConfig(
        # 代理配置
        proxy_type="mitmproxy",
        proxy_host="127.0.0.1",
        proxy_port=8080,
        
        # 目标配置 - 根据实际需求设置
        target_domains=[],  # 需要用户自定义
        target_apis=[],     # 需要用户自定义
        
        # 浏览器配置
        headless=True,      # 无头模式提高性能
        browser_type="chromium",
        
        # 数据存储
        output_dir="./high_performance_data",
        save_raw_data=False,  # 只保存解析后的数据
        save_parsed_data=True,
        
        # 性能配置 - 最大化性能
        max_concurrent=10,   # 高并发
        request_delay=0.1,   # 最小间隔
        timeout=10           # 短超时
    )


def get_safe_config() -> CrawlerConfig:
    """安全配置 - 适用于需要谨慎操作的场景"""
    return CrawlerConfig(
        # 代理配置
        proxy_type="mitmproxy",
        proxy_host="127.0.0.1",
        proxy_port=8080,
        
        # 目标配置 - 根据实际需求设置
        target_domains=[],  # 需要用户自定义
        target_apis=[],     # 需要用户自定义
        
        # 浏览器配置
        headless=False,     # 显示浏览器便于监控
        browser_type="chromium",
        
        # 数据存储
        output_dir="./safe_data",
        save_raw_data=True,
        save_parsed_data=True,
        
        # 性能配置 - 保守设置
        max_concurrent=1,    # 单线程
        request_delay=5.0,   # 长间隔
        timeout=60           # 长超时
    )


# 配置选择器
CONFIG_CHOICES = {
    "ecommerce": get_ecommerce_config,
    "social_media": get_social_media_config,
    "news": get_news_config,
    "financial": get_financial_config,
    "job_search": get_job_search_config,
    "real_estate": get_real_estate_config,
    "travel": get_travel_config,
    "test": get_test_config,
    "high_performance": get_high_performance_config,
    "safe": get_safe_config
}


def get_config_by_name(name: str) -> CrawlerConfig:
    """根据名称获取配置"""
    if name not in CONFIG_CHOICES:
        raise ValueError(f"未知的配置名称: {name}. 可选项: {list(CONFIG_CHOICES.keys())}")
    
    return CONFIG_CHOICES[name]()


def list_available_configs() -> List[str]:
    """列出所有可用的配置"""
    return list(CONFIG_CHOICES.keys())


if __name__ == "__main__":
    # 示例：如何使用配置
    print("可用的配置:")
    for config_name in list_available_configs():
        print(f"  - {config_name}")
    
    print("\n示例：获取电商配置")
    ecommerce_config = get_config_by_name("ecommerce")
    print(f"代理端口: {ecommerce_config.proxy_port}")
    print(f"目标域名: {ecommerce_config.target_domains[:3]}...")  # 只显示前3个
    print(f"输出目录: {ecommerce_config.output_dir}")