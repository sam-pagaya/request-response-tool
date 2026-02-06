@echo off
SETLOCAL EnableDelayedExpansion

echo ====================================================
echo   🚀 Request Response Tool (RRT) - One-Click Setup
echo ====================================================
echo.

:: 1. Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python 3 and add it to your PATH.
    pause
    exit /b
)
echo ✅ Python detected.

:: 2. Check for Node.js
node -v >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js not found. Please install Node.js (LTS) from nodejs.org.
    pause
    exit /b
)
echo ✅ Node.js detected.

echo.
echo ----------------------------------------------------
echo [1/2] Installing Python dependencies...
echo ----------------------------------------------------
:: Assuming requirements.txt is in 1-generator
if exist "1-generator\requirements.txt" (
    pip install -r 1-generator\requirements.txt
) else (
    echo ⚠️ 1-generator\requirements.txt not found. Installing pandas and openpyxl manually...
    pip install pandas openpyxl
)

echo.
echo ----------------------------------------------------
echo [2/2] Installing Node.js dependencies...
echo ----------------------------------------------------
:: Navigate to archiver to install express
if exist "2-archiver\package.json" (
    cd 2-archiver
    call npm install
    cd ..
) else (
    echo ⚠️ 2-archiver\package.json not found. Installing express manually...
    cd 2-archiver
    call npm install express
    cd ..
)

echo.
echo ====================================================
echo ✅ Setup Complete! Your environment is ready.
echo ====================================================
echo.
echo Quick Start Reminder:
echo 1. Start Server:    node 2-archiver/server.js
echo 2. Run Generator:   python 1-generator/generator.py
echo 3. Run Matcher:     python 3-matcher/matcher.py
echo.
pause