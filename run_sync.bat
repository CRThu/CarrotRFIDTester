@echo off
cd /d "%~dp0"

:: 自动同步环境
echo [INFO] Sync environment...
uv sync --reinstall
pause