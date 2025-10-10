#!/usr/bin/env python3
"""
高级JSON匹配规则 - 专门用于小红书等网站的数据提取
设计智能匹配规则，提取网页中最有价值的JSON数据
"""

import json
import re
import os
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import html


class AdvancedJSONMatcher:
    """高级JSON匹配器，使用智能规则提取网页中的关键数据"""
    
    def __init__(self):
        # 小红书特定的数据模式
        self.xiaohongshu_patterns = {
            'initial_state': {
                'pattern': r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
                'priority': 10,
                'description': '页面初始状态数据'
            },
            'nuxt_data': {
                'pattern': r'window\.__NUXT__\s*=\s*({.+?});',
                'priority': 9,
                'description': 'Nuxt.js应用数据'
            },
            'page_data': {
                'pattern': r'window\.pageData\s*=\s*({.+?});',
                'priority': 8,
                'description': '页面数据'
            },
            'feed_data': {
                'pattern': r'window\.feedData\s*=\s*({.+?});',
                'priority': 8,
                'description': '信息流数据'
            },
            'user_data': {
                'pattern': r'window\.userData\s*=\s*({.+?});',
                'priority': 7,
                'description': '用户数据'
            },
            'config_data': {
                'pattern': r'window\.configData\s*=\s*({.+?});',
                'priority': 6,
                'description': '配置数据'
            }
        }
        
        # 通用JSON数据模式
        self.generic_patterns = {
            'json_script': {
                'pattern': r'<script[^>]*type=["\']application/json["\'][^>]*>(.+?)</script>',
                'priority': 5,
                'description': 'JSON脚本标签'
            },
            'large_object': {
                'pattern': r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',
                'priority': 3,
                'description': '大型JSON对象'
            }
        }
        
        # 数据价值评估规则
        self.value_indicators = {
            'feed': ['notes', 'feeds', 'items', 'list', 'data'],
            'user': ['user', 'profile', 'author', 'creator'],
            'content': ['title', 'desc', 'content', 'text'],
            'media': ['images', 'videos', 'pics', 'media'],
            'interaction': ['likes', 'comments', 'shares', 'views'],
            'metadata': ['id', 'url', 'time', 'timestamp', 'createTime']
        }
    
    def extract_and_rank_json(self, html_content: str) -> List[Dict[str, Any]]:
        """提取并按价值排序JSON数据"""
        json_candidates = []
        
        # 0. 检查HTML完整性
        completeness_info = self._check_html_completeness(html_content)
        
        # 1. 使用小红书特定模式
        for name, config in self.xiaohongshu_patterns.items():
            matches = re.finditer(config['pattern'], html_content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                json_str = match.group(1) if match.groups() else match.group(0)
                json_obj = self._parse_json_safely(json_str)
                if json_obj:
                    candidate = {
                        'name': name,
                        'pattern_type': 'xiaohongshu_specific',
                        'priority': config['priority'],
                        'description': config['description'],
                        'size': len(json_str),
                        'data': json_obj,
                        'value_score': self._calculate_value_score(json_obj),
                        'raw': json_str[:200] + '...' if len(json_str) > 200 else json_str,
                        'html_completeness': completeness_info
                    }
                    json_candidates.append(candidate)
        
        # 2. 使用通用模式
        for name, config in self.generic_patterns.items():
            if name == 'large_object':
                # 特殊处理大型对象
                self._extract_large_objects(html_content, json_candidates, completeness_info)
            else:
                matches = re.finditer(config['pattern'], html_content, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    json_str = match.group(1) if match.groups() else match.group(0)
                    json_obj = self._parse_json_safely(json_str)
                    if json_obj:
                        candidate = {
                            'name': name,
                            'pattern_type': 'generic',
                            'priority': config['priority'],
                            'description': config['description'],
                            'size': len(json_str),
                            'data': json_obj,
                            'value_score': self._calculate_value_score(json_obj),
                            'raw': json_str[:200] + '...' if len(json_str) > 200 else json_str,
                            'html_completeness': completeness_info
                        }
                        json_candidates.append(candidate)
        
        # 3. 如果没有找到数据且HTML不完整，尝试更激进的提取
        if not json_candidates and not completeness_info['is_complete']:
            self._extract_partial_json(html_content, json_candidates, completeness_info)
        
        # 4. 按综合评分排序
        json_candidates.sort(key=lambda x: (x['value_score'], x['priority'], x['size']), reverse=True)
        
        return json_candidates
    
    def _extract_large_objects(self, html_content: str, candidates: List[Dict], completeness_info: Dict):
        """提取大型JSON对象"""
        # 在script标签中查找
        script_pattern = r'<script[^>]*>(.*?)</script>'
        script_matches = re.finditer(script_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        for script_match in script_matches:
            script_content = script_match.group(1)
            
            # 查找JSON对象
            brace_level = 0
            start_pos = -1
            
            for i, char in enumerate(script_content):
                if char == '{':
                    if brace_level == 0:
                        start_pos = i
                    brace_level += 1
                elif char == '}':
                    brace_level -= 1
                    if brace_level == 0 and start_pos != -1:
                        json_str = script_content[start_pos:i+1]
                        if len(json_str) > 500:  # 只考虑大型对象
                            json_obj = self._parse_json_safely(json_str)
                            if json_obj:
                                candidate = {
                                    'name': 'large_script_object',
                                    'pattern_type': 'generic',
                                    'priority': 4,
                                    'description': f'脚本中的大型JSON对象 ({len(json_str)}字符)',
                                    'size': len(json_str),
                                    'data': json_obj,
                                    'value_score': self._calculate_value_score(json_obj),
                                    'raw': json_str[:200] + '...' if len(json_str) > 200 else json_str,
                                    'html_completeness': completeness_info
                                }
                                candidates.append(candidate)
                        start_pos = -1
    
    def _check_html_completeness(self, html_content: str) -> Dict[str, Any]:
        """检查HTML内容的完整性"""
        completeness_info = {
            'is_complete': True,
            'missing_elements': [],
            'size': len(html_content),
            'has_closing_tags': True,
            'has_body': False,
            'has_scripts': False,
            'script_count': 0,
            'estimated_completeness': 0.0
        }
        
        # 检查基本HTML结构
        if not html_content.strip().endswith('</html>'):
            completeness_info['is_complete'] = False
            completeness_info['missing_elements'].append('closing_html_tag')
        
        if '</body>' not in html_content:
            completeness_info['missing_elements'].append('body_tag')
        else:
            completeness_info['has_body'] = True
        
        if '</head>' not in html_content:
            completeness_info['missing_elements'].append('head_tag')
        
        # 检查脚本标签
        script_matches = re.findall(r'<script[^>]*>.*?</script>', html_content, re.DOTALL | re.IGNORECASE)
        completeness_info['script_count'] = len(script_matches)
        completeness_info['has_scripts'] = len(script_matches) > 0
        
        # 估算完整性百分比
        completeness_score = 0
        if completeness_info['has_body']:
            completeness_score += 30
        if completeness_info['has_scripts']:
            completeness_score += 20
        if len(html_content) > 10000:  # 假设完整页面至少10KB
            completeness_score += 30
        if not completeness_info['missing_elements']:
            completeness_score += 20
        
        completeness_info['estimated_completeness'] = min(completeness_score, 100) / 100.0
        
        # 如果完整性低于50%，认为不完整
        if completeness_info['estimated_completeness'] < 0.5:
            completeness_info['is_complete'] = False
        
        return completeness_info
    
    def _extract_partial_json(self, html_content: str, candidates: List[Dict], completeness_info: Dict):
        """从不完整的HTML中尝试提取JSON数据"""
        # 尝试更激进的JSON提取策略
        
        # 1. 查找任何看起来像JSON的字符串
        json_like_patterns = [
            r'\{[^{}]*"[^"]*"[^{}]*:[^{}]*\}',  # 简单的键值对
            r'\[[^[\]]*\{[^{}]*\}[^[\]]*\]',   # 数组中的对象
            r'=\s*(\{[^;]+\});',               # 赋值语句中的对象
            r':\s*(\{[^,}]+\})',               # 冒号后的对象
        ]
        
        for i, pattern in enumerate(json_like_patterns):
            matches = re.finditer(pattern, html_content, re.DOTALL)
            for match in matches:
                json_str = match.group(1) if match.groups() else match.group(0)
                if len(json_str) > 50:  # 只考虑有意义的大小
                    json_obj = self._parse_json_safely(json_str)
                    if json_obj:
                        candidate = {
                            'name': f'partial_json_{i}',
                            'pattern_type': 'partial_extraction',
                            'priority': 2,
                            'description': f'从不完整HTML中提取的JSON (模式{i+1})',
                            'size': len(json_str),
                            'data': json_obj,
                            'value_score': self._calculate_value_score(json_obj),
                            'raw': json_str[:200] + '...' if len(json_str) > 200 else json_str,
                            'html_completeness': completeness_info
                        }
                        candidates.append(candidate)
        
        # 2. 查找可能的数据数组
        array_patterns = [
            r'\[\s*\{[^}]+\}[^]]*\]',  # 对象数组
            r':\s*\[([^]]+)\]',        # 冒号后的数组
        ]
        
        for i, pattern in enumerate(array_patterns):
            matches = re.finditer(pattern, html_content, re.DOTALL)
            for match in matches:
                json_str = match.group(1) if match.groups() else match.group(0)
                if len(json_str) > 50:
                    # 尝试包装成完整的JSON
                    if not json_str.strip().startswith('['):
                        json_str = f'[{json_str}]'
                    
                    json_obj = self._parse_json_safely(json_str)
                    if json_obj:
                        candidate = {
                            'name': f'partial_array_{i}',
                            'pattern_type': 'partial_extraction',
                            'priority': 1,
                            'description': f'从不完整HTML中提取的数组 (模式{i+1})',
                            'size': len(json_str),
                            'data': json_obj,
                            'value_score': self._calculate_value_score(json_obj),
                            'raw': json_str[:200] + '...' if len(json_str) > 200 else json_str,
                            'html_completeness': completeness_info
                        }
                        candidates.append(candidate)
    
    def _parse_json_safely(self, json_str: str) -> Optional[Dict]:
        """安全解析JSON字符串"""
        try:
            # 清理字符串
            json_str = json_str.strip()
            if json_str.endswith(';'):
                json_str = json_str[:-1]
            
            # 移除JavaScript注释 - 但要避免移除URL中的//
            # 只移除行首或空白后的//注释
            json_str = re.sub(r'(^|\s)//.*?$', r'\1', json_str, flags=re.MULTILINE)
            json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
            
            # 解码HTML实体
            json_str = html.unescape(json_str)
            
            # 尝试解析
            return json.loads(json_str)
        except:
            return None
    
    def _calculate_value_score(self, json_obj: Dict) -> int:
        """计算JSON数据的价值分数"""
        if not isinstance(json_obj, dict):
            return 0
        
        score = 0
        json_str = json.dumps(json_obj, ensure_ascii=False).lower()
        
        # 基础分数：根据数据大小
        score += min(len(json_str) // 1000, 10)
        
        # 内容价值分数
        for category, keywords in self.value_indicators.items():
            for keyword in keywords:
                if keyword in json_str:
                    if category == 'feed':
                        score += 20  # 信息流数据最有价值
                    elif category == 'content':
                        score += 15
                    elif category == 'user':
                        score += 10
                    elif category == 'media':
                        score += 8
                    elif category == 'interaction':
                        score += 5
                    else:
                        score += 3
        
        # 结构复杂度分数
        if isinstance(json_obj, dict):
            score += min(len(json_obj), 20)
            
            # 检查嵌套结构
            for value in json_obj.values():
                if isinstance(value, (dict, list)):
                    score += 5
        
        return score
    
    def analyze_xiaohongshu_data(self, json_data: Dict) -> Dict[str, Any]:
        """专门分析小红书数据结构"""
        analysis = {
            'data_type': 'unknown',
            'key_fields': [],
            'content_items': 0,
            'user_info': {},
            'media_info': {},
            'interaction_data': {},
            'recommendations': []
        }
        
        json_str = json.dumps(json_data, ensure_ascii=False).lower()
        
        # 判断数据类型
        if any(keyword in json_str for keyword in ['notes', 'feeds', 'explore']):
            analysis['data_type'] = 'feed_data'
        elif any(keyword in json_str for keyword in ['user', 'profile', 'author']):
            analysis['data_type'] = 'user_data'
        elif any(keyword in json_str for keyword in ['search', 'query']):
            analysis['data_type'] = 'search_data'
        
        # 提取关键字段
        analysis['key_fields'] = list(json_data.keys()) if isinstance(json_data, dict) else []
        
        # 分析内容项目
        analysis['content_items'] = self._count_content_items(json_data)
        
        # 提取用户信息
        analysis['user_info'] = self._extract_user_info(json_data)
        
        # 提取媒体信息
        analysis['media_info'] = self._extract_media_info(json_data)
        
        # 提取交互数据
        analysis['interaction_data'] = self._extract_interaction_data(json_data)
        
        return analysis
    
    def _count_content_items(self, data: Any) -> int:
        """统计内容项目数量"""
        count = 0
        if isinstance(data, dict):
            for key, value in data.items():
                if key.lower() in ['notes', 'items', 'list', 'data', 'feeds']:
                    if isinstance(value, list):
                        count += len(value)
                else:
                    count += self._count_content_items(value)
        elif isinstance(data, list):
            for item in data:
                count += self._count_content_items(item)
        return count
    
    def _extract_user_info(self, data: Any) -> Dict:
        """提取用户信息"""
        user_info = {}
        if isinstance(data, dict):
            for key, value in data.items():
                if key.lower() in ['user', 'author', 'creator', 'profile']:
                    if isinstance(value, dict):
                        user_info.update(value)
                else:
                    user_info.update(self._extract_user_info(value))
        elif isinstance(data, list):
            for item in data:
                user_info.update(self._extract_user_info(item))
        return user_info
    
    def _extract_media_info(self, data: Any) -> Dict:
        """提取媒体信息"""
        media_info = {'images': [], 'videos': []}
        if isinstance(data, dict):
            for key, value in data.items():
                if 'image' in key.lower() or 'pic' in key.lower():
                    if isinstance(value, str) and value.startswith('http'):
                        media_info['images'].append(value)
                    elif isinstance(value, list):
                        media_info['images'].extend([v for v in value if isinstance(v, str) and v.startswith('http')])
                elif 'video' in key.lower():
                    if isinstance(value, str) and value.startswith('http'):
                        media_info['videos'].append(value)
                    elif isinstance(value, list):
                        media_info['videos'].extend([v for v in value if isinstance(v, str) and v.startswith('http')])
                else:
                    sub_media = self._extract_media_info(value)
                    media_info['images'].extend(sub_media['images'])
                    media_info['videos'].extend(sub_media['videos'])
        elif isinstance(data, list):
            for item in data:
                sub_media = self._extract_media_info(item)
                media_info['images'].extend(sub_media['images'])
                media_info['videos'].extend(sub_media['videos'])
        return media_info
    
    def _extract_interaction_data(self, data: Any) -> Dict:
        """提取交互数据"""
        interaction = {}
        if isinstance(data, dict):
            for key, value in data.items():
                if key.lower() in ['likes', 'comments', 'shares', 'views', 'collects']:
                    interaction[key] = value
                else:
                    interaction.update(self._extract_interaction_data(value))
        elif isinstance(data, list):
            for item in data:
                interaction.update(self._extract_interaction_data(item))
        return interaction


def main():
    """主函数"""
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法: python advanced_json_matcher.py <抓包文件路径>")
        return
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return
    
    # 读取抓包数据
    with open(file_path, 'r', encoding='utf-8') as f:
        captured_data = json.load(f)
    
    matcher = AdvancedJSONMatcher()
    
    print(f"=== 高级JSON匹配分析 ===")
    print(f"文件: {file_path}")
    
    for item in captured_data.get('captured_data', []):
        if 'response_body' in item:
            print(f"\n--- 分析URL: {item.get('url', '')} ---")
            
            html_content = item['response_body']
            json_candidates = matcher.extract_and_rank_json(html_content)
            
            print(f"发现JSON对象: {len(json_candidates)}个")
            
            # 显示前5个最有价值的JSON对象
            for i, candidate in enumerate(json_candidates[:5]):
                print(f"\n{i+1}. {candidate['name']} (价值分数: {candidate['value_score']})")
                print(f"   类型: {candidate['pattern_type']}")
                print(f"   描述: {candidate['description']}")
                print(f"   大小: {candidate['size']} 字符")
                print(f"   预览: {candidate['raw']}")
                
                # 如果是最有价值的数据，进行详细分析
                if i == 0:
                    analysis = matcher.analyze_xiaohongshu_data(candidate['data'])
                    print(f"   详细分析:")
                    print(f"     数据类型: {analysis['data_type']}")
                    print(f"     关键字段: {analysis['key_fields'][:10]}")
                    print(f"     内容项目数: {analysis['content_items']}")
                    print(f"     用户信息: {len(analysis['user_info'])}个字段")
                    print(f"     图片数量: {len(analysis['media_info']['images'])}")
                    print(f"     视频数量: {len(analysis['media_info']['videos'])}")
            
            # 保存最有价值的JSON数据
            if json_candidates:
                best_candidate = json_candidates[0]
                output_file = f"best_json_{item.get('url', '').split('/')[-1]}.json"
                output_file = re.sub(r'[^\w\-_\.]', '_', output_file)
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'metadata': {
                            'url': item.get('url', ''),
                            'extraction_info': {
                                'name': best_candidate['name'],
                                'value_score': best_candidate['value_score'],
                                'size': best_candidate['size'],
                                'description': best_candidate['description']
                            }
                        },
                        'data': best_candidate['data']
                    }, f, ensure_ascii=False, indent=2)
                
                print(f"\n最有价值的JSON已保存到: {output_file}")


if __name__ == "__main__":
    main()