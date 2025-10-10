#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试修复后的ProxyHandler系统
验证JSON提取和HTML结构提取的集成功能
"""

import sys
import os
import json
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.proxy_handler import ProxyHandler
from src.utils.logger import setup_logger

# 设置日志
logger = setup_logger(__name__)

def test_json_response():
    """测试JSON响应处理"""
    print("\n=== 测试JSON响应处理 ===")
    
    # 模拟JSON响应
    json_response = {
        "data": {
            "items": [
                {
                    "id": "test_note_1",
                    "title": "测试笔记1",
                    "author": {"name": "测试用户1"},
                    "interact_info": {"liked_count": "100"}
                },
                {
                    "id": "test_note_2", 
                    "title": "测试笔记2",
                    "author": {"name": "测试用户2"},
                    "interact_info": {"liked_count": "200"}
                }
            ]
        },
        "success": True
    }
    
    return json.dumps(json_response, ensure_ascii=False)

def test_html_with_json():
    """测试包含JSON的HTML响应"""
    print("\n=== 测试包含JSON的HTML响应 ===")
    
    html_with_json = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>小红书</title>
    </head>
    <body>
        <div id="app"></div>
        <script>
            window.__INITIAL_STATE__ = {
                "data": {
                    "items": [
                        {
                            "id": "html_json_note_1",
                            "title": "HTML中的JSON笔记1",
                            "author": {"name": "HTML用户1"},
                            "interact_info": {"liked_count": "300"}
                        }
                    ]
                },
                "success": true
            };
        </script>
    </body>
    </html>
    """
    
    return html_with_json

def test_html_structure():
    """测试HTML结构提取"""
    print("\n=== 测试HTML结构提取 ===")
    
    # 读取demo.html文件
    demo_html_path = project_root / 'captured_data' / 'demo.html'
    if demo_html_path.exists():
        with open(demo_html_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        print(f"警告: demo.html文件不存在: {demo_html_path}")
        return None

def run_test():
    """运行测试"""
    try:
        print("开始测试修复后的ProxyHandler系统...")
        
        # 初始化ProxyHandler
        config_path = project_root / 'config' / 'xiaohongshu_config.exp'
        if not config_path.exists():
            print(f"警告: 配置文件不存在: {config_path}")
            print("使用默认配置进行测试...")
            # 创建临时配置文件
            config_path.parent.mkdir(exist_ok=True)
            temp_config = {
                "crawler": {
                    "target_urls": ["https://www.xiaohongshu.com/explore"]
                },
                "data_extraction": {
                    "table_name": "xiaohongshu_notes",
                    "deduplicate": True,
                    "deduplicate_field": "note_id"
                },
                "database": {
                    "type": "MySql",
                    "connection_string": "test_connection"
                }
            }
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(temp_config, f, ensure_ascii=False, indent=2)
        
        handler = ProxyHandler(str(config_path))
        print("ProxyHandler初始化成功")
        
        # 测试用例1: JSON响应
        print("\n" + "="*50)
        json_response = test_json_response()
        url1 = "https://edith.xiaohongshu.com/api/sns/web/v1/feed"
        result1 = handler.handle_api_response(url1, json_response)
        print(f"JSON响应测试结果: {result1}")
        
        # 测试用例2: HTML中包含JSON
        print("\n" + "="*50)
        html_json_response = test_html_with_json()
        url2 = "https://www.xiaohongshu.com/explore"
        result2 = handler.handle_api_response(url2, html_json_response)
        print(f"HTML中JSON测试结果: {result2}")
        
        # 测试用例3: HTML结构提取
        print("\n" + "="*50)
        html_structure_response = test_html_structure()
        if html_structure_response:
            url3 = "https://www.xiaohongshu.com/explore"
            result3 = handler.handle_api_response(url3, html_structure_response)
            print(f"HTML结构提取测试结果: {result3}")
        else:
            print("跳过HTML结构提取测试（demo.html文件不存在）")
            result3 = False
        
        # 显示统计信息
        print("\n" + "="*50)
        print("最终统计信息:")
        stats = handler.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # 测试结果总结
        print("\n" + "="*50)
        print("测试结果总结:")
        print(f"  JSON响应处理: {'✓' if result1 else '✗'}")
        print(f"  HTML中JSON提取: {'✓' if result2 else '✗'}")
        print(f"  HTML结构提取: {'✓' if result3 else '✗'}")
        
        success_count = sum([result1, result2, result3])
        total_tests = 3 if html_structure_response else 2
        print(f"  总体成功率: {success_count}/{total_tests}")
        
        if success_count == total_tests:
            print("\n🎉 所有测试通过！ProxyHandler修复成功！")
        else:
            print(f"\n⚠️  部分测试失败，需要进一步检查")
        
        return success_count == total_tests
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)