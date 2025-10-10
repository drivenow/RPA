# 高效爬虫方案 - 基于代理流量抓包

这是一个基于代理流量抓包的高效爬虫解决方案，通过拦截网页的API请求来获取结构化数据，避免了传统爬虫解析HTML元素的不稳定性。

## 🚀 核心优势

1. **高效稳定**: 直接获取API返回的结构化数据，不受页面结构变化影响
2. **自动化程度高**: 结合浏览器自动化，可以模拟用户操作触发API请求
3. **数据质量好**: 获取的是原始API数据，格式规范，易于处理
4. **扩展性强**: 支持多种代理配置和自定义数据处理逻辑

## 📁 文件结构

```
advanced_crawler/
├── proxy_crawler.py          # 完整版爬虫（功能丰富）
├── simple_proxy_crawler.py   # 简化版爬虫（快速上手）
├── requirements.txt          # 依赖包列表
├── README.md                # 使用说明（本文件）
└── examples/                # 示例代码（可选）
```

## 🛠️ 安装配置

### 方法一：自动安装（推荐）

```bash
# 运行自动安装脚本
python install.py
```

安装脚本会自动完成以下操作：
- 检查Python版本和系统要求
- 安装所有Python依赖包
- 安装Playwright浏览器
- 创建必要的目录结构
- 生成默认配置文件
- 测试安装是否成功

### 方法二：手动安装

```bash
# 1. 安装Python依赖
pip install -r requirements.txt

# 2. 安装Playwright浏览器
python -m playwright install

# 3. 创建数据目录
mkdir -p data logs config output temp
```

### 2. 验证安装

```bash
# 测试mitmproxy
mitmdump --version

# 测试playwright
playwright --version
```

## 🎯 快速开始

### 方法一：使用快速启动脚本（推荐）

```bash
# 交互式选择配置
python quick_start.py

# 直接指定配置
python quick_start.py -c ecommerce    # 电商爬虫
python quick_start.py -c news         # 新闻爬虫
python quick_start.py -c test         # 测试爬虫

# 使用简化版
python quick_start.py -c test -s

# 访问自定义URL
python quick_start.py -u https://example.com

# 查看所有可用配置
python quick_start.py --list
```

### 方法二：直接使用简化版

```bash
# 运行简化版爬虫
python simple_proxy_crawler.py
```

程序会：
1. 启动代理服务器（默认端口8080）
2. 打开配置了代理的浏览器
3. 自动拦截并保存所有API响应数据

### 方法三：使用完整版

```python
from proxy_crawler import AdvancedCrawler
from config_examples import get_config_by_name
import asyncio

async def main():
    # 使用预定义配置
    config = get_config_by_name("ecommerce")
    
    # 或者自定义配置
    # config = CrawlerConfig(
    #     target_domains=["api.example.com"],
    #     target_apis=["/api/data"],
    #     output_dir="./data"
    # )
    
    # 创建爬虫
    crawler = AdvancedCrawler(config)
    
    # 定义操作
    async def operations(page):
        await page.goto("https://example.com")
        # 执行更多操作...
    
    # 运行
    await crawler.run(operations)

asyncio.run(main())
```

### 方法四：运行示例

```bash
# 运行所有示例
python examples.py

# 查看配置示例
python config_examples.py
```

## 🔧 配置说明

### 代理配置

```python
config = CrawlerConfig(
    proxy_type="mitmproxy",     # 代理类型
    proxy_host="127.0.0.1",    # 代理主机
    proxy_port=8080,           # 代理端口
    
    # 目标过滤
    target_domains=[           # 要拦截的域名
        "api.example.com",
        "data.website.com"
    ],
    target_apis=[              # 要拦截的API路径
        "/api/",
        "/data/",
        "/v1/"
    ],
    
    # 浏览器配置
    headless=False,            # 是否无头模式
    browser_type="chromium",   # 浏览器类型
    
    # 数据存储
    output_dir="./output",     # 输出目录
    save_raw_data=True,        # 保存原始数据
    save_parsed_data=True,     # 保存解析后数据
    
    # 性能配置
    max_concurrent=5,          # 最大并发数
    request_delay=1.0,         # 请求间隔
    timeout=30                 # 超时时间
)
```

