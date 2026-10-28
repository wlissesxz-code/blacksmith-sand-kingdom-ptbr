@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
where python >nul 2>nul || (echo Python nao encontrado. Instale em https://www.python.org/downloads/ marcando "Add python.exe to PATH". & pause & exit /b 1)
python -m pip install -r requirements.txt --quiet
if "%~1"=="" (
  set /p GAME=Cole o caminho da pasta do jogo e aperte Enter:
) else (
  set GAME=%~1
)
python patch.py "%GAME:"=%"
pause
