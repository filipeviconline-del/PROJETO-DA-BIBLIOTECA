"""Instalador gráfico (assistente) do ToschiBook.

Um assistente visual no estilo "Avançar -> Avançar -> Concluir", com a
identidade do ToschiBook (logo e cores verdes), feito em Tkinter (já embutido
no Python — não requer dependências extras para o próprio instalador rodar).

Passos do assistente:
    1. Boas-vindas
    2. Termos de licença
    3. Pasta de instalação
    4. Opções (atalhos)
    5. Instalação (com barra de progresso)
    6. Conclusão (opção de iniciar)

O que a instalação faz:
    * copia os arquivos do projeto para a pasta escolhida;
    * cria um ambiente virtual (.venv) dentro dela;
    * instala as dependências do requirements.txt;
    * cria atalhos (menu de aplicativos / área de trabalho), conforme o SO;
    * cria um desinstalador.

Uso:
    python3 instalador_grafico.py
"""
import os
import queue
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, font as tkfont, messagebox, ttk

# ---------------------------------------------------------------------------
# Identidade visual (espelha o css/style.css do ToschiBook)
# ---------------------------------------------------------------------------
COR_PRIMARIA = "#16734a"
COR_ESCURA = "#0d4f35"
COR_CLARA = "#e9f6ee"
COR_SUAVE = "#f5fbf7"
COR_TEXTO = "#24352c"
COR_MUTED = "#718078"
COR_BRANCO = "#ffffff"
COR_ERRO = "#c0392b"

APP_NOME = "ToschiBook"
APP_VERSAO = "1.0.0"

# Raiz do projeto = pasta onde este instalador está.
ORIGEM = Path(__file__).resolve().parent

# Itens do projeto que devem ser copiados para a instalação.
ITENS_PROJETO = [
    "app.py", "auth.py", "ativacao.py", "database.py", "licenca.py",
    "models.py", "routes.py", "iniciar.py", "requirements.txt",
    "gerar_serial.py", "README.md",
    "html", "css", "javascript", "uploads",
]

# Pastas/arquivos que nunca devem ser copiados.
IGNORAR = {".venv", "venv", "__pycache__", "build", "dist", ".git",
           ".venv_test", "biblioteca.db"}

TERMOS = """TERMO DE LICENÇA DE USO — ToschiBook

1. Este software é fornecido para gerenciamento de bibliotecas.

2. O uso do sistema requer um número de série (serial) válido, fornecido
   pelo distribuidor. Cada serial possui um limite de ativações e, quando
   aplicável, uma data de validade.

3. É proibido redistribuir, revender ou compartilhar seriais sem autorização.

4. O software é fornecido "como está", sem garantias. O uso é de total
   responsabilidade do usuário.

5. Ao prosseguir com a instalação, você declara estar de acordo com estes
   termos.

ToschiBook © 2026 — Todos os direitos reservados.
"""


def pasta_padrao_instalacao() -> Path:
    """Sugere uma pasta de instalação padrão por sistema operacional."""
    home = Path.home()
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
        return base / APP_NOME
    if sys.platform == "darwin":
        return home / "Applications" / APP_NOME
    return home / ".local" / "share" / APP_NOME.lower()


