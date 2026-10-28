@echo off
REM Codex Auth App - 编译脚本

echo ========================================
echo Codex 授权应用 - 编译
echo ========================================
echo.

REM 检查 Java
java -version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Java，请先安装 JDK 11+
    pause
    exit /b 1
)

cd codex_app

REM 检查 Gradle
gradle --version >nul 2>&1
if errorlevel 1 (
    echo [警告] 未找到 Gradle，尝试使用 gradlew...
    if exist "gradlew.bat" (
        call gradlew.bat assembleDebug
    ) else (
        echo [错误] 未找到 Gradle 或 gradlew.bat
        echo 请使用 Android Studio 打开项目并编译
        pause
        exit /b 1
    )
) else (
    gradle assembleDebug
)

if errorlevel 1 (
    echo.
    echo [失败] 编译失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo 编译成功！
echo APK 位置：app\build\outputs\apk\debug\app-debug.apk
echo ========================================
echo.
echo 下一步：
echo 1. 连接 LX04 (adb connect 192.168.1.20:5555)
echo 2. 安装应用 (adb install app\build\outputs\apk\debug\app-debug.apk)
echo 3. 在 LX04 上打开应用，授予悬浮窗权限
echo 4. 点击"启动授权服务"
echo.
pause
