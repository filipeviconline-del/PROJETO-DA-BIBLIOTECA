@echo off
REM ============================================================
REM  Abre o instalador grafico do ToschiBook (Windows).
REM  Requer Python 3.9+ (o Tkinter ja vem incluido no Windows).
REM ============================================================
cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado no PATH.
    echo        Instale em https://www.python.org/downloads/
    echo        e marque "Add Python to PATH" durante a instalacao.
    pause
    exit /b 1
)

python instalador_grafico.py
