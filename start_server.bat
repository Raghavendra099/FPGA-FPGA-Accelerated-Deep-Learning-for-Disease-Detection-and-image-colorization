@echo off
REM ============================================
REM SmartMed AI — Server Start Script
REM ============================================
REM This script:
REM   1. Adds a Windows Firewall rule for port 8000
REM   2. Starts Django on 0.0.0.0:8000 (accessible from LAN)
REM ============================================

echo.
echo ╔══════════════════════════════════════════════╗
echo ║   SmartMed AI — Starting Server              ║
echo ╚══════════════════════════════════════════════╝
echo.

REM Add firewall rule (requires admin, will silently fail if not admin)
netsh advfirewall firewall delete rule name="SmartMed AI Port 8000" >nul 2>&1
netsh advfirewall firewall add rule name="SmartMed AI Port 8000" dir=in action=allow protocol=TCP localport=8000 >nul 2>&1
if %errorlevel%==0 (
    echo [OK] Firewall rule added for port 8000
) else (
    echo [!!] Could not add firewall rule. Run this script as Administrator,
    echo      or manually allow port 8000 in Windows Firewall.
)

echo.
echo Starting Django development server on 0.0.0.0:8000 ...
echo Access from laptop:  http://localhost:8000
echo Access from mobile:  Check QR code page for URL
echo.

cd /d "c:\Users\Raghavendra V M\Desktop\FPGA Project"
.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000 --settings=config.settings
