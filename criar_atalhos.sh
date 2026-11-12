#!/usr/bin/env bash
# ============================================================
#  Clique aqui UMA vez para criar os icones do ToschiBook
#  na Area de Trabalho e no menu de aplicativos.
#  Depois disso, use os icones criados (sem terminal).
# ============================================================
cd "$(dirname "$0")"

PY=python3
if [ -x ".venv/bin/python" ]; then PY=".venv/bin/python"; fi

"$PY" criar_atalhos.py

echo
read -p "Pressione Enter para fechar..."
