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
import os
import subprocess
import sys


MIN_PYTHON = (3, 9)
DIR_VENV = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv")


def em_venv() -> bool:
    """Indica se estamos rodando dentro de um ambiente virtual."""
    return (
        hasattr(sys, "real_prefix")
        or sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    )


def verificar_python():
    if sys.version_info < MIN_PYTHON:
        print(f"[ERRO] Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ é necessário. "
              f"Detectado: {sys.version.split()[0]}")
        sys.exit(1)
    print(f"[OK] Python {sys.version.split()[0]}")


def _ajuda_venv():
    """Mostra instruções para criar/ativar um venv e sai."""
    py = "python3" if os.name != "nt" else "python"
    ativar = (
        ".venv\\Scripts\\activate" if os.name == "nt"
        else "source .venv/bin/activate"
    )
    print("\n" + "=" * 60)
    print("  Seu sistema não permite instalar pacotes globalmente")
    print("  (PEP 668 / externally-managed-environment).")
    print("  Use um ambiente virtual — é rápido e seguro:")
    print("=" * 60)
    print(f"\n    {py} -m venv .venv")
    print(f"    {ativar}")
    print(f"    {py} instalar.py\n")
    print("Depois, para iniciar o sistema novamente, basta ativar o")
    print(f"ambiente ({ativar}) e rodar: {py} iniciar.py\n")
    print("Se faltar o módulo venv, instale-o antes:")
    print("    sudo apt install python3-venv python3-full   (Debian/Ubuntu/Mint)\n")


def instalar_dependencias():
    print("\n>>> Instalando dependências...")
    comando = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
    resultado = subprocess.run(comando, capture_output=True, text=True)

    if resultado.returncode == 0:
        print("[OK] Dependências instaladas.")
        return

    saida = (resultado.stdout or "") + (resultado.stderr or "")

    # Caso clássico do PEP 668 em Linux: oriente o uso de venv.
    if "externally-managed-environment" in saida and not em_venv():
        _ajuda_venv()
        sys.exit(1)

    # Qualquer outra falha: mostra a saída real do pip.
    print(saida.strip())
    print("\n[ERRO] Falha ao instalar as dependências.")
    sys.exit(1)


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
