# 高效爬虫流量抓包方案

## 项目概述
基于流量抓包的配置化爬虫系统，通过mitmproxy拦截API请求，配置化提取结构化数据。

## 核心需求
- 使用Python + mitmproxy实现流量抓包
- 配置化爬虫规则，无需重复编码
- 直接解析API返回的JSON数据
- 支持MySQL数据存储

## 技术选型

### 推荐方案：mitmproxy + 配置化系统
**优势**：
- Python原生支持，开发效率高
- 实时拦截HTTPS流量，自动处理SSL
- 配置驱动，扩展简单
- 与现有软件A完美配合

### 核心技术栈
- **代理层**：mitmproxy
- **配置层**：YAML配置文件
- **数据处理**：Python + JSONPath
- **数据存储**：MySQL + JSON/CSV输出
- **依赖管理**：requirements.txt

## 系统架构

### 文件结构
```
x:\RPA\tools_crawl\
├── requirements.txt          # 依赖管理
├── config\
│   ├── crawlers.yaml        # 爬虫配置
│   └── database.yaml        # 数据库配置
├── src\
│   ├── proxy_handler.py     # mitmproxy处理脚本
│   ├── config_parser.py     # 配置解析器
│   ├── data_processor.py    # 数据处理器
│   ├── mysql_manager.py     # MySQL管理器
│   └── main.py              # 主启动脚本
├── data\                    # 数据输出目录
├── logs\                    # 日志目录
└── examples\                # 示例配置
```

### 核心组件
1. **代理处理器** - 拦截HTTP请求/响应，过滤目标API
2. **配置解析器** - 解析YAML配置，支持热重载
3. **数据处理器** - JSONPath提取，数据转换和清洗
4. **MySQL管理器** - 数据库连接，批量写入，表结构管理

## 配置文件设计

### 爬虫配置 (crawlers.yaml)
```yaml
# 全局配置
global:
  proxy_port: 8080
  output_dir: "./data"
  log_level: "INFO"

# 数据库配置
database:
  host: "localhost"
  port: 3306
  username: "crawler_user"
  password: "password"
  database: "crawler_data"

# 爬虫规则
crawlers:
  - name: "产品API爬虫"
    enabled: true
    url_patterns:
      - "api.example.com/v1/products"
    data_extraction:
      - field: "product_name"
        json_path: "$.data.items[*].name"
        data_type: "string"
      - field: "price"
        json_path: "$.data.items[*].price"
        data_type: "decimal"
      - field: "category"
        json_path: "$.data.items[*].category.name"
        data_type: "string"
    output:
      mysql_table: "products"
      backup_format: "json"
```

## 实施计划

### 阶段一：基础架构 (1-2天)
1. 创建项目结构和依赖文件
2. 实现配置解析器和数据模型
3. 搭建MySQL连接和表管理

### 阶段二：核心功能 (2-3天)
4. 实现mitmproxy代理处理器
5. 开发数据处理和JSONPath提取
6. 集成MySQL数据存储功能

### 阶段三：完善优化 (1-2天)
7. 创建主启动脚本和命令行接口
8. 添加示例配置和使用文档
9. 性能优化和错误处理

### 技术依赖 (requirements.txt)
```
mitmproxy>=10.0.0
pydantic>=2.0.0
PyYAML>=6.0
jsonpath-ng>=1.6.0
PyMySQL>=1.1.0
SQLAlchemy>=2.0.0
asyncio-mqtt>=0.13.0
```

## 使用流程
1. **分析接口** - 使用软件A分析目标API
2. **配置规则** - 编写YAML配置文件
3. **启动代理** - 运行mitmproxy代理服务
4. **数据采集** - 自动拦截并存储数据
5. **数据查看** - 通过MySQL或导出文件查看结果

## 扩展特性
- 支持多种输出格式 (MySQL/JSON/CSV)
- 配置热重载，无需重启
- 数据去重和增量更新
- 性能监控和日志记录
- 错误重试和异常处理

# Current Execution Step (Updated by EXECUTE mode when starting a step)

# Task Progress (Appended by EXECUTE mode after each step completion)

# Final Review (Populated by REVIEW mode)