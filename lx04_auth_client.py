"""
LX04 授权客户端 - 供外部 AI (WorkBuddy / Codex / 自研 Agent) 通过 HTTP 调用
不依赖服务器进程内部状态，可与运行中的 web_auth_server.py 跨进程通信

用法:
    from lx04_auth_client import request_authorization
    ok = request_authorization("rm -rf /tmp/x", "删除临时文件", "high")

环境变量:
    LX04_AUTH_SERVER  授权服务地址，默认 http://127.0.0.1:8080
"""
import json
import os
import time
import urllib.request

SERVER = os.environ.get("LX04_AUTH_SERVER", "http://127.0.0.1:8080").rstrip("/")


def request_authorization(command, description="", risk_level="medium", timeout=60):
    """
    提交命令并等待用户在 LX04 音箱上授权
    返回 True(允许) / False(拒绝或超时)
    """
    # 提交命令
    req = urllib.request.Request(
        SERVER + "/api/add",
        data=json.dumps({
            "command": command,
            "description": description,
            "risk_level": risk_level,
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        cmd_id = json.loads(resp.read())["id"]

    print(f"  命令 #{cmd_id} 已提交，等待音箱授权 (超时 {timeout}s)...")

    # 轮询结果
    start = time.time()
    while time.time() - start < timeout:
        time.sleep(1)
        with urllib.request.urlopen(f"{SERVER}/api/check/{cmd_id}", timeout=5) as resp:
            status = json.loads(resp.read())["status"]
        if status == "authorized":
            return True
        if status == "denied":
            return False
    return False


if __name__ == "__main__":
    result = request_authorization(
        command="echo hello from agent",
        description="连通性测试命令",
        risk_level="low",
        timeout=60,
    )
    print("授权结果:", "允许" if result else "拒绝/超时")
