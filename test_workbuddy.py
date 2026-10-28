"""
Work Buddy 授权系统端到端测试
通过 HTTP API 向运行中的服务器提交命令，在 LX04 音箱上弹出授权窗口

先启动服务器: python web_auth_server.py
再运行本脚本，然后在音箱屏幕上点 ALLOW / DENY
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lx04_auth_client import SERVER, request_authorization

print("=" * 50)
print("  Work Buddy 授权系统端到端测试")
print(f"  服务器: {SERVER}")
print("  (命令将弹出到 LX04 音箱屏幕)")
print("=" * 50)
print()

print("测试: 低风险命令 (echo)")
print("-" * 50)
result = request_authorization(
    command="echo hello from workbuddy",
    description="WorkBuddy 连通性测试，无危险操作",
    risk_level="low",
    timeout=60,
)
print(f"结果: {'✓ 已授权' if result else '✗ 被拒绝或超时'}")
print()

if result:
    print("=" * 50)
    print("  ✓ 测试通过：音箱授权链路正常工作")
    print("  WorkBuddy 提交 → 服务器 → 音箱弹窗 → 用户点 YES → 返回允许")
    print("=" * 50)
else:
    print("=" * 50)
    print("  ✗ 未收到授权（检查音箱是否弹出窗口 / 是否点击）")
    print("=" * 50)
