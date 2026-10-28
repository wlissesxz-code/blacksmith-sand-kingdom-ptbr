@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  set /p GAME=Cole o caminho da pasta do jogo e aperte Enter:
) else (
  set GAME=%~1
)
python patch.py "%GAME:"=%" --restore
pause
