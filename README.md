# LX04 AI 命令授权系统

为小爱触屏音箱 LX04 开发的 AI 命令授权系统，类似 Codex/Work Buddy 的屏幕弹出授权界面。当 AI 需要执行命令时，LX04 屏幕会弹出 YES/NO 授权窗口。

## 📺 准备工作

**重要：在开始本项目之前，你需要先完成小米音箱的刷机！**

请参考 Bilibili 教程完成刷机：
👉 [小米小爱触屏音箱 LX04 刷机教程](https://www.bilibili.com/video/BV1fu4y1U7xz/)

### 刷机要求
- ✅ 完成 SP5 或更高版本的修改固件刷入
- ✅ 开启 ADB 调试功能（通过"英语绘本"隐藏菜单进入设置）
- ✅ 能够通过 WiFi 连接 ADB（默认 IP: 192.168.123.134:5555）

### 刷机材料
- 小爱触屏音箱 LX04 刷机资料包
- SP Flash Tool 刷机工具
- MTK 驱动程序
- 修改版固件（推荐 SP5）

**注意：** 刷机会影响设备保修，请谨慎操作！

## 🎯 项目简介

本项目实现了一个完整的 AI 命令授权系统：

1. **PC 端授权服务器** (`web_auth_server.py`)
   - 运行在电脑上
   - 提供 Web 界面和 API
   - 管理待授权命令队列

2. **LX04 端授权应用** (`codex_app/`)
   - Android 应用
   - 悬浮窗显示授权请求
   - 支持 Codex 和 Work Buddy 两种模式
   - 实时轮询 PC 服务器

3. **授权流程**
   ```
   AI 助手 → 提交命令到 PC 服务器 → LX04 弹出授权窗口 → 
   用户点击 YES/NO → 结果返回 PC → AI 执行或取消命令
   ```

## 🛠️ 系统要求

### PC 端
- Python 3.6+
- 局域网连接（与 LX04 同一网络）

### LX04 端
- 已完成刷机的 LX04（Android 8.1+）
- ADB 调试已开启
- 悬浮窗权限

## 📦 安装步骤

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd lx04-auth
```

### 2. 安装 PC 端依赖

```bash
pip install -r requirements.txt
```

### 3. 编译 LX04 应用

#### 方法 A：使用 Android Studio（推荐）

1. 用 Android Studio 打开 `codex_app/` 目录
2. 等待 Gradle 同步完成
3. 点击 Build → Build APK
4. APK 生成在 `app/build/outputs/apk/debug/app-debug.apk`

#### 方法 B：命令行编译

```bash
# 设置环境变量
export JAVA_HOME="/path/to/jdk-21"  # 需要 Java 21
export ANDROID_HOME="/path/to/android-sdk"

# 安装 SDK 组件
sdkmanager "platform-tools" "build-tools;34.0.0" "platforms;android-34"

# 编译
cd codex_app
gradle assembleDebug
```

**注意：** 
- 必须使用 Java 21（Java 25 不兼容 Gradle 8.12）
- 必须使用 Gradle 8.12+（支持 Java 21）
- Android SDK API 级别 34

### 4. 安装应用到 LX04

```bash
# 连接 ADB
adb connect 192.168.123.134:5555

# 安装 APK
adb install app/build/outputs/apk/debug/app-debug.apk

# 授予悬浮窗权限
adb shell appops set com.lx04.codexauth SYSTEM_ALERT_WINDOW allow
```

## 🚀 使用方法

### 1. 启动 PC 授权服务器

```bash
python web_auth_server.py
```

服务器会在 `http://<你的PC-IP>:8080` 启动。

### 2. 配置 LX04 应用

1. 在 LX04 上打开"Codex 授权"应用
2. 授予悬浮窗权限（首次运行）
3. 选择模式：
   - **CODEX** - Codex 模式
   - **WORK BUDDY** - Work Buddy 模式
4. 服务自动启动，开始轮询 PC 服务器

### 3. AI 集成示例

在你的 AI 助手代码中：

```python
from web_auth_server import check_authorization

# 执行命令前请求授权
if check_authorization(
    command="rm -rf /tmp/test",
    description="删除临时文件",
    risk_level="medium",
    timeout=60
):
    # 用户点击了 YES
    execute_command()
else:
    # 用户点击了 NO 或超时
    print("命令被拒绝")
```

### 4. 测试授权流程

```bash
# 运行测试脚本
python test_workbuddy.py
```

测试脚本会发送三个不同风险等级的命令，观察 LX04 屏幕是否弹出授权窗口。

## 📱 界面说明

### 主界面
- **CODEX 按钮**（蓝色）- 启动 Codex 模式
- **WORK BUDDY 按钮**（紫色）- 启动 Work Buddy 模式
- **停止服务按钮**（红色）- 停止授权服务

### 授权弹窗
- 黑色半透明背景
- 显示命令内容（等宽字体）
- 显示命令描述
- 风险等级标签（低/中/高）
- **NO 按钮**（红色）- 拒绝命令
- **YES 按钮**（绿色）- 授权命令

## 🔧 配置说明

### 修改 PC 服务器地址

编辑 `codex_app/app/src/main/java/com/lx04/codexauth/OverlayService.java`:

```java
private String pcServerUrl = "http://你的PC-IP:8080";
```

然后重新编译并安装应用。

### 修改端口

编辑 `web_auth_server.py`:

```python
PC_PORT = 9090    # PC 授权服务端口
WEB_PORT = 8080   # Web 界面端口
```

## 🐛 常见问题

### 1. 应用闪退
**原因：** 使用了 Java 9+ API（如 `readAllBytes()`）
**解决：** 已修复，使用 `BufferedReader` 替代

### 2. 服务无法启动
**原因：** Android 8.0+ 需要使用 `startForegroundService()`
**解决：** 已修复，根据系统版本选择正确的启动方式

### 3. LX04 无法连接 PC
**检查：**
- PC 和 LX04 是否在同一局域网
- PC 防火墙是否允许 8080 端口
- PC IP 地址是否正确（在 LX04 应用中配置）

### 4. 授权弹窗不显示
**检查：**
- 是否已授予悬浮窗权限
- 服务是否正在运行
- PC 服务器是否启动

## 📂 项目结构

```
lx04-auth/
├── web_auth_server.py          # PC 端授权服务器
├── requirements.txt            # Python 依赖
├── test_workbuddy.py          # Work Buddy 测试脚本
├── test_codex.py              # Codex 测试脚本
├── codex_app/                 # LX04 Android 应用
│   ├── app/
│   │   ├── src/main/
│   │   │   ├── java/com/lx04/codexauth/
│   │   │   │   ├── MainActivity.java
│   │   │   │   ├── OverlayService.java
│   │   │   │   └── BootReceiver.java
│   │   │   ├── res/layout/
│   │   │   │   ├── activity_main.xml
│   │   │   │   └── floating_auth.xml
│   │   │   └── AndroidManifest.xml
│   │   └── build.gradle
│   ├── build.gradle
│   ├── settings.gradle
│   ├── gradle.properties
│   └── local.properties
└── README.md                  # 本文件
```

## 🔒 安全说明

- 所有通信在局域网内进行，不经过互联网
- 授权请求超时时间默认 120 秒
- 高风险命令会显示红色警告
- 用户可以随时拒绝任何命令

## 📝 开发计划

- [ ] 支持自定义风险等级颜色
- [ ] 添加命令历史记录
- [ ] 支持批量授权
- [ ] WebSocket 实时通信（替代轮询）
- [ ] 支持多个 LX04 设备
- [ ] 移动端管理界面

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- 感谢 Bilibili UP 主提供的 LX04 刷机教程
- 感谢小米社区的反编译资料
- 感谢 Android 开源项目

## 📞 联系方式

如有问题，请通过 GitHub Issues 联系。

---

**免责声明：** 本项目仅供学习和研究使用。刷机有风险，操作需谨慎。因使用本项目导致的设备损坏或其他损失，作者不承担任何责任。
