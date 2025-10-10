#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速启动脚本

这个脚本提供了一个简单的命令行界面，
让用户可以快速选择和运行不同的爬虫配置。
"""

import asyncio
import argparse
import sys
from typing import Optional, Callable, Any
from pathlib import Path

# 导入爬虫相关模块
from simple_proxy_crawler import SimpleCrawler
from proxy_crawler import AdvancedCrawler
from config_examples import get_config_by_name, list_available_configs


def print_banner():
    """打印启动横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    高效代理爬虫系统                          ║
║                  Advanced Proxy Crawler                     ║
╠══════════════════════════════════════════════════════════════╣
║  功能特点:                                                   ║
║  • 自动代理配置 (mitmproxy/Proxifier)                       ║
║  • 智能API拦截和数据解析                                     ║
║  • 支持多种网站类型 (电商/社交/金融/新闻等)                  ║
║  • 高性能并发处理                                           ║
║  • 灵活的数据过滤和处理                                     ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_help():
    """打印帮助信息"""
    help_text = """
使用方法:
  python quick_start.py [选项]

选项:
  -h, --help              显示此帮助信息
  -l, --list              列出所有可用的配置
  -c, --config CONFIG     使用指定的配置运行爬虫
  -s, --simple            使用简化版爬虫
  -a, --advanced          使用完整版爬虫 (默认)
  -u, --url URL           指定要访问的URL
  -p, --port PORT         指定代理端口 (默认: 8080)
  --headless              使用无头模式运行浏览器
  --no-headless           显示浏览器窗口 (默认)

配置示例:
  python quick_start.py -c ecommerce          # 运行电商爬虫
  python quick_start.py -c news -s            # 运行简化版新闻爬虫
  python quick_start.py -c test --headless    # 无头模式运行测试爬虫
  python quick_start.py -u https://example.com # 访问指定URL

可用配置:
"""
    print(help_text)
    
    configs = list_available_configs()
    for i, config in enumerate(configs, 1):
        print(f"  {i:2d}. {config}")
    
    print("\n更多信息请查看 README.md 文件")


def interactive_config_selection() -> str:
    """交互式配置选择"""
    configs = list_available_configs()
    
    print("\n可用的爬虫配置:")
    for i, config in enumerate(configs, 1):
        print(f"  {i:2d}. {config}")
    
    while True:
        try:
            choice = input("\n请选择配置 (输入数字或配置名称): ").strip()
            
            # 尝试按数字选择
            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(configs):
                    return configs[index]
                else:
                    print(f"无效的数字，请输入 1-{len(configs)} 之间的数字")
                    continue
            
            # 尝试按名称选择
            if choice in configs:
                return choice
            
            # 模糊匹配
            matches = [c for c in configs if choice.lower() in c.lower()]
            if len(matches) == 1:
                return matches[0]
            elif len(matches) > 1:
                print(f"找到多个匹配: {', '.join(matches)}，请输入更精确的名称")
            else:
                print(f"未找到配置 '{choice}'，请重新选择")
                
        except KeyboardInterrupt:
            print("\n用户取消操作")
            sys.exit(0)
        except Exception as e:
            print(f"输入错误: {e}")


def get_custom_url() -> Optional[str]:
    """获取自定义URL"""
    while True:
        try:
            url = input("请输入要访问的URL (回车跳过): ").strip()
            if not url:
                return None
            
            # 简单的URL验证
            if not (url.startswith('http://') or url.startswith('https://')):
                url = 'https://' + url
            
            return url
            
        except KeyboardInterrupt:
            print("\n用户取消操作")
            return None
        except Exception as e:
            print(f"输入错误: {e}")


async def run_simple_crawler(config_name: str, custom_url: Optional[str] = None, proxy_port: int = 8080):
    """运行简化版爬虫"""
    print(f"\n启动简化版爬虫 (配置: {config_name})...")
    
    try:
        # 创建简化版爬虫
        crawler = SimpleCrawler(
            proxy_port=proxy_port,
            output_dir=f"./data/{config_name}"
        )
        
        # 定义操作函数
        async def simple_operations(page):
            if custom_url:
                print(f"访问自定义URL: {custom_url}")
                await page.goto(custom_url)
                await page.wait_for_timeout(5000)
            else:
                # 根据配置类型访问不同的默认页面
                default_urls = {
                    'ecommerce': 'https://www.taobao.com',
                    'social_media': 'https://weibo.com',
                    'news': 'https://news.sina.com.cn',
                    'financial': 'https://www.eastmoney.com',
                    'test': 'https://jsonplaceholder.typicode.com/posts'
                }
                
                url = default_urls.get(config_name, 'https://httpbin.org/json')
                print(f"访问默认URL: {url}")
                await page.goto(url)
                await page.wait_for_timeout(5000)
        
        # 运行爬虫
        await crawler.run(simple_operations)
        print(f"简化版爬虫完成，数据保存在: ./data/{config_name}")
        
    except Exception as e:
        print(f"运行简化版爬虫时出错: {e}")


