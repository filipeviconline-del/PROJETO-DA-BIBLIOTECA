"""Instalador leve do ToschiBook (execução a partir do código-fonte).

Prepara tudo para rodar o sistema diretamente do código, de forma automática:

  1. Verifica a versão do Python;
  2. Cria um ambiente virtual (.venv) automaticamente, se necessário,
     e se reexecuta dentro dele (resolve o erro "externally-managed"
     do PEP 668 em Linux sem o usuário precisar fazer nada);
  3. Instala as dependências do requirements.txt dentro do .venv;
  4. Inicializa o banco de dados;
  5. Inicia o sistema (abre no navegador).

Uso:
    python3 instalar.py               # cria o venv, instala e inicia
    python3 instalar.py --sem-iniciar # apenas prepara o ambiente
    python3 instalar.py --sem-venv    # usa o Python atual (sem criar venv)
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path


MIN_PYTHON = (3, 9)
RAIZ = Path(__file__).resolve().parent
DIR_VENV = RAIZ / ".venv"

# Marcador de ambiente para evitar loop de reexecução.
_FLAG_REEXEC = "TOSCHIBOOK_INSTALL_REEXEC"


def em_venv() -> bool:
    """Indica se estamos rodando dentro de um ambiente virtual."""
    return (
        hasattr(sys, "real_prefix")
        or sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    )


def python_do_venv() -> Path:
    """Caminho do interpretador Python dentro do .venv."""
    if os.name == "nt":
        return DIR_VENV / "Scripts" / "python.exe"
    return DIR_VENV / "bin" / "python"


def verificar_python():
    if sys.version_info < MIN_PYTHON:
        print(f"[ERRO] Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ é necessário. "
              f"Detectado: {sys.version.split()[0]}")
        sys.exit(1)
    print(f"[OK] Python {sys.version.split()[0]}")


def criar_venv():
    """Cria o ambiente virtual .venv, se ainda não existir."""
    if python_do_venv().exists():
        print(f"[OK] Ambiente virtual já existe em: {DIR_VENV}")
        return

    print(f"\n>>> Criando ambiente virtual em {DIR_VENV} ...")
    try:
        subprocess.check_call([sys.executable, "-m", "venv", str(DIR_VENV)])
    except subprocess.CalledProcessError:
        print("\n[ERRO] Não foi possível criar o ambiente virtual.")
        print("No Debian/Ubuntu/Mint, instale o venv e tente de novo:")
        print("    sudo apt install python3-venv python3-full\n")
        sys.exit(1)
    print("[OK] Ambiente virtual criado.")


def reexecutar_no_venv(args):
    """Reexecuta este instalador usando o Python do .venv."""
    py = python_do_venv()
    print(f"\n>>> Reexecutando dentro do ambiente virtual...\n")

    ambiente = dict(os.environ, **{_FLAG_REEXEC: "1"})
    cmd = [str(py), str(RAIZ / "instalar.py")]
    if args.sem_iniciar:
        cmd.append("--sem-iniciar")

    # Passa o controle para o Python do venv (herda stdout/stderr).
    resultado = subprocess.run(cmd, env=ambiente)
    sys.exit(resultado.returncode)


def instalar_dependencias():
    print("\n>>> Instalando dependências...")
    # Atualiza o pip (silencioso; se falhar, seguimos mesmo assim).
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
        capture_output=True, text=True,
    )

    comando = [sys.executable, "-m", "pip", "install",
               "-r", str(RAIZ / "requirements.txt")]
    resultado = subprocess.run(comando, capture_output=True, text=True)

    if resultado.returncode == 0:
        print("[OK] Dependências instaladas.")
        return

    saida = (resultado.stdout or "") + (resultado.stderr or "")
    print(saida.strip())

    print("\n" + "=" * 55)
    if "ProxyError" in saida or "Could not find a version" in saida \
            or "Failed to establish" in saida or "Temporary failure" in saida:
        print("  [ERRO] Falha ao BAIXAR as dependências.")
        print("  Verifique sua conexão com a internet e tente de novo.")
        print("  (Se estiver atrás de proxy/firewall, configure-o antes.)")
    else:
        print("  [ERRO] Falha ao instalar as dependências.")
        print("  Veja a mensagem do pip acima para o motivo.")
    print("=" * 55 + "\n")
    sys.exit(1)


def inicializar_banco():
    print("\n>>> Inicializando banco de dados...")
    sys.path.insert(0, str(RAIZ))
    from database import init_db
    init_db()
    print("[OK] Banco pronto.")


def iniciar_sistema():
    print("\n>>> Iniciando o ToschiBook...\n")
    sys.path.insert(0, str(RAIZ))
    import iniciar
    iniciar.main()


def _mensagem_final_sem_iniciar():
    if os.name == "nt":
        ativar = r".venv\Scripts\activate"
    else:
        ativar = "source .venv/bin/activate"
    py_venv = python_do_venv()
    print("\n" + "=" * 55)
    print("  Ambiente pronto!")
    print("=" * 55)
    print("  Para iniciar o sistema, use UMA das opções:")
    print(f"    1) {py_venv} iniciar.py")
    print(f"    2) {ativar}  &&  python iniciar.py")
    print("=" * 55 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Instalador do ToschiBook")
    parser.add_argument("--sem-iniciar", action="store_true",
                        help="Apenas prepara o ambiente, sem iniciar o sistema.")
    parser.add_argument("--sem-venv", action="store_true",
                        help="Instala no Python atual, sem criar um venv.")
    args = parser.parse_args()

    ja_reexec = os.environ.get(_FLAG_REEXEC) == "1"

    print("=" * 50)
    print("  Instalador do ToschiBook")
    print("=" * 50)

    verificar_python()

    # Se não estamos em um venv (e o usuário não pediu --sem-venv),
    # criamos o .venv e reexecutamos o instalador dentro dele.
    if not em_venv() and not args.sem_venv and not ja_reexec:
        criar_venv()
        reexecutar_no_venv(args)  # não retorna (chama sys.exit)

    instalar_dependencias()
    inicializar_banco()

    if args.sem_iniciar:
        _mensagem_final_sem_iniciar()
    else:
        iniciar_sistema()


if __name__ == "__main__":
    main()
