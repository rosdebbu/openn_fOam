@echo off
title OpenZess Studio - Auto Sync & Launcher
cd /d "%~dp0"
echo ========================================================
echo   Launching OpenZess Studio with Auto-Sync Check
echo ========================================================
python --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    python sync_and_launch.py
) else (
    py -3 sync_and_launch.py
)
pause
