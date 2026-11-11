"""Script de build do ToschiBook.

Instala as dependências e gera o executável único usando o PyInstaller,
com base na especificação ``ToschiBook.spec``.

Uso:
    python build.py            # build completo (instala deps + empacota)
    python build.py --skip-deps  # apenas empacota (deps já instaladas)

O resultado fica em ``dist/ToschiBook`` (ou ``dist/ToschiBook.exe`` no Windows).
"""
import argparse
import os
import shutil
import subprocess
import sys


RAIZ = os.path.dirname(os.path.abspath(__file__))


def executar(comando):
    print(f"\n>>> {' '.join(comando)}\n")
    subprocess.check_call(comando, cwd=RAIZ)


def instalar_dependencias():
    executar([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    executar([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])


def limpar():
    for pasta in ("build", "dist"):
        caminho = os.path.join(RAIZ, pasta)
        if os.path.isdir(caminho):
            print(f"Removendo {pasta}/ ...")
            shutil.rmtree(caminho, ignore_errors=True)


def empacotar():
    executar([sys.executable, "-m", "PyInstaller", "--clean", "ToschiBook.spec"])


def main():
    parser = argparse.ArgumentParser(description="Build do ToschiBook")
    parser.add_argument("--skip-deps", action="store_true",
                        help="Pula a instalação de dependências.")
    args = parser.parse_args()

    if not args.skip_deps:
        instalar_dependencias()

    limpar()
    empacotar()

    destino = os.path.join(RAIZ, "dist")
    print("\n" + "=" * 50)
    print("  Build concluido!")
    print(f"  Executavel gerado em: {destino}")
    print("=" * 50)


if __name__ == "__main__":
    main()