# ===========================================================================
# Lógica de instalação (executada em thread separada)
# ===========================================================================
class Instalador:
    """Executa os passos reais da instalação, reportando progresso."""

    def __init__(self, destino: Path, atalho_menu: bool, atalho_desktop: bool,
                 log, progresso, serial: str = ""):
        self.destino = destino
        self.atalho_menu = atalho_menu
        self.atalho_desktop = atalho_desktop
        self.serial = (serial or "").strip()
        self._log = log            # callable(str)
        self._progresso = progresso  # callable(int 0..100)

    # --- utilidades de UI ---
    def log(self, msg):
        self._log(msg)

    def progresso(self, valor):
        self._progresso(valor)

    # --- caminhos do ambiente instalado ---
    def python_venv(self) -> Path:
        if os.name == "nt":
            return self.destino / ".venv" / "Scripts" / "python.exe"
        return self.destino / ".venv" / "bin" / "python"

    # --- passos ---
    def copiar_arquivos(self):
        self.log(f"Copiando arquivos para {self.destino} ...")
        self.destino.mkdir(parents=True, exist_ok=True)

        for item in ITENS_PROJETO:
            origem = ORIGEM / item
            if not origem.exists():
                continue
            alvo = self.destino / item
            if origem.is_dir():
                shutil.copytree(
                    origem, alvo, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns(*IGNORAR),
                )
            else:
                shutil.copy2(origem, alvo)
            self.log(f"  + {item}")
        self.log("Arquivos copiados.")

    def criar_venv(self):
        self.log("Criando ambiente virtual (.venv) ...")
        subprocess.check_call(
            [sys.executable, "-m", "venv", str(self.destino / ".venv")]
        )
        self.log("Ambiente virtual criado.")

    def instalar_dependencias(self):
        self.log("Instalando dependências (pode levar um tempo) ...")
        py = str(self.python_venv())
        subprocess.run([py, "-m", "pip", "install", "--upgrade", "pip"],
                       capture_output=True, text=True)
        resultado = subprocess.run(
            [py, "-m", "pip", "install", "-r",
             str(self.destino / "requirements.txt")],
            capture_output=True, text=True,
        )
        if resultado.returncode != 0:
            saida = (resultado.stdout or "") + (resultado.stderr or "")
            self.log(saida.strip()[-800:])
            raise RuntimeError(
                "Falha ao instalar dependências. Verifique sua conexão "
                "com a internet e tente novamente."
            )
        self.log("Dependências instaladas.")

    def criar_atalhos(self):
        if sys.platform.startswith("linux"):
            self._atalho_linux()
        elif os.name == "nt":
            self._atalho_windows()
        elif sys.platform == "darwin":
            self._atalho_mac()

    def _conteudo_desktop(self) -> str:
        py = self.python_venv()
        iniciar = self.destino / "iniciar.py"
        return (
            "[Desktop Entry]\n"
            "Type=Application\n"
            f"Name={APP_NOME}\n"
            "Comment=Sistema de gerenciamento de biblioteca\n"
            f"Exec=\"{py}\" \"{iniciar}\"\n"
            f"Path={self.destino}\n"
            "Terminal=true\n"
            "Categories=Office;Education;\n"
        )

    def _atalho_linux(self):
        conteudo = self._conteudo_desktop()
        if self.atalho_menu:
            apps = Path.home() / ".local" / "share" / "applications"
            apps.mkdir(parents=True, exist_ok=True)
            destino = apps / f"{APP_NOME.lower()}.desktop"
            destino.write_text(conteudo, encoding="utf-8")
            os.chmod(destino, 0o755)
            self.log(f"Atalho no menu criado: {destino}")
        if self.atalho_desktop:
            desktop = Path.home() / "Desktop"
            if not desktop.exists():
                desktop = Path.home() / "Área de Trabalho"
            if desktop.exists():
                destino = desktop / f"{APP_NOME}.desktop"
                destino.write_text(conteudo, encoding="utf-8")
                os.chmod(destino, 0o755)
                self.log(f"Atalho na área de trabalho criado: {destino}")

    def _atalho_windows(self):
        # Cria um .bat simples e um atalho via PowerShell (sem dependências).
        py = self.python_venv()
        iniciar = self.destino / "iniciar.py"
        bat = self.destino / f"{APP_NOME}.bat"
        bat.write_text(
            f'@echo off\ncd /d "{self.destino}"\n"{py}" "{iniciar}"\n',
            encoding="utf-8",
        )
        destinos = []
        if self.atalho_menu:
            menu = (Path(os.environ["APPDATA"]) / "Microsoft" / "Windows"
                    / "Start Menu" / "Programs")
            destinos.append(menu / f"{APP_NOME}.lnk")
        if self.atalho_desktop:
            destinos.append(Path.home() / "Desktop" / f"{APP_NOME}.lnk")

        for lnk in destinos:
            lnk.parent.mkdir(parents=True, exist_ok=True)
            ps = (
                f"$s=(New-Object -COM WScript.Shell).CreateShortcut('{lnk}');"
                f"$s.TargetPath='{bat}';"
                f"$s.WorkingDirectory='{self.destino}';$s.Save()"
            )
            subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True)
            self.log(f"Atalho criado: {lnk}")

    def _atalho_mac(self):
        py = self.python_venv()
        iniciar = self.destino / "iniciar.py"
        comando = self.destino / f"{APP_NOME}.command"
        comando.write_text(
            f'#!/bin/bash\ncd "{self.destino}"\n"{py}" "{iniciar}"\n',
            encoding="utf-8",
        )
        os.chmod(comando, 0o755)
        if self.atalho_desktop:
            alvo = Path.home() / "Desktop" / f"{APP_NOME}.command"
            shutil.copy2(comando, alvo)
            os.chmod(alvo, 0o755)
            self.log(f"Atalho criado: {alvo}")

    def criar_desinstalador(self):
        """Gera um pequeno script de desinstalação dentro da pasta."""
        if os.name == "nt":
            script = self.destino / "desinstalar.bat"
            script.write_text(
                f'@echo off\necho Removendo {APP_NOME}...\n'
                f'rmdir /s /q "{self.destino}"\n'
                f'echo {APP_NOME} removido.\npause\n',
                encoding="utf-8",
            )
        else:
            script = self.destino / "desinstalar.sh"
            script.write_text(
                f'#!/bin/bash\necho "Removendo {APP_NOME}..."\n'
                f'rm -f "$HOME/.local/share/applications/{APP_NOME.lower()}.desktop"\n'
                f'rm -rf "{self.destino}"\n'
                f'echo "{APP_NOME} removido."\n',
                encoding="utf-8",
            )
            os.chmod(script, 0o755)
        self.log(f"Desinstalador criado: {script}")

    def ativar_licenca(self):
        """Ativa o produto com o serial informado, na instalação de destino.

        Executa com o Python do .venv, no diretório instalado, para que a
        ativação seja gravada no banco (biblioteca.db) da pasta correta.
        """
        if not self.serial:
            self.log("Nenhum serial informado — ativação adiada para o 1º uso.")
            return

        self.log("Ativando o produto com o serial informado ...")
        py = str(self.python_venv())
        codigo = (
            "import json, licenca; "
            "print(json.dumps(licenca.ativar(__import__('sys').argv[1])))"
        )
        resultado = subprocess.run(
            [py, "-c", codigo, self.serial],
            cwd=str(self.destino), capture_output=True, text=True,
        )

        import json
        dados = {}
        try:
            dados = json.loads((resultado.stdout or "").strip().splitlines()[-1])
        except Exception:  # noqa: BLE001
            dados = {}

        if resultado.returncode == 0 and dados.get("sucesso"):
            validade = dados.get("expira_em") or "sem expiração (perpétua)"
            self.log(f"Produto ATIVADO! Tipo: {dados.get('tipo')} | "
                     f"validade: {validade}")
        else:
            erro = dados.get("erro") or (resultado.stderr or "").strip()
            # Não interrompe a instalação: o usuário poderá ativar no 1º uso.
            self.log(f"[AVISO] Não foi possível ativar agora: {erro or 'erro'}")
            self.log("        O sistema pedirá o serial no primeiro acesso.")

    def executar(self):
        """Roda todos os passos na ordem, atualizando a barra de progresso."""
        try:
            self.progresso(5)
            self.copiar_arquivos()
            self.progresso(28)

            self.criar_venv()
            self.progresso(42)

            self.instalar_dependencias()
            self.progresso(80)

            self.criar_atalhos()
            self.progresso(88)

            self.criar_desinstalador()
            self.progresso(93)

            self.ativar_licenca()
            self.progresso(100)

            self.log("\nInstalação concluída com sucesso!")
            return True
        except Exception as e:  # noqa: BLE001
            self.log(f"\n[ERRO] {e}")
            return False


