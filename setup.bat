@echo off
REM NOVA Setup Script for Windows

echo ========================================
echo NOVA - Intelligent Vision Assistant
echo Setup Script
echo ========================================
echo.

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10 or higher from python.org
    pause
    exit /b 1
)

echo [1/5] Checking Python version...
python --version

echo.
echo [2/5] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists, skipping...
) else (
    python -m venv venv
    echo Virtual environment created!
)

echo.
echo [3/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [4/5] Installing dependencies...
echo This may take a few minutes...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo [5/5] Setting up configuration...
if exist .env (
    echo .env file already exists, skipping...
) else (
    copy .env.example .env
    echo .env file created! Please edit it and add your API keys.
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file and add your ANTHROPIC_API_KEY
echo 2. Run: venv\Scripts\activate
echo 3. Run: python main.py
echo.
echo For help, see README.md
echo.
pause
