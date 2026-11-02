@echo off
chcp 65001 >nul
echo ==========================================
echo   LX04 网络连接测试工具
echo ==========================================
echo.

:: 获取本机 IP
echo [1/4] 检测本机 IP 地址...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set IP=%%a
)
set IP=%IP: =%
echo 本机 IP: %IP%
echo.

:: 测试 LX04 连接
echo [2/4] 测试与 LX04 的连接...
ping -n 1 192.168.123.134 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ LX04 (192.168.123.134) 可到达
) else (
    echo ✗ LX04 (192.168.123.134) 不可到达
    echo   请检查：
    echo   - LX04 是否开机
    echo   - 是否在同一局域网
    echo   - ADB 是否已连接 (adb connect 192.168.123.134:5555^)
)
echo.

:: 测试端口监听
echo [3/4] 测试本地端口监听状态...
netstat -an | findstr ":8080 " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ 端口 8080 (授权服务^) 正在监听
) else (
    echo ✗ 端口 8080 未监听
    echo   请启动授权服务：python web_auth_server.py
)

netstat -an | findstr ":8081 " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ 端口 8081 (额度服务^) 正在监听
) else (
    echo ✗ 端口 8081 未监听
    echo   请启动额度服务：python codex_quota_server.py
)
echo.

:: 测试防火墙规则
echo [4/4] 检查防火墙规则...
netsh advfirewall firewall show rule name="LX04 Auth" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ 防火墙规则已配置
    netsh advfirewall firewall show rule name="LX04 Auth" | findstr "Enabled"
) else (
    echo ✗ 防火墙规则未配置
    echo   请以管理员身份运行：fix_firewall.bat
)
echo.

echo ==========================================
echo   测试完成
echo ==========================================
echo.
echo 下一步：
echo   1. 确保两个服务都在运行
echo   2. 在 LX04 上打开 Codex 授权应用
echo   3. 选择 CODEX 或 WORK BUDDY 模式
echo   4. 观察是否弹出授权窗口
echo.
pause
