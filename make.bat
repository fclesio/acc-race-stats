@echo off
rem Windows version of the Makefile: "make" in cmd, ".\make" in PowerShell, or double-click.
setlocal
chcp 65001 >nul
cd /d "%~dp0"
if not exist "%~dp0pyproject.toml" (
  echo Unzip the whole project folder first, then open this file from there.
  echo Descompacte a pasta inteira do projeto primeiro e abra este arquivo de la.
  pause
  exit /b 1
)
rem uv goes to a known folder and the PATH of the user is not changed, so the installer prints no
rem "restart your shell" instructions that a user would think they must follow
set "UV_INSTALL_DIR=%USERPROFILE%\.local\bin"
set "UV_NO_MODIFY_PATH=1"
set "PATH=%UV_INSTALL_DIR%;%USERPROFILE%\.cargo\bin;%PATH%"
where uv >nul 2>nul
if errorlevel 1 (
  echo First run: installing what is needed, only once. Nothing else to do.
  echo Primeira vez: instalando o necessario, so uma vez. Nao precisa fazer nada.
  powershell -NoProfile -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex" >nul
)
where uv >nul 2>nul
if errorlevel 1 (
  echo The installation did not work. Check the internet connection and try again.
  echo A instalacao nao funcionou. Verifique a internet e tente de novo.
  pause
  exit /b 1
)
if not exist "%~dp0.venv" echo Preparing, only the first time: it can take a few minutes... / Preparando, so na primeira vez: pode levar alguns minutos...
if /i "%~1"=="demo" (
  uv run --quiet --no-dev acc-race-stats --demo --session all
) else if /i "%~1"=="en" (
  uv run --quiet --no-dev acc-race-stats --lang en
) else if /i "%~1"=="pt-br" (
  uv run --quiet --no-dev acc-race-stats --lang pt-br
) else if /i "%~1"=="test" (
  uv run --quiet pytest
) else if /i "%~1"=="check" (
  uv run --quiet ruff check . && uv run --quiet ruff format --check . && uv run --quiet mypy
) else (
  uv run --quiet --no-dev acc-race-stats %*
)
set "CODE=%ERRORLEVEL%"
echo.
rem Keep the window open after a double-click.
echo %CMDCMDLINE% | find /i "/c" >nul && pause
exit /b %CODE%