### 自定义数据处理

```python
class CustomDataProcessor(DataProcessor):
    def _parse_data(self, data):
        """自定义数据解析逻辑"""
        if data.get("type") != "response":
            return None
            
        response_data = data.get("data")
        if not isinstance(response_data, dict):
            return None
            
        # 提取特定字段
        extracted = {
            "timestamp": data.get("timestamp"),
            "url": data.get("url"),
            "items": response_data.get("items", []),
            "total": response_data.get("total", 0),
            "page": response_data.get("page", 1)
        }
        
        return extracted
```

## 📊 使用场景

### 1. 电商数据采集

```python
# 配置电商网站API拦截
config = CrawlerConfig(
    target_domains=["api.shop.com"],
    target_apis=["/api/products", "/api/search"],
    output_dir="./ecommerce_data"
)

# 自定义操作：搜索商品
async def search_products(page):
    await page.fill("input[name='search']", "手机")
    await page.click("button[type='submit']")
    await page.wait_for_load_state("networkidle")
```

### 2. 社交媒体数据

```python
# 配置社交媒体API拦截
config = CrawlerConfig(
    target_domains=["api.social.com"],
    target_apis=["/api/posts", "/api/comments"],
    output_dir="./social_data"
)

# 自定义操作：滚动加载更多内容
async def scroll_for_more(page):
    for i in range(5):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2)
```

### 3. 新闻资讯采集

```python
# 配置新闻网站API拦截
config = CrawlerConfig(
    target_domains=["api.news.com"],
    target_apis=["/api/articles", "/api/categories"],
    output_dir="./news_data"
)
```

## 🔍 数据输出格式

### 原始数据格式

```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "url": "https://api.example.com/data",
  "method": "GET",
  "status_code": 200,
  "headers": {
    "content-type": "application/json"
  },
  "type": "response",
  "data": {
    "items": [...],
    "total": 100,
    "page": 1
  }
}
```

### 解析后数据格式

```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "url": "https://api.example.com/data",
  "status_code": 200,
  "method": "GET",
  "extracted_data": [
    {"id": 1, "title": "Item 1"},
    {"id": 2, "title": "Item 2"}
  ]
}
```

## 🛡️ 代理配置方案

### 方案一：mitmproxy（推荐）

**优点**：
- Python原生支持，集成度高
- 功能强大，支持HTTPS
- 可编程性强

**配置**：
```python
# 程序会自动启动mitmproxy代理服务器
# 浏览器会自动配置使用该代理
```

### 方案二：系统代理 + Proxifier

**优点**：
- 可以代理所有应用程序的流量
- 支持更复杂的路由规则

**配置步骤**：
1. 下载安装Proxifier
2. 配置代理服务器：127.0.0.1:8080
3. 设置代理规则，指定要代理的应用程序
4. 运行爬虫程序

### 方案三：浏览器插件代理

**优点**：
- 配置简单
- 只代理浏览器流量

**配置步骤**：
1. 安装SwitchyOmega等代理插件
2. 配置代理：127.0.0.1:8080
3. 启用代理配置
4. 运行爬虫程序

## 🚨 常见问题

### Q1: SSL证书错误

**问题**：访问HTTPS网站时出现证书错误

**解决方案**：
```bash
# 安装mitmproxy证书
# 1. 启动代理后访问 http://mitm.it
# 2. 下载并安装对应平台的证书
# 3. 或者在代码中设置忽略SSL错误
opts = options.Options(ssl_insecure=True)
```

### Q2: 代理端口被占用

**问题**：端口8080已被其他程序使用

**解决方案**：
```python
# 更改代理端口
config = CrawlerConfig(proxy_port=8081)  # 使用其他端口
```

