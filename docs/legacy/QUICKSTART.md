# 快速开始 - LX04 AI 命令授权系统

## 5 分钟上手

### 步骤 1：启动 PC 授权服务

打开命令提示符：
```cmd
cd C:\Users\VALEO\Documents\Qoder\2026-10-21\17272210\firmware_work\lx04_auth
python pc_auth_server.py
```

看到以下输出表示成功：
```
🔐 授权服务已启动：http://0.0.0.0:9090
 LX04 地址：192.168.1.20:8080

等待命令授权请求...
```

**保持这个窗口打开！**

---

### 步骤 2：编译 Android 应用

**方法 A：使用 Android Studio（推荐）**
1. 打开 Android Studio
2. File → Open → 选择 `lx04_auth` 文件夹
3. 等待 Gradle 同步完成
4. Build → Build APK(s)
5. APK 位置：`app\build\outputs\apk\debug\app-debug.apk`

**方法 B：使用命令行**
```cmd
cd C:\Users\VALEO\Documents\Qoder\2026-10-21\17272210\firmware_work\lx04_auth
build.bat
```

---

### 步骤 3：安装到 LX04

**首先确保 LX04 已开启 USB 调试：**
1. 在 LX04 上进入"英语绘本" → 设置
2. 连续点击"版本号"7 次
3. 进入"开发者选项"
4. 打开"USB 调试"
5. 选择"MTP 模式"

**然后安装应用：**
```cmd
cd C:\Users\VALEO\Documents\Qoder\2026-10-21\17272210\firmware_work\lx04_auth
install.bat
```

或手动安装：
```cmd
adb connect 192.168.1.20:5555
adb install app\build\outputs\apk\debug\app-debug.apk
```

---

### 步骤 4：在 LX04 上打开应用

1. 进入"英语绘本"
2. 找到"AuthCompanion"应用
3. 点击打开
4. 看到"监听中..."表示成功

---

### 步骤 5：测试授权

打开另一个命令提示符：
```cmd
cd C:\Users\VALEO\Documents\Qoder\2026-10-21\17272210\firmware_work\lx04_auth
python test_auth.py
```

你会看到：
1. PC 终端显示"等待授权：echo 'Hello from AI'"
2. LX04 屏幕显示命令卡片
3. 在 LX04 上点击"允许"或"拒绝"
4. PC 终端显示结果

---

## 集成到 AI 代码

### Python 示例

```python
from pc_auth_server import check_authorization
import os

# 执行任何命令前请求授权
if check_authorization(
    command="your command here",
    description="描述这个命令做什么",
    risk_level="medium",  # low, medium, high
    timeout=60
):
    # 用户已授权
    os.system("your command here")
else:
    # 用户拒绝或超时
    print("命令未执行")
```

### 实际使用示例

```python
# 示例 1：安装软件
if check_authorization(
    command="pip install requests",
    description="安装 requests 库",
    risk_level="low"
):
    os.system("pip install requests")

# 示例 2：删除文件
if check_authorization(
    command="rm -rf /tmp/old_files",
    description="删除临时文件",
    risk_level="high"
):
    os.system("rm -rf /tmp/old_files")

# 示例 3：查看系统信息
if check_authorization(
    command="systeminfo",
    description="查看系统信息",
    risk_level="low"
):
    os.system("systeminfo")
```

---

## 常见问题

### Q: LX04 无法连接 PC

**A:** 检查以下几点：
1. PC 防火墙是否允许 9090 端口
2. LX04 和 PC 是否在同一 WiFi
3. PC IP 地址是否正确（运行 `ipconfig` 查看）

修改 `pc_auth_server.py` 中的 LX04 IP：
```python
LX04_IP = "192.168.1.20"  # 改为你的 LX04 IP
```

### Q: 应用闪退

**A:** 可能是网络权限问题：
1. 在 LX04 设置 → 应用 → AuthCompanion → 权限
2. 确保"网络"权限已开启

### Q: 命令提交后 LX04 没反应

**A:** 检查：
1. PC 授权服务是否正在运行
2. LX04 应用是否打开
3. 查看 PC 终端是否有错误信息

### Q: 如何修改 PC 端口

**A:** 编辑 `pc_auth_server.py`：
```python
PC_PORT = 9090  # 改为你想要的端口
```

同时修改 LX04 应用中的 `MainActivity.java`：
```java
private String pcServerUrl = "http://192.168.1.10:9090";  // 改为你的 PC IP 和端口
```

---

## 下一步

- [ ] 添加命令历史记录
- [ ] 添加声音提醒
- [ ] 添加自动授权规则
- [ ] 添加命令分类过滤
- [ ] 添加授权统计

---

## 技术支持

遇到问题？检查：
1. `README.md` - 完整文档
2. PC 终端输出 - 错误信息
3. LX04 logcat - `adb logcat | grep AuthCompanion`
