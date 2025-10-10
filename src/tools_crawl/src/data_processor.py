#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据处理器
负责处理从API响应中提取的数据，包括数据清洗、转换、存储等
"""

import json
import hashlib
import time
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from pathlib import Path

import pymysql
from loguru import logger


class DataProcessor:
    """数据处理器类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化数据处理器
        
        Args:
            config: 输出配置
        """
        self.config = config
        self.processed_ids: Set[str] = set()  # 已处理的数据ID，用于去重
        self.mysql_connection = None
        self.backup_dir = Path(config.get('backup', {}).get('path', 'data/backup'))
        
        # 确保备份目录存在
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化MySQL连接
        self._init_mysql_connection()
        
        logger.info("数据处理器初始化完成")
    
    def _init_mysql_connection(self):
        """
        初始化MySQL连接
        """
        try:
            mysql_config = self.config.get('mysql', {})
            if not mysql_config.get('enabled', False):
                logger.info("MySQL存储未启用")
                return
            
            self.mysql_connection = pymysql.connect(
                host=mysql_config.get('host', 'localhost'),
                port=mysql_config.get('port', 3306),
                user=mysql_config.get('user', 'root'),
                password=mysql_config.get('password', ''),
                database=mysql_config.get('database', 'crawler'),
                charset='utf8mb4',
                autocommit=True
            )
            
            # 创建表
            self._create_table_if_not_exists()
            
            logger.info("MySQL连接初始化成功")
            
        except Exception as e:
            logger.error(f"MySQL连接初始化失败: {e}")
            self.mysql_connection = None
    
    def _create_table_if_not_exists(self):
        """
        创建数据表（如果不存在）
        """
        try:
            if not self.mysql_connection:
                return
            
            table_name = self.config.get('mysql', {}).get('table', 'xiaohongshu_feeds')
            
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS `{table_name}` (
                `id` varchar(64) NOT NULL COMMENT '笔记ID',
                `title` text COMMENT '标题',
                `description` text COMMENT '描述',
                `user_id` varchar(64) COMMENT '用户ID',
                `user_nickname` varchar(255) COMMENT '用户昵称',
                `like_count` int DEFAULT 0 COMMENT '点赞数',
                `comment_count` int DEFAULT 0 COMMENT '评论数',
                `share_count` int DEFAULT 0 COMMENT '分享数',
                `collect_count` int DEFAULT 0 COMMENT '收藏数',
                `image_urls` json COMMENT '图片URL列表',
                `video_url` varchar(500) COMMENT '视频URL',
                `tags` json COMMENT '标签列表',
                `publish_time` datetime COMMENT '发布时间',
                `crawl_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '抓取时间',
                `raw_data` json COMMENT '原始数据',
                `data_hash` varchar(64) COMMENT '数据哈希值',
                PRIMARY KEY (`id`),
                KEY `idx_user_id` (`user_id`),
                KEY `idx_crawl_time` (`crawl_time`),
                KEY `idx_data_hash` (`data_hash`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='小红书内容数据表';
            """
            
            with self.mysql_connection.cursor() as cursor:
                cursor.execute(create_sql)
            
            logger.info(f"数据表 {table_name} 检查/创建完成")
            
        except Exception as e:
            logger.error(f"创建数据表失败: {e}")
    
    def process_data(self, data_list: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        处理数据列表
        
        Args:
            data_list: 待处理的数据列表
            
        Returns:
            Dict[str, int]: 处理统计信息
        """
        stats = {
            'total': len(data_list),
            'processed': 0,
            'duplicated': 0,
            'failed': 0
        }
        
        logger.info(f"开始处理 {stats['total']} 条数据")
        
        for data in data_list:
            try:
                # 数据清洗和转换
                cleaned_data = self._clean_data(data)
                
                # 生成数据哈希值
                data_hash = self._generate_hash(cleaned_data)
                
                # 检查是否重复
                if self._is_duplicate(cleaned_data.get('id'), data_hash):
                    stats['duplicated'] += 1
                    logger.debug(f"跳过重复数据: {cleaned_data.get('id')}")
                    continue
                
                # 存储数据
                if self._store_data(cleaned_data, data_hash):
                    stats['processed'] += 1
                    self.processed_ids.add(cleaned_data.get('id', ''))
                else:
                    stats['failed'] += 1
                
            except Exception as e:
                logger.error(f"处理数据失败: {e}")
                stats['failed'] += 1
        
        logger.info(f"数据处理完成: {stats}")
        return stats
    
    def _clean_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        清洗和转换数据
        
        Args:
            raw_data: 原始数据
            
        Returns:
            Dict[str, Any]: 清洗后的数据
        """
        cleaned = {
            'id': str(raw_data.get('id', '')),
            'title': str(raw_data.get('title', '')).strip(),
            'description': str(raw_data.get('description', '')).strip(),
            'user_id': str(raw_data.get('user_id', '')),
            'user_nickname': str(raw_data.get('user_nickname', '')).strip(),
            'like_count': self._safe_int(raw_data.get('like_count', 0)),
            'comment_count': self._safe_int(raw_data.get('comment_count', 0)),
            'share_count': self._safe_int(raw_data.get('share_count', 0)),
            'collect_count': self._safe_int(raw_data.get('collect_count', 0)),
            'image_urls': raw_data.get('image_urls', []),
            'video_url': str(raw_data.get('video_url', '')),
            'tags': raw_data.get('tags', []),
            'publish_time': self._parse_timestamp(raw_data.get('publish_time')),
            'crawl_time': datetime.now(),
            'raw_data': raw_data
        }
        
        return cleaned
    
    def _safe_int(self, value: Any) -> int:
        """
        安全转换为整数
        
        Args:
            value: 待转换的值
            
        Returns:
            int: 转换后的整数
        """
        try:
            if isinstance(value, (int, float)):
                return int(value)
            elif isinstance(value, str):
                # 移除可能的非数字字符
                cleaned = ''.join(c for c in value if c.isdigit())
                return int(cleaned) if cleaned else 0
            else:
                return 0
        except (ValueError, TypeError):
            return 0
    
    def _parse_timestamp(self, timestamp: Any) -> Optional[datetime]:
        """
        解析时间戳
        
        Args:
            timestamp: 时间戳
            
        Returns:
            Optional[datetime]: 解析后的时间
        """
        try:
            if isinstance(timestamp, (int, float)):
                # Unix时间戳
                if timestamp > 1e10:  # 毫秒时间戳
                    timestamp = timestamp / 1000
                return datetime.fromtimestamp(timestamp)
            elif isinstance(timestamp, str):
                # 尝试解析ISO格式
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                return None
        except (ValueError, TypeError, OSError):
            return None
    
    def _generate_hash(self, data: Dict[str, Any]) -> str:
        """
        生成数据哈希值
        
        Args:
            data: 数据字典
            
        Returns:
            str: 哈希值
        """
        # 排除时间字段，只对内容字段生成哈希
        content_fields = ['id', 'title', 'description', 'user_id', 
                         'like_count', 'comment_count', 'share_count', 'collect_count']
        
        content_data = {k: data.get(k) for k in content_fields if k in data}
        content_str = json.dumps(content_data, sort_keys=True, ensure_ascii=False)
        
        return hashlib.md5(content_str.encode('utf-8')).hexdigest()
    
    def _is_duplicate(self, data_id: str, data_hash: str) -> bool:
        """
        检查是否为重复数据
        
        Args:
            data_id: 数据ID
            data_hash: 数据哈希值
            
        Returns:
            bool: 是否重复
        """
        # 内存去重
        if data_id in self.processed_ids:
            return True
        
        # 数据库去重
        if self.mysql_connection:
            try:
                table_name = self.config.get('mysql', {}).get('table', 'xiaohongshu_feeds')
                
                with self.mysql_connection.cursor() as cursor:
                    sql = f"SELECT COUNT(*) FROM `{table_name}` WHERE `id` = %s OR `data_hash` = %s"
                    cursor.execute(sql, (data_id, data_hash))
                    count = cursor.fetchone()[0]
                    
                    return count > 0
                    
            except Exception as e:
                logger.error(f"数据库去重检查失败: {e}")
        
        return False
    
    def _store_data(self, data: Dict[str, Any], data_hash: str) -> bool:
        """
        存储数据
        
        Args:
            data: 清洗后的数据
            data_hash: 数据哈希值
            
        Returns:
            bool: 是否存储成功
        """
        success = True
        
        # 添加哈希值
        data['data_hash'] = data_hash
        
        # 存储到MySQL
        if self.mysql_connection:
            success &= self._store_to_mysql(data)
        
        # 备份到文件
        if self.config.get('backup', {}).get('enabled', True):
            success &= self._backup_to_file(data)
        
        return success
    
    def _store_to_mysql(self, data: Dict[str, Any]) -> bool:
        """
        存储到MySQL数据库
        
        Args:
            data: 数据
            
        Returns:
            bool: 是否成功
        """
        try:
            table_name = self.config.get('mysql', {}).get('table', 'xiaohongshu_feeds')
            
            # 准备插入数据
            fields = ['id', 'title', 'description', 'user_id', 'user_nickname',
                     'like_count', 'comment_count', 'share_count', 'collect_count',
                     'image_urls', 'video_url', 'tags', 'publish_time', 'crawl_time',
                     'raw_data', 'data_hash']
            
            values = []
            for field in fields:
                value = data.get(field)
                if field in ['image_urls', 'tags', 'raw_data']:
                    # JSON字段
                    value = json.dumps(value, ensure_ascii=False) if value else None
                values.append(value)
            
            # 执行插入
            placeholders = ', '.join(['%s'] * len(fields))
            field_names = ', '.join([f'`{field}`' for field in fields])
            sql = f"INSERT INTO `{table_name}` ({field_names}) VALUES ({placeholders})"
            
            with self.mysql_connection.cursor() as cursor:
                cursor.execute(sql, values)
            
            logger.debug(f"数据存储到MySQL成功: {data.get('id')}")
            return True
            
        except Exception as e:
            logger.error(f"MySQL存储失败: {e}")
            return False
    
    def _backup_to_file(self, data: Dict[str, Any]) -> bool:
        """
        备份到文件
        
        Args:
            data: 数据
            
        Returns:
            bool: 是否成功
        """
        try:
            backup_format = self.config.get('backup', {}).get('format', 'json')
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d')
            filename = f"xiaohongshu_feeds_{timestamp}.{backup_format}"
            filepath = self.backup_dir / filename
            
            # 准备数据
            backup_data = data.copy()
            # 转换datetime为字符串
            for key, value in backup_data.items():
                if isinstance(value, datetime):
                    backup_data[key] = value.isoformat()
            
            # 写入文件
            if backup_format == 'json':
                # 追加到JSON Lines文件
                with open(filepath, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(backup_data, ensure_ascii=False) + '\n')
            
            return True
            
        except Exception as e:
            logger.error(f"文件备份失败: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取处理统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = {
            'processed_count': len(self.processed_ids),
            'mysql_enabled': self.mysql_connection is not None,
            'backup_enabled': self.config.get('backup', {}).get('enabled', True),
            'backup_path': str(self.backup_dir)
        }
        
        # 获取数据库统计
        if self.mysql_connection:
            try:
                table_name = self.config.get('mysql', {}).get('table', 'xiaohongshu_feeds')
                
                with self.mysql_connection.cursor() as cursor:
                    cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                    stats['mysql_total_count'] = cursor.fetchone()[0]
                    
                    cursor.execute(f"SELECT COUNT(*) FROM `{table_name}` WHERE DATE(crawl_time) = CURDATE()")
                    stats['mysql_today_count'] = cursor.fetchone()[0]
                    
            except Exception as e:
                logger.error(f"获取数据库统计失败: {e}")
        
        return stats
    
    def close(self):
        """
        关闭连接
        """
        if self.mysql_connection:
            try:
                self.mysql_connection.close()
                logger.info("MySQL连接已关闭")
            except Exception as e:
                logger.error(f"关闭MySQL连接失败: {e}")
        
        logger.info("数据处理器已关闭")


# 使用示例
if __name__ == "__main__":
    # 测试数据处理器
    test_config = {
        'mysql': {
            'enabled': False,  # 测试时禁用MySQL
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': '',
            'database': 'crawler',
            'table': 'xiaohongshu_feeds'
        },
        'backup': {
            'enabled': True,
            'format': 'json',
            'path': 'data/backup'
        }
    }
    
    processor = DataProcessor(test_config)
    
    # 测试数据
    test_data = [{
        'id': 'test_001',
        'title': '测试标题',
        'description': '测试描述',
        'user_id': 'user_001',
        'user_nickname': '测试用户',
        'like_count': '100',
        'comment_count': 50,
        'share_count': 10,
        'collect_count': 20,
        'image_urls': ['http://example.com/image1.jpg'],
        'tags': ['测试', '标签'],
        'publish_time': int(time.time())
    }]
    
    try:
        stats = processor.process_data(test_data)
        print(f"处理统计: {stats}")
        print(f"系统统计: {processor.get_stats()}")
        
    except Exception as e:
        print(f"测试失败: {e}")
    
    finally:
        processor.close()