"""Cria atalhos clicáveis do ToschiBook (sem precisar do terminal depois).

Gera ícones na Área de Trabalho e no menu de aplicativos para:
  * "ToschiBook"            -> abre o sistema (iniciar.py);
  * "ToschiBook - Seriais"  -> abre a central de emissão (gerador_serial_gui.py).

Compatível com Linux (.desktop), Windows (.lnk via PowerShell) e macOS
(.command). Use apenas a biblioteca padrão.

Depois de rodar UMA vez, é só clicar nos ícones — nunca mais precisa do terminal.

Uso:
    python3 criar_atalhos.py            # cria os dois atalhos
    python3 criar_atalhos.py --sistema  # só o atalho do sistema (p/ o cliente)
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
ICONE_PNG = RAIZ / "assets" / "toschibook.png"
ICONE_ICO = RAIZ / "html" / "favicon.ico"


def python_exec() -> str:
    """Caminho do Python a usar: prioriza o .venv da pasta, se existir."""
    if os.name == "nt":
        venv = RAIZ / ".venv" / "Scripts" / "python.exe"
    else:
        venv = RAIZ / ".venv" / "bin" / "python"
    return str(venv) if venv.exists() else sys.executable


def garantir_icone():
    """Garante que o ícone PNG exista (gera, se necessário)."""
    if ICONE_PNG.exists():
        return
    try:
        import criar_icone
        criar_icone.main()
    except Exception as e:  # noqa: BLE001
        print(f"[aviso] não foi possível gerar o ícone: {e}")


# ---------------------------------------------------------------------------
# Linux
# ---------------------------------------------------------------------------

def _desktop_linux(nome, script, icone):
    py = python_exec()
    alvo = RAIZ / script
    return (
        "[Desktop Entry]\n"
        "Version=1.0\n"
        "Type=Application\n"
        f"Name={nome}\n"
        "Comment=Sistema de gerenciamento de biblioteca ToschiBook\n"
        f"Exec=\"{py}\" \"{alvo}\"\n"
        f"Path={RAIZ}\n"
        f"Icon={icone}\n"
        "Terminal=false\n"
        "Categories=Office;Education;\n"
    )


def _instalar_linux(itens):
    apps = Path.home() / ".local" / "share" / "applications"
    apps.mkdir(parents=True, exist_ok=True)

    # Descobre a Área de Trabalho (pt-BR ou en).
    desktop = None
    for cand in ("Desktop", "Área de Trabalho", "Área de trabalho"):
        p = Path.home() / cand
        if p.is_dir():
            desktop = p
            break

    icone = str(ICONE_PNG if ICONE_PNG.exists() else ICONE_ICO)

    for nome, arq, script in itens:
        conteudo = _desktop_linux(nome, script, icone)
        # menu de aplicativos
        destino_menu = apps / arq
        destino_menu.write_text(conteudo, encoding="utf-8")
        os.chmod(destino_menu, 0o755)
        print(f"[OK] Menu de aplicativos: {destino_menu}")
        # área de trabalho
        if desktop:
            destino_desk = desktop / arq
            destino_desk.write_text(conteudo, encoding="utf-8")
            os.chmod(destino_desk, 0o755)
            # marca como confiável (GNOME) para abrir com 1 clique
            try:
                subprocess.run(
                    ["gio", "set", str(destino_desk),
                     "metadata::trusted", "true"],
                    capture_output=True)
            except Exception:
                pass
            print(f"[OK] Área de trabalho:    {destino_desk}")

    # Atualiza o cache do menu, se a ferramenta existir.
    try:
        subprocess.run(["update-desktop-database", str(apps)],
                       capture_output=True)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Windows
# ---------------------------------------------------------------------------

def _instalar_windows(itens):
    py = python_exec()
    icone = str(ICONE_ICO if ICONE_ICO.exists() else ICONE_PNG)
    desktop = Path.home() / "Desktop"
    menu = (Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows"
            / "Start Menu" / "Programs")

    for nome, arq, script in itens:
        alvo = RAIZ / script
        for pasta in (desktop, menu):
            pasta.mkdir(parents=True, exist_ok=True)
            lnk = pasta / f"{nome}.lnk"
            ps = (
                f"$s=(New-Object -COM WScript.Shell).CreateShortcut('{lnk}');"
                f"$s.TargetPath='{py}';"
                f"$s.Arguments='\"{alvo}\"';"
                f"$s.WorkingDirectory='{RAIZ}';"
                f"$s.IconLocation='{icone}';"
                f"$s.Save()"
            )
            subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True)
            print(f"[OK] Atalho: {lnk}")


# ---------------------------------------------------------------------------
# macOS
# ---------------------------------------------------------------------------

def _instalar_mac(itens):
    py = python_exec()
    desktop = Path.home() / "Desktop"
    for nome, arq, script in itens:
        alvo = RAIZ / script
        cmd = desktop / f"{nome}.command"
        cmd.write_text(
            f'#!/bin/bash\ncd "{RAIZ}"\n"{py}" "{alvo}"\n', encoding="utf-8")
        os.chmod(cmd, 0o755)
        print(f"[OK] Atalho: {cmd}")


def main():
    parser = argparse.ArgumentParser(description="Cria atalhos do ToschiBook")
    parser.add_argument("--sistema", action="store_true",
                        help="Cria apenas o atalho do sistema (para o cliente).")
    args = parser.parse_args()

    garantir_icone()

    # (Nome exibido, nome do arquivo .desktop, script a executar)
    itens = [("ToschiBook", "toschibook.desktop", "iniciar.py")]
    if not args.sistema:
        itens.append(
            ("ToschiBook - Seriais", "toschibook-seriais.desktop",
             "gerador_serial_gui.py"))

    print("Criando atalhos do ToschiBook...\n")
    if sys.platform.startswith("linux"):
        _instalar_linux(itens)
    elif os.name == "nt":
        _instalar_windows(itens)
    elif sys.platform == "darwin":
        _instalar_mac(itens)
    else:
        print("[ERRO] Sistema operacional não suportado para atalhos automáticos.")
        return 1

    print("\nPronto! Procure os ícones na Área de Trabalho e no menu de aplicativos.")
    print("A partir de agora é só clicar — sem precisar do terminal.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
