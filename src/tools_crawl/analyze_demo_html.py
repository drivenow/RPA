#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
分析demo.html文件，理解小红书页面结构
"""

import os
import re
import json
from src.extractor.advanced_json_matcher import AdvancedJSONMatcher

def analyze_demo_html():
    """分析demo.html文件"""
    demo_file = r"x:\RPA\tools_crawl\captured_data\demo.html"
    
    if not os.path.exists(demo_file):
        print(f"文件不存在: {demo_file}")
        return
    
    with open(demo_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"文件大小: {len(content)} 字符")
    print(f"文件行数: {content.count(chr(10)) + 1}")
    
    # 分析script标签
    script_pattern = r'<script[^>]*>(.*?)</script>'
    scripts = re.findall(script_pattern, content, re.DOTALL)
    print(f"\n找到 {len(scripts)} 个script标签:")
    
    for i, script in enumerate(scripts):
        script_size = len(script)
        print(f"  Script {i+1}: {script_size} 字符")
        if script_size > 100:
            # 显示前100个字符
            preview = script[:100].replace('\n', ' ').replace('\r', '')
            print(f"    预览: {preview}...")
        
        # 检查是否包含JSON数据
        if any(keyword in script for keyword in ['window.__', 'data:', '"items":', '"notes":']):
            print(f"    可能包含数据!")
    
    # 检查data属性
    data_attrs = re.findall(r'data-[^=]*="([^"]*)"', content)
    print(f"\n找到 {len(data_attrs)} 个data属性")
    
    large_data_attrs = [attr for attr in data_attrs if len(attr) > 100]
    print(f"其中 {len(large_data_attrs)} 个较大的data属性:")
    for attr in large_data_attrs[:5]:  # 只显示前5个
        preview = attr[:100].replace('\n', ' ')
        print(f"  {preview}...")
    
    # 使用AdvancedJSONMatcher测试
    print("\n=== 使用AdvancedJSONMatcher测试 ===")
    matcher = AdvancedJSONMatcher()
    candidates = matcher.extract_and_rank_json(content)
    
    print(f"找到 {len(candidates)} 个JSON候选")
    for i, candidate in enumerate(candidates):
        print(f"候选 {i+1}:")
        print(f"  来源: {candidate.get('source', 'unknown')}")
        print(f"  大小: {candidate.get('size', 0)} 字符")
        print(f"  置信度: {candidate.get('confidence', 0)}")
        if 'data' in candidate:
            data = candidate['data']
            if isinstance(data, dict):
                print(f"  键: {list(data.keys())[:10]}")  # 只显示前10个键
            elif isinstance(data, list):
                print(f"  列表长度: {len(data)}")
    
    # 检查页面完整性
    print("\n=== 页面完整性检查 ===")
    has_body_end = '</body>' in content
    has_html_end = '</html>' in content
    has_head_end = '</head>' in content
    
    print(f"包含 </body>: {has_body_end}")
    print(f"包含 </html>: {has_html_end}")
    print(f"包含 </head>: {has_head_end}")
    
    # 检查小红书特定元素
    xhs_indicators = [
        'data-v-',
        'xhscdn.com',
        'xiaohongshu',
        'note-item',
        'explore/',
        'xsec_token'
    ]
    
    print(f"\n=== 小红书特定元素检查 ===")
    for indicator in xhs_indicators:
        count = content.count(indicator)
        print(f"{indicator}: {count} 次")
    
    # 分析note-item结构
    note_items = re.findall(r'<section class="note-item"[^>]*>(.*?)</section>', content, re.DOTALL)
    print(f"\n找到 {len(note_items)} 个note-item")
    
    if note_items:
        # 分析第一个note-item
        first_item = note_items[0]
        print(f"第一个note-item大小: {len(first_item)} 字符")
        
        # 提取href链接
        href_pattern = r'href="([^"]*)"'
        hrefs = re.findall(href_pattern, first_item)
        print(f"包含 {len(hrefs)} 个链接:")
        for href in hrefs[:3]:  # 只显示前3个
            print(f"  {href}")

def test_improved_extraction():
    """测试改进的提取逻辑"""
    print("\n" + "="*50)
    print("测试改进的提取逻辑")
    print("="*50)
    
    # 模拟一个包含JSON数据的HTML响应
    test_html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test</title>
    </head>
    <body>
        <div id="app"></div>
        <script>
            window.__INITIAL_STATE__ = {
                "data": {
                    "items": [
                        {
                            "id": "test1",
                            "title": "测试笔记1",
                            "user": {"name": "用户1"}
                        },
                        {
                            "id": "test2", 
                            "title": "测试笔记2",
                            "user": {"name": "用户2"}
                        }
                    ]
                }
            };
        </script>
    </body>
    </html>
    '''
    
    matcher = AdvancedJSONMatcher()
    candidates = matcher.extract_and_rank_json(test_html)
    
    print(f"测试HTML找到 {len(candidates)} 个JSON候选")
    for i, candidate in enumerate(candidates):
        print(f"候选 {i+1}:")
        print(f"  来源: {candidate.get('source', 'unknown')}")
        print(f"  大小: {candidate.get('size', 0)} 字符")
        print(f"  置信度: {candidate.get('confidence', 0)}")
        if 'data' in candidate:
            data = candidate['data']
            if isinstance(data, dict) and 'data' in data and 'items' in data['data']:
                items = data['data']['items']
                print(f"  找到 {len(items)} 个items")
                for item in items:
                    print(f"    - {item.get('title', 'No title')}")

if __name__ == "__main__":
    analyze_demo_html()
    test_improved_extraction()