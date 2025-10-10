#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HTML结构化数据提取器 - 专门处理服务端渲染的小红书页面
当页面没有JSON数据时，直接从HTML结构中提取数据
"""

import re
import json
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import html


class HTMLStructureExtractor:
    """从HTML结构中提取小红书数据"""
    
    def __init__(self):
        self.note_selectors = {
            'note_item': 'section.note-item',
            'title': '.title span',
            'cover_image': '.cover img',
            'author_name': '.author .name',
            'author_avatar': '.author img',
            'author_link': '.author',
            'like_count': '.like-wrapper .count',
            'note_link': '.cover'
        }
    
    def extract_from_html(self, html_content: str) -> Dict[str, Any]:
        """从HTML结构中提取数据"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取笔记列表
            notes = self._extract_notes(soup)
            
            # 构造符合配置期望的数据结构
            result = {
                'data': {
                    'items': notes
                },
                'extraction_method': 'html_structure',
                'total_count': len(notes)
            }
            
            return result
            
        except Exception as e:
            print(f"HTML结构提取失败: {e}")
            return {'data': {'items': []}, 'error': str(e)}
    
    def _extract_notes(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """提取笔记数据"""
        notes = []
        note_items = soup.select(self.note_selectors['note_item'])
        
        for i, item in enumerate(note_items):
            try:
                note_data = self._extract_single_note(item, i)
                if note_data:
                    notes.append(note_data)
            except Exception as e:
                print(f"提取第{i+1}个笔记失败: {e}")
                continue
        
        return notes
    
    def _extract_single_note(self, item_soup: BeautifulSoup, index: int) -> Optional[Dict[str, Any]]:
        """提取单个笔记的数据"""
        try:
            # 提取标题
            title_elem = item_soup.select_one(self.note_selectors['title'])
            title = title_elem.get_text(strip=True) if title_elem else f"笔记{index+1}"
            
            # 提取封面图片
            cover_elem = item_soup.select_one(self.note_selectors['cover_image'])
            cover_url = cover_elem.get('src', '') if cover_elem else ''
            
            # 提取作者信息
            author_name_elem = item_soup.select_one(self.note_selectors['author_name'])
            author_name = author_name_elem.get_text(strip=True) if author_name_elem else '未知用户'
            
            author_avatar_elem = item_soup.select_one(self.note_selectors['author_avatar'])
            author_avatar = author_avatar_elem.get('src', '') if author_avatar_elem else ''
            
            author_link_elem = item_soup.select_one(self.note_selectors['author_link'])
            author_link = author_link_elem.get('href', '') if author_link_elem else ''
            
            # 提取点赞数
            like_elem = item_soup.select_one(self.note_selectors['like_count'])
            like_count_text = like_elem.get_text(strip=True) if like_elem else '0'
            like_count = self._parse_count(like_count_text)
            
            # 提取笔记链接
            note_link_elem = item_soup.select_one(self.note_selectors['note_link'])
            note_link = note_link_elem.get('href', '') if note_link_elem else ''
            
            # 提取笔记ID（从链接中解析）
            note_id = self._extract_note_id(note_link)
            
            # 检查是否为视频
            is_video = bool(item_soup.select_one('.play-icon'))
            
            # 构造笔记数据
            note_data = {
                'id': note_id,
                'title': title,
                'desc': title,  # 使用标题作为描述
                'type': 'video' if is_video else 'normal',
                'cover': {
                    'url': cover_url,
                    'width': item_soup.get('data-width', 0),
                    'height': item_soup.get('data-height', 0)
                },
                'user': {
                    'id': self._extract_user_id(author_link),
                    'nickname': author_name,
                    'avatar': author_avatar
                },
                'interact_info': {
                    'liked_count': like_count,
                    'liked': False
                },
                'note_card': {
                    'type': 'video' if is_video else 'normal',
                    'cover': {
                        'url': cover_url
                    }
                }
            }
            
            return note_data
            
        except Exception as e:
            print(f"解析笔记数据失败: {e}")
            return None
    
    def _parse_count(self, count_text: str) -> int:
        """解析点赞数等计数文本"""
        if not count_text:
            return 0
        
        count_text = count_text.strip().lower()
        
        # 处理中文数字单位
        if '万+' in count_text:
            return 10000  # 万+表示超过1万
        elif '万' in count_text:
            try:
                num = float(count_text.replace('万', ''))
                return int(num * 10000)
            except:
                return 10000
        elif '千+' in count_text:
            return 1000  # 千+表示超过1千
        elif '千' in count_text:
            try:
                num = float(count_text.replace('千', ''))
                return int(num * 1000)
            except:
                return 1000
        else:
            # 尝试直接解析数字
            try:
                return int(re.sub(r'[^\d]', '', count_text))
            except:
                return 0
    
    def _extract_note_id(self, note_link: str) -> str:
        """从笔记链接中提取ID"""
        if not note_link:
            return ''
        
        # 匹配 /explore/xxxxx 格式
        match = re.search(r'/explore/([a-f0-9]+)', note_link)
        return match.group(1) if match else ''
    
    def _extract_user_id(self, user_link: str) -> str:
        """从用户链接中提取用户ID"""
        if not user_link:
            return ''
        
        # 匹配 /user/profile/xxxxx 格式
        match = re.search(r'/user/profile/([a-f0-9]+)', user_link)
        return match.group(1) if match else ''


def test_html_extraction():
    """测试HTML结构提取"""
    demo_file = r"x:\RPA\tools_crawl\captured_data\demo.html"
    
    try:
        with open(demo_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        extractor = HTMLStructureExtractor()
        result = extractor.extract_from_html(html_content)
        
        print("=== HTML结构提取测试结果 ===")
        print(f"提取方法: {result.get('extraction_method', 'unknown')}")
        print(f"总数量: {result.get('total_count', 0)}")
        
        items = result.get('data', {}).get('items', [])
        print(f"实际提取: {len(items)} 个笔记")
        
        # 显示前3个笔记的详细信息
        for i, item in enumerate(items[:3]):
            print(f"\n笔记 {i+1}:")
            print(f"  ID: {item.get('id', 'N/A')}")
            print(f"  标题: {item.get('title', 'N/A')}")
            print(f"  类型: {item.get('type', 'N/A')}")
            print(f"  作者: {item.get('user', {}).get('nickname', 'N/A')}")
            print(f"  点赞: {item.get('interact_info', {}).get('liked_count', 0)}")
        
        # 保存提取结果
        output_file = r"x:\RPA\tools_crawl\captured_data\extracted_data.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存到: {output_file}")
        
        return result
        
    except Exception as e:
        print(f"测试失败: {e}")
        return None


if __name__ == "__main__":
    test_html_extraction()