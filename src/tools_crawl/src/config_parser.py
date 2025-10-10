#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强配置文件解析器
专门用于解析 .exp 格式的爬虫配置文件
支持 originalConfig 和 crawlerConfig 两种配置结构
同时支持加载 global.yaml 全局配置文件
"""

import json
import yaml
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigParser:
    """增强配置解析器类"""
    
    def __init__(self, config_path: str):
        """
        初始化增强配置解析器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = Path(config_path)
        self.config_data: Optional[Dict[str, Any]] = None
        self.original_config: Optional[Dict[str, Any]] = None
        self.crawler_config: Optional[Dict[str, Any]] = None
        self.global_config: Optional[Dict[str, Any]] = None
        self.last_modified: Optional[float] = None
        
        # 全局配置文件路径
        self.global_config_path = self.config_path.parent / "global.yaml"
        
        logger.info(f"增强配置解析器初始化: {self.config_path}")
        logger.info(f"全局配置文件路径: {self.global_config_path}")
    
    def load_config(self) -> Dict[str, Any]:
        """
        加载配置文件
        
        Returns:
            Dict[str, Any]: 完整配置数据
        """
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as file:
                self.config_data = json.load(file)
            
            # 分离两种配置
            self.original_config = self.config_data.get('originalConfig', {})
            self.crawler_config = self.config_data.get('crawlerConfig', {})
            
            # 加载全局配置
            self.load_global_config()
            
            # 更新修改时间
            self.last_modified = self.config_path.stat().st_mtime
            
            logger.info(f"配置文件加载成功: {self.config_path}")
            return self.config_data
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            raise
    
    def load_global_config(self) -> Optional[Dict[str, Any]]:
        """
        加载全局配置文件
        
        Returns:
            Optional[Dict[str, Any]]: 全局配置数据
        """
        try:
            if not self.global_config_path.exists():
                logger.warning(f"全局配置文件不存在: {self.global_config_path}")
                self.global_config = {}
                return self.global_config
            
            with open(self.global_config_path, 'r', encoding='utf-8') as file:
                self.global_config = yaml.safe_load(file)
            
            logger.info(f"全局配置文件加载成功: {self.global_config_path}")
            return self.global_config
            
        except Exception as e:
            logger.error(f"加载全局配置文件失败: {e}")
            self.global_config = {}
            return self.global_config
    
    def get_database_config(self) -> Dict[str, Any]:
        """
        获取数据库配置
        
        Returns:
            Dict[str, Any]: 数据库配置
        """
        if not self.original_config:
            self.load_config()
        
        return {
            'type': self.original_config.get('数库库类型', 'MySql'),
            'connection_string': self.original_config.get('连接字符串', ''),
            'table_configs': self.original_config.get('数据表对应配置', [])
        }
    
    def get_table_config(self, index: int = 0) -> Optional[Dict[str, Any]]:
        """
        获取数据表配置
        
        Args:
            index: 表配置索引，默认为0
            
        Returns:
            Optional[Dict[str, Any]]: 表配置
        """
        db_config = self.get_database_config()
        table_configs = db_config.get('table_configs', [])
        
        if index < len(table_configs):
            return table_configs[index]
        
        return None
    
    def get_data_extraction_config(self) -> Dict[str, Any]:
        """
        获取数据提取配置
        
        Returns:
            Dict[str, Any]: 数据提取配置
        """
        table_config = self.get_table_config()
        if not table_config:
            return {}
        
        return {
            'data_type': table_config.get('类型', 'json'),
            'data_path': table_config.get('路径', ''),
            'path_type': table_config.get('路径类型', 0),
            'table_name': table_config.get('数据库表名', ''),
            'table_fields': self._parse_table_fields(table_config.get('表字段', '')),
            'field_descriptions': table_config.get('字段说明', {}),
            'auto_create_view': table_config.get('自动创建视图', True),
            'deduplicate': table_config.get('数据是否去重', True),
            'deduplicate_field': table_config.get('数据去重字段', ''),
            'update_on_duplicate': table_config.get('去重时数据更新', False)
        }
    
    def _parse_table_fields(self, fields_str: str) -> List[str]:
        """
        解析表字段字符串
        
        Args:
            fields_str: 字段字符串，逗号分隔
            
        Returns:
            List[str]: 字段列表
        """
        if not fields_str:
            return []
        
        return [field.strip() for field in fields_str.split(',') if field.strip()]
    
    def get_field_mapping(self) -> Dict[str, Dict[str, str]]:
        """
        获取字段映射配置
        
        Returns:
            Dict[str, Dict[str, str]]: 字段映射，格式为 {field_name: {description, type}}
        """
        extraction_config = self.get_data_extraction_config()
        field_descriptions = extraction_config.get('field_descriptions', {})
        
        field_mapping = {}
        for field_name, field_info in field_descriptions.items():
            if isinstance(field_info, dict):
                field_mapping[field_name] = {
                    'description': field_info.get('Item1', ''),
                    'type': field_info.get('Item2', 'T')
                }
            else:
                field_mapping[field_name] = {
                    'description': str(field_info),
                    'type': 'T'
                }
        
        return field_mapping
    
    def get_request_config(self) -> Dict[str, Any]:
        """
        获取请求配置信息
        
        Returns:
            Dict[str, Any]: 请求配置
        """
        if not self.original_config:
            self.load_config()
        
        request_info = self.original_config.get('请求信息', {})
        
        return {
            'url': request_info.get('url', ''),
            'headers': self._parse_headers(request_info.get('headers', '')),
            'post_data': request_info.get('postData', ''),
            'response_body': request_info.get('body', '')
        }
    
    def _parse_headers(self, headers_str: str) -> Dict[str, str]:
        """
        解析请求头字符串
        
        Args:
            headers_str: 请求头字符串
            
        Returns:
            Dict[str, str]: 请求头字典
        """
        headers = {}
        if not headers_str:
            return headers
        
        lines = headers_str.split('\r\n')
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip()] = value.strip()
        
        return headers
    
    def get_crawler_config(self) -> Dict[str, Any]:
        """
        获取爬虫配置，合并全局配置中的浏览器和代理配置
        
        Returns:
            Dict[str, Any]: 爬虫配置
        """
        if not self.crawler_config:
            self.load_config()
        
        # 创建合并后的配置
        merged_config = self.crawler_config.copy()
        
        # 从全局配置中获取浏览器配置
        if self.global_config:
            # 合并浏览器配置
            global_browser_config = self.global_config.get('system', {}).get('browser', {})
            if global_browser_config:
                # 添加代理端口配置
                proxy_config = self.global_config.get('system', {}).get('proxy', {})
                if proxy_config and proxy_config.get('enabled', True):
                    global_browser_config['proxy_port'] = proxy_config.get('port', 8080)
                
                merged_config['browser'] = global_browser_config
                logger.info("已合并全局浏览器配置")

                cookie_config = self.global_config.get('system', {}).get('cookies', {})
                merged_config['cookies_path'] = cookie_config.get('file', '')
                global_browser_config['cookies_path'] = cookie_config.get('file', '')
            
            # 合并其他系统配置
            system_config = self.global_config.get('system', {})
            if system_config:
                merged_config['system'] = system_config
                
            # 合并通用字段映射
            common_fields = self.global_config.get('common_fields', {})
            if common_fields:
                merged_config['common_fields'] = common_fields
                
            # 合并数据提取配置
            extraction_config = self.global_config.get('extraction', {})
            if extraction_config:
                merged_config['extraction'] = extraction_config
                
            # 合并适配器配置
            adaptor_config = self.global_config.get('adaptor', {})
            if adaptor_config:
                merged_config['adaptor'] = adaptor_config
        
        return merged_config
    
    def get_target_urls(self) -> Dict[str, str]:
        """
        获取目标URL配置
        
        Returns:
            Dict[str, str]: 目标URL配置
        """
        crawler_config = self.get_crawler_config()
        return crawler_config.get('targetUrls', {})
    
    def get_browser_actions(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        获取浏览器动作配置
        
        Returns:
            Dict[str, List[Dict[str, Any]]]: 浏览器动作配置
        """
        crawler_config = self.get_crawler_config()
        return crawler_config.get('browserActions', {})
    
    def get_scroll_actions(self) -> List[Dict[str, Any]]:
        """
        获取滚动动作配置
        
        Returns:
            List[Dict[str, Any]]: 滚动动作列表
        """
        browser_actions = self.get_browser_actions()
        return browser_actions.get('scrollActions', [])
    
    def get_click_actions(self) -> List[Dict[str, Any]]:
        """
        获取点击动作配置
        
        Returns:
            List[Dict[str, Any]]: 点击动作列表
        """
        browser_actions = self.get_browser_actions()
        return browser_actions.get('clickActions', [])
    
    def get_wait_conditions(self) -> List[Dict[str, Any]]:
        """
        获取等待条件配置
        
        Returns:
            List[Dict[str, Any]]: 等待条件列表
        """
        browser_actions = self.get_browser_actions()
        return browser_actions.get('waitConditions', [])
    
    def extract_data_from_json(self, json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        根据配置从JSON数据中提取目标数据
        
        Args:
            json_data: 原始JSON数据
            
        Returns:
            List[Dict[str, Any]]: 提取的数据列表
        """
        extraction_config = self.get_data_extraction_config()
        data_path = extraction_config.get('data_path', '')
        
        if not data_path:
            logger.warning("未配置数据路径")
            return []
        
        # 根据路径提取数据
        extracted_data = self._get_nested_value(json_data, data_path)
        
        if not isinstance(extracted_data, list):
            logger.warning(f"提取的数据不是列表格式: {type(extracted_data)}")
            return []
        
        return extracted_data
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """
        根据路径获取嵌套值
        
        Args:
            data: 数据字典
            path: 路径，使用点号分隔
            
        Returns:
            Any: 提取的值
        """
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                logger.warning(f"路径 {path} 在数据中不存在")
                return None
        
        return current
    
    def validate_config(self) -> Tuple[bool, List[str]]:
        """
        验证配置文件的完整性
        
        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []
        
        try:
            if not self.config_data:
                self.load_config()
            
            # 检查必需的顶级结构
            if 'originalConfig' not in self.config_data:
                errors.append("缺少 originalConfig 配置")
            
            if 'crawlerConfig' not in self.config_data:
                errors.append("缺少 crawlerConfig 配置")
            
            # 检查数据表配置
            table_config = self.get_table_config()
            if not table_config:
                errors.append("缺少数据表配置")
            else:
                required_fields = ['类型', '路径', '数据库表名', '表字段']
                for field in required_fields:
                    if field not in table_config:
                        errors.append(f"数据表配置缺少字段: {field}")
            
            # 检查目标URL配置
            target_urls = self.get_target_urls()
            if not target_urls:
                errors.append("缺少目标URL配置")
            
        except Exception as e:
            errors.append(f"配置验证过程中出错: {e}")
        
        return len(errors) == 0, errors
    
    def get_summary(self) -> Dict[str, Any]:
        """
        获取配置摘要信息
        
        Returns:
            Dict[str, Any]: 配置摘要
        """
        if not self.config_data:
            self.load_config()
        
        extraction_config = self.get_data_extraction_config()
        target_urls = self.get_target_urls()
        
        return {
            'config_file': str(self.config_path),
            'database_type': self.original_config.get('数库库类型', ''),
            'table_name': extraction_config.get('table_name', ''),
            'data_path': extraction_config.get('data_path', ''),
            'field_count': len(extraction_config.get('table_fields', [])),
            'target_site': target_urls.get('mainSite', ''),
            'api_endpoint': target_urls.get('apiEndpoint', ''),
            'deduplicate': extraction_config.get('deduplicate', False),
            'deduplicate_field': extraction_config.get('deduplicate_field', '')
        }
    
    def reload_if_changed(self) -> bool:
        """
        如果文件已修改则重新加载
        
        Returns:
            bool: 是否重新加载了配置
        """
        try:
            if not self.config_path.exists():
                return False
            
            current_modified = self.config_path.stat().st_mtime
            
            if self.last_modified != current_modified:
                self.load_config()
                logger.info("检测到配置文件变化，已重新加载")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"检查配置文件变化失败: {e}")
            return False


# 使用示例
if __name__ == "__main__":
    # 测试增强配置解析器
    config_parser = ConfigParser('x:/RPA/tools_crawl/config/xiaohongshu.exp')
    
    try:
        # 加载配置
        config = config_parser.load_config()
        
        # 获取配置摘要
        summary = config_parser.get_summary()
        print("配置摘要:")
        for key, value in summary.items():
            print(f"  {key}: {value}")
        
        # 获取数据提取配置
        extraction_config = config_parser.get_data_extraction_config()
        print(f"\n数据提取配置:")
        print(f"  数据路径: {extraction_config['data_path']}")
        print(f"  表字段: {extraction_config['table_fields']}")
        
        # 获取字段映射
        field_mapping = config_parser.get_field_mapping()
        print(f"\n字段映射 (共{len(field_mapping)}个字段):")
        for field, info in list(field_mapping.items())[:5]:  # 只显示前5个
            print(f"  {field}: {info['description']}")
        
        # 验证配置
        is_valid, errors = config_parser.validate_config()
        print(f"\n配置验证: {'通过' if is_valid else '失败'}")
        if errors:
            for error in errors:
                print(f"  错误: {error}")
        
    except Exception as e:
        print(f"测试失败: {e}")