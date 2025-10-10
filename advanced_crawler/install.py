#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安装脚本

这个脚本帮助用户快速安装和配置高效代理爬虫系统的所有依赖。
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import List, Tuple


def print_banner():
    """打印安装横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                 高效代理爬虫系统安装程序                     ║
║               Advanced Proxy Crawler Installer              ║
╠══════════════════════════════════════════════════════════════╣
║  此脚本将自动安装所有必需的依赖包和配置环境                  ║
║  包括: Python包、Playwright浏览器、mitmproxy等               ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def check_python_version() -> bool:
    """检查Python版本"""
    print("检查Python版本...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python版本过低: {version.major}.{version.minor}")
        print("   需要Python 3.8或更高版本")
        return False
    
    print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
    return True


def check_pip() -> bool:
    """检查pip是否可用"""
    print("检查pip...")
    
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                              capture_output=True, text=True, check=True)
        print(f"✅ pip版本: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError:
        print("❌ pip不可用")
        return False


def install_requirements() -> bool:
    """安装Python依赖包"""
    print("\n安装Python依赖包...")
    
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ requirements.txt文件不存在")
        return False
    
    try:
        # 升级pip
        print("升级pip...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True)
        
        # 安装依赖
        print("安装依赖包...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)], 
                      check=True)
        
        print("✅ Python依赖包安装完成")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 安装依赖包失败: {e}")
        return False


def install_playwright_browsers() -> bool:
    """安装Playwright浏览器"""
    print("\n安装Playwright浏览器...")
    
    try:
        # 安装浏览器
        subprocess.run([sys.executable, "-m", "playwright", "install"], check=True)
        
        # 安装系统依赖（Linux）
        if platform.system() == "Linux":
            print("安装系统依赖...")
            subprocess.run([sys.executable, "-m", "playwright", "install-deps"], check=True)
        
        print("✅ Playwright浏览器安装完成")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 安装Playwright浏览器失败: {e}")
        return False


def create_directories() -> bool:
    """创建必要的目录"""
    print("\n创建目录结构...")
    
    directories = [
        "data",
        "logs",
        "config",
        "output",
        "temp"
    ]
    
    try:
        base_path = Path(__file__).parent
        
        for directory in directories:
            dir_path = base_path / directory
            dir_path.mkdir(exist_ok=True)
            print(f"✅ 创建目录: {directory}")
        
        return True
        
    except Exception as e:
        print(f"❌ 创建目录失败: {e}")
        return False


def create_config_files() -> bool:
    """创建配置文件"""
    print("\n创建配置文件...")
    
    try:
        base_path = Path(__file__).parent
        config_path = base_path / "config"
        
        # 创建默认配置文件
        default_config = """
# 默认配置文件
# 用户可以根据需要修改这些设置

[proxy]
host = 127.0.0.1
port = 8080
type = mitmproxy

[browser]
headless = false
type = chromium
timeout = 30

[data]
output_dir = ./data
save_raw_data = true
save_parsed_data = true

[performance]
max_concurrent = 3
request_delay = 1.0

[logging]
level = INFO
file = ./logs/crawler.log
"""
        
        config_file = config_path / "default.ini"
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(default_config)
        
        print("✅ 创建默认配置文件")
        
        # 创建环境变量文件
        env_content = """
# 环境变量配置
# 复制此文件为 .env 并根据需要修改

# 代理设置
PROXY_HOST=127.0.0.1
PROXY_PORT=8080

# 浏览器设置
BROWSER_HEADLESS=false
BROWSER_TIMEOUT=30

# 数据设置
OUTPUT_DIR=./data
SAVE_RAW_DATA=true

# 性能设置
MAX_CONCURRENT=3
REQUEST_DELAY=1.0

