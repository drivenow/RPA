#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键启动脚本

这是高效代理爬虫系统的主启动脚本，提供了最简单的使用方式。
用户只需运行这个脚本，就能快速开始使用爬虫系统。
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path
from typing import Optional


def print_welcome():
    """打印欢迎信息"""
    welcome = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🚀 高效代理爬虫系统 - 一键启动                           ║
║       Advanced Proxy Crawler - One-Click Launch             ║
║                                                              ║
║    ✨ 特点：流量拦截 + 智能解析 + 自动化操作                ║
║    🎯 优势：高效稳定，无惧页面结构变化                      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(welcome)


def check_installation() -> bool:
    """检查系统是否已安装"""
    print("检查系统安装状态...")
    
    # 检查核心文件
    required_files = [
        "proxy_crawler.py",
        "simple_proxy_crawler.py",
        "config_examples.py",
        "requirements.txt"
    ]
    
    base_path = Path(__file__).parent
    missing_files = []
    
    for file_name in required_files:
        if not (base_path / file_name).exists():
            missing_files.append(file_name)
    
    if missing_files:
        print(f"❌ 缺少文件: {', '.join(missing_files)}")
        return False
    
    # 检查Python包
    try:
        import mitmproxy
        import playwright
        import requests
        print("✅ 核心依赖已安装")
        return True
    except ImportError as e:
        print(f"❌ 缺少Python包: {e}")
        return False


def run_installation() -> bool:
    """运行安装程序"""
    print("\n开始安装系统...")
    
    try:
        # 运行安装脚本
        result = subprocess.run(
            [sys.executable, "install.py"],
            cwd=Path(__file__).parent,
            capture_output=False
        )
        
        return result.returncode == 0
    except Exception as e:
        print(f"安装失败: {e}")
        return False


def show_menu() -> str:
    """显示主菜单"""
    menu = """
请选择操作:

  🚀 快速开始
    1. 运行测试爬虫 (推荐新手)
    2. 电商数据采集
    3. 新闻资讯采集
    4. 金融数据采集
    5. 社交媒体采集

  🛠️ 高级选项
    6. 自定义配置
    7. 查看所有配置
    8. 运行示例代码

  🔧 系统工具
    9. 系统测试
    10. 重新安装
    11. 查看帮助

    0. 退出程序
"""
    
    print(menu)
    
    while True:
        try:
            choice = input("请输入选项编号 (0-11): ").strip()
            if choice in [str(i) for i in range(12)]:
                return choice
            else:
                print("无效选项，请输入 0-11 之间的数字")
        except KeyboardInterrupt:
            print("\n用户取消操作")
            return "0"
        except Exception:
            print("输入错误，请重试")


def run_quick_start(config_name: str, simple: bool = True) -> bool:
    """运行快速启动"""
    try:
        cmd = [sys.executable, "quick_start.py", "-c", config_name]
        if simple:
            cmd.append("-s")
        
        print(f"\n启动 {config_name} 爬虫...")
        print("提示: 按 Ctrl+C 可以停止爬虫")
        
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent
        )
        
        return result.returncode == 0
    except KeyboardInterrupt:
        print("\n用户停止爬虫")
        return True
    except Exception as e:
        print(f"运行失败: {e}")
        return False


def run_custom_config() -> bool:
    """运行自定义配置"""
    print("\n=== 自定义配置 ===")
    
    # 获取用户输入
    url = input("请输入要访问的URL: ").strip()
    if not url:
        print("URL不能为空")
        return False
    
    # 选择爬虫类型
    crawler_type = input("选择爬虫类型 (1=简化版, 2=完整版) [1]: ").strip() or "1"
    
    try:
        cmd = [sys.executable, "quick_start.py", "-u", url]
        if crawler_type == "1":
            cmd.append("-s")
        
        print(f"\n访问 {url}...")
        result = subprocess.run(cmd, cwd=Path(__file__).parent)
        return result.returncode == 0
    except Exception as e:
        print(f"运行失败: {e}")
        return False


