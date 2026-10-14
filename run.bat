@echo off
title Student Club Information AI Agent
color 0B

echo ======================================================================
echo          Student Club Information AI Agent - Windows Launcher
echo ======================================================================
echo.

chcp 65001 >nul
set PYTHONIOENCODING=utf-8

:: 1. Verify Python is installed or in User AppData
python --version >nul 2>&1
if %errorlevel% neq 0 (
    if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
        set "PATH=%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts;%PATH%"
    )
)

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found in your system PATH!
    echo Please download and install Python from https://www.python.org/
    echo Be sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: 2. Check and setup virtual environment
if not exist "venv\Scripts\activate.bat" (
    echo [SETUP] Creating Python virtual environment (venv)...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [SETUP] Virtual environment created successfully.
)

:: 3. Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

:: 4. Install dependencies
echo [INFO] Checking and installing dependencies from requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

:: 5. Launch the application
echo.
echo ======================================================================
echo  Server is starting!
echo  Open your browser at: http://127.0.0.1:5000
echo  Press Ctrl+C in this terminal window to stop the server.
echo ======================================================================
echo.

:: Optionally launch default browser after 2 seconds in background
start "" http://127.0.0.1:5000

python app.py

pause
