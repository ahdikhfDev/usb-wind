@echo off
title USB Backup Agent - Installer
color 0A

echo.
echo  ============================================
echo   USB Backup Agent - Installer
echo  ============================================
echo.

REM Check if running as admin
net session >nul 2>&1
if %errorlevel% equ 0 (
    echo [+] Running as Administrator
    set ADMIN=1
) else (
    echo [-] Not running as Administrator
    echo [i] Some features may not work without admin rights
    set ADMIN=0
)

echo.
echo [*] Setting up USB Backup Agent...
echo.

REM Change to script directory
cd /d "%~dp0"

REM Create backup folder if not exists
if not exist "hasil_backup" mkdir "hasil_backup"

REM Kill existing backup processes
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im pythonw.exe >nul 2>&1

echo [*] Creating scheduled task for auto-start...

REM Remove existing task
schtasks /delete /tn "USBBackupAgent" /f >nul 2>&1

REM Create new scheduled task - runs at logon
schtasks /create /tn "USBBackupAgent" /tr "\"%cd%backup-loop.bat\"" /sc ONLOGON /rl LIMITED /f

if %errorlevel% equ 0 (
    echo [+] Scheduled task created successfully!
) else (
    echo [!] Failed to create scheduled task.
    echo [i] You may need to run this as Administrator.
)

echo.
echo [*] Testing backup script...
call "%~dp0Backup Now.bat"

echo.
echo  ============================================
echo   INSTALLATION COMPLETE!
echo  ============================================
echo.
echo [+] USB Backup Agent has been installed!
echo.
echo [i] What happens next:
echo     - This app will auto-start when Windows starts
echo     - It will check for USB every 60 seconds
echo     - When USB is detected, it will auto-backup
echo     - Check notification when backup completes
echo.
echo [i] To uninstall, run uninstall.bat
echo.
pause
