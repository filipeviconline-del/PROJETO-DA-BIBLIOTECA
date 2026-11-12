#!/usr/bin/env bash
# ============================================================
#  Abre a central de emissao de seriais (GUI) - Linux/macOS.
#  Ferramenta ADMINISTRATIVA. Nao distribua com o produto.
# ============================================================
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERRO] python3 nao encontrado. Instale o Python 3.9+."
    exit 1
fi

if ! python3 -c "import tkinter" >/dev/null 2>&1; then
    echo "[ERRO] O Tkinter nao esta instalado."
    echo "       Debian/Ubuntu/Mint:  sudo apt install python3-tk"
    echo "       Fedora:              sudo dnf install python3-tkinter"
    exit 1
fi

python3 gerador_serial_gui.py
