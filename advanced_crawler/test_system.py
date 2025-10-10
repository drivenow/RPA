#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统测试脚本

这个脚本用于测试高效代理爬虫系统的各个组件是否正常工作。
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

# 导入测试模块
try:
    from simple_proxy_crawler import SimpleCrawler
    from proxy_crawler import AdvancedCrawler, CrawlerConfig
    from config_examples import get_config_by_name, list_available_configs
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    print("请确保已正确安装所有依赖")
    sys.exit(1)


class SystemTester:
    """系统测试器"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = time.time()
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """记录测试结果"""
        status = "✅" if success else "❌"
        result = {
            'test_name': test_name,
            'success': success,
            'message': message,
            'timestamp': time.time() - self.start_time
        }
        self.test_results.append(result)
        print(f"{status} {test_name}: {message}")
    
    def test_imports(self) -> bool:
        """测试模块导入"""
        print("\n=== 测试模块导入 ===")
        
        imports = [
            ("mitmproxy", "import mitmproxy"),
            ("playwright", "import playwright"),
            ("requests", "import requests"),
            ("asyncio", "import asyncio"),
            ("json", "import json"),
            ("pathlib", "from pathlib import Path"),
            ("typing", "from typing import Dict, Any, List"),
        ]
        
        all_success = True
        
        for module_name, import_code in imports:
            try:
                exec(import_code)
                self.log_test(f"导入{module_name}", True, "成功")
            except ImportError as e:
                self.log_test(f"导入{module_name}", False, str(e))
                all_success = False
        
        return all_success
    
    def test_config_system(self) -> bool:
        """测试配置系统"""
        print("\n=== 测试配置系统 ===")
        
        try:
            # 测试配置列表
            configs = list_available_configs()
            self.log_test("获取配置列表", len(configs) > 0, f"找到{len(configs)}个配置")
            
            # 测试获取配置
            test_config = get_config_by_name("test")
            self.log_test("获取测试配置", test_config is not None, "配置对象创建成功")
            
            # 测试配置属性
            required_attrs = ['proxy_host', 'proxy_port', 'target_domains', 'output_dir']
            for attr in required_attrs:
                has_attr = hasattr(test_config, attr)
                self.log_test(f"配置属性{attr}", has_attr, "存在" if has_attr else "缺失")
            
            return True
            
        except Exception as e:
            self.log_test("配置系统测试", False, str(e))
            return False
    
    def test_directory_structure(self) -> bool:
        """测试目录结构"""
        print("\n=== 测试目录结构 ===")
        
        base_path = Path(__file__).parent
        required_files = [
            "proxy_crawler.py",
            "simple_proxy_crawler.py",
            "config_examples.py",
            "requirements.txt",
            "README.md"
        ]
        
        all_exist = True
        
        for file_name in required_files:
            file_path = base_path / file_name
            exists = file_path.exists()
            self.log_test(f"文件{file_name}", exists, "存在" if exists else "缺失")
            if not exists:
                all_exist = False
        
        return all_exist
    
    async def test_simple_crawler(self) -> bool:
        """测试简化版爬虫"""
        print("\n=== 测试简化版爬虫 ===")
        
        try:
            # 创建测试目录
            test_dir = Path("./test_data/simple")
            test_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建爬虫实例
            crawler = SimpleCrawler(
                proxy_port=8090,  # 使用不同端口避免冲突
                output_dir=str(test_dir)
            )
            self.log_test("创建简化版爬虫", True, "实例创建成功")
            
            # 定义测试操作
            async def test_operations(page):
                try:
                    # 访问测试API
                    await page.goto("https://httpbin.org/json")
                    await page.wait_for_timeout(3000)
                    self.log_test("访问测试API", True, "页面加载成功")
                except Exception as e:
                    self.log_test("访问测试API", False, str(e))
            
            # 运行爬虫（短时间测试）
            try:
                # 设置较短的超时时间
                await asyncio.wait_for(crawler.run(test_operations), timeout=30)
                self.log_test("运行简化版爬虫", True, "执行完成")
                return True
            except asyncio.TimeoutError:
                self.log_test("运行简化版爬虫", False, "超时")
                return False
            
        except Exception as e:
            self.log_test("简化版爬虫测试", False, str(e))
            return False
    
    async def test_advanced_crawler(self) -> bool:
        """测试完整版爬虫"""
        print("\n=== 测试完整版爬虫 ===")
        
        try:
            # 获取测试配置
            config = get_config_by_name("test")
            config.proxy_port = 8091  # 使用不同端口
            config.output_dir = "./test_data/advanced"
            config.timeout = 20  # 较短超时
            
            # 创建爬虫实例
            crawler = AdvancedCrawler(config)
            self.log_test("创建完整版爬虫", True, "实例创建成功")
            
            # 定义测试数据处理器
            def test_processor(data: Dict[str, Any]) -> Dict[str, Any]:
                return {
                    'timestamp': data.get('timestamp'),
                    'url': data.get('url'),
                    'status': 'processed',
                    'test': True
                }
            
            crawler.set_custom_processor(test_processor)
            self.log_test("设置数据处理器", True, "处理器设置成功")
            
            # 定义测试操作
            async def test_operations(page):
                try:
                    await page.goto("https://jsonplaceholder.typicode.com/posts/1")
                    await page.wait_for_timeout(3000)
                    self.log_test("访问JSON API", True, "页面加载成功")
                except Exception as e:
                    self.log_test("访问JSON API", False, str(e))
            
            # 运行爬虫（短时间测试）
            try:
                await asyncio.wait_for(crawler.run(test_operations), timeout=30)
                self.log_test("运行完整版爬虫", True, "执行完成")
                return True
            except asyncio.TimeoutError:
                self.log_test("运行完整版爬虫", False, "超时")
                return False
            
        except Exception as e:
            self.log_test("完整版爬虫测试", False, str(e))
            return False
    
    def test_data_output(self) -> bool:
        """测试数据输出"""
        print("\n=== 测试数据输出 ===")
        
        test_dirs = [
            "./test_data/simple",
            "./test_data/advanced"
        ]
        
        all_success = True
        
        for test_dir in test_dirs:
            dir_path = Path(test_dir)
            if dir_path.exists():
                files = list(dir_path.glob("*.json"))
                has_files = len(files) > 0
                self.log_test(f"数据输出{test_dir}", has_files, f"找到{len(files)}个文件")
                
                # 检查文件内容
                if has_files:
                    try:
                        with open(files[0], 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        self.log_test(f"数据格式{test_dir}", True, "JSON格式正确")
                    except Exception as e:
                        self.log_test(f"数据格式{test_dir}", False, str(e))
                        all_success = False
            else:
                self.log_test(f"数据目录{test_dir}", False, "目录不存在")
                all_success = False
        
        return all_success
    
    def cleanup_test_data(self):
        """清理测试数据"""
        print("\n=== 清理测试数据 ===")
        
        try:
            import shutil
            test_data_dir = Path("./test_data")
            if test_data_dir.exists():
                shutil.rmtree(test_data_dir)
                self.log_test("清理测试数据", True, "测试数据已清理")
            else:
                self.log_test("清理测试数据", True, "无需清理")
        except Exception as e:
            self.log_test("清理测试数据", False, str(e))
    
    def generate_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        report = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'total_time': time.time() - self.start_time,
            'results': self.test_results
        }
        
        return report
    
    def print_summary(self, report: Dict[str, Any]):
        """打印测试总结"""
        print("\n" + "="*60)
        print("                    测试总结")
        print("="*60)
        print(f"总测试数: {report['total_tests']}")
        print(f"通过测试: {report['passed_tests']}")
        print(f"失败测试: {report['failed_tests']}")
        print(f"成功率: {report['success_rate']:.1f}%")
        print(f"总耗时: {report['total_time']:.2f}秒")
        
        if report['failed_tests'] > 0:
            print("\n失败的测试:")
            for result in report['results']:
                if not result['success']:
                    print(f"  ❌ {result['test_name']}: {result['message']}")
        
        print("\n" + "="*60)
        
        if report['success_rate'] >= 80:
            print("🎉 系统测试基本通过！")
        elif report['success_rate'] >= 60:
            print("⚠️  系统测试部分通过，建议检查失败项")
        else:
            print("❌ 系统测试失败较多，请检查安装和配置")


async def main():
    """主测试函数"""
    print("开始系统测试...")
    
    tester = SystemTester()
    
    # 运行所有测试
    tests = [
        ("模块导入测试", tester.test_imports),
        ("配置系统测试", tester.test_config_system),
        ("目录结构测试", tester.test_directory_structure),
    ]
    
    # 运行同步测试
    for test_name, test_func in tests:
        print(f"\n开始{test_name}...")
        test_func()
    
    # 运行异步测试（可选，因为可能需要网络）
    run_network_tests = input("\n是否运行网络测试？(y/N): ").strip().lower() == 'y'
    
    if run_network_tests:
        print("\n开始网络测试...")
        try:
            await tester.test_simple_crawler()
            await tester.test_advanced_crawler()
            tester.test_data_output()
        except Exception as e:
            tester.log_test("网络测试", False, str(e))
    
    # 清理测试数据
    if run_network_tests:
        tester.cleanup_test_data()
    
    # 生成并打印报告
    report = tester.generate_report()
    tester.print_summary(report)
    
    # 保存报告
    report_file = Path("test_report.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n详细报告已保存到: {report_file}")
    
    return report['success_rate'] >= 80


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n用户中断测试")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试过程中出现错误: {e}")
        sys.exit(1)