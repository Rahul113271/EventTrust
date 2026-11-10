@echo off
if exist "%~dp0venv\Scripts\python.exe" (
    "%~dp0venv\Scripts\python.exe" "%~dp0manage.py" runserver
) else (
    python "%~dp0manage.py" runserver
)
pause
