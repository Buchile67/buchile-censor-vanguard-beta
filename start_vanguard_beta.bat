@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Buchile Vanguard Beta

set "BUCHILE_PYTHON="
if exist ".conda\python.exe" set "BUCHILE_PYTHON=%~dp0.conda\python.exe"
if defined BUCHILE_PYTHON goto run

if defined LOCALAPPDATA set "BUCHILE_PYTHON=%LOCALAPPDATA%\BuchileRuntime\envs\vanguard-beta\python.exe"
if not defined LOCALAPPDATA set "BUCHILE_PYTHON=%~dp0.runtime\envs\vanguard-beta\python.exe"
set "BUCHILE_READY=%BUCHILE_PYTHON:\python.exe=\.buchile-ready%"

if not exist "%BUCHILE_PYTHON%" goto install
if not exist "%BUCHILE_READY%" goto install
goto run

:install
(
  call "%~dp0install_vanguard_beta.bat"
  if errorlevel 1 goto failed
)
if not exist "%BUCHILE_PYTHON%" goto failed
if not exist "%BUCHILE_READY%" goto failed

:run
echo [Buchile] Starting Vanguard Beta... Keep this window open while using the app.
"%BUCHILE_PYTHON%" -m streamlit run app.py --server.port 8502 --browser.gatherUsageStats false
goto end

:failed
echo Vanguard Beta could not start.
echo Copy this entire window when requesting help.
pause

:end
endlocal