# 日志设置
LOG_LEVEL=INFO
LOG_FILE=./logs/crawler.log
"""
        
        env_file = config_path / "env.example"
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("✅ 创建环境变量示例文件")
        
        return True
        
    except Exception as e:
        print(f"❌ 创建配置文件失败: {e}")
        return False


def test_installation() -> bool:
    """测试安装是否成功"""
    print("\n测试安装...")
    
    tests = [
        ("导入mitmproxy", "import mitmproxy"),
        ("导入playwright", "import playwright"),
        ("导入requests", "import requests"),
        ("导入asyncio", "import asyncio"),
        ("导入json", "import json"),
    ]
    
    all_passed = True
    
    for test_name, test_code in tests:
        try:
            subprocess.run([sys.executable, "-c", test_code], 
                          check=True, capture_output=True)
            print(f"✅ {test_name}")
        except subprocess.CalledProcessError:
            print(f"❌ {test_name}")
            all_passed = False
    
    return all_passed


def check_system_requirements() -> List[Tuple[str, bool]]:
    """检查系统要求"""
    print("\n检查系统要求...")
    
    requirements = []
    
    # 检查操作系统
    os_name = platform.system()
    print(f"操作系统: {os_name}")
    requirements.append((f"操作系统: {os_name}", True))
    
    # 检查内存（简单估算）
    try:
        if os_name == "Linux":
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
                for line in meminfo.split('\n'):
                    if 'MemTotal:' in line:
                        mem_kb = int(line.split()[1])
                        mem_gb = mem_kb / 1024 / 1024
                        sufficient = mem_gb >= 2
                        print(f"内存: {mem_gb:.1f}GB")
                        requirements.append((f"内存: {mem_gb:.1f}GB", sufficient))
                        break
        else:
            requirements.append(("内存检查", True))  # 其他系统暂时跳过
    except:
        requirements.append(("内存检查", True))  # 检查失败时假设满足
    
    # 检查磁盘空间
    try:
        disk_usage = os.statvfs('.')
        free_bytes = disk_usage.f_frsize * disk_usage.f_bavail
        free_gb = free_bytes / 1024 / 1024 / 1024
        sufficient = free_gb >= 1
        print(f"可用磁盘空间: {free_gb:.1f}GB")
        requirements.append((f"磁盘空间: {free_gb:.1f}GB", sufficient))
    except:
        requirements.append(("磁盘空间检查", True))
    
    return requirements


def print_installation_summary(success: bool):
    """打印安装总结"""
    if success:
        summary = """
╔══════════════════════════════════════════════════════════════╗
║                      安装成功完成！                         ║
╠══════════════════════════════════════════════════════════════╣
║  接下来你可以:                                              ║
║                                                              ║
║  1. 运行快速启动脚本:                                       ║
║     python quick_start.py                                   ║
║                                                              ║
║  2. 运行简化版爬虫:                                         ║
║     python simple_proxy_crawler.py                          ║
║                                                              ║
║  3. 查看使用示例:                                           ║
║     python examples.py                                      ║
║                                                              ║
║  4. 阅读详细文档:                                           ║
║     cat README.md                                           ║
║                                                              ║
║  5. 查看配置示例:                                           ║
║     python config_examples.py                               ║
╚══════════════════════════════════════════════════════════════╝
"""
    else:
        summary = """
╔══════════════════════════════════════════════════════════════╗
║                      安装遇到问题                           ║
╠══════════════════════════════════════════════════════════════╣
║  请检查以下事项:                                            ║
║                                                              ║
║  1. 确保Python版本 >= 3.8                                  ║
║  2. 确保网络连接正常                                        ║
║  3. 确保有足够的磁盘空间                                    ║
║  4. 尝试手动安装依赖:                                       ║
║     pip install -r requirements.txt                        ║
║     python -m playwright install                           ║
║                                                              ║
║  如果问题持续存在，请查看错误信息或寻求帮助                  ║
╚══════════════════════════════════════════════════════════════╝
"""
    
    print(summary)


def main():
    """主安装函数"""
    print_banner()
    
    # 检查系统要求
    system_reqs = check_system_requirements()
    
    # 检查Python版本
    if not check_python_version():
        print_installation_summary(False)
        return False
    
    # 检查pip
    if not check_pip():
        print_installation_summary(False)
        return False
    
    # 安装步骤
    steps = [
        ("安装Python依赖包", install_requirements),
        ("安装Playwright浏览器", install_playwright_browsers),
        ("创建目录结构", create_directories),
        ("创建配置文件", create_config_files),
        ("测试安装", test_installation)
    ]
    
    success = True
    
    for step_name, step_func in steps:
        print(f"\n{'='*60}")
        print(f"执行: {step_name}")
        print(f"{'='*60}")
        
        if not step_func():
            print(f"❌ {step_name} 失败")
            success = False
            break
        else:
            print(f"✅ {step_name} 完成")
    
    # 打印安装总结
    print_installation_summary(success)
    
    return success


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n用户中断安装")
        sys.exit(1)
    except Exception as e:
        print(f"\n安装过程中出现未预期的错误: {e}")
        sys.exit(1)