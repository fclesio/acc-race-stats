@echo off
rem Double-click on Windows. Installs uv once if it is missing, then asks everything step by step.
chcp 65001 >nul
cd /d "%~dp0"
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
where uv >nul 2>nul
if errorlevel 1 (
  echo Installing uv, only once...
  powershell -ExecutionPolicy ByPass -NoProfile -Command "irm https://astral.sh/uv/install.ps1 | iex"
)
uv run --quiet --no-dev acc-race-stats %*
echo.
pause
