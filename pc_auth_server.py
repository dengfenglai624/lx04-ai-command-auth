"""
PC 端授权服务 - 接收 AI 命令请求，转发到 LX04 等待授权
"""
import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests

# 配置
LX04_IP = "192.168.123.134"  # LX04 的 IP 地址
LX04_PORT = 8080
PC_PORT = 9090

# 待授权命令队列
pending_commands = []
authorized_commands = []
denied_commands = []


class AuthServer(BaseHTTPRequestHandler):
    """授权服务器 - 接收 AI 的命令请求"""

    def do_POST(self):
        """接收新命令请求"""
        if self.path == "/api/command":
            content_length = int(self.headers["Content-Length"])
            body = json.loads(self.rfile.read(content_length))

            command_id = str(time.time())
            command = {
                "id": command_id,
                "command": body.get("command", ""),
                "description": body.get("description", ""),
                "risk_level": body.get("risk_level", "medium"),
                "timestamp": time.time(),
                "status": "pending",
            }

            pending_commands.append(command)

            # 转发到 LX04
            try:
                requests.post(
                    f"http://{LX04_IP}:{LX04_PORT}/api/notify",
                    json=command,
                    timeout=5,
                )
            except Exception as e:
                print(f"Failed to notify LX04: {e}")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"id": command_id, "status": "pending"}).encode())

        elif self.path == "/api/auth/result":
            """接收 LX04 的授权结果"""
            content_length = int(self.headers["Content-Length"])
            body = json.loads(self.rfile.read(content_length))

            command_id = body.get("id")
            authorized = body.get("authorized", False)

            # 更新命令状态
            for cmd in pending_commands:
                if cmd["id"] == command_id:
                    cmd["status"] = "authorized" if authorized else "denied"
                    if authorized:
                        authorized_commands.append(cmd)
                    else:
                        denied_commands.append(cmd)
                    pending_commands.remove(cmd)
                    break

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())

    def do_GET(self):
        """查询命令状态"""
        if self.path.startswith("/api/command/"):
            command_id = self.path.split("/")[-1]

            for cmd in pending_commands + authorized_commands + denied_commands:
                if cmd["id"] == command_id:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(cmd).encode())
                    return

            self.send_response(404)
            self.end_headers()

        elif self.path == "/api/pending":
            """获取所有待授权命令"""
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(pending_commands).encode())

    def log_message(self, format, *args):
        print(f"[{time.strftime('%H:%M:%S')}] {args[0]}")


def check_authorization(command, description="", risk_level="medium", timeout=60):
    """
    同步等待授权结果
    用于 AI 在執行命令前调用
    """
    # 发送命令到授权服务
    response = requests.post(
        f"http://localhost:{PC_PORT}/api/command",
        json={
            "command": command,
            "description": description,
            "risk_level": risk_level,
        },
        timeout=5,
    )

    if response.status_code != 200:
        return False

    command_id = response.json()["id"]
    print(f" 等待授权：{command}")
    print(f"   命令 ID: {command_id}")

    # 轮询等待结果
    start_time = time.time()
    while time.time() - start_time < timeout:
        time.sleep(1)

        for cmd in authorized_commands + denied_commands:
            if cmd["id"] == command_id:
                if cmd["status"] == "authorized":
                    print(f"✅ 已授权：{command}")
                    return True
                else:
                    print(f"❌ 已拒绝：{command}")
                    return False

    print(f"⏰ 授权超时：{command}")
    return False


def run_server():
    """启动授权服务器"""
    server = HTTPServer(("0.0.0.0", PC_PORT), AuthServer)
    print(f"🔐 授权服务已启动：http://0.0.0.0:{PC_PORT}")
    print(f" LX04 地址：{LX04_IP}:{LX04_PORT}")
    print(f"\n等待命令授权请求...")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")
        server.server_close()


if __name__ == "__main__":
    run_server()