async def run_advanced_crawler(config_name: str, custom_url: Optional[str] = None, headless: bool = False):
    """运行完整版爬虫"""
    print(f"\n启动完整版爬虫 (配置: {config_name})...")
    
    try:
        # 获取配置
        config = get_config_by_name(config_name)
        
        # 应用命令行参数
        if headless is not None:
            config.headless = headless
        
        # 创建完整版爬虫
        crawler = AdvancedCrawler(config)
        
        # 定义操作函数
        async def advanced_operations(page):
            if custom_url:
                print(f"访问自定义URL: {custom_url}")
                await page.goto(custom_url)
                await page.wait_for_timeout(5000)
            else:
                # 根据配置类型执行不同的操作
                if config_name == 'ecommerce':
                    await page.goto("https://www.taobao.com")
                    await page.wait_for_timeout(3000)
                    
                    # 搜索商品
                    search_box = await page.query_selector("#q")
                    if search_box:
                        await search_box.fill("手机")
                        await page.keyboard.press("Enter")
                        await page.wait_for_timeout(5000)
                
                elif config_name == 'news':
                    await page.goto("https://news.sina.com.cn")
                    await page.wait_for_timeout(3000)
                    
                    # 滚动加载更多新闻
                    for i in range(3):
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await page.wait_for_timeout(2000)
                
                elif config_name == 'test':
                    test_urls = [
                        "https://jsonplaceholder.typicode.com/posts",
                        "https://jsonplaceholder.typicode.com/users",
                        "https://httpbin.org/json"
                    ]
                    
                    for url in test_urls:
                        print(f"访问测试URL: {url}")
                        await page.goto(url)
                        await page.wait_for_timeout(2000)
                
                else:
                    # 默认操作
                    await page.goto("https://httpbin.org/json")
                    await page.wait_for_timeout(3000)
        
        # 运行爬虫
        await crawler.run(advanced_operations)
        print(f"完整版爬虫完成，数据保存在: {config.output_dir}")
        
    except Exception as e:
        print(f"运行完整版爬虫时出错: {e}")


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='高效代理爬虫系统快速启动工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例:
  python quick_start.py -c ecommerce
  python quick_start.py -c test -s
  python quick_start.py -u https://example.com
  python quick_start.py --list"""
    )
    
    parser.add_argument('-l', '--list', action='store_true',
                       help='列出所有可用的配置')
    parser.add_argument('-c', '--config', type=str,
                       help='使用指定的配置运行爬虫')
    parser.add_argument('-s', '--simple', action='store_true',
                       help='使用简化版爬虫')
    parser.add_argument('-a', '--advanced', action='store_true',
                       help='使用完整版爬虫 (默认)')
    parser.add_argument('-u', '--url', type=str,
                       help='指定要访问的URL')
    parser.add_argument('-p', '--port', type=int, default=8080,
                       help='指定代理端口 (默认: 8080)')
    parser.add_argument('--headless', action='store_true',
                       help='使用无头模式运行浏览器')
    parser.add_argument('--no-headless', action='store_true',
                       help='显示浏览器窗口 (默认)')
    
    args = parser.parse_args()
    
    # 打印横幅
    print_banner()
    
    # 处理命令行参数
    if args.list:
        print("\n可用的爬虫配置:")
        configs = list_available_configs()
        for i, config in enumerate(configs, 1):
            print(f"  {i:2d}. {config}")
        return
    
    # 确定使用的配置
    config_name = args.config
    if not config_name:
        config_name = interactive_config_selection()
    
    # 验证配置
    available_configs = list_available_configs()
    if config_name not in available_configs:
        print(f"错误: 未知的配置 '{config_name}'")
        print(f"可用配置: {', '.join(available_configs)}")
        return
    
    # 确定URL
    custom_url = args.url
    if not custom_url and not args.config:
        custom_url = get_custom_url()
    
    # 确定爬虫类型
    use_simple = args.simple or (not args.advanced and not args.simple)
    if args.advanced:
        use_simple = False
    
    # 确定浏览器模式
    headless = None
    if args.headless:
        headless = True
    elif args.no_headless:
        headless = False
    
    # 运行爬虫
    try:
        if use_simple:
            asyncio.run(run_simple_crawler(config_name, custom_url, args.port))
        else:
            asyncio.run(run_advanced_crawler(config_name, custom_url, headless))
    
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"运行出错: {e}")
        print("\n如需帮助，请运行: python quick_start.py -h")


if __name__ == "__main__":
    main()