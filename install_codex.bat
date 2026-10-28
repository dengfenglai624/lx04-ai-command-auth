@echo off
REM Codex Auth App - 安装脚本

echo ========================================
echo Codex 授权应用 - 安装到 LX04
echo ========================================
echo.

REM 检查 ADB
adb version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 ADB
    pause
    exit /b 1
)

REM 检查 APK
if not exist "codex_app\app\build\outputs\apk\debug\app-debug.apk" (
    echo [错误] APK 不存在，请先运行 build_codex.bat
    pause
    exit /b 1
)

REM 连接 LX04
echo 正在连接 LX04...
adb connect 192.168.1.20:5555

REM 安装
echo.
echo 正在安装...
adb install codex_app\app\build\outputs\apk\debug\app-debug.apk

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
echo 1. 打开"Codex 授权"应用
echo 2. 点击"授予悬浮窗权限"
echo 3. 在设置中开启权限
echo 4. 返回点击"启动授权服务"
echo.
echo 启动后，AI 执行命令时屏幕会弹出 YES/NO 窗口
echo.
pause
