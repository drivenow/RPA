# 抓包功能测试说明

本文档介绍如何测试 `capture_traffic.py` 抓包功能是否正常工作。

## 📋 测试方法概览

我们提供了三种测试方法，从简单到复杂：

1. **快速验证** - 检查已有的抓包数据
2. **手动测试** - 手动启动代理和浏览器
3. **自动测试** - 全自动化测试流程

## 🔍 方法1：快速验证（推荐首选）

如果你已经运行过抓包，可以快速验证数据：

```bash
# 进入项目目录
cd x:\RPA\tools_crawl

# 运行验证脚本
python examples/verify_capture.py
```

**验证内容：**
- ✅ 检查环境依赖
- ✅ 分析抓包数据文件
- ✅ 统计API调用情况
- ✅ 检查数据质量

## 🚀 方法2：手动测试

### 步骤1：启动代理服务

```bash
# 设置测试模式（可选）
set CAPTURE_TEST_MODE=true

# 启动mitmproxy代理
python -m mitmproxy.tools.mitmdump -s examples/capture_traffic.py -p 8080
```

### 步骤2：配置浏览器代理

在浏览器中设置代理：
- 代理地址：`127.0.0.1`
- 端口：`8080`

或使用命令行启动Chrome：
```bash
chrome.exe --proxy-server=http://127.0.0.1:8080 --ignore-certificate-errors
```

### 步骤3：访问测试页面

访问小红书探索页面：
```
https://www.xiaohongshu.com/explore
```

### 步骤4：验证抓包结果

```bash
python examples/verify_capture.py
```

## 🤖 方法3：自动化测试（最全面）

运行完整的自动化测试：

```bash
# 进入项目目录
cd x:\RPA\tools_crawl

# 运行自动化测试
python examples/test_capture.py
```

**测试流程：**
1. 🚀 自动启动mitmproxy代理
2. 🌐 启动浏览器并配置代理
3. 📱 访问小红书页面
4. 📊 分析抓包数据
5. 📋 生成测试报告

## 📊 测试结果解读

### 成功指标

✅ **代理启动成功**
- mitmproxy服务正常运行
- 监听端口8080

✅ **浏览器连接成功**
- 浏览器通过代理访问网络
- SSL证书验证通过

✅ **页面加载成功**
- 小红书页面正常加载
- API调用被触发

✅ **数据捕获成功**
- 生成抓包数据文件
- 包含有效的API响应

### 数据文件位置

抓包数据保存在：
```
captured_data/
├── captured_20231201_143022.json  # 抓包数据
├── captured_20231201_143055.json
└── ...
```

### 数据文件格式

```json
{
  "capture_stats": {
    "start_time": "2023-12-01 14:30:22",
    "total_requests": 45,
    "total_responses": 42,
    "captured_count": 8,
    "test_mode": true
  },
  "captured_data": [
    {
      "url": "https://edith.xiaohongshu.com/api/sns/web_api/v1/homefeed",
      "method": "GET",
      "timestamp": "2023-12-01T14:30:25.123456",
      "request": {
        "headers": {...},
        "body": ""
      },
      "response": {
        "status_code": 200,
        "headers": {...},
        "body": "{...}"
      }
    }
  ]
}
```

## 🔧 常见问题排查

### 问题1：代理启动失败

**症状：** mitmproxy启动报错
**解决：**
```bash
# 检查端口占用
netstat -ano | findstr :8080

# 更换端口
python -m mitmproxy.tools.mitmdump -s examples/capture_traffic.py -p 8081
```

### 问题2：浏览器无法连接

**症状：** 浏览器显示代理错误
**解决：**
- 确认代理地址和端口正确
- 检查防火墙设置
- 尝试使用无痕模式

### 问题3：没有抓到数据

**症状：** captured_data目录为空或文件为空
**解决：**
- 检查域名过滤配置
- 确认访问了正确的页面
- 查看mitmproxy控制台输出

### 问题4：数据不完整

**症状：** 只抓到部分API调用
**解决：**
- 在页面上多滚动几次
- 等待页面完全加载
- 检查网络连接

## 🎯 测试模式说明

设置环境变量 `CAPTURE_TEST_MODE=true` 可启用测试模式：

**测试模式特性：**
- 📝 详细的控制台日志
- 📊 实时统计信息
- 💾 更低的保存阈值（1条即保存）
- 🎯 扩展的域名过滤

**启用方法：**
```bash
# Windows
set CAPTURE_TEST_MODE=true

# Linux/Mac
export CAPTURE_TEST_MODE=true
```

## 📈 性能监控

### 监控指标

- **请求处理速度**：每秒处理的请求数
- **内存使用**：缓存的数据量
- **文件大小**：生成的JSON文件大小
- **响应时间**：API调用的响应时间

### 查看实时统计

测试模式下，控制台会显示：
```
[14:30:25] [INFO] 📊 统计: 请求=45, 响应=42, 捕获=8
[14:30:26] [INFO] 🎯 捕获API: /api/sns/web_api/v1/homefeed
[14:30:27] [INFO] 💾 保存数据: captured_20231201_143027.json (8条)
```

## 🛠️ 高级配置

### 自定义域名过滤

编辑 `capture_traffic.py`，修改域名列表：
```python
target_domains = [
    "www.xiaohongshu.com",
    "edith.xiaohongshu.com",
    "your-custom-domain.com"  # 添加自定义域名
]
```

### 调整保存阈值

```python
# 测试模式：1条数据就保存
save_threshold = 1 if test_mode else 10

# 自定义阈值
save_threshold = 5  # 每5条保存一次
```

### 自定义输出目录

```python
output_dir = Path("custom_output")  # 自定义输出目录
```

## 📞 技术支持

如果遇到问题：

1. **查看日志**：检查mitmproxy控制台输出
2. **运行验证**：使用 `verify_capture.py` 诊断
3. **检查环境**：确认依赖安装正确
4. **重启服务**：重新启动代理和浏览器

## 📚 相关文档

- [mitmproxy官方文档](https://docs.mitmproxy.org/)
- [Playwright文档](https://playwright.dev/python/)
- [项目README](../README.md)

---

**最后更新：** 2023-12-01  
**版本：** 1.0.0