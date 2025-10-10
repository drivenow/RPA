"""
通用数据提取器
负责从HTML内容或API响应中提取核心JSON数据
"""
import re
import json
import logging
from typing import Dict, List, Any, Optional, Union
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseExtractor(ABC):
    """数据提取器基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
    @abstractmethod
    def extract(self, content: Union[str, Dict], **kwargs) -> List[Dict[str, Any]]:
        """提取数据的抽象方法"""
        pass

class JSONExtractor(BaseExtractor):
    """JSON数据提取器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.json_patterns = config.get('json_patterns', [])
        
    def extract(self, content: Union[str, Dict], **kwargs) -> List[Dict[str, Any]]:
        """
        从内容中提取JSON数据
        
        Args:
            content: HTML内容或已解析的字典
            **kwargs: 额外参数
            
        Returns:
            提取的JSON数据列表
        """
        if isinstance(content, dict):
            return self._extract_from_dict(content)
        elif isinstance(content, str):
            return self._extract_from_html(content)
        else:
            logger.warning(f"不支持的内容类型: {type(content)}")
            return []
    
    def _extract_from_html(self, html_content: str) -> List[Dict[str, Any]]:
        """从HTML内容中提取JSON"""
        extracted_data = []
        
        for pattern in self.json_patterns:
            try:
                matches = re.finditer(pattern, html_content, re.DOTALL)
                for match in matches:
                    json_str = match.group(1)
                    json_data = self._parse_json_safely(json_str)
                    if json_data:
                        extracted_data.append(json_data)
                        logger.info(f"成功提取JSON数据，模式: {pattern[:50]}...")
            except Exception as e:
                logger.error(f"JSON提取失败，模式: {pattern}, 错误: {e}")
                
        return extracted_data
    
    def _extract_from_dict(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从字典中提取数据"""
        return [data]
    
    def _parse_json_safely(self, json_str: str) -> Optional[Dict[str, Any]]:
        """安全解析JSON字符串"""
        try:
            # 清理JSON字符串
            json_str = self._clean_json_string(json_str)
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return None
    
    def _clean_json_string(self, json_str: str) -> str:
        """清理JSON字符串"""
        # 移除可能的尾随分号
        json_str = json_str.rstrip(';')
        # 移除可能的注释
        json_str = re.sub(r'//.*?$', '', json_str, flags=re.MULTILINE)
        # 移除多行注释
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        return json_str.strip()

class APIExtractor(BaseExtractor):
    """API响应数据提取器"""
    
    def extract(self, content: Union[str, Dict], **kwargs) -> List[Dict[str, Any]]:
        """
        从API响应中提取数据
        
        Args:
            content: API响应内容
            **kwargs: 额外参数，如data_path
            
        Returns:
            提取的数据列表
        """
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"API响应JSON解析失败: {e}")
                return []
        
        if not isinstance(content, dict):
            logger.warning(f"API响应格式不正确: {type(content)}")
            return []
        
        # 获取数据路径
        data_path = kwargs.get('data_path', 'data')
        
        # 根据路径提取数据
        data = self._get_nested_value(content, data_path)
        
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]
        else:
            logger.warning(f"提取的数据格式不正确: {type(data)}")
            return []
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """根据路径获取嵌套值"""
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                logger.warning(f"路径 {path} 中的键 {key} 不存在")
                return None
                
        return current

class UniversalExtractor:
    """通用数据提取器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        # 为JSONExtractor传递json_patterns配置
        json_config = {
            'json_patterns': config.get('json_patterns', [])
        }
        self.json_extractor = JSONExtractor(json_config)
        
        # 为APIExtractor传递基础配置
        api_config = config.get('api', {})
        self.api_extractor = APIExtractor(api_config)
        
    def extract_from_html(self, html_content: str) -> List[Dict[str, Any]]:
        """从HTML中提取数据"""
        return self.json_extractor.extract(html_content)
    
    def extract_from_api(self, api_response: Union[str, Dict], data_path: str = 'data') -> List[Dict[str, Any]]:
        """从API响应中提取数据"""
        return self.api_extractor.extract(api_response, data_path=data_path)
    
    def extract_by_config(self, content: Union[str, Dict], extraction_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """根据配置提取数据"""
        extraction_type = extraction_config.get('类型', 'json')
        data_path = extraction_config.get('路径', 'data')
        
        if extraction_type == 'json':
            if isinstance(content, str):
                return self.json_extractor.extract(content)
            else:
                return self.api_extractor.extract(content, data_path=data_path)
        elif extraction_type == 'api':
            return self.api_extractor.extract(content, data_path=data_path)
        else:
            logger.warning(f"不支持的提取类型: {extraction_type}")
            return []