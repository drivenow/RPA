#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓包数据验证脚本
快速验证capture_traffic.py是否正常工作
"""

import json
import os
import time
from pathlib import Path
from datetime import datetime, timedelta

def log(message, level="INFO"):
    """日志输出"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def check_environment():
    """检查环境配置"""
    log("🔍 检查环境配置...")
    
    issues = []
    
    # 检查mitmproxy
    try:
        import mitmproxy
        try:
            version = mitmproxy.__version__
        except AttributeError:
            # 某些版本的mitmproxy没有__version__属性
            version = "已安装"
        log(f"✅ mitmproxy: {version}")
    except ImportError:
        issues.append("❌ 未安装mitmproxy")
    
    # 检查capture_traffic.py文件
    capture_file = Path("examples/capture_traffic.py")
    if capture_file.exists():
        log(f"✅ 找到抓包脚本: {capture_file}")
    else:
        issues.append(f"❌ 未找到抓包脚本: {capture_file}")
    
    # 检查输出目录
    output_dir = Path("captured_data")
    if output_dir.exists():
        log(f"✅ 输出目录存在: {output_dir}")
    else:
        log(f"⚠️  输出目录不存在: {output_dir} (运行时会自动创建)")
    
    return issues

def analyze_captured_data():
    """分析抓包数据"""
    log("📊 分析抓包数据...")
    
    captured_dir = Path("captured_data")
    if not captured_dir.exists():
        log("❌ 未找到captured_data目录")
        return False
    
    # 查找JSON文件
    json_files = list(captured_dir.glob("captured_*.json"))
    
    if not json_files:
        log("❌ 未找到抓包数据文件")
        log("💡 提示: 请先运行mitmproxy抓包后再验证")
        return False
    
    log(f"📁 找到 {len(json_files)} 个数据文件")
    
    # 分析最新文件
    latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
    file_time = datetime.fromtimestamp(latest_file.stat().st_mtime)
    
    log(f"📄 最新文件: {latest_file.name}")
    log(f"🕒 修改时间: {file_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查文件是否是最近生成的
    if datetime.now() - file_time > timedelta(hours=1):
        log("⚠️  最新文件超过1小时，可能不是当前测试数据")
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 分析数据结构
        stats = data.get("capture_stats", {})
        captured_data = data.get("captured_data", [])
        
        log("📈 统计信息:")
        log(f"   总请求数: {stats.get('total_requests', 0)}")
        log(f"   总响应数: {stats.get('total_responses', 0)}")
        log(f"   捕获数据: {stats.get('captured_count', 0)}条")
        log(f"   测试模式: {stats.get('test_mode', False)}")
        log(f"   开始时间: {stats.get('start_time', 'N/A')}")
        
        if not captured_data:
            log("❌ 抓包文件为空")
            return False
        
        log(f"✅ 成功捕获 {len(captured_data)} 条数据")
        
        # 分析数据内容
        analyze_data_content(captured_data)
        
        return True
        
    except json.JSONDecodeError as e:
        log(f"❌ JSON解析失败: {e}", "ERROR")
        return False
    except Exception as e:
        log(f"❌ 读取文件失败: {e}", "ERROR")
        return False

def analyze_data_content(captured_data):
    """分析抓包数据内容"""
    log("\n🔍 数据内容分析:")
    
    # 统计域名
    domains = {}
    methods = {}
    status_codes = {}
    
    for item in captured_data:
        url = item.get("url", "")
        method = item.get("method", "")
        status = item.get("response", {}).get("status_code", 0)
        
        # 提取域名
        if "://" in url:
            domain = url.split("://")[1].split("/")[0]
            domains[domain] = domains.get(domain, 0) + 1
        
        # 统计方法
        if method:
            methods[method] = methods.get(method, 0) + 1
        
        # 统计状态码
        if status:
            status_codes[status] = status_codes.get(status, 0) + 1
    
    # 显示域名统计
    if domains:
        log("📍 域名分布:")
        for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True):
            log(f"   {domain}: {count}次")
    
    # 显示方法统计
    if methods:
        log("🔧 请求方法:")
        for method, count in methods.items():
            log(f"   {method}: {count}次")
    
    # 显示状态码统计
    if status_codes:
        log("📊 响应状态:")
        for status, count in status_codes.items():
            log(f"   {status}: {count}次")
    
    # 检查关键API
    api_patterns = [
        "homefeed", "feed", "explore", "api", "web_api"
    ]
    
    found_apis = []
    for item in captured_data:
        url = item.get("url", "")
        for pattern in api_patterns:
            if pattern in url.lower():
                found_apis.append((pattern, url))
                break
    
    if found_apis:
        log("🎯 发现关键API:")
        pattern_count = {}
        for pattern, url in found_apis:
            pattern_count[pattern] = pattern_count.get(pattern, 0) + 1
        
        for pattern, count in pattern_count.items():
            log(f"   {pattern}: {count}个")
        
        # 显示部分URL示例
        log("📝 URL示例:")
        for pattern, url in found_apis[:5]:  # 显示前5个
            short_url = url[:80] + "..." if len(url) > 80 else url
            log(f"   [{pattern}] {short_url}")
    else:
        log("⚠️  未发现关键API调用")

def check_recent_activity():
    """检查最近活动"""
    log("\n⏰ 检查最近活动...")
    
    captured_dir = Path("captured_data")
    if not captured_dir.exists():
        return
    
    now = datetime.now()
    recent_files = []
    
    for file in captured_dir.glob("captured_*.json"):
        file_time = datetime.fromtimestamp(file.stat().st_mtime)
        if now - file_time < timedelta(minutes=30):  # 30分钟内
            recent_files.append((file, file_time))
    
    if recent_files:
        log(f"📅 最近30分钟内有 {len(recent_files)} 个文件:")
        for file, file_time in sorted(recent_files, key=lambda x: x[1], reverse=True):
            log(f"   {file.name} - {file_time.strftime('%H:%M:%S')}")
    else:
        log("📅 最近30分钟内无新文件")

def provide_suggestions():
    """提供建议"""
    log("\n💡 使用建议:")
    log("1. 如果没有数据文件:")
    log("   - 确保mitmproxy正在运行")
    log("   - 检查代理配置是否正确")
    log("   - 访问小红书页面触发API调用")
    log("")
    log("2. 如果数据为空:")
    log("   - 检查域名过滤配置")
    log("   - 确认访问的是正确的页面")
    log("   - 查看mitmproxy控制台输出")
    log("")
    log("3. 测试命令:")
    log("   - 启动代理: python -m mitmproxy.tools.mitmdump -s examples/capture_traffic.py -p 8080")
    log("   - 完整测试: python examples/test_capture.py")
    log("   - 验证数据: python examples/verify_capture.py")

def main():
    """主函数"""
    print("🔍 抓包数据验证工具")
    print("快速检查capture_traffic.py的工作状态")
    print("-" * 60)
    
    # 1. 检查环境
    issues = check_environment()
    if issues:
        log("❌ 环境检查发现问题:")
        for issue in issues:
            log(f"   {issue}")
        log("")
    
    # 2. 分析数据
    has_data = analyze_captured_data()
    
    # 3. 检查最近活动
    check_recent_activity()
    
    # 4. 提供建议
    provide_suggestions()
    
    # 5. 总结
    log("\n" + "="*60)
    if has_data and not issues:
        log("✅ 验证完成: 抓包功能正常工作")
    elif has_data:
        log("⚠️  验证完成: 抓包有数据但环境有问题")
    else:
        log("❌ 验证完成: 未发现有效抓包数据")
    log("="*60)

if __name__ == "__main__":
    main()