@echo off
REM Check for Python installation
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python 3.7 or higher and add it to your PATH.
    pause
    exit /b
)

REM Set up virtual environment
echo Setting up virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo Failed to create virtual environment.
    pause
    exit /b
)

REM Activate virtual environment
call venv\Scripts\activate

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install required Python packages
echo Installing required packages...
pip install tkinterdnd2

REM Check if FFmpeg is installed
where ffmpeg >nul 2>nul
if %errorlevel% neq 0 (
    echo FFmpeg is not installed or not in PATH.
    echo Download FFmpeg from https://ffmpeg.org/download.html and add it to your PATH.
    pause
    exit /b
)

echo Setup complete! To run the script, activate the virtual environment with:
echo     call venv\Scripts\activate
echo And then run:
echo     python your_script.py
pause
