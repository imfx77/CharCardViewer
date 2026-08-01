@echo off

set "cwd=%~dp0"

cd /d "%cwd%"

setlocal enabledelayedexpansion

echo Character Card Viewer - Installation Script
echo ============================================

REM Check if uv exists
where uv >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] uv found
    set USE_UV=1
) else (
    echo [INFO] uv not found, will use pip
    set USE_UV=0
)

REM Check Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found in PATH
    echo Please install Python 3.12 or later
    pause
    exit /b 1
)

python --version
echo.

REM Check if conda environment is active
if defined CONDA_PREFIX (
    echo [OK] Conda environment detected: %CONDA_PREFIX%
    echo [INFO] Skipping venv creation, using conda environment
    echo [INFO] Installing dependencies with pip...
    
    REM Create requirements.txt from pyproject.toml if it doesn't exist
    if not exist "requirements.txt" (
        echo [INFO] Creating requirements.txt...
        echo PySide6>=6.6.0 > requirements.txt
        echo Pillow>=10.0.0 >> requirements.txt
    )
    
    pip install -r requirements.txt
) else (
    REM Create virtual environment if needed
    if !USE_UV! EQU 1 (
        echo [INFO] Using uv for package management
        if not exist ".venv" (
            echo [INFO] Creating virtual environment with uv...
            uv venv
        )
        echo [INFO] Installing dependencies with uv...
        uv pip install -r requirements.txt
    ) else (
        echo [INFO] Using pip for package management
        if not exist "venv" (
            echo [INFO] Creating virtual environment...
            python -m venv venv
        )
        echo [INFO] Activating virtual environment...
        call venv\Scripts\activate.bat
        echo [INFO] Installing dependencies with pip...
        
        REM Create requirements.txt from pyproject.toml if it doesn't exist
        if not exist "requirements.txt" (
            echo [INFO] Creating requirements.txt...
            echo PySide6>=6.6.0 > requirements.txt
            echo Pillow>=10.0.0 >> requirements.txt
        )
        
        pip install -r requirements.txt
    )
)

echo.
echo [SUCCESS] Installation complete!
echo.
echo To run the application, use start.bat
pause