# ===========================================================================
# Interface gráfica (assistente)
# ===========================================================================
class Assistente(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"Instalador do {APP_NOME} {APP_VERSAO}")
        self.geometry("680x460")
        self.resizable(False, False)
        self.configure(bg=COR_BRANCO)

        self.destino = tk.StringVar(value=str(pasta_padrao_instalacao()))
        self.aceitou = tk.BooleanVar(value=False)
        self.op_menu = tk.BooleanVar(value=True)
        self.op_desktop = tk.BooleanVar(value=True)
        self.op_iniciar = tk.BooleanVar(value=True)
        self.serial = tk.StringVar(value="")
        self._fila = queue.Queue()
        self._sucesso = False

        self._config_estilo()
        self._montar_layout()

        self.passos = [
            self._tela_boas_vindas,
            self._tela_termos,
            self._tela_pasta,
            self._tela_opcoes,
            self._tela_serial,
            self._tela_instalacao,
            self._tela_conclusao,
        ]
        self.indice = 0
        self._mostrar_passo()

    # --- estilo ---
    def _config_estilo(self):
        self.fonte_titulo = tkfont.Font(family="Helvetica", size=18, weight="bold")
        self.fonte_sub = tkfont.Font(family="Helvetica", size=11)
        self.fonte_normal = tkfont.Font(family="Helvetica", size=10)

        estilo = ttk.Style(self)
        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass
        estilo.configure("Verde.Horizontal.TProgressbar",
                         background=COR_PRIMARIA, troughcolor=COR_CLARA)

    # --- layout base: barra lateral verde + área de conteúdo + rodapé ---
    def _montar_layout(self):
        # Barra lateral verde com o logo
        self.lateral = tk.Frame(self, bg=COR_ESCURA, width=180)
        self.lateral.pack(side="left", fill="y")
        self.lateral.pack_propagate(False)

        self._desenhar_logo(self.lateral)

        tk.Label(self.lateral, text=APP_NOME, bg=COR_ESCURA, fg=COR_BRANCO,
                 font=tkfont.Font(family="Helvetica", size=16, weight="bold")
                 ).pack(pady=(4, 0))
        tk.Label(self.lateral, text="Sistema de Biblioteca", bg=COR_ESCURA,
                 fg=COR_CLARA, font=("Helvetica", 9)).pack()
        tk.Label(self.lateral, text=f"v{APP_VERSAO}", bg=COR_ESCURA,
                 fg=COR_CLARA, font=("Helvetica", 8)).pack(side="bottom", pady=14)

        # Área de conteúdo
        self.conteudo = tk.Frame(self, bg=COR_BRANCO)
        self.conteudo.pack(side="top", fill="both", expand=True, padx=28, pady=22)

        # Rodapé com botões
        rodape = tk.Frame(self, bg=COR_SUAVE, height=60)
        rodape.pack(side="bottom", fill="x")
        rodape.pack_propagate(False)

        self.btn_voltar = tk.Button(rodape, text="< Voltar", width=12,
                                    command=self._voltar, relief="flat",
                                    bg=COR_BRANCO, fg=COR_TEXTO)
        self.btn_voltar.pack(side="right", padx=(0, 10), pady=12)

        self.btn_avancar = tk.Button(rodape, text="Avançar >", width=14,
                                     command=self._avancar, relief="flat",
                                     bg=COR_PRIMARIA, fg=COR_BRANCO,
                                     activebackground=COR_ESCURA,
                                     activeforeground=COR_BRANCO)
        self.btn_avancar.pack(side="right", pady=12)

        self.btn_cancelar = tk.Button(rodape, text="Cancelar", width=12,
                                      command=self._cancelar, relief="flat",
                                      bg=COR_SUAVE, fg=COR_MUTED)
        self.btn_cancelar.pack(side="left", padx=14, pady=12)

    def _desenhar_logo(self, parent):
        """Desenha um 'livro' estilizado (logo do ToschiBook) em um Canvas."""
        c = tk.Canvas(parent, width=120, height=120, bg=COR_ESCURA,
                      highlightthickness=0)
        c.pack(pady=(34, 10))
        c.create_rectangle(30, 25, 92, 95, outline=COR_BRANCO, width=4)
        c.create_line(61, 25, 61, 95, fill=COR_BRANCO, width=4)
        c.create_line(38, 40, 55, 40, fill=COR_CLARA, width=2)
        c.create_line(38, 52, 55, 52, fill=COR_CLARA, width=2)
        c.create_line(67, 40, 84, 40, fill=COR_CLARA, width=2)
        c.create_line(67, 52, 84, 52, fill=COR_CLARA, width=2)

    # --- limpa a área de conteúdo ---
    def _limpar_conteudo(self):
        for w in self.conteudo.winfo_children():
            w.destroy()

    def _cabecalho(self, titulo, subtitulo):
        tk.Label(self.conteudo, text=titulo, bg=COR_BRANCO, fg=COR_ESCURA,
                 font=self.fonte_titulo, anchor="w").pack(fill="x")
        tk.Label(self.conteudo, text=subtitulo, bg=COR_BRANCO, fg=COR_MUTED,
                 font=self.fonte_sub, anchor="w", justify="left",
                 wraplength=440).pack(fill="x", pady=(4, 18))

    # =================== TELAS ===================
    def _tela_boas_vindas(self):
        self._limpar_conteudo()
        self._cabecalho(
            f"Bem-vindo ao instalador do {APP_NOME}",
            "Este assistente vai guiar você na instalação do ToschiBook no "
            "seu computador.",
        )
        txt = (
            "O ToschiBook é um sistema completo para gerenciar o acervo, os\n"
            "leitores e os empréstimos da sua biblioteca.\n\n"
            "O instalador irá:\n"
            "   •  copiar o programa para a pasta escolhida;\n"
            "   •  preparar um ambiente isolado (ambiente virtual);\n"
            "   •  instalar as dependências necessárias;\n"
            "   •  ativar o produto com o seu número de série;\n"
            "   •  criar atalhos para você abrir facilmente.\n\n"
            "Clique em \"Avançar\" para começar."
        )
        tk.Label(self.conteudo, text=txt, bg=COR_BRANCO, fg=COR_TEXTO,
                 font=self.fonte_normal, justify="left", anchor="w").pack(fill="x")

    def _tela_termos(self):
        self._limpar_conteudo()
        self._cabecalho("Termo de licença",
                        "Leia e aceite os termos para continuar.")
        quadro = tk.Frame(self.conteudo, bg=COR_BRANCO)
        quadro.pack(fill="both", expand=True)
        scroll = tk.Scrollbar(quadro)
        scroll.pack(side="right", fill="y")
        caixa = tk.Text(quadro, wrap="word", height=11, yscrollcommand=scroll.set,
                        bg=COR_SUAVE, fg=COR_TEXTO, relief="flat",
                        font=("Helvetica", 9), padx=10, pady=8)
        caixa.insert("1.0", TERMOS)
        caixa.config(state="disabled")
        caixa.pack(side="left", fill="both", expand=True)
        scroll.config(command=caixa.yview)

        tk.Checkbutton(self.conteudo, text="Li e aceito os termos de licença",
                       variable=self.aceitou, bg=COR_BRANCO, fg=COR_TEXTO,
                       activebackground=COR_BRANCO, font=self.fonte_normal,
                       command=self._atualizar_botoes).pack(anchor="w", pady=(12, 0))

    def _tela_pasta(self):
        self._limpar_conteudo()
        self._cabecalho("Pasta de instalação",
                        "Escolha onde o ToschiBook será instalado.")
        linha = tk.Frame(self.conteudo, bg=COR_BRANCO)
        linha.pack(fill="x", pady=(6, 0))
        entrada = tk.Entry(linha, textvariable=self.destino, font=self.fonte_normal,
                           relief="solid", bd=1)
        entrada.pack(side="left", fill="x", expand=True, ipady=5)
        tk.Button(linha, text="Procurar...", command=self._escolher_pasta,
                  relief="flat", bg=COR_CLARA, fg=COR_ESCURA).pack(side="left",
                                                                   padx=(8, 0))
        tk.Label(self.conteudo,
                 text="Se a pasta não existir, ela será criada automaticamente.",
                 bg=COR_BRANCO, fg=COR_MUTED, font=("Helvetica", 9),
                 anchor="w").pack(fill="x", pady=(10, 0))

    def _tela_opcoes(self):
        self._limpar_conteudo()
        self._cabecalho("Opções de instalação",
                        "Escolha os atalhos que deseja criar.")
        tk.Checkbutton(self.conteudo, text="Criar atalho no menu de aplicativos",
                       variable=self.op_menu, bg=COR_BRANCO, fg=COR_TEXTO,
                       activebackground=COR_BRANCO,
                       font=self.fonte_normal).pack(anchor="w", pady=4)
        tk.Checkbutton(self.conteudo, text="Criar atalho na área de trabalho",
                       variable=self.op_desktop, bg=COR_BRANCO, fg=COR_TEXTO,
                       activebackground=COR_BRANCO,
                       font=self.fonte_normal).pack(anchor="w", pady=4)

        resumo = (
            f"\nResumo:\n"
            f"   Programa:  {APP_NOME} {APP_VERSAO}\n"
            f"   Pasta:     {self.destino.get()}\n"
        )
        tk.Label(self.conteudo, text=resumo, bg=COR_BRANCO, fg=COR_MUTED,
                 font=("Helvetica", 9), justify="left", anchor="w").pack(
                     fill="x", pady=(16, 0))

    def _tela_serial(self):
        self._limpar_conteudo()
        self._cabecalho(
            "Ativação do produto",
            "Informe o número de série para ativar o ToschiBook agora. "
            "Se preferir, deixe em branco e ative no primeiro acesso.",
        )

        tk.Label(self.conteudo, text="Número de série", bg=COR_BRANCO,
                 fg=COR_TEXTO, font=self.fonte_normal, anchor="w").pack(fill="x")

        self.entrada_serial = tk.Entry(
            self.conteudo, textvariable=self.serial, font=("Courier", 14),
            justify="center", relief="solid", bd=1,
        )
        self.entrada_serial.pack(fill="x", ipady=7, pady=(4, 2))
        self.entrada_serial.bind("<KeyRelease>", self._ao_digitar_serial)

        # Mensagem de validação (atualizada ao digitar).
        self.lbl_serial = tk.Label(
            self.conteudo, text="Formato: XXXXX-XXXXX-XXXXX-XXXXX-XXXXX",
            bg=COR_BRANCO, fg=COR_MUTED, font=("Helvetica", 9), anchor="w",
        )
        self.lbl_serial.pack(fill="x")

        tk.Label(
            self.conteudo,
            text="\nO serial é validado offline. Após a instalação, você pode "
                 "ver e gerenciar as ativações no painel \"Ativações\" do sistema.",
            bg=COR_BRANCO, fg=COR_MUTED, font=("Helvetica", 9),
            justify="left", anchor="w", wraplength=440,
        ).pack(fill="x", pady=(10, 0))

        self._ao_digitar_serial()

    @staticmethod
    def _formatar_serial(valor: str) -> str:
        """Normaliza o texto do serial em grupos de 5 (A-Z e 2-9)."""
        permitido = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        limpo = "".join(c for c in valor.upper() if c in permitido)[:25]
        return "-".join(limpo[i:i + 5] for i in range(0, len(limpo), 5))

    def _ao_digitar_serial(self, _evento=None):
        formatado = self._formatar_serial(self.serial.get())
        if formatado != self.serial.get():
            self.serial.set(formatado)
            self.entrada_serial.icursor("end")

        limpo = formatado.replace("-", "")
        if not limpo:
            self.lbl_serial.config(
                text="Deixe em branco para ativar depois, no primeiro acesso.",
                fg=COR_MUTED)
            return

        if len(limpo) < 25:
            self.lbl_serial.config(
                text=f"Digite o serial completo ({len(limpo)}/25 caracteres).",
                fg=COR_MUTED)
            return

        # Validação offline do serial (não requer Flask).
        resultado = self._validar_serial_offline(formatado)
        if resultado.get("valido"):
            tipo = resultado.get("tipo", "—")
            self.lbl_serial.config(
                text=f"✓ Serial válido — licença: {tipo}.", fg=COR_PRIMARIA)
        else:
            self.lbl_serial.config(
                text="✗ Serial inválido. Verifique os caracteres digitados.",
                fg=COR_ERRO)

    def _validar_serial_offline(self, serial: str) -> dict:
        """Valida o serial importando o módulo licenca da origem."""
        try:
            if str(ORIGEM) not in sys.path:
                sys.path.insert(0, str(ORIGEM))
            import licenca
            return licenca.validar_serial(serial)
        except Exception:  # noqa: BLE001
            # Se não conseguir importar, aceita o formato e valida na ativação.
            return {"valido": True, "tipo": "a confirmar"}

    def _tela_instalacao(self):
        self._limpar_conteudo()
        self._cabecalho("Instalando...",
                        "Aguarde enquanto o ToschiBook é instalado.")
        self.barra = ttk.Progressbar(self.conteudo, style="Verde.Horizontal.TProgressbar",
                                     mode="determinate", maximum=100)
        self.barra.pack(fill="x", pady=(4, 12))

        self.log_caixa = tk.Text(self.conteudo, height=12, bg="#0c1f16",
                                 fg="#bfe9d2", relief="flat", font=("Courier", 9))
        self.log_caixa.pack(fill="both", expand=True)
        self.log_caixa.config(state="disabled")

        # Desabilita botões durante a instalação
        self.btn_voltar.config(state="disabled")
        self.btn_avancar.config(state="disabled")
        self.btn_cancelar.config(state="disabled")

        self._iniciar_instalacao()

    def _tela_conclusao(self):
        self._limpar_conteudo()
        if self._sucesso:
            self._cabecalho("Instalação concluída!",
                            f"O {APP_NOME} foi instalado com sucesso.")
            tk.Label(self.conteudo,
                     text=f"O programa foi instalado em:\n{self.destino.get()}\n\n"
                          "Você já pode abrir o ToschiBook pelos atalhos criados.",
                     bg=COR_BRANCO, fg=COR_TEXTO, font=self.fonte_normal,
                     justify="left", anchor="w").pack(fill="x")
            tk.Checkbutton(self.conteudo, text=f"Iniciar o {APP_NOME} agora",
                           variable=self.op_iniciar, bg=COR_BRANCO, fg=COR_TEXTO,
                           activebackground=COR_BRANCO,
                           font=self.fonte_normal).pack(anchor="w", pady=(18, 0))
        else:
            self._cabecalho("A instalação falhou",
                            "Ocorreu um erro durante a instalação.")
            tk.Label(self.conteudo,
                     text="Verifique as mensagens exibidas e tente novamente.\n"
                          "Se o problema for de internet, confira sua conexão.",
                     bg=COR_BRANCO, fg=COR_ERRO, font=self.fonte_normal,
                     justify="left", anchor="w").pack(fill="x")

        self.btn_voltar.pack_forget()
        self.btn_cancelar.pack_forget()
        self.btn_avancar.config(text="Concluir", state="normal",
                                command=self._concluir)

    # =================== NAVEGAÇÃO ===================
    def _mostrar_passo(self):
        self.passos[self.indice]()
        self._atualizar_botoes()

    def _atualizar_botoes(self):
        self.btn_voltar.config(state="normal" if self.indice > 0 else "disabled")
        # Na tela de termos, "Avançar" só habilita após aceitar.
        if self.passos[self.indice] == self._tela_termos:
            self.btn_avancar.config(
                state="normal" if self.aceitou.get() else "disabled")
        else:
            self.btn_avancar.config(state="normal")

    def _avancar(self):
        # Validação da pasta antes de sair da tela de pasta.
        if self.passos[self.indice] == self._tela_pasta:
            if not self.destino.get().strip():
                messagebox.showwarning(APP_NOME, "Informe uma pasta de instalação.")
                return

        # Validação do serial antes de sair da tela de serial.
        if self.passos[self.indice] == self._tela_serial:
            limpo = self.serial.get().replace("-", "").strip()
            if limpo:  # só valida se o usuário digitou algo
                if len(limpo) != 25 or not self._validar_serial_offline(
                        self.serial.get()).get("valido"):
                    if not messagebox.askyesno(
                        APP_NOME,
                        "O serial informado parece inválido.\n\n"
                        "Deseja continuar mesmo assim? (você poderá ativar "
                        "depois, no primeiro acesso)",
                    ):
                        return

        if self.indice < len(self.passos) - 1:
            self.indice += 1
            self._mostrar_passo()

    def _voltar(self):
        if self.indice > 0:
            self.indice -= 1
            self._mostrar_passo()

    def _cancelar(self):
        if messagebox.askyesno(APP_NOME, "Deseja realmente cancelar a instalação?"):
            self.destroy()

    def _escolher_pasta(self):
        escolha = filedialog.askdirectory(title="Escolha a pasta de instalação")
        if escolha:
            self.destino.set(str(Path(escolha) / APP_NOME))

    def _concluir(self):
        if self._sucesso and self.op_iniciar.get():
            self._abrir_programa()
        self.destroy()

    def _abrir_programa(self):
        py = (Path(self.destino.get()) / ".venv" /
              ("Scripts/python.exe" if os.name == "nt" else "bin/python"))
        iniciar = Path(self.destino.get()) / "iniciar.py"
        try:
            subprocess.Popen([str(py), str(iniciar)], cwd=self.destino.get())
        except Exception:  # noqa: BLE001
            messagebox.showinfo(
                APP_NOME,
                "Não foi possível iniciar automaticamente. Use o atalho criado.")

    # =================== INSTALAÇÃO (thread) ===================
    def _iniciar_instalacao(self):
        def _log(msg):
            self._fila.put(("log", msg))

        def _prog(valor):
            self._fila.put(("prog", valor))

        def _rodar():
            inst = Instalador(
                Path(self.destino.get()), self.op_menu.get(),
                self.op_desktop.get(), _log, _prog,
                serial=self.serial.get(),
            )
            ok = inst.executar()
            self._fila.put(("fim", ok))

        threading.Thread(target=_rodar, daemon=True).start()
        self.after(100, self._processar_fila)

    def _processar_fila(self):
        try:
            while True:
                tipo, dado = self._fila.get_nowait()
                if tipo == "log":
                    self.log_caixa.config(state="normal")
                    self.log_caixa.insert("end", dado + "\n")
                    self.log_caixa.see("end")
                    self.log_caixa.config(state="disabled")
                elif tipo == "prog":
                    self.barra["value"] = dado
                elif tipo == "fim":
                    self._sucesso = dado
                    self.indice += 1
                    self._mostrar_passo()
                    return
        except queue.Empty:
            pass
        self.after(100, self._processar_fila)


def main():
    # Garante que o Tkinter está disponível (mensagem amigável se faltar).
    try:
        app = Assistente()
    except tk.TclError as e:
        print("[ERRO] Não foi possível abrir a interface gráfica.")
        print("No Linux, instale o Tkinter:  sudo apt install python3-tk")
        print(f"Detalhe: {e}")
        sys.exit(1)
    app.mainloop()


if __name__ == "__main__":
    main()
