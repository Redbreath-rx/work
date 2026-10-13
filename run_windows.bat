@echo off
setlocal
cd /d "%~dp0"
py -3.12 -c "import sys; sys.exit(0 if sys.version_info[:2] == (3, 12) else 1)" >nul 2>&1
if errorlevel 1 goto python_error
if not exist ".venv\Scripts\python.exe" goto create_venv
".venv\Scripts\python.exe" -c "import sys; sys.exit(0 if sys.version_info[:2] == (3, 12) else 1)" >nul 2>&1
if not errorlevel 1 goto install
echo Preserving the incompatible virtual environment before creating a Python 3.12 environment.
move ".venv" ".venv-python-backup-%RANDOM%" >nul
if errorlevel 1 goto venv_error
:create_venv
py -3.12 -m venv .venv
if errorlevel 1 goto venv_error
:install
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto install_error
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto install_error
".venv\Scripts\python.exe" start_demo.py
if errorlevel 1 goto start_error
goto end
:python_error
echo Python 3.12 is required. Install it alongside your existing Python:
echo winget install -e --id Python.Python.3.12
goto end
:venv_error
echo Could not prepare the virtual environment. Close Python processes and retry.
goto end
:install_error
echo Dependency installation failed. Read the error above.
goto end
:start_error
echo Startup failed. Ensure Docker Desktop is running and read the error above.
:end
pause
endlocal
