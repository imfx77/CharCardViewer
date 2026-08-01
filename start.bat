@echo off

set "cwd=%~dp0"

cd /d "%cwd%"

setlocal enabledelayedexpansion

echo Character Card Viewer - Starting...
echo ====================================

REM Check if conda environment is active
if defined CONDA_PREFIX (
    echo [OK] Conda environment detected: %CONDA_PREFIX%
    echo.
    python main.py
) else (
    REM Check if uv exists
    where uv >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        echo [OK] uv found, using uv to run
        echo.
        uv run main.py
    ) else (
        echo [INFO] uv not found, using python directly
        echo.
        
        REM Check for venv
        if exist "venv\Scripts\activate.bat" (
            echo [INFO] Activating virtual environment...
            call venv\Scripts\activate.bat
        ) else if exist ".venv\Scripts\activate.bat" (
            echo [INFO] Activating virtual environment...
            call .venv\Scripts\activate.bat
        )
        
        python main.py
    )
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Application exited with error code %ERRORLEVEL%
    pause
)

