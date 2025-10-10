#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的代理测试脚本
用于验证mitmdump是否正确捕获HTTP请求
"""

import requests
import time

def test_proxy_capture():
    """测试代理捕获功能"""
    
    # 配置代理
    proxies = {
        'http': 'http://127.0.0.1:8080',
        'https': 'http://127.0.0.1:8080'
    }
    
    # 禁用SSL验证（因为使用了--ssl-insecure）
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    print("🚀 开始测试代理捕获功能...")
    print(f"代理配置: {proxies}")
    
    # 测试URL列表
    test_urls = [
        "https://www.xiaohongshu.com/explore",
        "https://search.bilibili.com/all?keyword=zhoujielun%E5%91%A8%E6%9D%B0%E4%BC%A6&from_source=webtop_search&spm_id_from=333.1007&search_source=5"
    ]
    
    for i, url in enumerate(test_urls, 1):
        try:
            print(f"\n📡 测试 {i}/{len(test_urls)}: {url}")
            
            response = requests.get(
                url, 
                proxies=proxies, 
                verify=False,  # 禁用SSL验证
                timeout=10,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            
            print(f"✅ 响应状态: {response.status_code}")
            print(f"📊 响应大小: {len(response.content)} bytes")
            
            # 等待一下让mitmproxy处理
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ 请求失败: {e}")
    
    print("\n🎯 测试完成！请检查mitmdump控制台输出和captured_data目录")

if __name__ == "__main__":
    test_proxy_capture()