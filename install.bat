@echo off
setlocal

:: Check for administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Please run this script as Administrator.
    pause
    exit /b 1
)

set SCRIPT_DIR=%~dp0
set PYTHON=python

:: Check if Python is available
%PYTHON% --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Python not found. Please install Python and add it to PATH.
    pause
    exit /b 1
)

echo [1/3] Installing dependencies...
%PYTHON% -m pip install -r "%SCRIPT_DIR%requirements.txt"
if %errorLevel% neq 0 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

echo [2/3] Registering the service...
%PYTHON% "%SCRIPT_DIR%service.py" install
if %errorLevel% neq 0 (
    echo Failed to register the service.
    pause
    exit /b 1
)

echo [3/3] Starting the service...
%PYTHON% "%SCRIPT_DIR%service.py" start
if %errorLevel% neq 0 (
    echo Failed to start the service.
    pause
    exit /b 1
)

netsh advfirewall firewall add rule name="GpuControl API TCP" protocol=TCP dir=in localport=5000 action=allow

netsh advfirewall firewall add rule name="GpuControl API UDP" protocol=UPD dir=in localport=9999 action=allow

echo.
echo Service successfully installed and started.
pause