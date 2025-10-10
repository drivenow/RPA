#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓包功能完整测试脚本
自动启动mitmproxy代理，配置浏览器，访问测试页面，验证抓包效果
"""

import asyncio
import subprocess
import time
import os
import sys
import json
import signal
from pathlib import Path
from playwright.async_api import async_playwright

class CaptureTest:
    def __init__(self):
        self.proxy_port = 8080
        self.proxy_process = None
        self.test_results = {
            "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "proxy_started": False,
            "browser_connected": False,
            "page_loaded": False,
            "data_captured": False,
            "files_generated": [],
            "errors": []
        }
    
    def log(self, message, level="INFO"):
        """日志输出"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    async def start_proxy(self):
        """启动mitmproxy代理服务"""
        try:
            self.log("正在启动mitmproxy代理服务...")
            
            # 设置测试模式环境变量
            env = os.environ.copy()
            env['CAPTURE_TEST_MODE'] = 'true'
            
            # 启动mitmproxy
            cmd = [
                sys.executable, "-m", "mitmproxy.tools.mitmdump",
                "-s", "examples/capture_traffic.py",
                "-p", str(self.proxy_port),
                "--set", "confdir=~/.mitmproxy"
            ]
            
            self.log(f"执行命令: {' '.join(cmd)}")
            
            self.proxy_process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=Path(__file__).parent.parent
            )
            
            # 等待代理启动
            await asyncio.sleep(3)
            
            if self.proxy_process.poll() is None:
                self.test_results["proxy_started"] = True
                self.log("✅ mitmproxy代理服务启动成功")
                return True
            else:
                stdout, stderr = self.proxy_process.communicate()
                self.test_results["errors"].append(f"代理启动失败: {stderr}")
                self.log(f"❌ 代理启动失败: {stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.test_results["errors"].append(f"启动代理异常: {str(e)}")
            self.log(f"❌ 启动代理异常: {e}", "ERROR")
            return False
    
    async def test_browser_connection(self):
        """测试浏览器代理连接"""
        try:
            self.log("正在测试浏览器代理连接...")
            
            async with async_playwright() as p:
                # 启动浏览器，配置代理
                browser = await p.chromium.launch(
                    headless=False,
                    args=[
                        f'--proxy-server=http://127.0.0.1:{self.proxy_port}',
                        '--ignore-certificate-errors',
                        '--ignore-ssl-errors',
                        '--disable-web-security'
                    ]
                )
                
                context = await browser.new_context(
                    ignore_https_errors=True
                )
                
                page = await context.new_page()
                
                self.test_results["browser_connected"] = True
                self.log("✅ 浏览器代理连接成功")
                
                # 访问小红书探索页面
                self.log("正在访问小红书探索页面...")
                try:
                    await page.goto("https://www.xiaohongshu.com/explore", timeout=30000)
                    await page.wait_for_load_state('networkidle', timeout=10000)
                    
                    self.test_results["page_loaded"] = True
                    self.log("✅ 页面加载成功")
                    
                    # 等待一段时间让页面完全加载和API调用
                    self.log("等待API调用完成...")
                    await asyncio.sleep(10)
                    
                    # 滚动页面触发更多API调用
                    self.log("滚动页面触发更多数据加载...")
                    for i in range(3):
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await asyncio.sleep(3)
                    
                    self.log("✅ 页面交互完成")
                    
                except Exception as e:
                    self.test_results["errors"].append(f"页面访问失败: {str(e)}")
                    self.log(f"❌ 页面访问失败: {e}", "ERROR")
                
                await browser.close()
                
        except Exception as e:
            self.test_results["errors"].append(f"浏览器连接失败: {str(e)}")
            self.log(f"❌ 浏览器连接失败: {e}", "ERROR")
            return False
        
        return True
    
    def check_captured_data(self):
        """检查抓包数据"""
        try:
            self.log("正在检查抓包数据...")
            
            # 检查captured_data目录
            captured_dir = Path("captured_data")
            if not captured_dir.exists():
                self.test_results["errors"].append("未找到captured_data目录")
                self.log("❌ 未找到captured_data目录", "ERROR")
                return False
            
            # 查找生成的文件
            json_files = list(captured_dir.glob("captured_*.json"))
            
            if not json_files:
                self.test_results["errors"].append("未找到抓包数据文件")
                self.log("❌ 未找到抓包数据文件", "ERROR")
                return False
            
            # 分析最新的文件
            latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
            self.test_results["files_generated"].append(str(latest_file))
            
            self.log(f"📁 找到抓包文件: {latest_file}")
            
            # 读取并分析数据
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            stats = data.get("capture_stats", {})
            captured_data = data.get("captured_data", [])
            
            self.log(f"📊 统计信息:")
            self.log(f"   总请求数: {stats.get('total_requests', 0)}")
            self.log(f"   总响应数: {stats.get('total_responses', 0)}")
            self.log(f"   捕获数据: {stats.get('captured_count', 0)}条")
            self.log(f"   测试模式: {stats.get('test_mode', False)}")
            
            if captured_data:
                self.test_results["data_captured"] = True
                self.log("✅ 成功捕获到数据")
                
                # 分析捕获的数据类型
                api_urls = [item.get("url", "") for item in captured_data]
                feed_apis = [url for url in api_urls if "homefeed" in url or "feed" in url]
                
                if feed_apis:
                    self.log(f"🎯 发现 {len(feed_apis)} 个feed API调用")
                    for url in feed_apis[:3]:  # 显示前3个
                        self.log(f"   - {url}")
                else:
                    self.log("⚠️  未发现feed API调用")
                
                return True
            else:
                self.test_results["errors"].append("抓包文件为空")
                self.log("❌ 抓包文件为空", "ERROR")
                return False
                
        except Exception as e:
            self.test_results["errors"].append(f"检查数据异常: {str(e)}")
            self.log(f"❌ 检查数据异常: {e}", "ERROR")
            return False
    
    def stop_proxy(self):
        """停止代理服务"""
        if self.proxy_process:
            try:
                self.log("正在停止代理服务...")
                self.proxy_process.terminate()
                self.proxy_process.wait(timeout=5)
                self.log("✅ 代理服务已停止")
            except subprocess.TimeoutExpired:
                self.log("强制终止代理服务...")
                self.proxy_process.kill()
            except Exception as e:
                self.log(f"停止代理服务异常: {e}", "ERROR")
    
    def generate_report(self):
        """生成测试报告"""
        self.test_results["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 计算总体结果
        success_count = sum([
            self.test_results["proxy_started"],
            self.test_results["browser_connected"],
            self.test_results["page_loaded"],
            self.test_results["data_captured"]
        ])
        
        total_tests = 4
        success_rate = (success_count / total_tests) * 100
        
        self.log("\n" + "="*60)
        self.log("📋 测试报告")
        self.log("="*60)
        self.log(f"开始时间: {self.test_results['start_time']}")
        self.log(f"结束时间: {self.test_results['end_time']}")
        self.log(f"成功率: {success_rate:.1f}% ({success_count}/{total_tests})")
        self.log("")
        self.log("详细结果:")
        self.log(f"  代理启动: {'✅' if self.test_results['proxy_started'] else '❌'}")
        self.log(f"  浏览器连接: {'✅' if self.test_results['browser_connected'] else '❌'}")
        self.log(f"  页面加载: {'✅' if self.test_results['page_loaded'] else '❌'}")
        self.log(f"  数据捕获: {'✅' if self.test_results['data_captured'] else '❌'}")
        
        if self.test_results["files_generated"]:
            self.log(f"\n生成文件:")
            for file in self.test_results["files_generated"]:
                self.log(f"  📁 {file}")
        
        if self.test_results["errors"]:
            self.log(f"\n错误信息:")
            for error in self.test_results["errors"]:
                self.log(f"  ❌ {error}")
        
        self.log("="*60)
        
        # 保存报告到文件
        report_file = f"test_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        self.log(f"📄 测试报告已保存到: {report_file}")
        
        return success_rate >= 75  # 75%以上算测试通过
    
    async def run_test(self):
        """运行完整测试"""
        self.log("🚀 开始抓包功能测试")
        self.log("="*60)
        
        try:
            # 1. 启动代理
            if not await self.start_proxy():
                return False
            
            # 2. 测试浏览器连接
            await self.test_browser_connection()
            
            # 等待数据处理
            self.log("等待数据处理完成...")
            await asyncio.sleep(5)
            
            # 3. 检查抓包数据
            self.check_captured_data()
            
            return True
            
        finally:
            # 4. 清理资源
            self.stop_proxy()
            
            # 5. 生成报告
            return self.generate_report()

async def main():
    """主函数"""
    print("🧪 抓包功能测试工具")
    print("本工具将自动测试capture_traffic.py的抓包功能")
    print("-" * 60)
    
    # 检查依赖
    try:
        import mitmproxy
        import playwright
        print("✅ 依赖检查通过")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install mitmproxy playwright")
        return
    
    # 运行测试
    test = CaptureTest()
    
    def signal_handler(signum, frame):
        print("\n收到中断信号，正在清理...")
        test.stop_proxy()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        success = await test.run_test()
        if success:
            print("\n🎉 测试完成！抓包功能正常工作")
            sys.exit(0)
        else:
            print("\n⚠️  测试发现问题，请检查错误信息")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n用户中断测试")
        test.stop_proxy()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        test.stop_proxy()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())