#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用示例文件

这个文件包含了各种实际使用场景的完整示例，
展示如何使用高效爬虫系统进行数据采集。
"""

import asyncio
import json
from typing import Dict, Any, List
from proxy_crawler import AdvancedCrawler
from config_examples import get_config_by_name


# ============================================================================
# 示例1: 电商商品信息采集
# ============================================================================

def custom_ecommerce_processor(data: Dict[str, Any]) -> Dict[str, Any]:
    """电商数据自定义处理函数"""
    processed = {
        'timestamp': data.get('timestamp'),
        'url': data.get('url'),
        'method': data.get('method'),
        'status_code': data.get('status_code')
    }
    
    # 解析响应数据
    response_data = data.get('response_data', {})
    
    # 处理商品搜索结果
    if 'items' in response_data or 'products' in response_data:
        items = response_data.get('items', response_data.get('products', []))
        processed['products'] = []
        
        for item in items:
            product = {
                'id': item.get('id', item.get('itemId', item.get('productId'))),
                'title': item.get('title', item.get('name', item.get('productName'))),
                'price': item.get('price', item.get('salePrice', item.get('currentPrice'))),
                'original_price': item.get('originalPrice', item.get('marketPrice')),
                'sales': item.get('sales', item.get('sellCount', item.get('soldCount'))),
                'shop_name': item.get('shopName', item.get('storeName')),
                'image_url': item.get('imageUrl', item.get('picUrl', item.get('mainPic'))),
                'detail_url': item.get('detailUrl', item.get('itemUrl'))
            }
            processed['products'].append(product)
    
    # 处理商品详情
    elif 'item' in response_data or 'product' in response_data:
        item = response_data.get('item', response_data.get('product', {}))
        processed['product_detail'] = {
            'id': item.get('id', item.get('itemId')),
            'title': item.get('title', item.get('name')),
            'price': item.get('price', item.get('salePrice')),
            'description': item.get('description', item.get('desc')),
            'specifications': item.get('specifications', item.get('specs', [])),
            'images': item.get('images', item.get('pics', [])),
            'reviews_count': item.get('reviewsCount', item.get('commentCount')),
            'rating': item.get('rating', item.get('score'))
        }
    
    return processed


async def example_ecommerce_crawler():
    """电商爬虫示例"""
    print("=== 电商爬虫示例 ===")
    
    # 获取电商配置
    config = get_config_by_name("ecommerce")
    
    # 创建爬虫实例
    crawler = AdvancedCrawler(config)
    
    # 设置自定义数据处理函数
    crawler.set_custom_processor(custom_ecommerce_processor)
    
    # 定义操作函数
    async def ecommerce_operations(page):
        """电商网站操作"""
        try:
            # 访问淘宝搜索页面
            await page.goto("https://www.taobao.com")
            await page.wait_for_timeout(3000)
            
            # 搜索商品
            search_box = await page.query_selector("#q")
            if search_box:
                await search_box.fill("iPhone 15")
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(5000)
            
            # 点击第一个商品
            first_product = await page.query_selector(".item .title a")
            if first_product:
                await first_product.click()
                await page.wait_for_timeout(5000)
            
            print("电商操作完成")
            
        except Exception as e:
            print(f"电商操作出错: {e}")
    
    # 运行爬虫
    await crawler.run(ecommerce_operations)
    print("电商爬虫示例完成\n")


# ============================================================================
# 示例2: 社交媒体数据采集
# ============================================================================

def custom_social_processor(data: Dict[str, Any]) -> Dict[str, Any]:
    """社交媒体数据自定义处理函数"""
    processed = {
        'timestamp': data.get('timestamp'),
        'url': data.get('url'),
        'platform': 'unknown'
    }
    
    # 识别平台
    url = data.get('url', '')
    if 'weibo.com' in url:
        processed['platform'] = 'weibo'
    elif 'twitter.com' in url:
        processed['platform'] = 'twitter'
    elif 'facebook.com' in url:
        processed['platform'] = 'facebook'
    
    response_data = data.get('response_data', {})
    
    # 处理微博数据
    if processed['platform'] == 'weibo':
        if 'statuses' in response_data:
            processed['posts'] = []
            for status in response_data['statuses']:
                post = {
                    'id': status.get('id'),
                    'text': status.get('text'),
                    'user': status.get('user', {}).get('screen_name'),
                    'created_at': status.get('created_at'),
                    'reposts_count': status.get('reposts_count'),
                    'comments_count': status.get('comments_count'),
                    'attitudes_count': status.get('attitudes_count')
                }
                processed['posts'].append(post)
    
    # 处理Twitter数据
    elif processed['platform'] == 'twitter':
        if 'data' in response_data:
            processed['tweets'] = []
            tweets = response_data['data'] if isinstance(response_data['data'], list) else [response_data['data']]
            for tweet in tweets:
                tweet_data = {
                    'id': tweet.get('id'),
                    'text': tweet.get('text'),
                    'author_id': tweet.get('author_id'),
                    'created_at': tweet.get('created_at'),
                    'public_metrics': tweet.get('public_metrics', {})
                }
                processed['tweets'].append(tweet_data)
    
    return processed


async def example_social_media_crawler():
    """社交媒体爬虫示例"""
    print("=== 社交媒体爬虫示例 ===")
    
    config = get_config_by_name("social_media")
    crawler = AdvancedCrawler(config)
    crawler.set_custom_processor(custom_social_processor)
    
    async def social_operations(page):
        """社交媒体操作"""
        try:
            # 访问微博热搜
            await page.goto("https://weibo.com/hot/search")
            await page.wait_for_timeout(5000)
            
            # 滚动页面加载更多内容
            for i in range(3):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)
            
            print("社交媒体操作完成")
            
        except Exception as e:
            print(f"社交媒体操作出错: {e}")
    
    await crawler.run(social_operations)
    print("社交媒体爬虫示例完成\n")


# ============================================================================
# 示例3: 金融数据采集
# ============================================================================

def custom_financial_processor(data: Dict[str, Any]) -> Dict[str, Any]:
    """金融数据自定义处理函数"""
    processed = {
        'timestamp': data.get('timestamp'),
        'url': data.get('url'),
        'data_type': 'unknown'
    }
    
    response_data = data.get('response_data', {})
    
    # 处理股票行情数据
    if 'data' in response_data and 'diff' in response_data['data']:
        processed['data_type'] = 'stock_quotes'
        processed['stocks'] = []
        
        for stock in response_data['data']['diff']:
            stock_data = {
                'code': stock.get('f12'),  # 股票代码
                'name': stock.get('f14'),  # 股票名称
                'price': stock.get('f2'),  # 当前价格
                'change': stock.get('f3'),  # 涨跌额
                'change_percent': stock.get('f3'),  # 涨跌幅
                'volume': stock.get('f5'),  # 成交量
                'amount': stock.get('f6'),  # 成交额
                'high': stock.get('f15'),  # 最高价
                'low': stock.get('f16'),   # 最低价
                'open': stock.get('f17'),  # 开盘价
                'prev_close': stock.get('f18')  # 昨收价
            }
            processed['stocks'].append(stock_data)
    
    # 处理K线数据
    elif 'data' in response_data and 'klines' in response_data['data']:
        processed['data_type'] = 'kline_data'
        processed['klines'] = []
        
        for kline in response_data['data']['klines']:
            # K线数据通常是字符串，需要分割
            if isinstance(kline, str):
                parts = kline.split(',')
                if len(parts) >= 6:
                    kline_data = {
                        'date': parts[0],
                        'open': float(parts[1]) if parts[1] else 0,
                        'close': float(parts[2]) if parts[2] else 0,
                        'high': float(parts[3]) if parts[3] else 0,
                        'low': float(parts[4]) if parts[4] else 0,
                        'volume': float(parts[5]) if parts[5] else 0
                    }
                    processed['klines'].append(kline_data)
    
    return processed


async def example_financial_crawler():
    """金融数据爬虫示例"""
    print("=== 金融数据爬虫示例 ===")
    
    config = get_config_by_name("financial")
    crawler = AdvancedCrawler(config)
    crawler.set_custom_processor(custom_financial_processor)
    
    async def financial_operations(page):
        """金融网站操作"""
        try:
            # 访问东方财富网
            await page.goto("https://www.eastmoney.com")
            await page.wait_for_timeout(3000)
            
            # 点击股票行情
            stock_link = await page.query_selector("a[href*='quote']")
            if stock_link:
                await stock_link.click()
                await page.wait_for_timeout(5000)
            
            # 搜索特定股票
            search_input = await page.query_selector("input[placeholder*='搜索']")
            if search_input:
                await search_input.fill("000001")
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(3000)
            
            print("金融操作完成")
            
        except Exception as e:
            print(f"金融操作出错: {e}")
    
    await crawler.run(financial_operations)
    print("金融数据爬虫示例完成\n")


# ============================================================================
# 示例4: 新闻资讯采集
# ============================================================================

def custom_news_processor(data: Dict[str, Any]) -> Dict[str, Any]:
    """新闻数据自定义处理函数"""
    processed = {
        'timestamp': data.get('timestamp'),
        'url': data.get('url'),
        'source': 'unknown'
    }
    
    # 识别新闻源
    url = data.get('url', '')
    if 'sina.com' in url:
        processed['source'] = 'sina'
    elif '163.com' in url:
        processed['source'] = 'netease'
    elif 'toutiao.com' in url:
        processed['source'] = 'toutiao'
    
    response_data = data.get('response_data', {})
    
    # 处理新闻列表
    if 'data' in response_data and isinstance(response_data['data'], list):
        processed['articles'] = []
        
        for article in response_data['data']:
            article_data = {
                'id': article.get('id', article.get('docid')),
                'title': article.get('title'),
                'summary': article.get('summary', article.get('digest')),
                'url': article.get('url', article.get('docurl')),
                'publish_time': article.get('ptime', article.get('publish_time')),
                'source': article.get('source'),
                'author': article.get('author'),
                'category': article.get('category', article.get('channel')),
                'tags': article.get('tags', [])
            }
            processed['articles'].append(article_data)
    
    # 处理单篇新闻详情
    elif 'title' in response_data:
        processed['article_detail'] = {
            'title': response_data.get('title'),
            'content': response_data.get('content', response_data.get('body')),
            'publish_time': response_data.get('publish_time', response_data.get('ptime')),
            'author': response_data.get('author'),
            'source': response_data.get('source'),
            'tags': response_data.get('tags', []),
            'images': response_data.get('images', [])
        }
    
    return processed


async def example_news_crawler():
    """新闻爬虫示例"""
    print("=== 新闻爬虫示例 ===")
    
    config = get_config_by_name("news")
    crawler = AdvancedCrawler(config)
    crawler.set_custom_processor(custom_news_processor)
    
    async def news_operations(page):
        """新闻网站操作"""
        try:
            # 访问新浪新闻
            await page.goto("https://news.sina.com.cn")
            await page.wait_for_timeout(3000)
            
            # 点击科技新闻分类
            tech_link = await page.query_selector("a[href*='tech']")
            if tech_link:
                await tech_link.click()
                await page.wait_for_timeout(3000)
            
            # 滚动加载更多新闻
            for i in range(3):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)
            
            print("新闻操作完成")
            
        except Exception as e:
            print(f"新闻操作出错: {e}")
    
    await crawler.run(news_operations)
    print("新闻爬虫示例完成\n")


# ============================================================================
# 示例5: 批量运行多个爬虫
# ============================================================================

async def example_batch_crawlers():
    """批量运行多个爬虫示例"""
    print("=== 批量爬虫示例 ===")
    
    # 定义要运行的爬虫列表
    crawlers = [
        ("test", lambda page: page.goto("https://jsonplaceholder.typicode.com")),
        ("test", lambda page: page.goto("https://httpbin.org/json")),
    ]
    
    # 并发运行多个爬虫
    tasks = []
    for config_name, operation in crawlers:
        config = get_config_by_name(config_name)
        config.proxy_port += len(tasks)  # 使用不同端口避免冲突
        
        crawler = AdvancedCrawler(config)
        task = crawler.run(operation)
        tasks.append(task)
    
    # 等待所有任务完成
    await asyncio.gather(*tasks)
    print("批量爬虫示例完成\n")


# ============================================================================
# 示例6: 自定义数据过滤和处理
# ============================================================================

def advanced_data_filter(data: Dict[str, Any]) -> bool:
    """高级数据过滤函数"""
    # 只保留状态码为200的请求
    if data.get('status_code') != 200:
        return False
    
    # 只保留包含有效JSON数据的响应
    response_data = data.get('response_data')
    if not response_data or not isinstance(response_data, dict):
        return False
    
    # 过滤掉空数据
    if not any(response_data.values()):
        return False
    
    return True


def advanced_data_processor(data: Dict[str, Any]) -> Dict[str, Any]:
    """高级数据处理函数"""
    processed = {
        'timestamp': data.get('timestamp'),
        'url': data.get('url'),
        'method': data.get('method'),
        'status_code': data.get('status_code'),
        'response_size': len(str(data.get('response_data', ''))),
        'processed_at': asyncio.get_event_loop().time()
    }
    
    # 提取关键信息
    response_data = data.get('response_data', {})
    
    # 统计数据
    if isinstance(response_data, dict):
        processed['data_stats'] = {
            'keys_count': len(response_data.keys()),
            'has_list_data': any(isinstance(v, list) for v in response_data.values()),
            'has_nested_data': any(isinstance(v, dict) for v in response_data.values()),
            'total_items': sum(len(v) if isinstance(v, list) else 0 for v in response_data.values())
        }
    
    # 保留原始数据的摘要
    processed['data_summary'] = {
        'top_level_keys': list(response_data.keys())[:10] if isinstance(response_data, dict) else [],
        'data_type': type(response_data).__name__
    }
    
    return processed


async def example_advanced_processing():
    """高级数据处理示例"""
    print("=== 高级数据处理示例 ===")
    
    config = get_config_by_name("test")
    crawler = AdvancedCrawler(config)
    
    # 设置数据过滤器和处理器
    crawler.set_data_filter(advanced_data_filter)
    crawler.set_custom_processor(advanced_data_processor)
    
    async def test_operations(page):
        """测试操作"""
        urls = [
            "https://jsonplaceholder.typicode.com/posts",
            "https://jsonplaceholder.typicode.com/users",
            "https://httpbin.org/json"
        ]
        
        for url in urls:
            await page.goto(url)
            await page.wait_for_timeout(2000)
    
    await crawler.run(test_operations)
    print("高级数据处理示例完成\n")


# ============================================================================
# 主函数 - 运行所有示例
# ============================================================================

async def main():
    """运行所有示例"""
    print("开始运行爬虫示例...\n")
    
    try:
        # 运行基础示例
        await example_news_crawler()  # 新闻爬虫相对简单，先运行
        
        # 运行测试示例
        await example_advanced_processing()
        
        # 运行批量示例
        await example_batch_crawlers()
        
        # 注意：以下示例需要实际的网站访问，可能需要登录或有反爬措施
        # 在实际使用时请谨慎运行
        
        # await example_ecommerce_crawler()
        # await example_social_media_crawler()
        # await example_financial_crawler()
        
        print("所有示例运行完成！")
        
    except Exception as e:
        print(f"运行示例时出错: {e}")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())