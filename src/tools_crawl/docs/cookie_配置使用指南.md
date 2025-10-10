# Cookie 配置使用指南

## 概述

本系统支持自动加载和保存浏览器 cookies，支持多种格式和配置方式。**现已支持直接使用浏览器导出的 JSON 格式，无需手动转换！**

## 配置说明

### 1. 全局配置 (global.yaml)

在 `config/global.yaml` 文件中的 `browser.cookies` 节配置：

```yaml
browser:
  cookies:
    enabled: true              # 启用cookie功能
    default_file: "cookies/default_cookies.json"  # 默认cookie文件
    format: "auto"            # 默认格式：auto, json, netscape
    
    # 多站点配置
    sites:
      feishu:
        enabled: true
        domains: ["feishu.cn", "feishu.com"]
        file: "cookies/feishu_cookies.json"  # 浏览器导出的JSON格式
        format: "json"        # 自动识别并转换浏览器格式
      
      xiaohongshu:
        enabled: true
        domains: ["xiaohongshu.com", "xhscdn.com"]
        file: "cookies/xhs_cookies.json"     # 推荐使用JSON格式
        format: "json"        # 支持浏览器导出格式
      
```

### 2. 支持的文件格式

#### 浏览器导出格式（推荐）✨

**直接支持浏览器导出的 JSON 格式**，包括：
- Chrome 导出的 JSON 格式
- Edge 导出的 JSON 格式  
- Firefox 导出的 JSON 格式
- 其他浏览器扩展导出的标准格式

示例（飞书网站 cookies）：
```json
[
  {
    "domain": ".feishu.cn",
    "expirationDate": 1755605145.503983,
    "hostOnly": false,
    "httpOnly": true,
    "name": "_uuid_hera_ab_path_1",
    "path": "/",
    "sameSite": "unspecified",
    "secure": false,
    "session": false,
    "storeId": "0",
    "value": "7529134173731258387"
  }
]
```

**系统会自动转换为 Playwright 兼容格式**：
- `expirationDate` → `expires`
- `sameSite: "unspecified"` → `sameSite: "Lax"`
- `sameSite: "no_restriction"` → `sameSite: "None"`
- 自动过滤不需要的字段（`hostOnly`, `storeId` 等）

#### Playwright 原生格式
```json
[
  {
    "name": "session_id",
    "value": "abc123",
    "domain": ".xiaohongshu.com",
    "path": "/",
    "expires": 1735689600,
    "secure": false,
    "httpOnly": true
  }
]
```

#### Netscape 格式 (谷歌浏览器插件导出)
```
# Netscape HTTP Cookie File
# This is a generated file! Do not edit.

.xiaohongshu.com	TRUE	/	FALSE	1735689600	session_id	abc123
xiaohongshu.com	FALSE	/	TRUE	1735689600	user_token	xyz789
```

## 使用方法

### 1. 从浏览器导出 Cookie（推荐）✨

#### 方法一：浏览器扩展导出 JSON 格式
1. 安装 Cookie 导出扩展（如 "Cookie Editor", "EditThisCookie" 等）
2. 访问目标网站并登录
3. 使用扩展导出 cookies 为 JSON 文件
4. **直接使用导出的文件，无需任何转换！**

#### 方法二：开发者工具导出
1. 按 F12 打开开发者工具
2. 进入 Application/Storage → Cookies
3. 选择并复制所需 cookies
4. 保存为 JSON 格式

#### 方法三：传统插件导出 Netscape 格式
1. 安装 Cookie 导出插件（如 "Get cookies.txt"）
2. 访问目标网站并登录
3. 使用插件导出 cookies 为 txt 文件
4. 将文件保存到配置中指定的路径

### 2. 自动加载 Cookie

系统会在以下时机自动加载 cookies：

- 创建浏览器上下文时
- 根据当前访问的域名匹配相应的站点配置
- 优先加载站点特定的 cookie 文件，然后是默认文件

### 3. 自动保存 Cookie

系统会在以下时机自动保存 cookies：

- 检测到用户登录成功后
- 根据当前页面 URL 确定保存到哪个站点配置
- 如果没有匹配的站点，保存到默认文件

### 4. 手动操作 Cookie

```python
# 手动加载 cookies
await browser_manager.load_cookies_from_file("cookies/xhs_cookies.txt", "netscape")

# 手动保存 cookies
await browser_manager.save_cookies_to_file("cookies/xhs_cookies.json", "json")

# 获取当前 cookies
cookies = await browser_manager.get_cookies()

# 设置 cookies
await browser_manager.set_cookies(cookies)
```

## 目录结构建议

```
project/
├── config/
│   └── global.yaml
├── cookies/
│   ├── default_cookies.json
│   ├── xhs_cookies.txt          # 小红书 cookies (Netscape格式)
│   ├── weibo_cookies.json       # 微博 cookies (JSON格式)
│   └── other_site_cookies.txt
└── src/
    ├── browser_manager.py
    └── config_parser.py
```

## 配置参数详解

### 全局参数

- `enabled`: 是否启用 cookie 功能
- `auto_load`: 是否在创建浏览器上下文时自动加载 cookies
- `auto_save`: 是否在检测到登录后自动保存 cookies
- `default_file`: 默认 cookie 文件路径
- `format`: 默认文件格式 (auto/json/netscape)

### 站点参数

- `enabled`: 是否启用该站点的 cookie 配置
- `domains`: 匹配的域名列表
- `file`: 该站点的 cookie 文件路径
- `format`: 该站点的文件格式

## 注意事项

1. **推荐格式**: 优先使用浏览器导出的 JSON 格式，系统会自动转换为 Playwright 兼容格式
2. **文件路径**: 支持相对路径和绝对路径，相对路径基于项目根目录
3. **格式检测**: 当 format 设为 "auto" 时，系统会自动检测文件格式
4. **智能转换**: 系统自动处理浏览器导出格式与 Playwright 格式的差异
5. **域名匹配**: 系统使用包含匹配，即配置的域名在当前 URL 中出现即匹配
6. **文件安全**: cookie 文件包含敏感信息，请妥善保管，不要提交到版本控制
7. **向后兼容**: 完全兼容原有的 Netscape 格式和 Playwright 原生格式

## 故障排除

### 常见问题

1. **Cookie 文件不存在**
   - 检查文件路径是否正确
   - 确保目录存在且有读写权限

2. **格式解析失败**
   - 检查文件格式是否正确
   - 尝试使用 "auto" 格式让系统自动检测

3. **域名不匹配**
   - 检查配置中的域名列表
   - 确保域名配置包含目标网站的主域名

4. **自动保存失败**
   - 检查目标目录是否存在
   - 确保有写入权限
   - 查看日志获取详细错误信息

### 调试方法

启用详细日志查看 cookie 操作过程：

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

查看日志中的 cookie 相关信息：
- "Cookie自动加载功能未启用"
- "成功加载cookie文件"
- "已为站点 xxx 自动保存cookies"
- "解析Netscape格式cookie文件，获得X个cookies"