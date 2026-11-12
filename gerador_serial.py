"""Central de emissão de seriais do ToschiBook (ferramenta administrativa).

Versão avançada e segura do gerador de seriais. Além de gerar, ela:

  * exige/gerencia uma CHAVE MESTRA forte (anti-cracker) fora do código;
  * registra TODO serial emitido em um log assinado (auditoria/controle de
    vendas), para você saber o que já foi gerado e para quem;
  * associa cada serial a um cliente/pedido (rótulo);
  * valida seriais e lista o histórico de emissões;
  * oferece um MENU interativo, além da linha de comando.

NÃO distribua este arquivo com o produto final — é de uso interno de quem
emite/vende as licenças.

Exemplos de linha de comando:

    # 1) Primeiro uso: cria uma chave mestra forte (salva em licenca.key)
    python gerador_serial.py chave --criar

    # 2) Emite 5 seriais anuais para um cliente
    python gerador_serial.py emitir --tipo anual -q 5 --cliente "Escola Modelo"

    # 3) Lista o que já foi emitido
    python gerador_serial.py historico

    # 4) Valida um serial
    python gerador_serial.py validar XXXXX-XXXXX-XXXXX-XXXXX-XXXXX

    # 5) Menu interativo (sem argumentos)
    python gerador_serial.py
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
ARQUIVO_CHAVE = RAIZ / "licenca.key"            # chave mestra (NÃO versionar!)
ARQUIVO_LOG = RAIZ / "seriais_emitidos.jsonl"   # log de emissões (auditoria)


# ---------------------------------------------------------------------------
# Gestão da chave mestra
# ---------------------------------------------------------------------------

def _recarregar_modulos():
    """(Re)carrega seguranca/licenca para refletir a chave atual do ambiente."""
    for nome in ("licenca", "seguranca"):
        if nome in sys.modules:
            del sys.modules[nome]
    import seguranca  # noqa: F401
    import licenca     # noqa: F401
    return sys.modules["seguranca"], sys.modules["licenca"]


def _aplicar_chave_do_arquivo():
    """Se existir o arquivo de chave e nenhuma env estiver definida, usa-o."""
    if not os.environ.get("TOSCHIBOOK_LICENSE_KEY") and ARQUIVO_CHAVE.exists():
        chave = ARQUIVO_CHAVE.read_text(encoding="utf-8").strip()
        if chave:
            os.environ["TOSCHIBOOK_LICENSE_KEY"] = chave


def cmd_chave(args) -> int:
    seguranca, _ = _recarregar_modulos()

    if args.criar:
        if ARQUIVO_CHAVE.exists() and not args.forcar:
            print(f"[ERRO] Já existe uma chave em {ARQUIVO_CHAVE}.")
            print("       Use --forcar para SUBSTITUIR (isso invalida os seriais "
                  "já emitidos com a chave anterior!).")
            return 1
        nova = seguranca.gerar_chave_forte()
        ARQUIVO_CHAVE.write_text(nova + "\n", encoding="utf-8")
        try:
            os.chmod(ARQUIVO_CHAVE, 0o600)  # leitura só para o dono
        except OSError:
            pass
        os.environ["TOSCHIBOOK_LICENSE_KEY"] = nova
        seguranca, _ = _recarregar_modulos()
        print(f"[OK] Chave mestra criada e salva em: {ARQUIVO_CHAVE}")
        print(f"     Impressão digital: {seguranca.impressao_digital_chave()}")
        print("\n  GUARDE este arquivo com segurança e NÃO o versione no git.")
        print("  Use a MESMA chave no produto (via TOSCHIBOOK_LICENSE_KEY ou")
        print("  copiando o arquivo e apontando TOSCHIBOOK_LICENSE_KEY_FILE).")
        return 0

    # Sem --criar: mostra o estado atual da chave.
    _aplicar_chave_do_arquivo()
    seguranca, _ = _recarregar_modulos()
    if seguranca.usando_chave_insegura():
        print("Chave em uso: PADRÃO (INSEGURA).")
        print("Crie uma chave forte com:  python gerador_serial.py chave --criar")
    else:
        origem = "arquivo licenca.key" if ARQUIVO_CHAVE.exists() else "variável de ambiente"
        print(f"Chave em uso: segura (origem: {origem}).")
        print(f"Impressão digital: {seguranca.impressao_digital_chave()}")
    return 0


# ---------------------------------------------------------------------------
# Log de emissões (auditoria assinada)
# ---------------------------------------------------------------------------

def _registrar_emissao(seguranca, registro: dict):
    """Anexa uma linha ao log de emissões, assinada contra adulteração."""
    registro = dict(registro)
    registro["assinatura"] = seguranca.assinar_registro((
        registro["serial"], registro["tipo"], registro["dias_validade"],
        registro["max_ativacoes"], registro["emitido_em"], registro["cliente"],
    ))
    with open(ARQUIVO_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")


def _ler_log() -> list[dict]:
    if not ARQUIVO_LOG.exists():
        return []
    linhas = []
    for linha in ARQUIVO_LOG.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha:
            try:
                linhas.append(json.loads(linha))
            except json.JSONDecodeError:
                continue
    return linhas


# ---------------------------------------------------------------------------
# Comandos: emitir / validar / historico / exportar
# ---------------------------------------------------------------------------

def _exigir_chave_segura(seguranca, forcar: bool) -> bool:
    if seguranca.usando_chave_insegura() and not forcar:
        print("[ERRO] Você está usando a CHAVE PADRÃO (insegura).")
        print("       Crie uma chave forte antes de emitir seriais reais:")
        print("         python gerador_serial.py chave --criar")
        print("       (ou use --forcar para emitir mesmo assim, apenas em testes)")
        return False
    return True


def cmd_emitir(args) -> int:
    _aplicar_chave_do_arquivo()
    seguranca, licenca = _recarregar_modulos()

    if args.tipo not in licenca.TIPOS_LICENCA:
        print(f"[ERRO] Tipo inválido: {args.tipo}")
        return 1
    if not _exigir_chave_segura(seguranca, args.forcar):
        return 1
    if args.quantidade < 1:
        print("[ERRO] A quantidade deve ser >= 1.")
        return 1

    validade = (args.dias if args.dias is not None
                else licenca.TIPOS_LICENCA[args.tipo])
    max_ativ = (args.ativacoes if args.ativacoes is not None
                else licenca.ATIVACOES_PADRAO.get(args.tipo, 1))

    print(f"\n== Emitindo {args.quantidade} serial(is) ==")
    print(f"   Tipo: {args.tipo} | validade: "
          f"{'perpetua' if validade == 0 else str(validade) + ' dias'} | "
          f"ativacoes: {'ilimitadas' if max_ativ == 0 else max_ativ} | "
          f"cliente: {args.cliente or '-'}")
    print(f"   Impressão digital da chave: {seguranca.impressao_digital_chave()}\n")

    emitidos = []
    for i in range(1, args.quantidade + 1):
        serial = licenca.gerar_serial(
            tipo=args.tipo, dias_validade=args.dias, max_ativacoes=args.ativacoes)
        registro = {
            "serial": serial,
            "tipo": args.tipo,
            "dias_validade": validade,
            "max_ativacoes": max_ativ,
            "emitido_em": dt.datetime.now().isoformat(timespec="seconds"),
            "cliente": args.cliente or "",
        }
        _registrar_emissao(seguranca, registro)
        emitidos.append(serial)
        print(f"  {i:>3}. {serial}")

    print(f"\n[OK] {len(emitidos)} serial(is) emitido(s) e registrado(s) em "
          f"{ARQUIVO_LOG.name}.")
    return 0


def cmd_validar(args) -> int:
    _aplicar_chave_do_arquivo()
    seguranca, licenca = _recarregar_modulos()
    r = licenca.validar_serial(args.serial)
    print()
    if r["valido"]:
        print("  [VALIDO]")
        print(f"    Tipo ........ {r['tipo']}")
        print(f"    Validade .... {r['dias_validade'] or 'perpetua'} dias")
        print(f"    Ativacoes ... {'ilimitadas' if r.get('max_ativacoes') == 0 else r.get('max_ativacoes')}")
    else:
        print(f"  [INVALIDO] - {r.get('erro')}")
        print(f"  (Confira se a chave em uso é a mesma usada na emissão. "
              f"Impressão digital atual: {seguranca.impressao_digital_chave()})")
    print()
    return 0


def cmd_historico(args) -> int:
    _aplicar_chave_do_arquivo()
    seguranca, _ = _recarregar_modulos()
    registros = _ler_log()
    if not registros:
        print("Nenhum serial emitido ainda.")
        return 0

    print(f"\n== Histórico de emissões ({len(registros)}) ==\n")
    print(f"  {'serial':<31}{'tipo':<13}{'ativ.':<7}{'cliente':<20}{'emitido em':<20}{'integro'}")
    print("  " + "-" * 98)
    for r in registros:
        integro = seguranca.verificar_registro((
            r.get("serial"), r.get("tipo"), r.get("dias_validade"),
            r.get("max_ativacoes"), r.get("emitido_em"), r.get("cliente"),
        ), r.get("assinatura"))
        print(f"  {r.get('serial',''):<31}{r.get('tipo',''):<13}"
              f"{str(r.get('max_ativacoes','')):<7}{(r.get('cliente') or '-'):<20}"
              f"{r.get('emitido_em',''):<20}{'sim' if integro else 'NAO!'}")
    print()
    return 0


def cmd_exportar(args) -> int:
    registros = _ler_log()
    if not registros:
        print("Nenhum serial emitido para exportar.")
        return 0
    destino = Path(args.saida)
    with open(destino, "w", newline="", encoding="utf-8") as f:
        campos = ["serial", "tipo", "dias_validade", "max_ativacoes",
                  "emitido_em", "cliente"]
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        for r in registros:
            w.writerow(r)
    print(f"[OK] {len(registros)} registro(s) exportado(s) para {destino}.")
    return 0


# ---------------------------------------------------------------------------
# Menu interativo
# ---------------------------------------------------------------------------

def menu_interativo() -> int:
    _aplicar_chave_do_arquivo()
    seguranca, licenca = _recarregar_modulos()

    while True:
        print("\n" + "=" * 46)
        print("   Central de Emissão de Seriais - ToschiBook")
        print("=" * 46)
        estado = ("PADRAO (insegura)" if seguranca.usando_chave_insegura()
                  else f"segura [{seguranca.impressao_digital_chave()}]")
        print(f"   Chave: {estado}")
        print("-" * 46)
        print("   1) Emitir seriais")
        print("   2) Validar um serial")
        print("   3) Ver histórico de emissões")
        print("   4) Criar/renovar chave mestra forte")
        print("   5) Exportar histórico para CSV")
        print("   0) Sair")
        escolha = input("\n   Opção: ").strip()

        if escolha == "0":
            return 0
        elif escolha == "1":
            tipos = list(licenca.TIPOS_LICENCA)
            print("\n   Tipos:", ", ".join(tipos))
            tipo = input("   Tipo [anual]: ").strip() or "anual"
            if tipo not in licenca.TIPOS_LICENCA:
                print("   Tipo inválido."); continue
            try:
                qtd = int(input("   Quantidade [1]: ").strip() or "1")
            except ValueError:
                qtd = 1
            cliente = input("   Cliente/pedido (opcional): ").strip()
            ns = argparse.Namespace(tipo=tipo, quantidade=qtd, dias=None,
                                    ativacoes=None, cliente=cliente, forcar=False)
            cmd_emitir(ns)
            seguranca, licenca = _recarregar_modulos()
        elif escolha == "2":
            serial = input("   Serial: ").strip()
            cmd_validar(argparse.Namespace(serial=serial))
        elif escolha == "3":
            cmd_historico(argparse.Namespace())
        elif escolha == "4":
            conf = input("   Criar nova chave? Isso invalida seriais antigos "
                         "se já existir (s/N): ").strip().lower()
            if conf == "s":
                cmd_chave(argparse.Namespace(criar=True, forcar=True))
                seguranca, licenca = _recarregar_modulos()
        elif escolha == "5":
            saida = input("   Arquivo de saída [seriais.csv]: ").strip() or "seriais.csv"
            cmd_exportar(argparse.Namespace(saida=saida))
        else:
            print("   Opção inválida.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Central de emissão de seriais do ToschiBook")
    sub = parser.add_subparsers(dest="cmd")

    p_chave = sub.add_parser("chave", help="Gerencia a chave mestra.")
    p_chave.add_argument("--criar", action="store_true",
                         help="Cria uma chave forte e salva em licenca.key.")
    p_chave.add_argument("--forcar", action="store_true",
                         help="Substitui a chave existente.")

    p_emitir = sub.add_parser("emitir", help="Emite seriais e registra no log.")
    p_emitir.add_argument("--tipo", default="perpetua")
    p_emitir.add_argument("--quantidade", "-q", type=int, default=1)
    p_emitir.add_argument("--dias", type=int, default=None)
    p_emitir.add_argument("--ativacoes", "-a", type=int, default=None)
    p_emitir.add_argument("--cliente", default="")
    p_emitir.add_argument("--forcar", action="store_true",
                          help="Permite emitir com a chave padrão (só testes).")

    p_val = sub.add_parser("validar", help="Valida um serial.")
    p_val.add_argument("serial")

    sub.add_parser("historico", help="Lista os seriais já emitidos.")

    p_exp = sub.add_parser("exportar", help="Exporta o histórico para CSV.")
    p_exp.add_argument("--saida", default="seriais.csv")

    args = parser.parse_args()

    if args.cmd == "chave":
        return cmd_chave(args)
    if args.cmd == "emitir":
        return cmd_emitir(args)
    if args.cmd == "validar":
        return cmd_validar(args)
    if args.cmd == "historico":
        return cmd_historico(args)
    if args.cmd == "exportar":
        return cmd_exportar(args)

    # Sem subcomando -> menu interativo.
    return menu_interativo()


if __name__ == "__main__":
    raise SystemExit(main())
