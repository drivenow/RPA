from mitmproxy import http, ctx
import json
import time
import os
from urllib.parse import urlparse

class RequestCapture:
    def __init__(self):
        self.captured_data = []
        self.request_count = 0
        self.response_count = 0
        self.start_time = time.time()
        
        # 测试模式：从环境变量读取，默认为False
        self.test_mode = os.getenv('CAPTURE_TEST_MODE', 'false').lower() == 'true'
        
        # 扩展域名过滤，包含小红书、微博、B站的主要API域名
        self.filter_domains = [
            # 小红书域名
            "www.xiaohongshu.com",
            "edith.xiaohongshu.com",  # API域名
            "www.xiaohongshu.com/explore",
            "fe-api.xiaohongshu.com",  # 前端API域名
            
            # 微博域名
            "m.weibo.cn",
            "weibo.cn",
            "api.weibo.cn",
            "m.weibo.com",
            "weibo.com",
            "api.weibo.com",
            
            # B站域名
            "www.bilibili.com",
            "api.bilibili.com",
            "search.bilibili.com",
            "space.bilibili.com",
            "passport.bilibili.com"
        ]
        
        # 测试模式下降低保存阈值
        self.save_threshold = 1 if self.test_mode else 10
        
        ctx.log.info(f"RequestCapture初始化完成")
        ctx.log.info(f"测试模式: {'开启' if self.test_mode else '关闭'}")
        ctx.log.info(f"保存阈值: {self.save_threshold}条")
        ctx.log.info(f"监控域名: {', '.join(self.filter_domains)}")
    
    def request(self, flow: http.HTTPFlow):
        self.request_count += 1
        print(1)
        
        # 按域名过滤请求
        url_matched = any(domain in flow.request.url for domain in self.filter_domains)
        
        if self.test_mode:
            ctx.log.info(f"请求 #{self.request_count}: {flow.request.method} {flow.request.url}")
            ctx.log.info(f"域名匹配: {'是' if url_matched else '否'}")
        
        if not url_matched:
            return
        
        entry = {
            "url": flow.request.url,
            "method": flow.request.method,
            "headers": dict(flow.request.headers),
            "timestamp": time.time(),
            "capture_time": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if flow.request.content:
            try:
                entry["request_body"] = flow.request.text
            except:
                entry["request_body"] = "[binary data]"
        
        flow.metadata["capture"] = entry  # 暂存到元数据
        
        ctx.log.info(f"✅ 捕获请求: {flow.request.method} {flow.request.url}")

    def response(self, flow: http.HTTPFlow):
        if "capture" not in flow.metadata:
            return
        
        self.response_count += 1
        capture = flow.metadata["capture"]
        capture["status_code"] = flow.response.status_code
        capture["response_headers"] = dict(flow.response.headers)
        
        if flow.response.content:
            try:
                response_text = flow.response.text
                capture["response_body"] = response_text
                
                # 尝试解析JSON响应
                try:
                    json_data = json.loads(response_text)
                    capture["response_json"] = json_data
                    
                    # 检查是否包含小红书feed数据
                    if "data" in json_data and "items" in json_data.get("data", {}):
                        items_count = len(json_data["data"]["items"])
                        ctx.log.info(f"🎯 发现小红书feed数据: {items_count}条内容")
                        capture["feed_items_count"] = items_count
                        capture["platform"] = "xiaohongshu"
                    
                    # 检查是否包含微博数据
                    elif "data" in json_data and "cards" in json_data.get("data", {}):
                        cards_count = len(json_data["data"]["cards"])
                        ctx.log.info(f"🎯 发现微博cards数据: {cards_count}条内容")
                        capture["cards_count"] = cards_count
                        capture["platform"] = "weibo"
                    elif "statuses" in json_data:
                        statuses_count = len(json_data["statuses"])
                        ctx.log.info(f"🎯 发现微博statuses数据: {statuses_count}条内容")
                        capture["statuses_count"] = statuses_count
                        capture["platform"] = "weibo"
                    
                    # 检查是否包含B站数据
                    elif "data" in json_data and "result" in json_data.get("data", {}):
                        result_data = json_data["data"]["result"]
                        if isinstance(result_data, list) and len(result_data) > 0:
                            total_items = sum(len(item.get("data", [])) for item in result_data if "data" in item)
                            ctx.log.info(f"🎯 发现B站搜索数据: {total_items}条内容")
                            capture["bilibili_items_count"] = total_items
                            capture["platform"] = "bilibili"
                    elif "data" in json_data and "list" in json_data.get("data", {}):
                        list_count = len(json_data["data"]["list"])
                        ctx.log.info(f"🎯 发现B站列表数据: {list_count}条内容")
                        capture["bilibili_list_count"] = list_count
                        capture["platform"] = "bilibili"
                        
                except json.JSONDecodeError:
                    pass
                    
            except:
                capture["response_body"] = "[binary data]"
        
        # 记录到内存
        self.captured_data.append(capture)
        
        ctx.log.info(f"✅ 捕获响应: {capture['status_code']} {capture['url']}")
        
        if self.test_mode:
            print(f"=== 捕获数据 #{len(self.captured_data)} ===")
            print(f"URL: {capture['url']}")
            print(f"状态码: {capture['status_code']}")
            print(f"时间: {capture['capture_time']}")
            
            # 显示平台特定的数据统计
            if 'platform' in capture:
                print(f"平台: {capture['platform']}")
                
            if 'feed_items_count' in capture:
                print(f"小红书Feed条数: {capture['feed_items_count']}")
            if 'cards_count' in capture:
                print(f"微博Cards条数: {capture['cards_count']}")
            if 'statuses_count' in capture:
                print(f"微博Statuses条数: {capture['statuses_count']}")
            if 'bilibili_items_count' in capture:
                print(f"B站搜索条数: {capture['bilibili_items_count']}")
            if 'bilibili_list_count' in capture:
                print(f"B站列表条数: {capture['bilibili_list_count']}")
                
            print("=" * 50)
        
        # 根据阈值保存数据
        if len(self.captured_data) >= self.save_threshold:
            self.save_data()
    
    def save_data(self):
        if not self.captured_data:
            return
        
        # 确保输出目录存在
        os.makedirs("captured_data", exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"captured_data/captured_{timestamp}.json"
        
        # 添加统计信息
        stats = {
            "capture_stats": {
                "total_requests": self.request_count,
                "total_responses": self.response_count,
                "captured_count": len(self.captured_data),
                "start_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.start_time)),
                "save_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "test_mode": self.test_mode
            },
            "captured_data": self.captured_data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        ctx.log.info(f"💾 已保存 {len(self.captured_data)} 条记录到 {filename}")
        
        if self.test_mode:
            print(f"\n📊 统计信息:")
            print(f"总请求数: {self.request_count}")
            print(f"总响应数: {self.response_count}")
            print(f"捕获数据: {len(self.captured_data)}条")
            print(f"保存文件: {filename}")
            print("-" * 50)
        
        self.captured_data = []  # 清空缓存

addons = [RequestCapture()]