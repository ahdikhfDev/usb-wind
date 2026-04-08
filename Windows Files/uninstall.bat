@echo off
title USB Backup Agent - Uninstaller
color 0A

echo.
echo  ============================================
echo   USB Backup Agent - Uninstaller
echo  ============================================
echo.

REM Kill running processes
echo [*] Stopping backup processes...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im pythonw.exe >nul 2>&1
taskkill /f /im backup-loop.bat >nul 2>&1

echo [*] Removing scheduled task...
schtasks /delete /tn "USBBackupAgent" /f >nul 2>&1

echo.
echo  ============================================
echo   UNINSTALLATION COMPLETE!
echo  ============================================
echo.
echo [+] USB Backup Agent has been removed!
echo.
echo [i] Note: Your backup data in hasil_backup/ is preserved.
echo.
pause
