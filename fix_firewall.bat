@echo off
echo ==========================================
echo   LX04 Firewall Rule Setup
echo ==========================================
echo.
echo Your network is set to PUBLIC profile.
echo Adding firewall rules for ALL profiles...
echo.

:: Delete old rule if exists
netsh advfirewall firewall delete rule name="LX04 Auth" >nul 2>&1

:: Add inbound rule for ports 8080 and 8081 on ALL profiles (public + private)
netsh advfirewall firewall add rule name="LX04 Auth" dir=in action=allow protocol=TCP localport=8080,8081 profile=any

if %errorlevel% equ 0 (
    echo.
    echo [OK] Firewall rule added successfully!
    echo.
    echo Rule details:
    echo   Name: LX04 Auth
    echo   Direction: Inbound
    echo   Protocol: TCP
    echo   Ports: 8080, 8081
    echo   Profile: ANY (Public + Private)
    echo.
) else (
    echo.
    echo [FAILED] Could not add firewall rule.
    echo.
    echo RIGHT-CLICK this file and select
    echo "Run as administrator" to fix this.
    echo.
)

echo Verifying rule...
netsh advfirewall firewall show rule name="LX04 Auth"
echo.

echo ==========================================
echo   Also allowing ICMP (ping)
echo ==========================================
netsh advfirewall firewall delete rule name="LX04 Ping" >nul 2>&1
netsh advfirewall firewall add rule name="LX04 Ping" dir=in action=allow protocol=icmpv4 profile=any
echo.

pause