### Q3: 浏览器无法连接代理

**问题**：浏览器显示无法连接到代理服务器

**解决方案**：
1. 检查防火墙设置
2. 确认代理服务器已启动
3. 检查端口是否正确

### Q4: 数据没有被拦截

**问题**：访问网站但没有拦截到API数据

**解决方案**：
1. 检查target_domains和target_apis配置
2. 确认网站确实使用了API请求
3. 查看日志输出，确认请求被正确拦截

### Q5: 性能问题

**问题**：爬虫运行缓慢或占用资源过多

**解决方案**：
```python
# 优化配置
config = CrawlerConfig(
    max_concurrent=3,      # 降低并发数
    request_delay=2.0,     # 增加请求间隔
    headless=True,         # 使用无头模式
    save_raw_data=False    # 只保存解析后的数据
)
```

## 📈 高级功能

### 1. 数据去重

```python
class DeduplicatedDataProcessor(DataProcessor):
    def __init__(self, config):
        super().__init__(config)
        self.seen_urls = set()
    
    def process_data(self, data):
        url = data.get("url")
        if url in self.seen_urls:
            return None  # 跳过重复数据
        
        self.seen_urls.add(url)
        return super().process_data(data)
```

### 2. 数据过滤

```python
def custom_filter(data):
    """自定义数据过滤器"""
    response_data = data.get("data", {})
    
    # 只保存包含特定字段的数据
    if "items" not in response_data:
        return False
    
    # 只保存非空数据
    if not response_data.get("items"):
        return False
    
    return True
```

### 3. 实时数据处理

```python
import asyncio
from datetime import datetime

class RealTimeProcessor:
    def __init__(self):
        self.data_buffer = []
    
    async def process_realtime(self, data):
        """实时处理数据"""
        self.data_buffer.append(data)
        
        # 每收集10条数据处理一次
        if len(self.data_buffer) >= 10:
            await self.batch_process()
            self.data_buffer.clear()
    
    async def batch_process(self):
        """批量处理数据"""
        # 数据清洗、转换、存储等操作
        processed_data = []
        for item in self.data_buffer:
            # 处理逻辑
            processed_item = self.transform_data(item)
            processed_data.append(processed_item)
        
        # 保存到数据库或文件
        await self.save_to_database(processed_data)
```

## 🔗 扩展集成

### 与数据库集成

```python
import asyncpg  # PostgreSQL
import aiomysql  # MySQL

class DatabaseIntegration:
    async def save_to_postgres(self, data):
        conn = await asyncpg.connect(
            host='localhost',
            database='crawler_db',
            user='user',
            password='password'
        )
        
        await conn.execute(
            "INSERT INTO api_data (url, data, timestamp) VALUES ($1, $2, $3)",
            data['url'], json.dumps(data['data']), data['timestamp']
        )
        
        await conn.close()
```

### 与消息队列集成

```python
import aio_pika  # RabbitMQ

class MessageQueueIntegration:
    async def send_to_queue(self, data):
        connection = await aio_pika.connect_robust("amqp://localhost/")
        channel = await connection.channel()
        
        await channel.default_exchange.publish(
            aio_pika.Message(json.dumps(data).encode()),
            routing_key="crawler_data"
        )
        
        await connection.close()
```

## 📝 最佳实践

1. **合理设置请求间隔**：避免对目标网站造成过大压力
2. **使用数据去重**：避免重复采集相同数据
3. **监控资源使用**：定期检查内存和磁盘使用情况
4. **错误处理**：实现完善的异常处理机制
5. **日志记录**：记录详细的运行日志便于调试
6. **遵守robots.txt**：尊重网站的爬虫协议
7. **数据备份**：定期备份重要的采集数据

## 📄 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 📞 支持

如果您在使用过程中遇到问题，可以：
1. 查看本文档的常见问题部分
2. 提交GitHub Issue
3. 查看mitmproxy和playwright的官方文档