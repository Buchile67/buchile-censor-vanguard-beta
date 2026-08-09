@echo off
setlocal
cd /d "%~dp0"
title Buchile Vanguard Beta

if not exist ".conda\python.exe" (
  call install_vanguard_beta.bat
  if errorlevel 1 goto failed
)

echo [Buchile] Starting Vanguard Beta... Keep this window open while using the app.
".conda\python.exe" -m streamlit run app.py --server.port 8502 --browser.gatherUsageStats false
goto end

:failed
echo Vanguard Beta could not start.
pause

:end
endlocal

