@echo off
title USB Backup Agent
color 0A

echo.
echo  ============================================
echo   USB Backup Agent - Windows
echo  ============================================
echo.

cd /d "%~dp0"

if exist "python-embed\python.exe" (
    echo [*] Using embedded Python...
    set PYTHON=python-embed\python.exe
) else (
    echo [*] Using system Python...
    set PYTHON=python
)

echo [*] Starting backup...
echo.

%PYTHON% backup.py

echo.
if %errorlevel% equ 0 (
    echo [+] Backup completed successfully!
) else (
    echo [!] Backup failed with error code: %errorlevel%
)

echo.
pause
