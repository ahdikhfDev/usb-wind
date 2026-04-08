@echo off
title USB Backup Agent
color 0A

echo.
echo  ============================================
echo   USB Backup Agent - Background Mode
echo  ============================================
echo.

REM Check if Python is available
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python not found!
    echo [i] Please install Python from python.org
    pause
    exit /b 1
)

REM Change to script directory
cd /d "%~dp0"

REM Check for python-embed
if exist "python-embed\python.exe" (
    set PYTHON=python-embed\python.exe
) else (
    set PYTHON=python
)

:LOOP
echo [%date% %time%] Checking for USB...

REM Run backup (will exit if no USB or already backed up today)
%PYTHON% backup_agent\backup.py

REM Check result
if %errorlevel% equ 0 (
    echo [%date% %time%] Backup completed or nothing to backup.
) else (
    echo [%date% %time%] No USB detected or error occurred.
)

REM Wait before next check (60 seconds)
echo [%date% %time%] Waiting 60 seconds before next check...
timeout /t 60 /nobreak >nul

goto LOOP
