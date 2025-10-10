# 小红书内容抓取系统

一个基于 Playwright 和 mitmproxy 的小红书内容抓取系统，支持自动化浏览器操作和 API 数据拦截。

## 功能特性

### 核心功能
- 🚀 **自动化浏览器操作**: 基于 Playwright 的无头浏览器自动化
- 🔍 **API 数据拦截**: 使用 mitmproxy 拦截和提取小红书 API 响应数据
- 📊 **数据处理**: 支持数据清洗、去重、转换和存储
- 🗄️ **多种存储方式**: 支持 MySQL 数据库和文件存储
- ⚙️ **配置化管理**: 基于 YAML 的灵活配置系统
- 🔄 **热重载**: 支持配置文件热重载，无需重启程序

### 技术特性
- 异步架构设计，高性能数据处理
- 模块化设计，易于扩展和维护
- 完善的错误处理和日志记录
- 支持代理功能的优雅降级
- 内存和数据库双重去重机制

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   XHSCrawler    │    │ BrowserManager  │    │  ProxyHandler   │
│   (主控制器)     │────│   (浏览器管理)   │    │   (代理处理)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ ConfigParser    │    │   Playwright    │    │   mitmproxy     │
│   (配置解析)     │    │   (浏览器驱动)   │    │   (代理服务)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                                             │
         │                                             │
         ▼                                             ▼
┌─────────────────┐                        ┌─────────────────┐
│ DataProcessor   │                        │     MySQL       │
│   (数据处理)     │────────────────────────│   (数据存储)     │
└─────────────────┘                        └─────────────────┘
```

## 安装说明

### 环境要求
- Python 3.8+
- Linux/macOS/Windows
- MySQL 5.7+ (可选)

### 安装步骤

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **安装 Playwright 浏览器驱动**
```bash
playwright install
```

3. **安装系统依赖** (Linux)
```bash
sudo playwright install-deps
# 或者
sudo apt-get install libnspr4 libnss3 libasound2
```

## 使用方法

### 基础使用

```python
import asyncio
from src.xhs_crawler import XHSCrawler

async def main():
    # 创建爬虫实例
    crawler = XHSCrawler('config/xiaohongshu.yaml')
    
    try:
        # 初始化组件
        await crawler.initialize()
        
        # 开始爬取
        await crawler.start_crawling()
        
    except Exception as e:
        print(f"爬取失败: {e}")
    finally:
        # 清理资源
        await crawler.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
```

### 运行示例

```bash
# 运行基础功能测试
python test_basic.py

# 运行完整示例
python examples/xiaohongshu_example.py
```

## 项目结构

```
tools_crawl/
├── src/                    # 源代码目录
│   ├── xhs_crawler.py      # 主控制器
│   ├── browser_manager.py  # 浏览器管理器
│   ├── proxy_handler.py    # 代理处理器
│   ├── config_parser.py    # 配置解析器
│   └── data_processor.py   # 数据处理器
├── config/                 # 配置文件目录
│   └── xiaohongshu.yaml    # 主配置文件
├── examples/               # 使用示例
│   └── xiaohongshu_example.py
├── data/                   # 数据目录
│   └── backup/             # 备份文件
├── requirements.txt        # 依赖列表
├── test_basic.py          # 基础功能测试
└── README.md              # 项目说明
```

## 注意事项

### 系统依赖
- 如果遇到 Playwright 浏览器启动失败，请安装系统依赖：
  ```bash
  sudo playwright install-deps
  ```

### mitmproxy 依赖
- 如果 mitmproxy 安装失败，系统会自动禁用代理功能
- 可以只使用浏览器自动化功能，不影响基本操作

### 数据库配置
- MySQL 数据库是可选的，可以只使用文件存储
- 确保数据库连接信息正确配置

### 登录要求
- 小红书需要登录才能获取完整数据
- 系统会等待用户手动登录，然后继续执行

## 许可证

本项目仅供学习和研究使用，请遵守相关网站的使用条款和法律法规。