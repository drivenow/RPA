#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
浏览器管理器
负责Playwright浏览器的启动、配置、登录态维护、页面操作等功能
"""

import asyncio
import time
import json
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Locator
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from helper import convert_cookies_for_playwright

logger = logging.getLogger(__name__)


class BrowserManager:
    """浏览器管理器类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化浏览器管理器
        
        Args:
            config: 浏览器配置字典
        """
        self.config = config
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # 从配置中提取参数
        self.headless = config.get('headless', False)
        self.proxy_port = config['proxy_port']  # 必需的代理端口
        self.user_agent = config.get('user_agent', '')
        self.viewport = config.get('viewport', {'width': 1920, 'height': 1080})
        self.wait_timeout = config.get('wait_timeout', 30000)
        self.cookies_path = config.get('cookies_path', "")
        
        # SSL/TLS证书配置
        self.ssl_config = config.get('ssl', {})
        self.ignore_certificate_errors = self.ssl_config.get('ignore_certificate_errors', True)
        self.ignore_ssl_errors = self.ssl_config.get('ignore_ssl_errors', True)
        self.allow_insecure_content = self.ssl_config.get('allow_insecure_content', True)
        self.reduce_security_for_testing = self.ssl_config.get('reduce_security_for_testing', True)
        
        logger.info(f"浏览器管理器初始化完成，代理端口: {self.proxy_port}")
    
    async def start_browser(self) -> Browser:
        """
        启动浏览器实例
        
        Returns:
            Browser: Playwright浏览器实例
        """
        try:
            self.playwright = await async_playwright().start()
            
            # 基础浏览器启动参数
            launch_args = [
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                f'--proxy-server=http://127.0.0.1:{self.proxy_port}'
            ]
            
            # 根据配置添加SSL/TLS相关参数
            if self.ignore_certificate_errors:
                launch_args.extend([
                    '--ignore-certificate-errors',
                    '--ignore-certificate-errors-spki-list',
                    '--ignore-certificate-errors-skip-list'
                ])
            
            if self.ignore_ssl_errors:
                launch_args.append('--ignore-ssl-errors')
            
            if self.allow_insecure_content:
                launch_args.extend([
                    '--allow-running-insecure-content',
                    '--disable-extensions-except',
                    '--disable-extensions-file-access-check'
                ])
            
            if self.reduce_security_for_testing:
                launch_args.append('--reduce-security-for-testing')
            
            logger.info(f"使用代理服务器: http://127.0.0.1:{self.proxy_port}")
            
            # 浏览器启动参数
            launch_options = {
                'headless': self.headless,
                'args': launch_args
            }
            
            self.browser = await self.playwright.chromium.launch(**launch_options)
            logger.info("浏览器启动成功")
            
            return self.browser
            
        except Exception as e:
            logger.error(f"浏览器启动失败: {e}")
            raise
    
    async def create_context(self) -> BrowserContext:
        """
        创建浏览器上下文
        
        Returns:
            BrowserContext: 浏览器上下文
        """
        try:
            if not self.browser:
                await self.start_browser()
            
            # 上下文配置
            context_options = {
                'viewport': self.viewport,
                'user_agent': self.user_agent,
                'ignore_https_errors': True,
                'java_script_enabled': True
            }
            
            self.context = await self.browser.new_context(**context_options)
            
            # 设置默认超时时间
            self.context.set_default_timeout(self.wait_timeout)
            if self.cookies_path:
                raw_cookies = json.load(open(self.cookies_path, 'r'))
                playwright_cookies = convert_cookies_for_playwright(raw_cookies)

                await self.set_cookies(playwright_cookies)
            
            logger.info("浏览器上下文创建成功")
            return self.context
            
        except Exception as e:
            logger.error(f"创建浏览器上下文失败: {e}")
            raise
    
    async def create_page(self) -> Page:
        """
        创建新页面
        
        Returns:
            Page: 页面实例
        """
        try:
            if not self.context:
                await self.create_context()
            
            self.page = await self.context.new_page()
            
            # 设置页面事件监听
            await self._setup_page_listeners()
            
            logger.info("页面创建成功")
            return self.page
            
        except Exception as e:
            logger.error(f"创建页面失败: {e}")
            raise
    
    async def navigate_to_page(self, url: str) -> Page:
        """
        导航到指定页面
        
        Args:
            url: 目标URL
            
        Returns:
            Page: 页面实例
        """
        try:
            if not self.page:
                await self.create_page()
            
            logger.info(f"正在导航到: {url}")
            await self.page.goto(url, wait_until='networkidle')
            
            # 等待页面加载完成
            await self.page.wait_for_load_state('domcontentloaded')
            
            logger.info(f"页面导航成功: {url}")
            return self.page
            
        except Exception as e:
            logger.error(f"页面导航失败: {e}")
            raise
    
    async def wait_for_login(self, timeout: int = 60) -> bool:
        """
        等待用户登录
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            bool: 是否登录成功
        """
        try:
            logger.info("等待用户登录...")
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # 检查是否已登录（通过URL变化或特定元素判断）
                current_url = self.page.url
                
                # 检查登录状态的几种方式
                login_indicators = [
                    # URL包含用户相关路径
                    '/user/' in current_url,
                    # 页面包含用户头像或用户名
                    await self._check_login_elements()
                ]
                
                if any(login_indicators):
                    logger.info("检测到用户已登录")
                    
                    # 自动保存cookies（如果配置启用）
                    # await self.auto_save_cookies(current_url)
                    
                    return True
                
                await asyncio.sleep(2)  # 每2秒检查一次
            
            logger.warning(f"登录等待超时 ({timeout}秒)")
            return False
            
        except Exception as e:
            logger.error(f"等待登录过程中出错: {e}")
            return False
    
    async def _check_login_elements(self) -> bool:
        """
        检查页面中的登录状态元素
        
        Returns:
            bool: 是否检测到登录状态
        """
        try:
            # 检查常见的登录状态元素
            login_selectors = [
                '[data-testid="user-avatar"]',  # 用户头像
                '.user-info',  # 用户信息
                '.avatar',  # 头像
                '[class*="avatar"]',  # 包含avatar的类名
            ]
            
            for selector in login_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    return True
            
            return False
            
        except Exception:
            return False
    
    async def scroll_page(self, scroll_count: int = 3, interval: float = 2.0):
        """
        滚动页面以加载更多内容
        
        Args:
            scroll_count: 滚动次数
            interval: 滚动间隔（秒）
        """
        try:
            logger.info(f"开始滚动页面，滚动{scroll_count}次")
            
            for i in range(scroll_count):
                # 滚动到页面底部
                await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                
                # 等待内容加载
                await asyncio.sleep(interval)
                
                logger.debug(f"完成第{i+1}次滚动")
            
            logger.info("页面滚动完成")
            
        except Exception as e:
            logger.error(f"页面滚动失败: {e}")
    
    async def click_element(self, selector: str, timeout: int = 30000, wait_for_visible: bool = True) -> bool:
        """
        点击页面元素
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（毫秒）
            wait_for_visible: 是否等待元素可见
            
        Returns:
            bool: 是否点击成功
        """
        try:
            logger.info(f"尝试点击元素: {selector}")
            
            if wait_for_visible:
                await self.page.wait_for_selector(selector, timeout=timeout, state='visible')
            
            await self.page.click(selector, timeout=timeout)
            logger.info(f"成功点击元素: {selector}")
            return True
            
        except PlaywrightTimeoutError:
            logger.warning(f"点击元素超时: {selector}")
            return False
        except Exception as e:
            logger.error(f"点击元素失败: {selector}, 错误: {e}")
            return False
    
    async def wait_for_element(self, selector: str, timeout: int = 30000, state: str = 'visible') -> bool:
        """
        等待元素出现
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（毫秒）
            state: 元素状态 ('attached', 'detached', 'visible', 'hidden')
            
        Returns:
            bool: 是否找到元素
        """
        try:
            logger.info(f"等待元素: {selector}, 状态: {state}")
            await self.page.wait_for_selector(selector, timeout=timeout, state=state)
            logger.info(f"元素已出现: {selector}")
            return True
            
        except PlaywrightTimeoutError:
            logger.warning(f"等待元素超时: {selector}")
            return False
        except Exception as e:
            logger.error(f"等待元素失败: {selector}, 错误: {e}")
            return False
    
    async def fill_input(self, selector: str, value: str, timeout: int = 30000) -> bool:
        """
        填写输入框
        
        Args:
            selector: 输入框选择器
            value: 要填写的值
            timeout: 超时时间（毫秒）
            
        Returns:
            bool: 是否填写成功
        """
        try:
            logger.info(f"填写输入框: {selector}")
            await self.page.wait_for_selector(selector, timeout=timeout)
            await self.page.fill(selector, value)
            logger.info(f"成功填写输入框: {selector}")
            return True
            
        except PlaywrightTimeoutError:
            logger.warning(f"填写输入框超时: {selector}")
            return False
        except Exception as e:
            logger.error(f"填写输入框失败: {selector}, 错误: {e}")
            return False
    
    async def get_element_text(self, selector: str, timeout: int = 30000) -> Optional[str]:
        """
        获取元素文本内容
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（毫秒）
            
        Returns:
            Optional[str]: 元素文本内容，失败返回None
        """
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            text = await self.page.text_content(selector)
            logger.debug(f"获取元素文本: {selector} -> {text}")
            return text
            
        except PlaywrightTimeoutError:
            logger.warning(f"获取元素文本超时: {selector}")
            return None
        except Exception as e:
            logger.error(f"获取元素文本失败: {selector}, 错误: {e}")
            return None
    
    async def get_element_attribute(self, selector: str, attribute: str, timeout: int = 30000) -> Optional[str]:
        """
        获取元素属性值
        
        Args:
            selector: 元素选择器
            attribute: 属性名
            timeout: 超时时间（毫秒）
            
        Returns:
            Optional[str]: 属性值，失败返回None
        """
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            value = await self.page.get_attribute(selector, attribute)
            logger.debug(f"获取元素属性: {selector}[{attribute}] -> {value}")
            return value
            
        except PlaywrightTimeoutError:
            logger.warning(f"获取元素属性超时: {selector}[{attribute}]")
            return None
        except Exception as e:
            logger.error(f"获取元素属性失败: {selector}[{attribute}], 错误: {e}")
            return None
    
    async def execute_browser_action(self, action_config: Dict[str, Any]) -> bool:
        """
        执行浏览器动作配置
        
        Args:
            action_config: 动作配置字典
            
        Returns:
            bool: 是否执行成功
        """
        try:
            action_type = action_config.get('type')
            
            if action_type == 'click':
                selector = action_config.get('selector')
                timeout = action_config.get('timeout', 30000)
                return await self.click_element(selector, timeout)
                
            elif action_type == 'scroll':
                count = action_config.get('count', 3)
                interval = action_config.get('interval', 2.0)
                await self.scroll_page(count, interval)
                return True
                
            elif action_type == 'wait':
                selector = action_config.get('selector')
                timeout = action_config.get('timeout', 30000)
                state = action_config.get('state', 'visible')
                return await self.wait_for_element(selector, timeout, state)
                
            elif action_type == 'fill':
                selector = action_config.get('selector')
                value = action_config.get('value', '')
                timeout = action_config.get('timeout', 30000)
                return await self.fill_input(selector, value, timeout)
                
            elif action_type == 'navigate':
                url = action_config.get('url')
                await self.navigate_to_page(url)
                return True
                
            else:
                logger.warning(f"未知的动作类型: {action_type}")
                return False
                
        except Exception as e:
            logger.error(f"执行浏览器动作失败: {e}")
            return False
    
    async def execute_action_sequence(self, actions: List[Dict[str, Any]]) -> bool:
        """
        执行一系列浏览器动作
        
        Args:
            actions: 动作配置列表
            
        Returns:
            bool: 是否全部执行成功
        """
        try:
            logger.info(f"开始执行动作序列，共{len(actions)}个动作")
            
            for i, action in enumerate(actions):
                logger.info(f"执行第{i+1}个动作: {action.get('type', 'unknown')}")
                
                success = await self.execute_browser_action(action)
                if not success:
                    logger.error(f"第{i+1}个动作执行失败")
                    return False
                
                # 动作间延迟
                delay = action.get('delay', 1.0)
                if delay > 0:
                    await asyncio.sleep(delay)
            
            logger.info("动作序列执行完成")
            return True
            
        except Exception as e:
            logger.error(f"执行动作序列失败: {e}")
            return False
    
    async def take_screenshot(self, path: Optional[str] = None, full_page: bool = True) -> Optional[bytes]:
        """
        截取页面截图
        
        Args:
            path: 保存路径，为None时返回字节数据
            full_page: 是否截取整个页面
            
        Returns:
            Optional[bytes]: 截图字节数据（当path为None时）
        """
        try:
            screenshot_options = {'full_page': full_page}
            if path:
                screenshot_options['path'] = path
                await self.page.screenshot(**screenshot_options)
                logger.info(f"截图已保存到: {path}")
                return None
            else:
                screenshot_data = await self.page.screenshot(**screenshot_options)
                logger.info("截图已生成")
                return screenshot_data
                
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return None
    
    async def _setup_page_listeners(self):
        """
        设置页面事件监听器
        """
        try:
            # 监听控制台消息
            self.page.on('console', lambda msg: logger.debug(f"Console: {msg.text}"))
            
            # 监听页面错误
            self.page.on('pageerror', lambda error: logger.error(f"Page error: {error}"))
            
            # 监听请求失败
            self.page.on('requestfailed', 
                        lambda request: logger.warning(f"Request failed: {request.url}"))
            
        except Exception as e:
            logger.error(f"设置页面监听器失败: {e}")
    
    async def get_cookies(self) -> list:
        """
        获取当前页面的cookies
        
        Returns:
            list: cookies列表
        """
        try:
            if self.context:
                cookies = await self.context.cookies()
                logger.info(f"获取到{len(cookies)}个cookies")
                return cookies
            return []
            
        except Exception as e:
            logger.error(f"获取cookies失败: {e}")
            return []
    
    async def set_cookies(self, cookies: list):
        """
        设置cookies
        
        Args:
            cookies: cookies列表
        """
        try:
            if self.context and cookies:
                await self.context.add_cookies(cookies)
                logger.info(f"设置了{len(cookies)}个cookies")
                
        except Exception as e:
            logger.error(f"设置cookies失败: {e}")
    
    async def close(self):
        """
        关闭浏览器和相关资源
        """
        try:
            if self.page:
                await self.page.close()
                logger.debug("页面已关闭")
            
            if self.context:
                await self.context.close()
                logger.debug("浏览器上下文已关闭")
            
            if self.browser:
                await self.browser.close()
                logger.debug("浏览器已关闭")
            
            if self.playwright:
                await self.playwright.stop()
                logger.debug("Playwright已停止")
            
            logger.info("浏览器管理器已完全关闭")
            
        except Exception as e:
            logger.error(f"关闭浏览器时出错: {e}")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()


# 使用示例
if __name__ == "__main__":
    async def test_browser_manager():
        config = {
            'headless': False,
            'proxy_port': 8080,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'viewport': {'width': 1920, 'height': 1080},
            'wait_timeout': 30000
        }
        
        async with BrowserManager(config) as browser_manager:
            page = await browser_manager.navigate_to_page('https://www.xiaohongshu.com/explore')
            await browser_manager.wait_for_login()
            await browser_manager.scroll_page(3, 2)
    
    # 运行测试
    asyncio.run(test_browser_manager())