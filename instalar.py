"""Instalador leve do ToschiBook (execução a partir do código-fonte).

Para quem NÃO quer gerar um executável, este script prepara tudo para rodar
o sistema diretamente do código:

  1. Verifica a versão do Python;
  2. Instala as dependências do requirements.txt;
  3. Inicializa o banco de dados;
  4. Inicia o sistema (abre no navegador).

Uso:
    python instalar.py             # instala e inicia
    python instalar.py --sem-iniciar  # apenas instala
"""
import argparse
import subprocess
import sys


MIN_PYTHON = (3, 9)


def verificar_python():
    if sys.version_info < MIN_PYTHON:
        print(f"[ERRO] Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ é necessário. "
              f"Detectado: {sys.version.split()[0]}")
        sys.exit(1)
    print(f"[OK] Python {sys.version.split()[0]}")


def instalar_dependencias():
    print("\n>>> Instalando dependências...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
    )
    print("[OK] Dependências instaladas.")


def inicializar_banco():
    print("\n>>> Inicializando banco de dados...")
    from database import init_db
    init_db()
    print("[OK] Banco pronto.")


def iniciar_sistema():
    print("\n>>> Iniciando o ToschiBook...\n")
    import iniciar
    iniciar.main()


def main():
    parser = argparse.ArgumentParser(description="Instalador do ToschiBook")
    parser.add_argument("--sem-iniciar", action="store_true",
                        help="Apenas instala, sem iniciar o sistema.")
    args = parser.parse_args()

    print("=" * 50)
    print("  Instalador do ToschiBook")
    print("=" * 50)

    verificar_python()
    instalar_dependencias()
    inicializar_banco()

    if args.sem_iniciar:
        print("\nInstalação concluída. Rode 'python iniciar.py' para abrir o sistema.")
    else:
        iniciar_sistema()


if __name__ == "__main__":
    main()