def show_all_configs() -> bool:
    """显示所有配置"""
    try:
        subprocess.run(
            [sys.executable, "quick_start.py", "--list"],
            cwd=Path(__file__).parent
        )
        return True
    except Exception as e:
        print(f"显示配置失败: {e}")
        return False


def run_examples() -> bool:
    """运行示例代码"""
    try:
        print("\n运行示例代码...")
        print("注意: 示例代码可能需要网络连接")
        
        result = subprocess.run(
            [sys.executable, "examples.py"],
            cwd=Path(__file__).parent
        )
        return result.returncode == 0
    except Exception as e:
        print(f"运行示例失败: {e}")
        return False


def run_system_test() -> bool:
    """运行系统测试"""
    try:
        print("\n运行系统测试...")
        result = subprocess.run(
            [sys.executable, "test_system.py"],
            cwd=Path(__file__).parent
        )
        return result.returncode == 0
    except Exception as e:
        print(f"系统测试失败: {e}")
        return False


def show_help() -> bool:
    """显示帮助信息"""
    help_text = """
=== 高效代理爬虫系统帮助 ===

📖 基本概念:
  本系统通过代理服务器拦截网页的API请求，直接获取结构化数据，
  避免了传统爬虫解析HTML的复杂性和不稳定性。

🚀 快速开始:
  1. 选择"运行测试爬虫"进行初次体验
  2. 根据需要选择对应的网站类型配置
  3. 查看生成的数据文件了解结果

🔧 工作原理:
  1. 启动mitmproxy代理服务器
  2. 配置浏览器使用代理
  3. 访问目标网站并执行操作
  4. 自动拦截API请求和响应
  5. 解析并保存结构化数据

📁 输出文件:
  - 原始数据: data/raw/
  - 处理后数据: data/processed/
  - 日志文件: logs/

⚙️ 配置文件:
  - 预定义配置: config_examples.py
  - 自定义配置: 可通过代码修改

🛠️ 故障排除:
  1. 运行"系统测试"检查安装
  2. 查看日志文件了解错误
  3. 确保网络连接正常
  4. 检查防火墙和代理设置

📚 更多信息:
  - README.md: 详细使用说明
  - PROJECT_OVERVIEW.md: 项目总览
  - examples.py: 代码示例

💡 提示:
  - 首次使用建议先运行测试爬虫
  - 注意遵守网站的使用条款
  - 合理控制访问频率
  - 定期更新系统和依赖
"""
    
    print(help_text)
    input("\n按回车键返回主菜单...")
    return True


def main():
    """主函数"""
    print_welcome()
    
    # 检查安装状态
    if not check_installation():
        print("\n系统未安装或安装不完整")
        install = input("是否现在安装？(y/N): ").strip().lower()
        
        if install == 'y':
            if not run_installation():
                print("安装失败，程序退出")
                return
            print("\n安装完成！")
        else:
            print("请先安装系统后再使用")
            return
    
    # 主循环
    while True:
        choice = show_menu()
        
        if choice == "0":
            print("\n感谢使用高效代理爬虫系统！")
            break
        
        elif choice == "1":
            run_quick_start("test", simple=True)
        
        elif choice == "2":
            run_quick_start("ecommerce", simple=True)
        
        elif choice == "3":
            run_quick_start("news", simple=True)
        
        elif choice == "4":
            run_quick_start("financial", simple=True)
        
        elif choice == "5":
            run_quick_start("social_media", simple=True)
        
        elif choice == "6":
            run_custom_config()
        
        elif choice == "7":
            show_all_configs()
        
        elif choice == "8":
            run_examples()
        
        elif choice == "9":
            run_system_test()
        
        elif choice == "10":
            if run_installation():
                print("\n重新安装完成！")
            else:
                print("\n重新安装失败")
        
        elif choice == "11":
            show_help()
        
        # 等待用户确认
        if choice != "0":
            input("\n按回车键继续...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断程序")
    except Exception as e:
        print(f"\n程序出现错误: {e}")
        print("请检查安装或联系技术支持")
    finally:
        print("程序结束")