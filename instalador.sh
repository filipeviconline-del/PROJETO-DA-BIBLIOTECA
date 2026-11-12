#!/usr/bin/env bash
# ============================================================
#  Abre o instalador grafico do ToschiBook (Linux/macOS).
#  Requer Python 3.9+ com Tkinter.
# ============================================================
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERRO] python3 nao encontrado. Instale o Python 3.9+."
    exit 1
fi

# Verifica o Tkinter e orienta a instalacao, se faltar.
if ! python3 -c "import tkinter" >/dev/null 2>&1; then
    echo "[ERRO] O Tkinter nao esta instalado."
    echo "       Debian/Ubuntu/Mint:  sudo apt install python3-tk"
    echo "       Fedora:              sudo dnf install python3-tkinter"
    exit 1
fi

python3 instalador_grafico.py
