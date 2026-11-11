"""Ponto de entrada do ToschiBook para o usuário final.

Inicia o servidor Flask local e abre o navegador padrão apontando para a
aplicação. É este arquivo que o executável gerado pelo PyInstaller executa.

O servidor roda em modo de produção (sem debug/reloader) em 127.0.0.1:5000.
"""
import os
import sys
import threading
import webbrowser

# Garante que os módulos sejam encontrados quando empacotado pelo PyInstaller.
if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(sys.executable))

from app import app  # noqa: E402  (import após ajuste de diretório)

HOST = "127.0.0.1"
PORT = int(os.environ.get("TOSCHIBOOK_PORT", "5000"))
URL = f"http://{HOST}:{PORT}/"


def abrir_navegador():
    """Abre o navegador padrão após um pequeno atraso para o servidor subir."""
    try:
        webbrowser.open(URL)
    except Exception:
        pass


def main():
    print("=" * 50)
    print("  ToschiBook - Sistema de Biblioteca")
    print("=" * 50)
    print(f"  Servidor iniciado em: {URL}")
    print("  Feche esta janela para encerrar o sistema.")
    print("=" * 50)

    # Abre o navegador assim que o servidor estiver pronto.
    threading.Timer(1.5, abrir_navegador).start()

    # Modo produção: sem debug nem reloader.
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
