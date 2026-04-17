@echo off

:: 1. 检查当前环境是否已经有 cl 指令
where cl >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] 正在调用 setup_msvc.bat 初始化环境...
    call setup_msvc.bat
)

:: 2. 执行编译
echo [BUILD] 正在编译 main_cl.exe...
cl /W4 /O2 /MT /Fe:main_msvc.exe main.c crypto1.c

:: 删除生成的 .obj 文件，保持目录整洁
if exist *.obj del *.obj

:: 3. 简单的结果判断
if %ERRORLEVEL% EQU 0 (
    echo [OK] 编译成功！
) else (
    echo [ERROR] 编译失败，请检查代码。
)