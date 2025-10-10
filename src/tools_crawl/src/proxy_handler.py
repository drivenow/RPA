#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置驱动的代理处理器
基于 .exp 配置文件进行URL匹配和数据处理
使用增强配置解析器和配置驱动适配器
"""

import json
import time
import logging
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse

from mitmproxy import http

from config_parser import ConfigParser
from adaptor.universal_adaptor import UniversalAdaptor
from data_processor import DataProcessor
from extractor.advanced_json_matcher import AdvancedJSONMatcher
from extractor.html_structure_extractor import HTMLStructureExtractor

logger = logging.getLogger(__name__)

class ProxyHandler:
    """配置驱动的代理处理器类"""
    
    def __init__(self, config_path: str):
        """
        初始化代理处理器
        
        Args:
            config_path: 配置文件路径 (.exp 格式)
        """
        self.config_parser = ConfigParser(config_path)
        self.config_parser.load_config()
        
        # 初始化组件
        self._init_components()
        
        # 获取配置信息
        self.crawler_config = self.config_parser.get_crawler_config()
        self.extraction_config = self.config_parser.get_data_extraction_config()
        self.request_config = self.config_parser.get_request_config()
        
        # 提取URL匹配模式 - 从配置中获取
        try:
            # 首先尝试从 ConfigParser 的 get_target_urls 方法获取
            config_target_urls = self.config_parser.get_target_urls()
            if config_target_urls:
                # 如果是字典，提取所有值作为URL列表
                if isinstance(config_target_urls, dict):
                    self.target_urls = list(config_target_urls.values())
                    logger.info(f"从配置获取目标URLs(字典): {config_target_urls}")
                    logger.info(f"转换为URL列表: {self.target_urls}")
                # 如果是列表，直接使用
                elif isinstance(config_target_urls, list):
                    self.target_urls = config_target_urls
                    logger.info(f"从配置获取目标URLs(列表): {self.target_urls}")
                else:
                    # 其他类型，尝试转换为列表
                    self.target_urls = [str(config_target_urls)]
                    logger.info(f"从配置获取目标URLs(其他): {config_target_urls} -> {self.target_urls}")
            else:
                # 如果配置中没有，使用默认的小红书URL
                self.target_urls = [
                    "https://www.xiaohongshu.com/explore",
                    "https://edith.xiaohongshu.com/api/sns/web/v1/feed"
                ]
                logger.warning(f"配置中未找到目标URLs，使用默认值: {self.target_urls}")
        except Exception as e:
            logger.error(f"获取目标URLs失败: {e}")
            # 使用默认值
            self.target_urls = [
                "https://www.xiaohongshu.com/explore", 
                "https://edith.xiaohongshu.com/api/sns/web/v1/feed"
            ]
            logger.warning(f"使用默认目标URLs: {self.target_urls}")
        
        self.site_name = self._extract_site_name()
        
        # 初始化统计信息
        self.stats = {
            'total_requests': 0,
            'matched_requests': 0,
            'api_calls_intercepted': 0,
            'extracted_items': 0,
            'processed_items': 0,
            'failed_extractions': 0,
            'json_extractions': 0,
            'html_extractions': 0
        }
        
        logger.info(f"配置驱动代理处理器初始化完成")
        logger.info(f"目标站点: {self.site_name}")
        logger.info(f"监听URL数量: {len(self.target_urls)}")
        logger.info(f"目标表: {self.extraction_config.get('table_name', 'unknown')}")
    
    def _init_components(self):
        """初始化各个组件"""
        try:
            # 初始化配置驱动数据适配器
            self.adaptor = UniversalAdaptor(self.config_parser.config_path)
            
            # 初始化JSON提取器
            self.json_matcher = AdvancedJSONMatcher()
            
            # 初始化HTML结构提取器
            self.html_extractor = HTMLStructureExtractor()
            
            # 初始化数据处理器
            db_config = self.config_parser.get_database_config()
            output_config = {
                'database_type': db_config.get('type', 'MySql'),
                'connection_string': db_config.get('connection_string', ''),
                'table_name': self.config_parser.get_data_extraction_config().get('table_name', ''),
                'deduplicate': self.config_parser.get_data_extraction_config().get('deduplicate', True),
                'deduplicate_field': self.config_parser.get_data_extraction_config().get('deduplicate_field', '')
            }
            self.data_processor = DataProcessor(output_config)
            
            logger.info("配置驱动组件初始化完成")
            
        except Exception as e:
            logger.error(f"组件初始化失败: {e}")
            raise
    
    def _extract_site_name(self) -> str:
        """从配置中提取站点名称"""
        try:
            # 从目标URL中提取域名作为站点名称
            if self.target_urls:
                first_url = self.target_urls[0]
                parsed = urlparse(first_url)
                domain = parsed.netloc
                if 'xiaohongshu' in domain or 'xhs' in domain:
                    return 'xiaohongshu'
                elif 'douyin' in domain:
                    return 'douyin'
                else:
                    return domain.split('.')[0] if domain else 'unknown'
            
            # 从表名中推断
            table_name = self.extraction_config.get('table_name', '')
            if 'xiaohongshu' in table_name:
                return 'xiaohongshu'
            elif 'douyin' in table_name:
                return 'douyin'
            
            return 'unknown'
            
        except Exception as e:
            logger.warning(f"站点名称提取失败: {e}")
            return 'unknown'
    
    def is_target_request(self, url: str, method: str = 'GET') -> bool:
        """
        判断是否为目标请求
        
        Args:
            url: 请求URL
            method: 请求方法
            
        Returns:
            bool: 是否匹配目标请求
        """
        try:
            # 检查是否匹配目标URL列表
            for target_url in self.target_urls:
                if self._match_url_pattern(url, target_url):
                    logger.debug(f"URL匹配成功: {url} -> {target_url}")
                    return True
            
            # 检查是否匹配请求配置中的URL
            request_url = self.request_config.get('url', '')
            if request_url and self._match_url_pattern(url, request_url):
                logger.debug(f"URL匹配请求配置: {url} -> {request_url}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"URL匹配检查失败: {e}")
            return False
    
    def _match_url_pattern(self, url: str, pattern: str) -> bool:
        """匹配URL模式"""
        # 支持通配符匹配
        if '*' in pattern:
            # 简单的通配符匹配
            pattern_parts = pattern.split('*')
            url_check = url
            for part in pattern_parts:
                if part and part not in url_check:
                    return False
                if part:
                    url_check = url_check[url_check.find(part) + len(part):]
            return True
        else:
            # 直接字符串匹配
            return pattern in url
    
    def handle_api_response(self, url: str, response_text: str) -> bool:
        """
        处理API响应数据
        
        Args:
            url: 请求URL
            response_text: 响应文本
            
        Returns:
            bool: 处理是否成功
        """
        try:
            self.stats['matched_requests'] += 1
            
            # 尝试直接解析JSON响应
            response_data = None
            extraction_method = None
            
            try:
                response_data = json.loads(response_text)
                extraction_method = 'direct_json'
                self.stats['json_extractions'] += 1
                logger.info(f"直接解析JSON成功: {url}")
            except json.JSONDecodeError:
                # 如果不是JSON，尝试从HTML中提取JSON
                logger.info(f"响应不是JSON，尝试从HTML中提取JSON: {url}")
                
                # 检查HTML完整性
                completeness_info = self._check_response_completeness(response_text, url)
                
                # 使用AdvancedJSONMatcher从HTML中提取JSON
                json_candidates = self.json_matcher.extract_and_rank_json(response_text)
                
                if json_candidates:
                    # 使用价值分数最高的JSON数据
                    best_candidate = json_candidates[0]
                    response_data = best_candidate['data']
                    extraction_method = 'json_from_html'
                    self.stats['json_extractions'] += 1
                    
                    logger.info(f"从HTML中提取JSON成功: {url}")
                    logger.info(f"提取的JSON类型: {best_candidate['name']}, 价值分数: {best_candidate['value_score']}, 大小: {best_candidate['size']}字符")
                    
                    # 记录HTML完整性信息
                    html_completeness = best_candidate.get('html_completeness', {})
                    if not html_completeness.get('is_complete', True):
                        logger.warning(f"注意：从不完整的HTML中提取数据，完整性: {html_completeness.get('estimated_completeness', 0):.1%}")
                    
                    # 如果是小红书数据，进行详细分析
                    if 'xiaohongshu' in url.lower() or 'xhs' in url.lower():
                        analysis = self.json_matcher.analyze_xiaohongshu_data(response_data)
                        logger.info(f"小红书数据分析: 类型={analysis['data_type']}, 内容项目={analysis['content_items']}, 图片={len(analysis['media_info']['images'])}")
                
                else:
                    # JSON提取失败，尝试HTML结构提取
                    logger.info(f"JSON提取失败，尝试HTML结构提取: {url}")
                    
                    if completeness_info['response_type'] == 'html' and completeness_info['is_complete']:
                        # 使用HTML结构提取器
                        try:
                            extracted_notes = self.html_extractor.extract_notes(response_text)
                            if extracted_notes:
                                # 将提取的笔记转换为标准格式
                                response_data = {
                                    'data': {
                                        'items': extracted_notes
                                    },
                                    'success': True,
                                    'extraction_method': 'html_structure'
                                }
                                extraction_method = 'html_structure'
                                self.stats['html_extractions'] += 1
                                logger.info(f"HTML结构提取成功: {url}, 提取到{len(extracted_notes)}条笔记")
                            else:
                                logger.warning(f"HTML结构提取未找到数据: {url}")
                        except Exception as e:
                            logger.error(f"HTML结构提取失败: {e}")
                    
                    if not response_data:
                        if not completeness_info['is_complete']:
                            logger.warning(f"HTML内容不完整，可能需要等待页面完全加载: {url}")
                            logger.warning(f"HTML完整性: {completeness_info['estimated_completeness']:.1%}, 缺失元素: {completeness_info['missing_elements']}")
                        else:
                            logger.warning(f"未能从完整HTML中提取到数据: {url}")
                        self.stats['failed_extractions'] += 1
                        return False
            
            if not response_data:
                logger.error(f"无法获取有效的响应数据: {url}")
                self.stats['failed_extractions'] += 1
                return False
            
            # 使用配置驱动适配器处理数据
            adapted_data = self.adaptor.adapt_data(response_data)
            
            if not adapted_data:
                logger.warning(f"数据适配后为空: {url}")
                return False
            
            self.stats['extracted_items'] += len(adapted_data)
            logger.info(f"适配后得到{len(adapted_data)}条数据 (提取方法: {extraction_method})")
            
            # 处理每条数据
            for item in adapted_data:
                try:
                    # 添加元数据
                    item.update({
                        'source_url': url,
                        'extract_time': int(time.time()),
                        'site_name': self.site_name,
                        'extraction_method': extraction_method
                    })
                    
                    # 使用数据处理器处理
                    self.data_processor.process_data(item)
                    self.stats['processed_items'] += 1
                    
                except Exception as e:
                    logger.error(f"数据处理失败: {e}")
                    continue
            
            logger.info(f"成功处理{len(adapted_data)}条数据")
            return True
            
        except Exception as e:
            logger.error(f"API响应处理失败: {e}")
            self.stats['failed_extractions'] += 1
            return False
    
    def _check_response_completeness(self, response_text: str, url: str) -> Dict[str, Any]:
        """检查响应内容的完整性"""
        completeness_info = {
            'is_complete': True,
            'estimated_completeness': 1.0,
            'missing_elements': [],
            'size': len(response_text),
            'response_type': 'unknown'
        }
        
        # 判断响应类型
        if response_text.strip().startswith('{') or response_text.strip().startswith('['):
            completeness_info['response_type'] = 'json'
            return completeness_info
        elif response_text.strip().startswith('<!DOCTYPE') or response_text.strip().startswith('<html'):
            completeness_info['response_type'] = 'html'
        else:
            completeness_info['response_type'] = 'other'
        
        # 对于HTML响应，检查完整性
        if completeness_info['response_type'] == 'html':
            # 检查基本结构
            if not response_text.strip().endswith('</html>'):
                completeness_info['is_complete'] = False
                completeness_info['missing_elements'].append('closing_html_tag')
            
            if '</body>' not in response_text:
                completeness_info['missing_elements'].append('body_tag')
            
            if '</head>' not in response_text:
                completeness_info['missing_elements'].append('head_tag')
            
            # 检查小红书特定的数据注入点
            xhs_indicators = ['__INITIAL_STATE__', '__NUXT__', 'pageData', 'feedData']
            found_indicators = sum(1 for indicator in xhs_indicators if indicator in response_text)
            
            # 估算完整性
            completeness_score = 0
            if '</body>' in response_text:
                completeness_score += 30
            if len(response_text) > 10000:  # 假设完整页面至少10KB
                completeness_score += 30
            if found_indicators > 0:
                completeness_score += 20 + (found_indicators * 5)  # 每个指标额外加分
            if not completeness_info['missing_elements']:
                completeness_score += 20
            
            completeness_info['estimated_completeness'] = min(completeness_score, 100) / 100.0
            
            # 如果完整性低于60%，认为不完整
            if completeness_info['estimated_completeness'] < 0.6:
                completeness_info['is_complete'] = False
        
        return completeness_info
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.stats.copy()
        
        # 添加配置信息
        stats.update({
            'site_name': self.site_name,
            'target_table': self.extraction_config.get('table_name', 'unknown'),
            'target_urls_count': len(self.target_urls),
            'deduplicate_enabled': self.extraction_config.get('deduplicate', False),
            'deduplicate_field': self.extraction_config.get('deduplicate_field', '')
        })
        
        # 添加数据处理器统计
        if hasattr(self.data_processor, 'get_stats'):
            processor_stats = self.data_processor.get_stats()
            stats.update(processor_stats)
        
        return stats
    
    def clear_stats(self):
        """清空统计信息"""
        self.stats = {
            'total_requests': 0,
            'matched_requests': 0,
            'api_calls_intercepted': 0,
            'extracted_items': 0,
            'processed_items': 0,
            'failed_extractions': 0,
            'json_extractions': 0,
            'html_extractions': 0
        }
    
    def response(self, flow: http.HTTPFlow):
        """
        mitmproxy addon 响应处理方法
        
        Args:
            flow: HTTP流对象
        """
        try:
            self.stats['total_requests'] += 1
            
            url = flow.request.pretty_url
            method = flow.request.method
            
            logger.debug(f"收到请求: {method} {url}")
            
            # 检查是否为目标请求
            if self.is_target_request(url, method):
                logger.info(f"处理目标请求: {method} {url}")
                
                # 获取响应内容
                response_text = flow.response.get_text()
                if response_text:
                    success = self.handle_api_response(url, response_text)
                    if success:
                        self.stats['api_calls_intercepted'] += 1
                        logger.info(f"成功拦截并处理API调用: {url}")
                    else:
                        logger.warning(f"API响应处理失败: {url}")
                else:
                    logger.warning(f"响应内容为空: {url}")
            else:
                logger.debug(f"非目标请求，跳过: {url}")
        
        except Exception as e:
            logger.error(f"响应处理失败: {e}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
    
    def request(self, flow: http.HTTPFlow):
        """
        mitmproxy addon 请求处理方法（可选）
        
        Args:
            flow: HTTP流对象
        """
        try:
            url = flow.request.pretty_url
            method = flow.request.method
            
            # 记录请求日志用于调试
            logger.debug(f"拦截请求: {method} {url}")
            
            # 可以在这里添加请求预处理逻辑
            # 例如：修改请求头、添加认证信息等
            
        except Exception as e:
            logger.error(f"请求处理失败: {e}")

# mitmproxy入口函数
# proxy_handler = None

# def load(loader):
#     """mitmproxy加载函数"""
#     global proxy_handler
#     try:
#         # 使用新的 .exp 配置文件
#         config_path = "config/xiaohongshu.exp"
#         proxy_handler = ProxyHandler(config_path)
#         logger.info("配置驱动代理处理器加载成功")
#     except Exception as e:
#         logger.error(f"代理处理器加载失败: {e}")
#         raise

# def response(flow: http.HTTPFlow):
#     """mitmproxy响应处理函数"""
#     global proxy_handler
    
#     if not proxy_handler:
#         return
    
#     try:
#         proxy_handler.stats['total_requests'] += 1
        
#         url = flow.request.pretty_url
#         method = flow.request.method
        
#         # 检查是否为目标请求
#         if proxy_handler.is_target_request(url, method):
#             logger.info(f"处理目标请求: {method} {url}")
            
#             # 获取响应内容
#             response_text = flow.response.get_text()
#             if response_text:
#                 proxy_handler.handle_api_response(url, response_text)
#             else:
#                 logger.warning(f"响应内容为空: {url}")
        
#     except Exception as e:
#         logger.error(f"响应处理失败: {e}")

# def done():
#     """mitmproxy关闭函数"""
#     global proxy_handler
    
#     if proxy_handler:
#         try:
#             # 输出统计信息
#             stats = proxy_handler.get_stats()
#             logger.info(f"配置驱动代理处理器统计信息: {stats}")
            
#             # 关闭数据处理器
#             if hasattr(proxy_handler.data_processor, 'close'):
#                 proxy_handler.data_processor.close()
                
#             logger.info("配置驱动代理处理器关闭完成")
            
#         except Exception as e:
#             logger.error(f"代理处理器关闭失败: {e}")