@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Buchile Vanguard Beta Setup

set "CONDA_EXE="
if exist "%~dp0miniconda\Scripts\conda.exe" set "CONDA_EXE=%~dp0miniconda\Scripts\conda.exe"
if not defined CONDA_EXE if exist "%USERPROFILE%\miniconda3\Scripts\conda.exe" set "CONDA_EXE=%USERPROFILE%\miniconda3\Scripts\conda.exe"
if not defined CONDA_EXE if exist "%LOCALAPPDATA%\miniconda3\Scripts\conda.exe" set "CONDA_EXE=%LOCALAPPDATA%\miniconda3\Scripts\conda.exe"
if not defined CONDA_EXE for /f "delims=" %%I in ('where conda 2^>nul') do if not defined CONDA_EXE set "CONDA_EXE=%%I"

if not defined CONDA_EXE (
  echo [Buchile] Miniconda was not found. Downloading a private copy for this folder...
  set "MINICONDA_INSTALLER=%TEMP%\Buchile-Miniconda3-latest-Windows-x86_64.exe"
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -UseBasicParsing 'https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe' -OutFile $env:MINICONDA_INSTALLER"
  if errorlevel 1 goto failed
  start /wait "" "%MINICONDA_INSTALLER%" /InstallationType=JustMe /RegisterPython=0 /AddToPath=0 /S /D=%~dp0miniconda
  if errorlevel 1 goto failed
  set "CONDA_EXE=%~dp0miniconda\Scripts\conda.exe"
)

if not exist "%CONDA_EXE%" goto failed
if not exist "vendor\sam2\setup.py" (
  echo SAM2 source is missing. Clone this repository with --recurse-submodules,
  echo or download the model-included package from GitHub Releases.
  goto failed
)

if not exist ".conda\python.exe" (
  echo [Buchile] Creating an isolated Python environment...
  set "CONDA_NO_PLUGINS=true"
  "%CONDA_EXE%" create --solver classic --prefix "%~dp0.conda" python=3.12 pip -y
  if errorlevel 1 goto failed
)

echo [Buchile] Installing GPU/CPU runtime and app dependencies...
".conda\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto failed
".conda\python.exe" -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu130
if errorlevel 1 goto failed
".conda\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
set "SAM2_BUILD_CUDA=0"
".conda\python.exe" -m pip install -e vendor\sam2
if errorlevel 1 goto failed

echo.
echo [Buchile] Setup complete. You can now use start_vanguard_beta.bat.
exit /b 0

:failed
echo.
echo Setup failed. Existing Buchile installations were not changed.
pause
exit /b 1

