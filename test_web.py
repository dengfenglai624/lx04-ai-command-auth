"""
测试授权系统 - 演示 AI 如何请求授权
"""
import requests
import time

PC_IP = "192.168.1.10"
WEB_PORT = 8080

def test_authorization():
    """测试提交命令并等待授权"""
    print("=" * 50)
    print("测试 AI 命令授权系统")
    print("=" * 50)
    print()

    # 测试 1: 提交一个命令
    print("1. 提交测试命令...")
    try:
        # 直接通过 Web 界面的 API 提交
        response = requests.post(
            f"http://{PC_IP}:{WEB_PORT}/api/test",
            json={
                "command": "echo 'Hello from AI'",
                "description": "测试命令 - 打印问候语",
                "risk_level": "low"
            },
            timeout=5
        )
        print(f"   响应：{response.status_code}")
    except Exception as e:
        print(f"   注意：{e}")
        print("   这是正常的，因为 Web 版本使用不同的 API")

    print()
    print("2. 请在 LX04 上操作：")
    print("   - 打开浏览器")
    print("   - 访问：http://192.168.1.10:8080")
    print("   - 或者打开文件：/sdcard/AuthCompanion/index.html")
    print()
    print("3. 在 PC 上按 Ctrl+C 停止服务")
    print()

    # 轮询等待
    print("等待授权请求...")
    try:
        while True:
            response = requests.get(f"http://{PC_IP}:{WEB_PORT}/api/pending", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if len(data) > 0:
                    print(f"  发现 {len(data)} 个待授权命令")
                    for cmd in data:
                        print(f"    - {cmd['command']}")
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n测试结束")


if __name__ == "__main__":
    test_authorization()
