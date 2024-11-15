@echo off
setlocal

REM Check if FFmpeg is already installed and accessible
where ffmpeg >nul 2>nul
if %errorlevel% equ 0 (
    echo FFmpeg is already installed and accessible in PATH.
    exit /b
)

REM Create a temporary directory for FFmpeg download
set "TEMP_DIR=%cd%\ffmpeg_temp"
mkdir "%TEMP_DIR%"

REM Download FFmpeg (Windows static build)
echo Downloading FFmpeg...
powershell -Command "Invoke-WebRequest -Uri https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip -OutFile %TEMP_DIR%\ffmpeg.zip"

REM Check if the download was successful
if %errorlevel% neq 0 (
    echo Failed to download FFmpeg. Please check your internet connection.
    rmdir /s /q "%TEMP_DIR%"
    pause
    exit /b
)

REM Extract FFmpeg to Program Files
echo Extracting FFmpeg...
powershell -Command "Expand-Archive -Path %TEMP_DIR%\ffmpeg.zip -DestinationPath %TEMP_DIR% -Force"

REM Locate the extracted FFmpeg folder
for /d %%d in ("%TEMP_DIR%\ffmpeg-*") do set "FFMPEG_DIR=%%d"

REM Move FFmpeg to Program Files directory
set "FFMPEG_DEST=%ProgramFiles%\FFmpeg"
move "%FFMPEG_DIR%" "%FFMPEG_DEST%" >nul
if %errorlevel% neq 0 (
    echo Failed to move FFmpeg to Program Files.
    rmdir /s /q "%TEMP_DIR%"
    pause
    exit /b
)

REM Clean up temporary files
rmdir /s /q "%TEMP_DIR%"

REM Add FFmpeg to the system PATH
echo Adding FFmpeg to the system PATH...
setx /M PATH "%FFMPEG_DEST%\bin;%PATH%"

echo FFmpeg installation complete and added to system PATH.
echo You may need to restart your command prompt or system for the changes to take effect.
pause
