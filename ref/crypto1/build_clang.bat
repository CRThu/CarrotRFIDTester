@echo off
setlocal

:: 1. 寻找 clang.exe
where clang >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [!] 未在 PATH 中找到 clang.exe。
    echo [!] 请确保已安装 LLVM 并将其 bin 目录加入环境变量。
    pause & exit /b
)

:: 2. 编译
:: -Wall: 显示所有警告
:: -O3: 高级优化
:: -o: 指定输出文件名
echo [BUILD] 正在使用 Clang (LLVM) 构建 main_clang.exe...
clang -Wall -O3 main.c crypto1.c -o main_clang.exe

:: 注意：独立的 clang 在 Windows 上通常不产生 .obj 文件，
:: 而是直接生成 .exe，或者产生 .o 文件。

if %ERRORLEVEL% EQU 0 (
    echo [OK] 编译成功！
)
pause