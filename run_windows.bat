@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>&1
if errorlevel 1 (
    set "PYTHON_CMD=python"
) else (
    set "PYTHON_CMD=py"
)
if not exist ".venv\Scripts\python.exe" (
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 goto failure
)
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto failure
.venv\Scripts\python.exe start_demo.py
if errorlevel 1 goto failure
goto end
:failure
echo 请检查 Python 3.10 或以上版本、Docker Desktop 及网络连接。
:end
pause
