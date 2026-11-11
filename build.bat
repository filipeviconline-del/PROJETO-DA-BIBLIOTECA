@echo off
REM ============================================================
REM  Gera o executavel do ToschiBook no Windows.
REM  Requer Python 3.11+ instalado e no PATH.
REM ============================================================
echo.
echo  == Build do ToschiBook (Windows) ==
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado no PATH.
    echo        Instale em https://www.python.org/downloads/
    pause
    exit /b 1
)

python build.py
if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao gerar o executavel.
    pause
    exit /b 1
)

echo.
echo Pronto! O executavel esta em: dist\ToschiBook.exe
echo Para gerar o instalador, compile o arquivo instalador.iss no Inno Setup.
echo.
pause
