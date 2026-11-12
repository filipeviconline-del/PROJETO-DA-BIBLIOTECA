"""Interface gráfica da central de emissão de seriais do ToschiBook.

Janela Tkinter (sem dependências externas) com a identidade do ToschiBook
(logo e cores verdes) para, de forma visual:

  * gerenciar a CHAVE MESTRA (criar chave forte, ver impressão digital);
  * emitir seriais vinculados a um cliente (registrados no log assinado);
  * ver o histórico de emissões (com verificação de integridade);
  * validar um serial;
  * exportar o histórico para CSV.

Reutiliza toda a lógica já testada do módulo ``gerador_serial`` — esta GUI é
apenas uma camada visual por cima.

Uso:
    python3 gerador_serial_gui.py
"""
import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, font as tkfont, messagebox, ttk

import gerador_serial as core

# ---------------------------------------------------------------------------
# Identidade visual (igual ao instalador/CSS do ToschiBook)
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


class GeradorGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Central de Emissão de Seriais - ToschiBook")
        self.geometry("760x560")
        self.minsize(720, 520)
        self.configure(bg=COR_BRANCO)

        # Aplica a chave do arquivo licenca.key, se existir.
        core._aplicar_chave_do_arquivo()
        self.seguranca, self.licenca = core._recarregar_modulos()

        self._config_estilo()
        self._montar_layout()
        self._construir_abas()
        self._atualizar_estado_chave()

    # --- estilo ---
    def _config_estilo(self):
        self.f_titulo = tkfont.Font(family="Helvetica", size=16, weight="bold")
        self.f_normal = tkfont.Font(family="Helvetica", size=10)
        self.f_peq = tkfont.Font(family="Helvetica", size=9)
        estilo = ttk.Style(self)
        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass
        estilo.configure("TNotebook", background=COR_BRANCO, borderwidth=0)
        estilo.configure("TNotebook.Tab", padding=(16, 8),
                         font=("Helvetica", 10))
        estilo.map("TNotebook.Tab",
                   background=[("selected", COR_CLARA)],
                   foreground=[("selected", COR_ESCURA)])
        estilo.configure("Treeview", rowheight=24, font=("Helvetica", 9))
        estilo.configure("Treeview.Heading", font=("Helvetica", 9, "bold"))

    # --- topo com logo + estado da chave ---
    def _montar_layout(self):
        topo = tk.Frame(self, bg=COR_ESCURA, height=78)
        topo.pack(side="top", fill="x")
        topo.pack_propagate(False)

        c = tk.Canvas(topo, width=52, height=52, bg=COR_ESCURA,
                      highlightthickness=0)
        c.pack(side="left", padx=(18, 10), pady=13)
        c.create_rectangle(12, 10, 42, 44, outline=COR_BRANCO, width=3)
        c.create_line(27, 10, 27, 44, fill=COR_BRANCO, width=3)

        txt = tk.Frame(topo, bg=COR_ESCURA)
        txt.pack(side="left", pady=16)
        tk.Label(txt, text="Central de Emissão de Seriais", bg=COR_ESCURA,
                 fg=COR_BRANCO, font=self.f_titulo).pack(anchor="w")
        tk.Label(txt, text="ToschiBook — ferramenta administrativa", bg=COR_ESCURA,
                 fg=COR_CLARA, font=self.f_peq).pack(anchor="w")

        # Indicador do estado da chave (direita)
        self.lbl_chave = tk.Label(topo, text="", bg=COR_ESCURA, fg=COR_CLARA,
                                  font=self.f_peq, justify="right")
        self.lbl_chave.pack(side="right", padx=18)

        self.abas = ttk.Notebook(self)
        self.abas.pack(fill="both", expand=True, padx=14, pady=12)

    def _atualizar_estado_chave(self):
        if self.seguranca.usando_chave_insegura():
            self.lbl_chave.config(
                text="Chave: PADRÃO (insegura)\nCrie uma na aba 'Chave'",
                fg="#ffd9b3")
        else:
            self.lbl_chave.config(
                text=f"Chave: segura\nImpressão: {self.seguranca.impressao_digital_chave()}",
                fg=COR_CLARA)

    def _recarregar(self):
        self.seguranca, self.licenca = core._recarregar_modulos()
        self._atualizar_estado_chave()

    # =====================================================================
    # Abas
    # =====================================================================
    def _construir_abas(self):
        self._aba_emitir()
        self._aba_maquina()
        self._aba_historico()
        self._aba_validar()
        self._aba_chave()

    # ---------- ABA: Emitir ----------
    def _aba_emitir(self):
        aba = tk.Frame(self.abas, bg=COR_BRANCO)
        self.abas.add(aba, text="  Emitir  ")

        form = tk.Frame(aba, bg=COR_BRANCO)
        form.pack(fill="x", padx=20, pady=(18, 8))

        tk.Label(form, text="Tipo de licença", bg=COR_BRANCO, fg=COR_TEXTO,
                 font=self.f_normal).grid(row=0, column=0, sticky="w", pady=6)
        self.cb_tipo = ttk.Combobox(form, values=list(self.licenca.TIPOS_LICENCA),
                                    state="readonly", width=20)
        self.cb_tipo.set("anual")
        self.cb_tipo.grid(row=0, column=1, sticky="w", padx=10)
        self.cb_tipo.bind("<<ComboboxSelected>>", lambda e: self._preencher_padrao())

        tk.Label(form, text="Quantidade", bg=COR_BRANCO, fg=COR_TEXTO,
                 font=self.f_normal).grid(row=1, column=0, sticky="w", pady=6)
        self.sp_qtd = tk.Spinbox(form, from_=1, to=999, width=8)
        self.sp_qtd.grid(row=1, column=1, sticky="w", padx=10)

        tk.Label(form, text="Validade (dias, 0=perpétua)", bg=COR_BRANCO,
                 fg=COR_TEXTO, font=self.f_normal).grid(row=2, column=0, sticky="w", pady=6)
        self.e_dias = tk.Entry(form, width=10)
        self.e_dias.grid(row=2, column=1, sticky="w", padx=10)

        tk.Label(form, text="Ativações (máquinas, 0=ilimitado)", bg=COR_BRANCO,
                 fg=COR_TEXTO, font=self.f_normal).grid(row=3, column=0, sticky="w", pady=6)
        self.e_ativ = tk.Entry(form, width=10)
        self.e_ativ.grid(row=3, column=1, sticky="w", padx=10)

        tk.Label(form, text="Cliente / pedido (opcional)", bg=COR_BRANCO,
                 fg=COR_TEXTO, font=self.f_normal).grid(row=4, column=0, sticky="w", pady=6)
        self.e_cliente = tk.Entry(form, width=32)
        self.e_cliente.grid(row=4, column=1, sticky="w", padx=10)

        self._preencher_padrao()

        tk.Button(aba, text="Emitir seriais", command=self._emitir,
                  relief="flat", bg=COR_PRIMARIA, fg=COR_BRANCO,
                  activebackground=COR_ESCURA, activeforeground=COR_BRANCO,
                  font=("Helvetica", 11, "bold"), padx=18, pady=8).pack(pady=10)

        tk.Label(aba, text="Seriais emitidos (também salvos no histórico):",
                 bg=COR_BRANCO, fg=COR_MUTED, font=self.f_peq,
                 anchor="w").pack(fill="x", padx=20)
        self.txt_emitidos = tk.Text(aba, height=9, bg="#0c1f16", fg="#bfe9d2",
                                    relief="flat", font=("Courier", 11))
        self.txt_emitidos.pack(fill="both", expand=True, padx=20, pady=(4, 16))
        self.txt_emitidos.config(state="disabled")

    def _preencher_padrao(self):
        tipo = self.cb_tipo.get()
        self.e_dias.delete(0, "end")
        self.e_dias.insert(0, str(self.licenca.TIPOS_LICENCA.get(tipo, 0)))
        self.e_ativ.delete(0, "end")
        self.e_ativ.insert(0, str(self.licenca.ATIVACOES_PADRAO.get(tipo, 1)))

    def _emitir(self):
        self._recarregar()
        if self.seguranca.usando_chave_insegura():
            if not messagebox.askyesno(
                APP_NOME,
                "Você está usando a CHAVE PADRÃO (insegura).\n\n"
                "Seriais emitidos agora NÃO são seguros. Recomendado: crie uma "
                "chave forte na aba 'Chave'.\n\nEmitir mesmo assim (apenas testes)?",
            ):
                return

        tipo = self.cb_tipo.get()
        try:
            qtd = max(int(self.sp_qtd.get()), 1)
            dias = int(self.e_dias.get())
            ativ = int(self.e_ativ.get())
        except ValueError:
            messagebox.showerror(APP_NOME, "Validade e ativações devem ser números.")
            return
        cliente = self.e_cliente.get().strip()

        import datetime as dt
        emitidos = []
        for _ in range(qtd):
            serial = self.licenca.gerar_serial(
                tipo=tipo, dias_validade=dias, max_ativacoes=ativ)
            registro = {
                "serial": serial, "tipo": tipo, "dias_validade": dias,
                "max_ativacoes": ativ,
                "emitido_em": dt.datetime.now().isoformat(timespec="seconds"),
                "cliente": cliente,
            }
            core._registrar_emissao(self.seguranca, registro)
            emitidos.append(serial)

        self.txt_emitidos.config(state="normal")
        self.txt_emitidos.delete("1.0", "end")
        self.txt_emitidos.insert("end", "\n".join(emitidos))
        self.txt_emitidos.config(state="disabled")

        messagebox.showinfo(
            APP_NOME,
            f"{len(emitidos)} serial(is) emitido(s) e registrado(s) no histórico.")
        if hasattr(self, "_recarregar_historico"):
            self._recarregar_historico()

    # ---------- ABA: Código por máquina (desafio/resposta) ----------
    def _aba_maquina(self):
        aba = tk.Frame(self.abas, bg=COR_BRANCO)
        self.abas.add(aba, text="  Código p/ máquina  ")

        tk.Label(aba,
                 text=("Gere um código de ativação EXCLUSIVO para o computador "
                       "do cliente.\nPeça ao cliente o 'ID desta máquina' (aparece "
                       "na tela de ativação dele),\ncole abaixo e envie o código "
                       "gerado. Ele só ativa naquela máquina."),
                 bg=COR_BRANCO, fg=COR_MUTED, font=self.f_peq,
                 justify="left", anchor="w").pack(fill="x", padx=20, pady=(16, 8))

        form = tk.Frame(aba, bg=COR_BRANCO)
        form.pack(fill="x", padx=20)

        tk.Label(form, text="ID da máquina do cliente", bg=COR_BRANCO,
                 fg=COR_TEXTO, font=self.f_normal).grid(row=0, column=0, sticky="w", pady=6)
        self.e_maquina = tk.Entry(form, font=("Courier", 12), width=28,
                                  relief="solid", bd=1)
        self.e_maquina.grid(row=0, column=1, sticky="w", padx=10)

        tk.Label(form, text="Tipo de licença", bg=COR_BRANCO, fg=COR_TEXTO,
                 font=self.f_normal).grid(row=1, column=0, sticky="w", pady=6)
        self.cb_tipo_m = ttk.Combobox(form, values=list(self.licenca.TIPOS_LICENCA),
                                      state="readonly", width=18)
        self.cb_tipo_m.set("anual")
        self.cb_tipo_m.grid(row=1, column=1, sticky="w", padx=10)

        tk.Label(form, text="Cliente / pedido (opcional)", bg=COR_BRANCO,
                 fg=COR_TEXTO, font=self.f_normal).grid(row=2, column=0, sticky="w", pady=6)
        self.e_cliente_m = tk.Entry(form, width=28)
        self.e_cliente_m.grid(row=2, column=1, sticky="w", padx=10)

        tk.Button(aba, text="Gerar código para esta máquina",
                  command=self._gerar_codigo_maquina, relief="flat",
                  bg=COR_PRIMARIA, fg=COR_BRANCO, activebackground=COR_ESCURA,
                  activeforeground=COR_BRANCO,
                  font=("Helvetica", 11, "bold"), padx=16, pady=8).pack(pady=12)

        tk.Label(aba, text="Código gerado (envie ao cliente):", bg=COR_BRANCO,
                 fg=COR_MUTED, font=self.f_peq, anchor="w").pack(fill="x", padx=20)
        self.txt_codigo = tk.Text(aba, height=3, bg="#0c1f16", fg="#bfe9d2",
                                  relief="flat", font=("Courier", 12), wrap="word")
        self.txt_codigo.pack(fill="x", padx=20, pady=(4, 10))
        self.txt_codigo.config(state="disabled")

        tk.Button(aba, text="Copiar código", command=self._copiar_codigo,
                  relief="flat", bg=COR_CLARA, fg=COR_ESCURA).pack(padx=20, anchor="w")

    def _gerar_codigo_maquina(self):
        self._recarregar()
        if self.seguranca.usando_chave_insegura():
            if not messagebox.askyesno(
                APP_NOME,
                "Você está com a CHAVE PADRÃO (insegura). O código pode não ser "
                "aceito.\n\nGerar mesmo assim (apenas testes)?"):
                return
        maquina = self.e_maquina.get().strip().upper()
        if not maquina:
            messagebox.showwarning(APP_NOME, "Informe o ID da máquina do cliente.")
            return
        tipo = self.cb_tipo_m.get()
        cliente = self.e_cliente_m.get().strip()
        try:
            codigo = self.licenca.gerar_codigo_maquina(maquina, tipo=tipo)
        except ValueError as e:
            messagebox.showerror(APP_NOME, str(e))
            return

        import datetime as dt
        core._registrar_emissao(self.seguranca, {
            "serial": codigo, "tipo": tipo,
            "dias_validade": self.licenca.TIPOS_LICENCA[tipo],
            "max_ativacoes": 1,
            "emitido_em": dt.datetime.now().isoformat(timespec="seconds"),
            "cliente": cliente + f" [maquina {maquina}]",
        })

        self.txt_codigo.config(state="normal")
        self.txt_codigo.delete("1.0", "end")
        self.txt_codigo.insert("end", codigo)
        self.txt_codigo.config(state="disabled")
        if hasattr(self, "_recarregar_historico"):
            self._recarregar_historico()

    def _copiar_codigo(self):
        texto = self.txt_codigo.get("1.0", "end").strip()
        if not texto:
            return
        self.clipboard_clear()
        self.clipboard_append(texto)
        messagebox.showinfo(APP_NOME, "Código copiado para a área de transferência.")

    # ---------- ABA: Histórico ----------
    def _aba_historico(self):
        aba = tk.Frame(self.abas, bg=COR_BRANCO)
        self.abas.add(aba, text="  Histórico  ")

        barra = tk.Frame(aba, bg=COR_BRANCO)
        barra.pack(fill="x", padx=16, pady=(14, 6))
        tk.Button(barra, text="Atualizar", command=lambda: self._recarregar_historico(),
                  relief="flat", bg=COR_CLARA, fg=COR_ESCURA).pack(side="left")
        tk.Button(barra, text="Exportar CSV...", command=self._exportar,
                  relief="flat", bg=COR_CLARA, fg=COR_ESCURA).pack(side="left", padx=8)
        self.lbl_hist = tk.Label(barra, text="", bg=COR_BRANCO, fg=COR_MUTED,
                                 font=self.f_peq)
        self.lbl_hist.pack(side="right")

        cols = ("serial", "tipo", "ativ", "cliente", "emitido", "integro")
        self.tree = ttk.Treeview(aba, columns=cols, show="headings")
        larguras = {"serial": 230, "tipo": 90, "ativ": 50, "cliente": 150,
                    "emitido": 150, "integro": 70}
        titulos = {"serial": "Serial", "tipo": "Tipo", "ativ": "Ativ.",
                   "cliente": "Cliente", "emitido": "Emitido em",
                   "integro": "Íntegro"}
        for col in cols:
            self.tree.heading(col, text=titulos[col])
            self.tree.column(col, width=larguras[col],
                             anchor="center" if col in ("ativ", "integro") else "w")
        self.tree.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self._recarregar_historico()

    def _recarregar_historico(self):
        self._recarregar()
        for i in self.tree.get_children():
            self.tree.delete(i)
        registros = core._ler_log()
        for r in registros:
            integro = self.seguranca.verificar_registro((
                r.get("serial"), r.get("tipo"), r.get("dias_validade"),
                r.get("max_ativacoes"), r.get("emitido_em"), r.get("cliente"),
            ), r.get("assinatura"))
            self.tree.insert("", "end", values=(
                r.get("serial", ""), r.get("tipo", ""),
                r.get("max_ativacoes", ""), r.get("cliente") or "-",
                r.get("emitido_em", ""), "sim" if integro else "NÃO!",
            ))
        self.lbl_hist.config(text=f"{len(registros)} emissão(ões)")

    def _exportar(self):
        registros = core._ler_log()
        if not registros:
            messagebox.showinfo(APP_NOME, "Nenhum serial emitido para exportar.")
            return
        destino = filedialog.asksaveasfilename(
            title="Exportar histórico", defaultextension=".csv",
            initialfile="seriais.csv", filetypes=[("CSV", "*.csv")])
        if not destino:
            return
        import csv
        with open(destino, "w", newline="", encoding="utf-8") as f:
            campos = ["serial", "tipo", "dias_validade", "max_ativacoes",
                      "emitido_em", "cliente"]
            w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
            w.writeheader()
            for r in registros:
                w.writerow(r)
        messagebox.showinfo(APP_NOME, f"{len(registros)} registro(s) exportado(s).")

    # ---------- ABA: Validar ----------
    def _aba_validar(self):
        aba = tk.Frame(self.abas, bg=COR_BRANCO)
        self.abas.add(aba, text="  Validar  ")

        tk.Label(aba, text="Digite um serial para validar:", bg=COR_BRANCO,
                 fg=COR_TEXTO, font=self.f_normal, anchor="w").pack(
                     fill="x", padx=20, pady=(20, 6))
        self.e_validar = tk.Entry(aba, font=("Courier", 14), justify="center",
                                 relief="solid", bd=1)
        self.e_validar.pack(fill="x", padx=20, ipady=7)

        tk.Button(aba, text="Validar", command=self._validar, relief="flat",
                  bg=COR_PRIMARIA, fg=COR_BRANCO, activebackground=COR_ESCURA,
                  activeforeground=COR_BRANCO,
                  font=("Helvetica", 11, "bold"), padx=18, pady=7).pack(pady=12)

        self.lbl_validar = tk.Label(aba, text="", bg=COR_BRANCO, fg=COR_TEXTO,
                                    font=self.f_normal, justify="left", anchor="w")
        self.lbl_validar.pack(fill="x", padx=20)

    def _validar(self):
        self._recarregar()
        serial = self.e_validar.get().strip()
        if not serial:
            return
        r = self.licenca.validar_serial(serial)
        if r["valido"]:
            ativ = "ilimitadas" if r.get("max_ativacoes") == 0 else r.get("max_ativacoes")
            self.lbl_validar.config(
                fg=COR_PRIMARIA,
                text=(f"✓ Serial VÁLIDO\n"
                      f"    Tipo: {r['tipo']}\n"
                      f"    Validade: {r['dias_validade'] or 'perpétua'} dias\n"
                      f"    Ativações: {ativ}"))
        else:
            self.lbl_validar.config(
                fg=COR_ERRO,
                text=(f"✗ Serial INVÁLIDO — {r.get('erro')}\n"
                      f"    Confira se a chave é a mesma da emissão.\n"
                      f"    Impressão digital atual: "
                      f"{self.seguranca.impressao_digital_chave()}"))

    # ---------- ABA: Chave ----------
    def _aba_chave(self):
        aba = tk.Frame(self.abas, bg=COR_BRANCO)
        self.abas.add(aba, text="  Chave  ")

        self.lbl_chave_info = tk.Label(aba, text="", bg=COR_BRANCO, fg=COR_TEXTO,
                                      font=self.f_normal, justify="left", anchor="w")
        self.lbl_chave_info.pack(fill="x", padx=20, pady=(20, 10))

        tk.Button(aba, text="Criar / renovar chave mestra forte",
                  command=self._criar_chave, relief="flat", bg=COR_PRIMARIA,
                  fg=COR_BRANCO, activebackground=COR_ESCURA,
                  activeforeground=COR_BRANCO,
                  font=("Helvetica", 11, "bold"), padx=16, pady=8).pack(pady=6)

        tk.Label(aba,
                 text=("A chave é salva em 'licenca.key' (fora do código).\n"
                       "Use a MESMA chave no produto para os seriais serem aceitos:\n"
                       "  • defina TOSCHIBOOK_LICENSE_KEY_FILE apontando para o arquivo, ou\n"
                       "  • defina TOSCHIBOOK_LICENSE_KEY com o conteúdo dele.\n\n"
                       "NUNCA versione nem compartilhe este arquivo."),
                 bg=COR_BRANCO, fg=COR_MUTED, font=self.f_peq,
                 justify="left", anchor="w").pack(fill="x", padx=20, pady=10)

        self._atualizar_info_chave()

    def _atualizar_info_chave(self):
        if self.seguranca.usando_chave_insegura():
            self.lbl_chave_info.config(
                fg=COR_ERRO,
                text="Chave em uso: PADRÃO (INSEGURA).\n"
                     "Crie uma chave forte antes de emitir seriais reais.")
        else:
            origem = ("arquivo licenca.key" if core.ARQUIVO_CHAVE.exists()
                      else "variável de ambiente")
            self.lbl_chave_info.config(
                fg=COR_PRIMARIA,
                text=f"Chave em uso: SEGURA (origem: {origem}).\n"
                     f"Impressão digital: {self.seguranca.impressao_digital_chave()}")

    def _criar_chave(self):
        if core.ARQUIVO_CHAVE.exists():
            if not messagebox.askyesno(
                APP_NOME,
                "Já existe uma chave.\n\nCriar uma NOVA chave invalida TODOS os "
                "seriais já emitidos com a chave anterior.\n\nContinuar?",
            ):
                return
        nova = self.seguranca.gerar_chave_forte()
        core.ARQUIVO_CHAVE.write_text(nova + "\n", encoding="utf-8")
        try:
            os.chmod(core.ARQUIVO_CHAVE, 0o600)
        except OSError:
            pass
        os.environ["TOSCHIBOOK_LICENSE_KEY"] = nova
        self._recarregar()
        self._atualizar_info_chave()
        messagebox.showinfo(
            APP_NOME,
            f"Chave mestra criada e salva em:\n{core.ARQUIVO_CHAVE}\n\n"
            f"Impressão digital: {self.seguranca.impressao_digital_chave()}")


def main():
    try:
        app = GeradorGUI()
    except tk.TclError as e:
        print("[ERRO] Não foi possível abrir a interface gráfica.")
        print("No Linux, instale o Tkinter:  sudo apt install python3-tk")
        print(f"Detalhe: {e}")
        raise SystemExit(1)
    app.mainloop()


if __name__ == "__main__":
    main()
