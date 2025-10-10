import pyshark
import json
from datetime import datetime
import os


def capture_chat_api_traffic(interface, target_host, target_endpoint):
    """
    捕获特定聊天API的网络流量

    Args:
        interface (str): 网络接口名称
        target_host (str): 目标主机域名
        target_endpoint (str): 目标API端点
    """
    # 构建显示过滤器
    display_filter = f'http contains "{target_host}" and http contains "{target_endpoint}"'

    try:
        # 创建实时捕获
        print(2222222222221)

        capture = pyshark.LiveCapture(
            interface=interface,
            display_filter=display_filter
        )
        print(2222222222222)

        print(f"开始捕获网络流量... 监听 {target_host}{target_endpoint}")
        print("等待API请求...")

        # 遍历捕获的数据包
        for packet in capture.sniff_continuously():
            try:
                if hasattr(packet, 'http') and hasattr(packet.http, 'response_for_uri'):
                    # 检查是否是目标请求的响应
                    if target_host in packet.http.response_for_uri and target_endpoint in packet.http.response_for_uri:
                        # 获取响应内容
                        if hasattr(packet.http, 'file_data'):
                            response_data = packet.http.file_data

                            # 尝试解析JSON响应
                            try:
                                json_data = json.loads(response_data)

                                # 保存响应数据到文件
                                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                                filename = f'chat_response_{timestamp}.json'

                                with open(filename, 'w', encoding='utf-8') as f:
                                    json.dump(json_data, f, ensure_ascii=False, indent=2)

                                print(f"\n成功捕获响应数据！已保存到文件: {filename}")
                                print("\n响应数据预览:")
                                print(json.dumps(json_data, ensure_ascii=False, indent=2)[:500] + "...")

                                # 询问是否继续捕获
                                user_input = input("\n是否继续捕获? (y/n): ")
                                if user_input.lower() != 'y':
                                    break

                            except json.JSONDecodeError:
                                print("警告: 捕获的响应不是有效的JSON格式")
                                continue

            except AttributeError as e:
                print(f"解析数据包时出现错误: {str(e)}")
                continue

    except KeyboardInterrupt:
        print("\n用户中断捕获")
    finally:
        capture.close()


def main():
    # 配置参数
    interface = '本地连接* 8'  # Windows通常是'Wi-Fi'或'Ethernet'，Linux通常是'eth0'或'wlan0'
    target_host = 'kimi.moonshot.cn'
    target_endpoint = '/api/chat/cu1i45kr4djrsk3joj20/segment/scroll'

    # 检查是否以管理员权限运行
    print(11111111111111111)
    # if os.name == 'nt' and not os.environ.get('USERNAME') == 'Administrator':
    #     print("警告: 此脚本需要管理员权限才能捕获网络流量")
    #     print("请以管理员身份重新运行此脚本")
    #     return

    # 开始捕获
    capture_chat_api_traffic(interface, target_host, target_endpoint)
    print(222222222222)


if __name__ == "__main__":
    print(1)
    main()
    print(2)
