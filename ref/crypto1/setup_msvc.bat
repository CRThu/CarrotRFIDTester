@echo off
set "vswhere=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"

for /f "usebackq tokens=*" %%i in (`"%vswhere%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do (
  set "InstallDir=%%i"
)

if exist "%InstallDir%\VC\Auxiliary\Build\vcvarsall.bat" (
    call "%InstallDir%\VC\Auxiliary\Build\vcvarsall.bat" x64
    echo MSVC Environment Loaded.
) else (
    echo Error: Visual Studio C++ tools not found.
)