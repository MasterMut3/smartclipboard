@echo off
echo Creating Portable Package...
echo ============================

REM Create portable folder
set PORTABLE_FOLDER=SmartClipboard-Portable-v1.0
mkdir %PORTABLE_FOLDER% 2>nul

REM Copy files
copy dist\SmartClipboard-Portable.exe %PORTABLE_FOLDER%\
copy icon.ico %PORTABLE_FOLDER%\
copy README.md %PORTABLE_FOLDER%\README.txt

REM Create portable info file
echo Smart Clipboard Portable v1.0 > %PORTABLE_FOLDER%\PORTABLE.txt
echo ========================= >> %PORTABLE_FOLDER%\PORTABLE.txt
echo. >> %PORTABLE_FOLDER%\PORTABLE.txt
echo This is the PORTABLE version. It stores all data in this folder. >> %PORTABLE_FOLDER%\PORTABLE.txt
echo. >> %PORTABLE_FOLDER%\PORTABLE.txt
echo TO USE: >> %PORTABLE_FOLDER%\PORTABLE.txt
echo 1. Run SmartClipboard-Portable.exe >> %PORTABLE_FOLDER%\PORTABLE.txt
echo 2. Copy any text to start saving >> %PORTABLE_FOLDER%\PORTABLE.txt
echo 3. Data will be saved in this folder >> %PORTABLE_FOLDER%\PORTABLE.txt
echo. >> %PORTABLE_FOLDER%\PORTABLE.txt
echo Files created: >> %PORTABLE_FOLDER%\PORTABLE.txt
echo - clipboard_data.json (your saved items) >> %PORTABLE_FOLDER%\PORTABLE.txt
echo - logs\app.log (application log) >> %PORTABLE_FOLDER%\PORTABLE.txt

REM Create ZIP
powershell Compress-Archive -Path %PORTABLE_FOLDER% -DestinationPath %PORTABLE_FOLDER%.zip -Force

echo.
echo ✅ Portable package created!
echo.
echo Files:
echo   - %PORTABLE_FOLDER%.zip
echo   - %PORTABLE_FOLDER%\ (folder)
pause
