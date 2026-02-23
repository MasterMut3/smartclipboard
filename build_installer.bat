@echo off
echo Building Smart Clipboard Installer Version...
echo =============================================

REM Clean previous builds
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
del /q *.spec 2>nul

REM Build installer version using main.py (your original)
pyinstaller --onefile --windowed ^
    --name "SmartClipboard" ^
    --icon=icon.ico ^
    --add-data "icon.ico;." ^
    --hidden-import=win32clipboard ^
    --hidden-import=win32con ^
    --hidden-import=win32gui ^
    --hidden-import=win32api ^
    --hidden-import=winreg ^
    --hidden-import=pystray ^
    --hidden-import=PIL ^
    src/main.py

if %errorlevel% equ 0 (
    echo.
    echo ✅ Installer build successful!
    echo.
    echo File created: dist\SmartClipboard.exe
    echo.
    echo This version stores data in: %%USERPROFILE%%\.smart_clipboard\
) else (
    echo ❌ Build failed!
)
pause
