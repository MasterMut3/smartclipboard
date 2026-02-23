@echo off
echo Preparing Release Files...
echo =========================

REM Create release folder
mkdir release 2>nul
mkdir release\installer 2>nul
mkdir release\portable 2>nul
mkdir release\source 2>nul

REM Copy installer files
copy installer\SmartClipboard-Setup.exe release\installer\ 2>nul
copy dist\SmartClipboard.exe release\installer\ 2>nul

REM Copy portable files
copy SmartClipboard-Portable-v1.0.zip release\portable\ 2>nul
copy dist\SmartClipboard-Portable.exe release\portable\ 2>nul

REM Create version info
echo Smart Clipboard v1.0.0 > release\version.txt
echo Release Date: %date% >> release\version.txt
echo. >> release\version.txt
echo Files: >> release\version.txt
echo - installer\SmartClipboard-Setup.exe (Installer) >> release\version.txt
echo - portable\SmartClipboard-Portable.zip (Portable ZIP) >> release\version.txt

echo.
echo ✅ Release files prepared in 'release' folder
echo.
dir release /s
pause
