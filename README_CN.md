# LX04 AI 命令授权系统

为小爱触屏音箱 LX04 开发的 AI 命令授权系统，类似 Codex/Work Buddy 的屏幕弹出授权界面。当 AI 需要执行命令时，LX04 屏幕会弹出 YES/NO 授权窗口。

## 📺 准备工作

**⚠️ 重要：在开始本项目之前，你需要先完成小米音箱的刷机！**

请参考 Bilibili 教程完成刷机：
👉 [小米小爱触屏音箱 LX04 刷机教程](https://www.bilibili.com/video/BV1fu4y1U7xz/)

### 刷机要求
- ✅ 完成 SP5 或更高版本的修改固件刷入
- ✅ 开启 ADB 调试功能（通过"英语绘本"隐藏菜单进入设置）
- ✅ 能够通过 WiFi 连接 ADB（默认 IP: 192.168.123.134:5555）

### 刷机材料准备
1. **下载刷机资料包**（包含以下内容）：
   - SP Flash Tool 刷机工具
   - MTK 驱动程序
   - 修改版固件（推荐 SP5）
   - 刷机教程文档

2. **进入 BROM 模式**：
   - 关机状态下按住 **音量+** 键
   - 连接 USB 到电脑
   - 等待 SP Flash Tool 识别设备

3. **刷入固件**：
   - 打开 SP Flash Tool
   - 加载 scatter 文件
   - 点击 Download
   - 等待刷机完成

**注意：** 刷机会影响设备保修，请谨慎操作！

## 🎯 项目简介

本项目实现了一个完整的 AI 命令授权系统：

### 系统架构

```
┌─────────────┐
│  AI 助手    │
│ (Codex/WB)  │
└──────┬──────┘
       │ 1. 提交命令
       ▼
┌─────────────────┐
│  PC 授权服务器   │
│  (Python)       │
│  端口: 8080     │
└──────┬──────────┘
       │ 2. 轮询待授权命令
       ▼
┌─────────────────┐
│  LX04 授权应用   │
│  (Android)      │
└──────┬──────────┘
       │ 3. 显示授权弹窗
       ▼
┌─────────────────┐
│  用户点击       │
│  YES / NO       │
└──────┬──────────┘
       │ 4. 返回授权结果
       ▼
┌─────────────────┐
│  AI 执行/取消   │
│  命令           │
└─────────────────┘
```

### 核心组件

1. **PC 端授权服务器** (`web_auth_server.py`)
   - 运行在电脑上
   - 提供 Web 界面和 REST API
   - 管理待授权命令队列
   - 记录授权历史

2. **LX04 端授权应用** (`codex_app/`)
   - Android 原生应用
   - 悬浮窗显示授权请求
   - 支持 Codex 和 Work Buddy 两种模式
   - 每 2 秒轮询 PC 服务器
   - 开机自动启动

3. **授权流程**
   - AI 提交命令 → PC 服务器接收 → LX04 弹出窗口 → 用户授权 → 结果返回

## 🛠️ 系统要求

### PC 端
- Windows 10/11 或 Linux
- Python 3.6+
- 局域网连接（与 LX04 同一网络）
- 防火墙允许 8080 端口

### LX04 端
- 已完成刷机的 LX04（Android 8.1+，API 27+）
- ADB 调试已开启
- 悬浮窗权限
- 与 PC 在同一局域网

### 开发环境
- Java 21（必须，Java 25 不兼容）
- Android SDK API 34
- Gradle 8.12+
- Android Studio（可选，推荐）

## 📦 安装步骤

### 步骤 1：克隆项目

```bash
git clone https://github.com/your-username/lx04-auth.git
cd lx04-auth
```

### 步骤 2：安装 PC 端依赖

```bash
# 本项目仅使用 Python 标准库，无需安装额外依赖
# 但建议创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 步骤 3：编译 LX04 应用

#### 方法 A：使用 Android Studio（推荐新手）

1. **下载并安装 Android Studio**
   - 访问 https://developer.android.com/studio
   - 下载并安装最新版本

2. **打开项目**
   - File → Open → 选择 `codex_app/` 目录
   - 等待 Gradle 同步完成（首次可能需要下载依赖）

3. **配置 SDK**
   - File → Settings → Languages & Frameworks → Android SDK
   - 安装 SDK Platform 34
   - 安装 Build-Tools 34.0.0

4. **编译 APK**
   - Build → Build Bundle(s) / APK(s) → Build APK(s)
   - 等待编译完成
   - APK 位置：`app/build/outputs/apk/debug/app-debug.apk`

#### 方法 B：命令行编译（适合有经验的用户）

```bash
# 1. 设置环境变量
export JAVA_HOME="/c/Program Files/Microsoft/jdk-21.0.12.101-hotspot"
export ANDROID_HOME="/c/Users/你的用户名/android-sdk"
export PATH="$JAVA_HOME/bin:$ANDROID_HOME/platform-tools:$PATH"

# 2. 下载 Gradle 8.12
cd codex_app
curl -L -o gradle.zip "https://mirrors.cloud.tencent.com/gradle/gradle-8.12-bin.zip"
unzip gradle.zip

# 3. 安装 SDK 组件
sdkmanager "platform-tools" "build-tools;34.0.0" "platforms;android-34"

# 4. 编译
gradle assembleDebug

# 5. APK 位置
ls app/build/outputs/apk/debug/app-debug.apk
```

**⚠️ 重要提示：**
- 必须使用 **Java 21**（Java 25 会导致 Gradle 崩溃）
- 必须使用 **Gradle 8.12+**（支持 Java 21）
- 国内用户建议使用腾讯镜像下载 Gradle

### 步骤 4：安装应用到 LX04

```bash
# 1. 连接 ADB
adb connect 192.168.123.134:5555

# 2. 验证连接
adb devices
# 应该看到: 192.168.123.134:5555  device

# 3. 安装 APK
adb install app/build/outputs/apk/debug/app-debug.apk

# 4. 授予悬浮窗权限
adb shell appops set com.lx04.codexauth SYSTEM_ALERT_WINDOW allow

# 5. 启动应用
adb shell am start -n com.lx04.codexauth/.MainActivity
```

## 🚀 使用方法

### 1. 启动 PC 授权服务器

```bash
python web_auth_server.py
```

你会看到：
```
==================================================
  LX04 AI 命令授权系统 - Web 版
==================================================
  Web 界面: http://192.168.123.38:8080
  API 端口: 9090
==================================================
```

### 2. 配置 LX04 应用

1. 在 LX04 上打开"Codex 授权"应用
2. 首次运行会请求悬浮窗权限，点击"允许"
3. 选择模式：
   - 点击 **CODEX**（蓝色按钮）- Codex 模式
   - 点击 **WORK BUDDY**（紫色按钮）- Work Buddy 模式
4. 看到"🟢 服务运行中"表示成功

### 3. AI 集成示例

在你的 AI 助手代码中导入授权模块：

```python
from web_auth_server import check_authorization

# 示例 1：低风险命令
if check_authorization(
    command="ls -la /home",
    description="列出主目录文件",
    risk_level="low",
    timeout=60
):
    # 用户点击了 YES，执行命令
    os.system("ls -la /home")
else:
    # 用户点击了 NO 或超时
    print("命令被拒绝")

# 示例 2：高风险命令
if check_authorization(
    command="rm -rf /tmp/*",
    description="清理临时文件",
    risk_level="high",
    timeout=120
):
    os.system("rm -rf /tmp/*")
```

### 4. 测试授权流程

```bash
# 运行测试脚本
python test_workbuddy.py
```

测试会依次发送三个命令：
1. 低风险（ls）- 绿色标签
2. 中风险（rm）- 黄色标签
3. 高风险（format）- 红色标签

观察 LX04 屏幕是否弹出对应的授权窗口。

## 📱 界面说明

### LX04 主界面

```
┌─────────────────────────┐
│    AI 授权助手           │
│   选择 AI 助手模式       │
│                         │
│  ✅ 悬浮窗权限已授予     │
│                         │
│  ┌─────────────────┐   │
│  │    CODEX        │   │
│  │   (蓝色按钮)     │   │
│  └─────────────────┘   │
│                         │
│  ┌─────────────────┐   │
│  │  WORK BUDDY     │   │
│  │   (紫色按钮)     │   │
│  └─────────────────┘   │
│                         │
│  ┌─────────────────┐   │
│  │   停止服务       │   │
│  │   (红色按钮)     │   │
│  └─────────────────┘   │
└─────────────────────────┘
```

### 授权弹窗

```
┌─────────────────────────┐
│  AI 请求执行命令         │
│                         │
│  [低风险]               │
│                         │
│  ┌───────────────────┐ │
│  │ ls -la /home/user │ │
│  └───────────────────┘ │
│                         │
│  列出用户主目录文件      │
│                         │
│  ┌──────┐  ┌──────┐   │
│  │  NO  │  │ YES  │   │
│  │(红色)│  │(绿色)│   │
│  └──────┘  └──────┘   │
└─────────────────────────┘
```

## 🔧 配置说明

### 修改 PC 服务器地址

编辑 `codex_app/app/src/main/java/com/lx04/codexauth/OverlayService.java`:

```java
// 第 38 行
private String pcServerUrl = "http://你的PC-IP:8080";
```

然后重新编译并安装应用。

### 修改端口

编辑 `web_auth_server.py`:

```python
# 第 13-14 行
PC_PORT = 9090    # PC 授权服务端口（用于 API）
WEB_PORT = 8080   # Web 界面端口（用于显示）
```

### 获取 PC IP 地址

**Windows:**
```bash
ipconfig
# 查找 "IPv4 地址"，例如 192.168.123.38
```

**Linux/Mac:**
```bash
ifconfig | grep inet
# 或
ip addr show | grep inet
```

## 🐛 常见问题

### 1. 应用闪退

**错误信息：**
```
java.lang.NoSuchMethodError: No virtual method readAllBytes()
```

**原因：** 使用了 Java 9+ API，但 Android 8.1 只支持 Java 8

**解决：** 已修复！使用 `BufferedReader` 替代 `readAllBytes()`

### 2. 服务无法启动

**错误信息：**
```
Background execution not allowed
```

**原因：** Android 8.0+ 对后台服务有限制

**解决：** 已修复！使用 `startForegroundService()` 替代 `startService()`

### 3. LX04 无法连接 PC

**症状：** 授权弹窗不出现

**检查步骤：**
1. 确认 PC 和 LX04 在同一局域网
2. 检查 PC 防火墙是否允许 8080 端口
3. 在 LX04 上测试连接：
   ```bash
   adb shell ping 192.168.123.38
   ```
4. 确认 PC 服务器正在运行
5. 检查 LX04 应用中的 IP 地址配置

### 4. 授权弹窗不显示

**可能原因：**
- 未授予悬浮窗权限
- 服务未启动
- PC 服务器未运行

**解决：**
```bash
# 检查权限
adb shell appops get com.lx04.codexauth

# 授予权限
adb shell appops set com.lx04.codexauth SYSTEM_ALERT_WINDOW allow

# 检查服务
adb shell ps | grep codexauth

# 重启服务
adb shell am force-stop com.lx04.codexauth
adb shell am start -n com.lx04.codexauth/.MainActivity
```

### 5. Gradle 编译失败

**错误：**
```
Unsupported class file major version 69
```

**原因：** Java 25 与 Gradle 8.12 不兼容

**解决：** 使用 Java 21
```bash
export JAVA_HOME="/path/to/jdk-21"
```

## 📂 项目结构

```
lx04-auth/
├── README.md                      # 英文文档
├── README_CN.md                   # 中文文档（本文件）
├── requirements.txt               # Python 依赖（空）
├── .gitignore                     # Git 忽略文件
│
├── web_auth_server.py            # PC 端授权服务器
├── test_workbuddy.py             # Work Buddy 测试脚本
├── test_codex.py                 # Codex 测试脚本
│
└── codex_app/                    # LX04 Android 应用
    ├── app/
    │   ├── src/main/
    │   │   ├── java/com/lx04/codexauth/
    │   │   │   ├── MainActivity.java       # 主界面
    │   │   │   ├── OverlayService.java     # 悬浮窗服务
    │   │   │   └── BootReceiver.java       # 开机自启
    │   │   ├── res/layout/
    │   │   │   ├── activity_main.xml       # 主界面布局
    │   │   │   └── floating_auth.xml       # 授权弹窗布局
    │   │   ├── res/mipmap-anydpi-v26/
    │   │   │   ├── ic_launcher.xml         # 应用图标
    │   │   │   └── ic_launcher_round.xml
    │   │   └── AndroidManifest.xml         # 应用清单
    │   └── build.gradle                    # 模块构建配置
    ├── build.gradle                        # 项目构建配置
    ├── settings.gradle                     # 项目设置
    ├── gradle.properties                   # Gradle 属性
    └── local.properties                    # 本地 SDK 路径
```

## 🔒 安全说明

- ✅ 所有通信在局域网内进行，不经过互联网
- ✅ 授权请求超时时间默认 120 秒
- ✅ 高风险命令会显示红色警告
- ✅ 用户可以随时拒绝任何命令
- ✅ 不存储敏感信息
- ✅ 开源代码可审计

## 📝 开发计划

- [ ] 支持自定义风险等级颜色
- [ ] 添加命令历史记录
- [ ] 支持批量授权
- [ ] WebSocket 实时通信（替代轮询）
- [ ] 支持多个 LX04 设备
- [ ] 移动端管理界面
- [ ] 语音授权支持
- [ ] 指纹/面部识别授权

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

MIT License

Copyright (c) 2026 LX04 Auth Project

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## 🙏 致谢

- 感谢 Bilibili UP 主提供的 [LX04 刷机教程](https://www.bilibili.com/video/BV1fu4y1U7xz/)
- 感谢小米社区的反编译资料分享
- 感谢 Android 开源项目
- 感谢所有贡献者

## 📞 联系方式

- GitHub Issues: [提交问题](https://github.com/your-username/lx04-auth/issues)
- Bilibili: [刷机教程](https://www.bilibili.com/video/BV1fu4y1U7xz/)

## 🌟 星标历史

[![Stargazers over time](https://starchart.cc/your-username/lx04-auth.svg)](https://starchart.cc/your-username/lx04-auth)

---

**⚠️ 免责声明：** 

本项目仅供学习和研究使用。刷机有风险，操作需谨慎。因使用本项目导致的设备损坏、数据丢失或其他损失，作者不承担任何责任。

请在刷机前备份重要数据，并确保您已了解所有风险。

---

**如果觉得本项目有用，请给个 Star ⭐ 支持一下！**
