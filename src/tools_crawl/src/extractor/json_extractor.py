#!/usr/bin/env python3
"""
JSON提取器 - 从网页HTML中提取JSON数据
专门用于分析小红书等网站的页面数据
"""

import json
import re
import os
from typing import List, Dict, Any, Tuple
from pathlib import Path


class JSONExtractor:
    """从HTML内容中提取JSON数据的工具类"""
    
    def __init__(self):
        self.json_patterns = [
            # 常见的JSON数据模式
            r'window\.__INITIAL_STATE__\s*=\s*({.+?});',  # 初始状态数据
            r'window\.__NUXT__\s*=\s*({.+?});',          # Nuxt.js数据
            r'window\.__APOLLO_STATE__\s*=\s*({.+?});',   # Apollo状态
            r'window\.g_initialProps\s*=\s*({.+?});',     # 初始属性
            r'window\.pageData\s*=\s*({.+?});',           # 页面数据
            r'window\.initialData\s*=\s*({.+?});',        # 初始数据
            r'<script[^>]*>.*?var\s+\w+\s*=\s*({.+?});.*?</script>',  # script标签中的变量
            r'<script[^>]*type=["\']application/json["\'][^>]*>(.+?)</script>',  # JSON script标签
            r'<script[^>]*>.*?({["\'].*?["\']:.+?}[^}]*}).*?</script>',  # 通用JSON对象
        ]
    
    def extract_json_from_html(self, html_content: str) -> List[Dict[str, Any]]:
        """从HTML内容中提取所有JSON数据"""
        json_objects = []
        
        # 1. 使用正则表达式匹配常见模式
        for pattern in self.json_patterns:
            matches = re.finditer(pattern, html_content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                json_str = match.group(1) if match.groups() else match.group(0)
                try:
                    # 清理JSON字符串
                    json_str = self._clean_json_string(json_str)
                    json_obj = json.loads(json_str)
                    json_objects.append({
                        'pattern': pattern,
                        'size': len(json_str),
                        'data': json_obj,
                        'raw': json_str[:500] + '...' if len(json_str) > 500 else json_str
                    })
                except (json.JSONDecodeError, Exception) as e:
                    continue
        
        # 2. 查找script标签中的大型JSON对象
        script_pattern = r'<script[^>]*>(.*?)</script>'
        script_matches = re.finditer(script_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        for script_match in script_matches:
            script_content = script_match.group(1)
            # 在script内容中查找JSON对象
            json_candidates = self._find_json_candidates(script_content)
            for candidate in json_candidates:
                try:
                    json_obj = json.loads(candidate)
                    json_objects.append({
                        'pattern': 'script_content',
                        'size': len(candidate),
                        'data': json_obj,
                        'raw': candidate[:500] + '...' if len(candidate) > 500 else candidate
                    })
                except (json.JSONDecodeError, Exception):
                    continue
        
        # 按大小排序，返回最大的JSON对象
        json_objects.sort(key=lambda x: x['size'], reverse=True)
        return json_objects
    
    def _clean_json_string(self, json_str: str) -> str:
        """清理JSON字符串，移除多余的字符"""
        # 移除前后空白
        json_str = json_str.strip()
        
        # 移除末尾的分号
        if json_str.endswith(';'):
            json_str = json_str[:-1]
        
        # 移除JavaScript注释
        json_str = re.sub(r'//.*?$', '', json_str, flags=re.MULTILINE)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        
        return json_str
    
    def _find_json_candidates(self, content: str) -> List[str]:
        """在内容中查找可能的JSON对象"""
        candidates = []
        
        # 查找以{开始的大型对象
        brace_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.finditer(brace_pattern, content, re.DOTALL)
        
        for match in matches:
            candidate = match.group(0)
            # 只考虑较大的JSON对象（超过100字符）
            if len(candidate) > 100:
                candidates.append(candidate)
        
        return candidates
    
    def analyze_captured_data(self, file_path: str) -> Dict[str, Any]:
        """分析抓包数据文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                captured_data = json.load(f)
            
            results = {
                'file_path': file_path,
                'capture_stats': captured_data.get('capture_stats', {}),
                'extracted_json': []
            }
            
            # 分析每个捕获的请求
            for item in captured_data.get('captured_data', []):
                if 'response_body' in item:
                    html_content = item['response_body']
                    json_objects = self.extract_json_from_html(html_content)
                    
                    if json_objects:
                        results['extracted_json'].append({
                            'url': item.get('url', ''),
                            'method': item.get('method', ''),
                            'status_code': item.get('status_code', ''),
                            'json_count': len(json_objects),
                            'largest_json': json_objects[0] if json_objects else None,
                            'all_json': json_objects
                        })
            
            return results
            
        except Exception as e:
            return {'error': str(e), 'file_path': file_path}
    
    def save_extracted_json(self, results: Dict[str, Any], output_dir: str = None):
        """保存提取的JSON数据"""
        if output_dir is None:
            output_dir = os.path.dirname(results['file_path'])
        
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        # 保存分析结果
        timestamp = results['capture_stats'].get('save_time', '').replace(':', '-').replace(' ', '_')
        output_file = output_dir / f"extracted_json_{timestamp}.json"
        
        # 创建简化的输出（移除原始HTML内容）
        simplified_results = {
            'file_path': results['file_path'],
            'capture_stats': results['capture_stats'],
            'summary': {
                'total_requests': len(results['extracted_json']),
                'total_json_objects': sum(item['json_count'] for item in results['extracted_json'])
            },
            'extracted_data': []
        }
        
        for item in results['extracted_json']:
            simplified_item = {
                'url': item['url'],
                'method': item['method'],
                'status_code': item['status_code'],
                'json_count': item['json_count'],
                'largest_json_size': item['largest_json']['size'] if item['largest_json'] else 0,
                'largest_json_data': item['largest_json']['data'] if item['largest_json'] else None
            }
            simplified_results['extracted_data'].append(simplified_item)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(simplified_results, f, ensure_ascii=False, indent=2)
        
        print(f"提取结果已保存到: {output_file}")
        return output_file


def main():
    """主函数 - 分析指定的抓包文件"""
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法: python json_extractor.py <抓包文件路径>")
        print("示例: python json_extractor.py captured_data/captured_20250726-162846.json")
        return
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return
    
    extractor = JSONExtractor()
    print(f"正在分析文件: {file_path}")
    
    results = extractor.analyze_captured_data(file_path)
    
    if 'error' in results:
        print(f"分析失败: {results['error']}")
        return
    
    # 显示分析结果
    print(f"\n=== 分析结果 ===")
    print(f"文件: {results['file_path']}")
    print(f"捕获统计: {results['capture_stats']}")
    print(f"发现的请求数: {len(results['extracted_json'])}")
    
    for i, item in enumerate(results['extracted_json']):
        print(f"\n--- 请求 {i+1} ---")
        print(f"URL: {item['url']}")
        print(f"方法: {item['method']}")
        print(f"状态码: {item['status_code']}")
        print(f"发现JSON对象数: {item['json_count']}")
        
        if item['largest_json']:
            largest = item['largest_json']
            print(f"最大JSON大小: {largest['size']} 字符")
            print(f"匹配模式: {largest['pattern']}")
            print(f"JSON预览: {largest['raw']}")
            
            # 分析JSON结构
            if isinstance(largest['data'], dict):
                print(f"JSON键数量: {len(largest['data'])}")
                print(f"主要键: {list(largest['data'].keys())[:10]}")
    
    # 保存结果
    output_file = extractor.save_extracted_json(results)
    print(f"\n详细结果已保存到: {output_file}")


if __name__ == "__main__":
    main()