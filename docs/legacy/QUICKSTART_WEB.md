# LX04 AI 命令授权系统 - Web 版

## 快速开始

### 步骤 1：在 PC 上启动授权服务

打开命令提示符，运行：

```cmd
cd C:\Users\VALEO\Documents\Qoder\2026-10-21\17272210\firmware_work\lx04_auth
python web_auth_server.py
```

你会看到：
```
==================================================
  LX04 AI 命令授权系统 - Web 版
==================================================

  本机 IP: 192.168.1.10
  授权服务：http://192.168.1.10:9090
  Web 界面：http://192.168.1.10:8080

  在 LX04 浏览器中打开：
  http://192.168.1.10:8080

  按 Ctrl+C 停止服务
==================================================
```

**保持这个窗口打开！**

---

### 步骤 2：在 LX04 上打开授权界面

**方法 A：通过浏览器访问（推荐）**

1. 在 LX04 上打开浏览器
2. 访问：`http://192.168.1.10:8080`
3. 看到授权界面

**方法 B：打开本地文件**

1. 在 LX04 上进入"英语绘本" → 设置 → 存储
2. 找到文件管理器
3. 进入 `AuthCompanion` 文件夹
4. 点击 `index.html`
5. 点击"打开授权界面"按钮

---

### 步骤 3：测试授权

在 PC 上打开另一个命令提示符：

```cmd
cd C:\Users\VALEO\Documents\Qoder\2026-10-21\17272210\firmware_work\lx04_auth
python test_web.py
```

或者手动测试：

```cmd
curl -X POST http://192.168.1.10:8080/api/test ^
    -H "Content-Type: application/json" ^
    -d "{\"command\":\"echo test\",\"description\":\"测试\",\"risk_level\":\"low\"}"
```

---

## 在 AI 代码中使用

### Python 示例

```python
import requests

PC_IP = "192.168.1.10"
WEB_PORT = 8080

def request_authorization(command, description="", risk_level="medium", timeout=120):
    """
    请求用户授权命令
    返回 True 如果授权，False 如果拒绝或超时
    """
    import time

    # 提交命令
    response = requests.post(
        f"http://{PC_IP}:{WEB_PORT}/api/command",
        json={
            "command": command,
            "description": description,
            "risk_level": risk_level
        },
        timeout=5
    )

    if response.status_code != 200:
        return False

    cmd_id = response.json().get("id")
    print(f"等待授权：{command}")

    # 轮询等待结果
    start_time = time.time()
    while time.time() - start_time < timeout:
        time.sleep(1)

        # 检查历史
        history_response = requests.get(
            f"http://{PC_IP}:{WEB_PORT}/api/history",
            timeout=5
        )

        if history_response.status_code == 200:
            history = history_response.json()
            for cmd in history:
                if cmd.get("id") == cmd_id:
                    if cmd["status"] == "authorized":
                        print(f"已授权：{command}")
                        return True
                    else:
                        print(f"已拒绝：{command}")
                        return False

    print(f"超时：{command}")
    return False


# 使用示例
if request_authorization(
    command="pip install requests",
    description="安装 requests 库",
    risk_level="low"
):
    import os
    os.system("pip install requests")
else:
    print("命令未执行")
```

---

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | Web 授权界面 |
| `/api/pending` | GET | 获取待授权命令列表 |
| `/api/history` | GET | 获取授权历史 |
| `/api/auth` | POST | 提交授权结果 |

### 提交授权结果

```json
POST /api/auth
{
    "id": "命令 ID",
    "authorized": true
}
```

---

## 文件说明

```
lx04_auth/
── web_auth_server.py      # PC 端 Web 授权服务（主要文件）
├── test_web.py             # 测试脚本
├── QUICKSTART_WEB.md       # 本文档
── app/                    # Android 应用版本（可选）
    └── src/main/
        └── ...
```

---

## 常见问题

### Q: LX04 无法访问 PC 的 Web 界面

**A:** 检查：
1. PC 防火墙是否允许 8080 端口
2. LX04 和 PC 是否在同一 WiFi
3. PC IP 地址是否正确

开放防火墙端口：
```cmd
netsh advfirewall firewall add rule name="LX04 Auth" dir=in action=allow protocol=TCP localport=8080
```

### Q: 服务启动失败

**A:** 端口可能被占用，修改 `web_auth_server.py` 中的端口：
```python
WEB_PORT = 8081  # 改为其他端口
```

### Q: 如何在 Codex/Claude 中集成

**A:** 在 AI 执行命令前调用 `request_authorization()` 函数，示例见上方代码。

---

## 下一步

- [ ] 添加声音提醒
- [ ] 添加命令分类
- [ ] 添加自动授权规则
- [ ] 添加授权统计图表
- [ ] 支持 HTTPS 加密

---

## 技术支持

遇到问题？
1. 检查 PC 终端输出
2. 查看 LX04 浏览器控制台
3. 确认网络连接正常
