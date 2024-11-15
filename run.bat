@echo off
REM Check if virtual environment exists
if not exist "venv\Scripts\activate" (
    echo Virtual environment not found. Please run setup.bat first to create it.
    pause
    exit /b
)

REM Activate virtual environment
call venv\Scripts\activate

REM Run main.py
python main.py

REM Deactivate virtual environment
deactivate
