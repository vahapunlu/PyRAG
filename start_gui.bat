@echo off
REM PyRAG GUI Launcher for Windows

echo.
echo ========================================
echo   PyRAG - Engineering Standards AI
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo [!] Virtual environment not found.
    echo [*] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [X] Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if dependencies are installed
python -c "import customtkinter" 2>nul
if errorlevel 1 (
    echo [*] Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [X] Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Launch GUI
echo [*] Launching PyRAG GUI...
echo.
python main.py gui

if errorlevel 1 (
    echo.
    echo [X] Application exited with error
    pause
)
