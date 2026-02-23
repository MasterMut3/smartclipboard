@echo off
echo Building Smart Clipboard Portable Version...
echo ============================================

REM Clean previous builds
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
del /q *.spec 2>nul

REM Build portable version using main_portable.py
pyinstaller --onefile --windowed ^
    --name "SmartClipboard-Portable" ^
    --icon=icon.ico ^
    --add-data "icon.ico;." ^
    --hidden-import=win32clipboard ^
    --hidden-import=win32con ^
    --hidden-import=win32gui ^
    --hidden-import=win32api ^
    --hidden-import=pystray ^
    --hidden-import=PIL ^
    src/main_portable.py

if %errorlevel% equ 0 (
    echo.
    echo ✅ Portable build successful!
    echo.
    echo File created: dist\SmartClipboard-Portable.exe
    echo.
    echo This version stores data in the SAME folder as the .exe
    echo Test it by running from any location!
) else (
    echo ❌ Build failed!
)
pause
