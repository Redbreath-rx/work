@echo off
setlocal
cd /d "%~dp0"
set "PYTHON_CMD=py"
where py >nul 2>&1
if errorlevel 1 set "PYTHON_CMD=python"
"%PYTHON_CMD%" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 goto python_error
if exist ".venv\Scripts\python.exe" goto install
"%PYTHON_CMD%" -m venv .venv
if errorlevel 1 goto python_error
:install
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto install_error
".venv\Scripts\python.exe" start_demo.py
if errorlevel 1 goto start_error
goto end
:python_error
echo Python 3.10 or newer was not found. Check your Python installation.
goto end
:install_error
echo Dependency installation failed. Read the error above.
goto end
:start_error
echo Startup failed. Check the error above and ensure Docker Desktop is running.
:end
pause
endlocal
