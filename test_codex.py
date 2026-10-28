"""
测试 Codex 授权系统
"""
import sys
sys.path.insert(0, r'C:\Users\VALEO\Documents\Qoder\2026-10-21\17272210\firmware_work\lx04_auth')

from web_auth_server import check_authorization

print("发送测试命令到 LX04...")
print("请在 LX04 屏幕上点击 YES 或 NO")
print()

result = check_authorization(
    command="ls -la /home",
    description="列出主目录文件",
    risk_level="low",
    timeout=60
)

if result:
    print("\n✓ 命令已授权，可以执行")
else:
    print("\n✗ 命令被拒绝或超时")
