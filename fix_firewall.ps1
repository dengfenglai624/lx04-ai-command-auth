# LX04 Firewall Fix - Run as Administrator
# Your network is "Public" profile, so we need rules for ALL profiles

$ErrorActionPreference = "Stop"

# Check for admin
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host ""
    Write-Host "  ERROR: This script requires Administrator privileges!" -ForegroundColor Red
    Write-Host ""
    Write-Host "  How to fix:"
    Write-Host "  1. Right-click PowerShell"
    Write-Host "  2. Select 'Run as administrator'"
    Write-Host "  3. Paste this command again"
    Write-Host ""
    Read-Host "  Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "  ============================================" -ForegroundColor Cyan
Write-Host "    LX04 Firewall Fix" -ForegroundColor Cyan
Write-Host "  ============================================" -ForegroundColor Cyan
Write-Host ""

# Show current network profile
$profile = Get-NetConnectionProfile | Select-Object -First 1
Write-Host "  Network: $($profile.Name)" -ForegroundColor Yellow
Write-Host "  Profile: $($profile.NetworkCategory)" -ForegroundColor Yellow
Write-Host ""

# Remove old rules
Write-Host "  Removing old firewall rules..." -ForegroundColor Gray
Remove-NetFirewallRule -DisplayName "LX04 Auth" -ErrorAction SilentlyContinue
Remove-NetFirewallRule -DisplayName "LX04 Ping" -ErrorAction SilentlyContinue

# Add TCP rule for ALL profiles
Write-Host "  Adding TCP rule for ports 8080,8081 (All profiles)..." -ForegroundColor Gray
New-NetFirewallRule -DisplayName "LX04 Auth" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8080,8081 -Profile Any | Out-Null

# Add ICMP rule for debugging
Write-Host "  Adding ICMP (ping) rule..." -ForegroundColor Gray
New-NetFirewallRule -DisplayName "LX04 Ping" -Direction Inbound -Action Allow -Protocol ICMPv4 -Profile Any | Out-Null

Write-Host ""
Write-Host "  [OK] Firewall rules added!" -ForegroundColor Green
Write-Host ""

# Verify
$rule = Get-NetFirewallRule -DisplayName "LX04 Auth" -ErrorAction SilentlyContinue
if ($rule) {
    Write-Host "  Verified: $($rule.DisplayName) - $($rule.Action) - $($rule.Profile)" -ForegroundColor Green
}

Write-Host ""
Write-Host "  Now test from LX04:" -ForegroundColor Cyan
Write-Host "  adb -s 192.168.123.134:5555 shell ping -c 2 192.168.123.38" -ForegroundColor White
Write-Host ""
Read-Host "  Press Enter to exit"
