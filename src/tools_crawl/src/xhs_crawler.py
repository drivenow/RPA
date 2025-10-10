#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书爬虫主控制器
协调浏览器管理器和代理处理器，实现完整的数据抓取流程
"""

import asyncio
import signal
import sys
import time
from typing import Dict, Any, Optional
from pathlib import Path

from loguru import logger

from mitmproxy import options
from mitmproxy.tools.dump import DumpMaster
from proxy_handler import ProxyHandler

from browser_manager import BrowserManager
from config_parser import ConfigParser


class XHSCrawler:
    """小红书爬虫主控制器"""
    
    def __init__(self, config_path: str):
        """
        初始化爬虫控制器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config_parser = ConfigParser(config_path)
        self.config = self.config_parser.load_config()
        
        # 组件实例
        self.browser_manager = None
        self.dump_master = None
        self.proxy_handler = None
        
        # 运行状态
        self.is_running = False
        self.proxy_task = None  # 添加代理任务引用
        
        # 统计信息
        self.crawl_stats = {
            'start_time': None,
            'end_time': None,
            'pages_visited': 0,
            'scroll_count': 0,
            'api_calls_intercepted': 0,
            'data_extracted': 0
        }
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"小红书爬虫控制器初始化完成: {self.config.get('crawler', {}).get('name', 'Unknown')}")
    
    def _signal_handler(self, signum, frame):
        """
        信号处理器
        
        Args:
            signum: 信号编号
            frame: 当前栈帧
        """
        logger.info(f"接收到信号 {signum}，开始优雅关闭...")
        self.is_running = False
        
        # 取消代理任务
        if self.proxy_task and not self.proxy_task.done():
            logger.info("取消代理服务器任务...")
            self.proxy_task.cancel()
    
    async def initialize(self):
        """
        初始化所有组件
        """
        try:
            logger.info("开始初始化爬虫组件...")
            
            # 初始化代理处理器
            await self._init_proxy_handler()
            
            # 初始化浏览器管理器
            await self._init_browser_manager()
            
            logger.info("所有组件初始化完成")
            
        except Exception as e:
            logger.error(f"组件初始化失败: {e}")
            raise
    
    async def _init_proxy_handler(self):
        """
        初始化代理处理器
        """
        try:
            # 创建mitmproxy选项
            crawler_config = self.config_parser.get_crawler_config()
            proxy_port = crawler_config.get('proxy_port', 8080)
            
            opts = options.Options(
                listen_port=proxy_port,
                confdir='~/.mitmproxy',
                ssl_insecure=True
            )
            
            # 创建DumpMaster
            self.dump_master = DumpMaster(opts)
            
            # 创建并添加代理处理器实例，使用相同的 .exp 配置文件
            proxy_handler_instance = ProxyHandler(self.config_path)
            self.dump_master.addons.add(proxy_handler_instance)
            
            # 保存代理处理器实例的引用
            self.proxy_handler = proxy_handler_instance
            
            logger.info(f"代理服务器初始化完成，监听端口: {proxy_port}")
            
        except Exception as e:
            logger.error(f"代理处理器初始化失败: {e}")
            raise
    
    async def _init_browser_manager(self):
        """
        初始化浏览器管理器
        """
        try:
            crawler_config = self.config_parser.get_crawler_config()
            browser_config = crawler_config.get('browser', {})
            self.browser_manager = BrowserManager(browser_config)
            
            await self.browser_manager.start_browser()
            
            logger.info("浏览器管理器初始化完成")
            
        except Exception as e:
            logger.error(f"浏览器管理器初始化失败: {e}")
            raise
    
    async def start_crawling(self):
        """
        开始爬取流程
        """
        try:
            if not self.browser_manager:
                raise RuntimeError("浏览器管理器未初始化")
            
            self.is_running = True
            self.crawl_stats['start_time'] = time.time()
            
            logger.info("开始小红书内容抓取...")
            
            # 启动代理服务器
            self.proxy_task = asyncio.create_task(self._run_proxy_server())
            # 等待代理服务器启动
            await asyncio.sleep(2)
            
            # 开始浏览器爬取
            await self._start_browser_crawling()
            
            # 等待代理任务完成或取消
            if self.proxy_task and not self.proxy_task.done():
                try:
                    logger.info("等待代理服务器任务完成...")
                    await self.proxy_task
                except asyncio.CancelledError:
                    logger.info("代理服务器任务已取消")
                except Exception as e:
                    logger.error(f"代理服务器任务异常: {e}")
            
        except Exception as e:
            logger.error(f"爬取过程中发生错误: {e}")
            raise
        finally:
            self.crawl_stats['end_time'] = time.time()
            await self._cleanup()
    
    async def _run_proxy_server(self):
        """
        运行代理服务器
        """
        try:
            logger.info("启动mitmproxy代理服务器...")
            await self.dump_master.run()
        except Exception as e:
            logger.error(f"代理服务器运行失败: {e}")
    
    async def _start_browser_crawling(self):
        """
        开始浏览器爬取
        """
        try:
            crawler_config = self.config_parser.get_crawler_config()
            
            target_url = crawler_config.get('target_url', 'https://www.xiaohongshu.com/explore')
            scroll_count = crawler_config.get('scroll_count', 5)
            scroll_interval = crawler_config.get('scroll_interval', 3)
            
            # 导航到目标页面
            logger.info(f"导航到目标页面: {target_url}")
            await self.browser_manager.navigate_to_page(target_url)
            self.crawl_stats['pages_visited'] += 1
            
            # 检查登录状态
            if await self.browser_manager.wait_for_login(timeout=5):
                logger.info("检测到已登录状态")
            else:
                logger.warning("未检测到登录状态，可能影响数据获取")
            
            # 等待页面加载
            await asyncio.sleep(5)
            
            # 开始滚动加载
            logger.info(f"开始滚动加载，计划滚动 {scroll_count} 次")
            
            for i in range(scroll_count):
                if not self.is_running:
                    logger.info("收到停止信号，中断滚动")
                    break
                
                logger.info(f"执行第 {i+1}/{scroll_count} 次滚动")
                
                # 滚动页面
                await self.browser_manager.scroll_page()
                self.crawl_stats['scroll_count'] += 1
                
                # 等待数据加载
                await asyncio.sleep(scroll_interval)
                
                # 检查配置是否有更新
                if self.config_parser.reload_if_changed():
                    logger.info("检测到配置更新，重新加载配置")
                    self.config = self.config_parser.load_config()
            
            logger.info("浏览器爬取完成")
            
        except Exception as e:
            logger.error(f"浏览器爬取失败: {e}")
            raise
    
    async def _cleanup(self):
        """
        清理资源
        """
        logger.info("开始清理资源...")
        
        try:
            # 取消代理任务（如果还在运行）
            if self.proxy_task and not self.proxy_task.done():
                logger.info("取消代理服务器任务...")
                self.proxy_task.cancel()
                try:
                    await asyncio.wait_for(self.proxy_task, timeout=5.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    logger.info("代理服务器任务已取消")
                except Exception as e:
                    logger.warning(f"代理任务取消时发生异常: {e}")
            
            # 关闭代理服务器
            if self.dump_master:
                try:
                    self.dump_master.shutdown()
                    logger.info("代理服务器已关闭")
                except Exception as e:
                    logger.warning(f"关闭代理服务器时发生异常: {e}")
            
            # 关闭浏览器管理器
            if self.browser_manager:
                await self.browser_manager.close()
                logger.info("浏览器管理器已关闭")
            
            # 关闭数据处理器
            if self.proxy_handler and hasattr(self.proxy_handler, 'data_processor'):
                if hasattr(self.proxy_handler.data_processor, 'close'):
                    self.proxy_handler.data_processor.close()
                    logger.info("数据处理器已关闭")
            
        except Exception as e:
            logger.error(f"资源清理失败: {e}")
        
        logger.info("资源清理完成")
    
    def get_crawl_stats(self) -> Dict[str, Any]:
        """
        获取爬取统计信息
        
        Returns:
            Dict[str, Any]: 爬取统计信息
        """
        stats = self.crawl_stats.copy()
        
        # 计算运行时间
        if stats['start_time']:
            if stats['end_time']:
                stats['duration'] = stats['end_time'] - stats['start_time']
            else:
                stats['duration'] = time.time() - stats['start_time']
        
        # 添加组件统计
        if self.browser_manager:
            stats['browser_stats'] = {
                'is_running': self.browser_manager.browser is not None,
                'current_url': getattr(self.browser_manager.page, 'url', None) if self.browser_manager.page else None
            }
        
        # 添加代理统计信息
        if self.proxy_handler:
            proxy_stats = self.proxy_handler.get_stats()
            stats.update(proxy_stats)
        
        return stats
    
    async def stop(self):
        """
        停止爬虫
        """
        logger.info("正在停止爬虫...")
        self.is_running = False
        
        # 取消代理任务
        if self.proxy_task and not self.proxy_task.done():
            logger.info("取消代理服务器任务...")
            self.proxy_task.cancel()
        
        # 等待一段时间让正在进行的操作完成
        await asyncio.sleep(1)
        
        await self._cleanup()
        logger.info("爬虫已停止")


async def main():
    """
    主函数
    """
    try:
        # 配置日志
        logger.remove()
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="INFO"
        )
        logger.add(
            "logs/xhs_crawler.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",
            rotation="1 day",
            retention="7 days"
        )
        
        # 创建爬虫实例
        config_path = "config/xiaohongshu.exp"
        crawler = XHSCrawler(config_path)
        
        # 初始化组件
        await crawler.initialize()
        
        # 开始爬取
        await crawler.start_crawling()
        
        # 输出统计信息
        stats = crawler.get_crawl_stats()
        logger.info(f"爬取完成，统计信息: {stats}")
        
    except KeyboardInterrupt:
        logger.info("用户中断程序")
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 确保日志目录存在
    Path("logs").mkdir(exist_ok=True)
    
    # 运行主程序
    asyncio.run(main())