@echo off
cd /d "%~dp0"

:: 自动增加版本号并运行测试
uv run bump-my-version bump patch && uv run pytest
pause