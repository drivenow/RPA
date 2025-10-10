#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于配置文件的通用数据适配器
根据 .exp 配置文件自动解析和转换数据
"""

import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_parser import ConfigParser

logger = logging.getLogger(__name__)


class UniversalAdaptor:
    """基于配置文件的通用数据适配器"""
    
    def __init__(self, config_path: str):
        """
        初始化适配器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_parser = ConfigParser(config_path)
        self.config_parser.load_config()
        
        # 获取配置信息
        self.extraction_config = self.config_parser.get_data_extraction_config()
        self.field_mapping = self.config_parser.get_field_mapping()
        self.table_fields = self.extraction_config.get('table_fields', [])
        
        logger.info(f"配置驱动适配器初始化完成，目标表: {self.extraction_config.get('table_name')}")
        logger.info(f"配置字段数量: {len(self.table_fields)}")
    
    def adapt_data(self, raw_data: Union[Dict, List, str]) -> List[Dict[str, Any]]:
        """
        根据配置适配原始数据
        
        Args:
            raw_data: 原始数据，可以是字典、列表或JSON字符串
            
        Returns:
            List[Dict[str, Any]]: 适配后的数据列表
        """
        try:
            # 处理输入数据格式
            if isinstance(raw_data, str):
                raw_data = json.loads(raw_data)
            
            # 根据配置提取数据
            if isinstance(raw_data, dict):
                extracted_items = self.config_parser.extract_data_from_json(raw_data)
            elif isinstance(raw_data, list):
                extracted_items = raw_data
            else:
                logger.error(f"不支持的数据格式: {type(raw_data)}")
                return []
            
            # 适配每个数据项
            adapted_data = []
            for item in extracted_items:
                adapted_item = self._adapt_single_item(item)
                if adapted_item:
                    adapted_data.append(adapted_item)
            
            logger.info(f"数据适配完成: {len(extracted_items)} -> {len(adapted_data)}")
            return adapted_data
            
        except Exception as e:
            logger.error(f"数据适配失败: {e}")
            return []
    
    def _adapt_single_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        适配单个数据项
        
        Args:
            item: 原始数据项
            
        Returns:
            Optional[Dict[str, Any]]: 适配后的数据项
        """
        try:
            adapted_item = {}
            
            for field in self.table_fields:
                value = self._extract_field_value(item, field)
                adapted_item[field] = self._format_field_value(field, value)
            
            # 添加元数据
            adapted_item['_extracted_at'] = datetime.now().isoformat()
            adapted_item['_source'] = 'config_based_adaptor'
            
            return adapted_item
            
        except Exception as e:
            logger.error(f"单项数据适配失败: {e}")
            return None
    
    def _extract_field_value(self, item: Dict[str, Any], field_path: str) -> Any:
        """
        根据字段路径提取值
        
        Args:
            item: 数据项
            field_path: 字段路径，支持嵌套路径如 'user.nickname'
            
        Returns:
            Any: 提取的值
        """
        try:
            # 处理嵌套字段路径
            if '.' in field_path:
                keys = field_path.split('.')
                current = item
                for key in keys:
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        return None
                return current
            else:
                return item.get(field_path)
                
        except Exception as e:
            logger.warning(f"字段值提取失败 {field_path}: {e}")
            return None
    
    def _format_field_value(self, field: str, value: Any) -> Any:
        """
        根据字段配置格式化值
        
        Args:
            field: 字段名
            value: 原始值
            
        Returns:
            Any: 格式化后的值
        """
        if value is None:
            return None
        
        # 获取字段类型信息
        field_info = self.field_mapping.get(field, {})
        field_type = field_info.get('type', 'T')
        
        try:
            # 根据字段类型进行格式化
            if field_type == 'I':  # 整数
                return int(value) if value != '' else 0
            elif field_type == 'F':  # 浮点数
                return float(value) if value != '' else 0.0
            elif field_type == 'B':  # 布尔值
                if isinstance(value, bool):
                    return value
                return str(value).lower() in ('true', '1', 'yes', 'on')
            elif field_type == 'D':  # 日期时间
                return self._format_datetime(value)
            elif field_type == 'J':  # JSON
                if isinstance(value, (dict, list)):
                    return json.dumps(value, ensure_ascii=False)
                return str(value)
            else:  # 默认文本类型
                return str(value) if value is not None else ''
                
        except Exception as e:
            logger.warning(f"字段值格式化失败 {field}: {e}")
            return str(value) if value is not None else ''
    
    def _format_datetime(self, value: Any) -> Optional[str]:
        """
        格式化日期时间值
        
        Args:
            value: 原始时间值
            
        Returns:
            Optional[str]: 格式化后的时间字符串
        """
        if value is None:
            return None
        
        try:
            # 如果是时间戳
            if isinstance(value, (int, float)):
                # 判断是秒级还是毫秒级时间戳
                if value > 1e10:  # 毫秒级
                    timestamp = value / 1000
                else:  # 秒级
                    timestamp = value
                
                dt = datetime.fromtimestamp(timestamp)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # 如果已经是字符串格式
            elif isinstance(value, str):
                # 尝试解析常见的时间格式
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y/%m/%d %H:%M:%S']:
                    try:
                        dt = datetime.strptime(value, fmt)
                        return dt.strftime('%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        continue
                
                # 如果无法解析，返回原值
                return str(value)
            
            else:
                return str(value)
                
        except Exception as e:
            logger.warning(f"时间格式化失败: {e}")
            return str(value)
    
    def validate_adapted_data(self, adapted_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        验证适配后的数据
        
        Args:
            adapted_data: 适配后的数据
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        validation_result = {
            'total_items': len(adapted_data),
            'valid_items': 0,
            'invalid_items': 0,
            'missing_fields': {},
            'field_coverage': {},
            'errors': []
        }
        
        if not adapted_data:
            validation_result['errors'].append('没有数据需要验证')
            return validation_result
        
        # 统计字段覆盖率
        for field in self.table_fields:
            field_count = sum(1 for item in adapted_data if item.get(field) is not None)
            validation_result['field_coverage'][field] = {
                'count': field_count,
                'percentage': (field_count / len(adapted_data)) * 100
            }
            
            if field_count == 0:
                validation_result['missing_fields'][field] = '完全缺失'
            elif field_count < len(adapted_data) * 0.5:
                validation_result['missing_fields'][field] = f'覆盖率低 ({field_count}/{len(adapted_data)})'
        
        # 验证必需字段
        deduplicate_field = self.extraction_config.get('deduplicate_field', '')
        for item in adapted_data:
            is_valid = True
            
            # 检查去重字段
            if deduplicate_field and not item.get(deduplicate_field):
                is_valid = False
                validation_result['errors'].append(f'缺少去重字段: {deduplicate_field}')
            
            if is_valid:
                validation_result['valid_items'] += 1
            else:
                validation_result['invalid_items'] += 1
        
        return validation_result
    
    def get_database_schema(self) -> Dict[str, Any]:
        """
        根据配置生成数据库表结构
        
        Returns:
            Dict[str, Any]: 数据库表结构信息
        """
        schema = {
            'table_name': self.extraction_config.get('table_name', ''),
            'fields': [],
            'indexes': [],
            'constraints': []
        }
        
        # 生成字段定义
        for field in self.table_fields:
            field_info = self.field_mapping.get(field, {})
            field_type = field_info.get('type', 'T')
            description = field_info.get('description', '')
            
            # 映射字段类型到SQL类型
            sql_type = self._map_to_sql_type(field_type, field)
            
            schema['fields'].append({
                'name': field,
                'type': sql_type,
                'description': description,
                'nullable': True,
                'default': None
            })
        
        # 添加元数据字段
        schema['fields'].extend([
            {
                'name': '_extracted_at',
                'type': 'DATETIME',
                'description': '数据提取时间',
                'nullable': False,
                'default': 'CURRENT_TIMESTAMP'
            },
            {
                'name': '_source',
                'type': 'VARCHAR(100)',
                'description': '数据来源',
                'nullable': True,
                'default': None
            }
        ])
        
        # 添加主键和索引
        deduplicate_field = self.extraction_config.get('deduplicate_field', '')
        if deduplicate_field:
            schema['indexes'].append({
                'name': f'idx_{deduplicate_field}',
                'fields': [deduplicate_field],
                'unique': True
            })
        
        return schema
    
    def _map_to_sql_type(self, field_type: str, field_name: str) -> str:
        """
        将字段类型映射到SQL类型
        
        Args:
            field_type: 字段类型标识
            field_name: 字段名
            
        Returns:
            str: SQL类型
        """
        type_mapping = {
            'I': 'INT',
            'F': 'DECIMAL(10,2)',
            'B': 'BOOLEAN',
            'D': 'DATETIME',
            'J': 'TEXT',
            'T': 'VARCHAR(500)'  # 默认文本类型
        }
        
        sql_type = type_mapping.get(field_type, 'VARCHAR(500)')
        
        # 特殊字段的类型调整
        if 'id' in field_name.lower():
            sql_type = 'VARCHAR(100)'
        elif 'url' in field_name.lower():
            sql_type = 'VARCHAR(1000)'
        elif 'desc' in field_name.lower() or 'content' in field_name.lower():
            sql_type = 'TEXT'
        
        return sql_type
    
    def export_sample_data(self, adapted_data: List[Dict[str, Any]], 
                          output_path: str, sample_size: int = 5) -> bool:
        """
        导出样本数据用于检查
        
        Args:
            adapted_data: 适配后的数据
            output_path: 输出文件路径
            sample_size: 样本数量
            
        Returns:
            bool: 是否成功
        """
        try:
            sample_data = adapted_data[:sample_size] if len(adapted_data) > sample_size else adapted_data
            
            export_info = {
                'config_summary': self.config_parser.get_summary(),
                'validation_result': self.validate_adapted_data(adapted_data),
                'database_schema': self.get_database_schema(),
                'sample_data': sample_data,
                'export_time': datetime.now().isoformat()
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_info, f, ensure_ascii=False, indent=2)
            
            logger.info(f"样本数据导出成功: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"样本数据导出失败: {e}")
            return False


# 使用示例和测试
if __name__ == "__main__":
    # 测试配置驱动的通用适配器
    adaptor = UniversalAdaptor('x:/RPA/tools_crawl/config/xiaohongshu.exp')
    
    # 模拟小红书API响应数据
    mock_api_response = {
        "data": {
            "items": [
                {
                    "note_id": "64a1b2c3d4e5f6789",
                    "display_title": "测试笔记标题",
                    "desc": "这是一个测试笔记的描述内容",
                    "type": "normal",
                    "user": {
                        "user_id": "user123456",
                        "nickname": "测试用户",
                        "avatar": "https://example.com/avatar.jpg"
                    },
                    "interact_info": {
                        "liked_count": 128,
                        "collected_count": 45,
                        "comment_count": 23,
                        "share_count": 12
                    },
                    "cover": {
                        "url": "https://example.com/cover.jpg",
                        "width": 720,
                        "height": 960
                    },
                    "tag_list": ["美食", "生活"],
                    "time": 1703123456,
                    "last_update_time": 1703123456,
                    "ip_location": "上海",
                    "image_list": ["https://example.com/img1.jpg"],
                    "video": None
                }
            ]
        }
    }
    
    print("开始测试配置驱动的数据适配...")
    
    # 适配数据
    adapted_data = adaptor.adapt_data(mock_api_response)
    print(f"适配结果: {len(adapted_data)} 条数据")
    
    if adapted_data:
        # 显示第一条适配后的数据
        print("\n第一条适配数据:")
        for key, value in adapted_data[0].items():
            print(f"  {key}: {value}")
        
        # 验证数据
        validation = adaptor.validate_adapted_data(adapted_data)
        print(f"\n数据验证结果:")
        print(f"  总数据量: {validation['total_items']}")
        print(f"  有效数据: {validation['valid_items']}")
        print(f"  字段覆盖率: {len([f for f, info in validation['field_coverage'].items() if info['percentage'] > 0])}/{len(validation['field_coverage'])}")
        
        # 导出样本数据
        output_path = 'x:/RPA/tools_crawl/captured_data/config_based_sample.json'
        success = adaptor.export_sample_data(adapted_data, output_path)
        print(f"\n样本数据导出: {'成功' if success else '失败'}")
        
        # 显示数据库表结构
        schema = adaptor.get_database_schema()
        print(f"\n数据库表结构 ({schema['table_name']}):")
        print(f"  字段数量: {len(schema['fields'])}")
        print(f"  索引数量: {len(schema['indexes'])}")
    
    print("\n配置驱动适配器测试完成！")