@echo off
REM ============================================================
REM  Clique aqui UMA vez para criar os icones do ToschiBook
REM  na Area de Trabalho e no Menu Iniciar.
REM  Depois disso, use os icones criados (sem terminal).
REM ============================================================
cd /d "%~dp0"

set PY=python
if exist ".venv\Scripts\python.exe" set PY=.venv\Scripts\python.exe

"%PY%" criar_atalhos.py

echo.
pause
