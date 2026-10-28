@echo off
REM LX04 Auth Companion - 安装脚本

echo ========================================
echo LX04 AI 命令授权应用 - 安装
echo ========================================
echo.

REM 检查 ADB
adb version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 ADB，请先安装 Android Platform Tools
    pause
    exit /b 1
)

REM 检查 APK 是否存在
if not exist "app\build\outputs\apk\debug\app-debug.apk" (
    echo [错误] APK 文件不存在，请先运行 build.bat 编译
    pause
    exit /b 1
)

REM 连接 LX04
echo 正在连接 LX04...
adb connect 192.168.1.20:5555

if errorlevel 1 (
    echo.
    echo [失败] 无法连接到 LX04
    echo 请确认：
    echo 1. LX04 已开启 USB 调试
    echo 2. LX04 和 PC 在同一 WiFi 网络
    echo 3. LX04 的 IP 地址是 192.168.1.20
    pause
    exit /b 1
)

REM 安装 APK
echo.
echo 正在安装应用...
adb install app\build\outputs\apk\debug\app-debug.apk

if errorlevel 1 (
    echo.
    echo [失败] 安装失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo 安装成功！
echo ========================================
echo.
echo 在 LX04 上：
echo 1. 进入"英语绘本"
echo 2. 找到"AuthCompanion"应用
echo 3. 打开应用
echo.
echo 在 PC 上：
echo 1. 运行授权服务：python pc_auth_server.py
echo 2. AI 执行命令时会自动请求授权
echo.
pause
