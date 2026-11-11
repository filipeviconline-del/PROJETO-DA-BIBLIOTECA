#!/usr/bin/env bash
# ============================================================
#  Gera o executavel do ToschiBook no Linux/macOS.
#  Requer Python 3.11+ instalado.
# ============================================================
set -e

echo
echo " == Build do ToschiBook (Linux/macOS) =="
echo

if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERRO] python3 nao encontrado. Instale o Python 3.11+."
    exit 1
fi

python3 build.py

echo
echo "Pronto! O executavel esta em: dist/ToschiBook"
echo
