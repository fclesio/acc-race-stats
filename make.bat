@echo off
rem Windows version of the Makefile: "make" in cmd, ".\make" in PowerShell, or double-click.
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
where uv >nul 2>nul
if errorlevel 1 (
  echo First run: installing what is needed, only once...
  powershell -NoProfile -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"
)
where uv >nul 2>nul
if errorlevel 1 (
  echo The installation did not work. Check the internet connection and try again.
  pause
  exit /b 1
)
if /i "%~1"=="demo" (
  uv run --quiet --no-dev acc-race-stats --demo --session all
) else if /i "%~1"=="en" (
  uv run --quiet --no-dev acc-race-stats --lang en
) else if /i "%~1"=="pt-br" (
  uv run --quiet --no-dev acc-race-stats --lang pt-br
) else if /i "%~1"=="test" (
  uv run --quiet pytest
) else (
  uv run --quiet --no-dev acc-race-stats %*
)
set "CODE=%ERRORLEVEL%"
echo.
rem Keep the window open after a double-click.
echo %CMDCMDLINE% | find /i "/c" >nul && pause
exit /b %CODE%
