"""
AI 命令授权示例 - 演示 Codex/Claude 如何使用授权系统
"""
import os
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from pc_auth_server import check_authorization


def example_safe_command():
    """示例：安全命令（低风险）"""
    print("\n=== 示例 1: 安全命令 ===")

    if check_authorization(
        command="echo 'Hello from AI'",
        description="打印问候语",
        risk_level="low",
        timeout=30
    ):
        os.system("echo 'Hello from AI'")
        print("✅ 命令已执行")
    else:
        print("❌ 命令未执行")


def example_medium_command():
    """示例：中等风险命令"""
    print("\n=== 示例 2: 中等风险命令 ===")

    if check_authorization(
        command="pip list",
        description="列出已安装的 Python 包",
        risk_level="medium",
        timeout=60
    ):
        os.system("pip list")
        print("✅ 命令已执行")
    else:
        print("❌ 命令未执行")


def example_high_risk_command():
    """示例：高风险命令"""
    print("\n=== 示例 3: 高风险命令 ===")

    if check_authorization(
        command="rm -rf /tmp/test_folder",
        description="删除临时测试文件夹",
        risk_level="high",
        timeout=60
    ):
        os.system("rm -rf /tmp/test_folder")
        print("✅ 命令已执行")
    else:
        print("❌ 命令未执行")


def example_file_operation():
    """示例：文件操作"""
    print("\n=== 示例 4: 文件操作 ===")

    if check_authorization(
        command="cat /etc/passwd",
        description="查看系统用户列表",
        risk_level="medium",
        timeout=60
    ):
        os.system("cat /etc/passwd")
        print("✅ 命令已执行")
    else:
        print("❌ 命令未执行")


if __name__ == "__main__":
    print("🤖 AI 命令授权示例")
    print("=" * 50)
    print("\n请确保：")
    print("1. PC 授权服务已运行 (python pc_auth_server.py)")
    print("2. LX04 应用已打开并连接到 PC")
    print("\n开始测试...\n")

    # 运行示例
    example_safe_command()
    example_medium_command()
    example_high_risk_command()
    example_file_operation()

    print("\n" + "=" * 50)
    print("测试完成！")
