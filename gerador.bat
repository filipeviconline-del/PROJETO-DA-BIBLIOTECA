@echo off
REM ============================================================
REM  Abre a central de emissao de seriais (GUI) - Windows.
REM  Ferramenta ADMINISTRATIVA. Nao distribua com o produto.
REM ============================================================
cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado no PATH.
    echo        Instale em https://www.python.org/downloads/
    pause
    exit /b 1
)

python gerador_serial_gui.py
