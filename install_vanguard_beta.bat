@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Buchile Vanguard Beta Setup

echo [Buchile] First-time setup will prepare a private runtime.
echo [Buchile] You do not need to install Python or Miniconda yourself.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_runtime.ps1" -Edition vanguard -AppRoot "%~dp0"
if errorlevel 1 goto failed

echo.
echo [Buchile] Setup complete.
exit /b 0

:failed
echo.
echo Setup failed. Existing Buchile installations were not changed.
echo Copy this entire window when requesting help.
pause
exit /b 1
