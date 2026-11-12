"""Gerador de seriais do ToschiBook (ferramenta administrativa).

Use esta ferramenta para emitir números de série que serão fornecidos aos
clientes. Ela usa a MESMA chave secreta do produto (``TOSCHIBOOK_LICENSE_KEY``)
para assinar os seriais.

NÃO distribua este arquivo junto com o produto final — ele é de uso interno
de quem vende/administra as licenças.

Exemplos de uso:

    # Gera 1 serial perpétuo
    python gerar_serial.py

    # Gera 5 seriais do tipo anual
    python gerar_serial.py --tipo anual --quantidade 5

    # Gera um trial de 15 dias
    python gerar_serial.py --tipo trial --dias 15

    # Gera licença corporativa com até 50 ativações (máquinas)
    python gerar_serial.py --tipo corporativa --ativacoes 50

    # Gera licença com ativações ILIMITADAS
    python gerar_serial.py --tipo perpetua --ativacoes 0

    # Lista os tipos de licença disponíveis
    python gerar_serial.py --listar-tipos

    # Valida um serial existente
    python gerar_serial.py --validar ABCDE-FGHJK-LMNPQ-RSTUV-WXYZ2
"""
import argparse
import sys

import licenca


def _rotulo_validade(dias: int) -> str:
    return "perpetua" if dias == 0 else f"{dias} dias"


def _rotulo_ativacoes(n: int) -> str:
    return "ilimitadas" if n == 0 else f"{n} maquina(s)"


def listar_tipos() -> None:
    print("\n== Tipos de licenca disponiveis ==\n")
    print(f"  {'tipo':<14}{'validade':<14}{'ativacoes (padrao)'}")
    print(f"  {'-'*12:<14}{'-'*12:<14}{'-'*18}")
    for tipo, dias in licenca.TIPOS_LICENCA.items():
        ativ = licenca.ATIVACOES_PADRAO.get(tipo, 1)
        print(f"  {tipo:<14}{_rotulo_validade(dias):<14}{_rotulo_ativacoes(ativ)}")
    print()


def gerar(tipo: str, quantidade: int, dias: int | None,
          ativacoes: int | None) -> None:
    validade = dias if dias is not None else licenca.TIPOS_LICENCA[tipo]
    max_ativ = ativacoes if ativacoes is not None else licenca.ATIVACOES_PADRAO.get(tipo, 1)

    print(f"\n== Gerando {quantidade} serial(is) do tipo '{tipo}' ==")
    print(f"   Validade: {_rotulo_validade(validade)}  |  "
          f"Ativacoes: {_rotulo_ativacoes(max_ativ)}\n")

    for i in range(1, quantidade + 1):
        serial = licenca.gerar_serial(
            tipo=tipo, dias_validade=dias, max_ativacoes=ativacoes
        )
        print(f"  {i:>3}. {serial}")
    print()


def validar(serial: str) -> None:
    resultado = licenca.validar_serial(serial)
    print()
    if resultado["valido"]:
        print("  [VALIDO]")
        print(f"    Tipo ............ {resultado['tipo']}")
        print(f"    Validade (dias).. {resultado['dias_validade'] or 'perpetua'}")
        print(f"    Ativacoes ....... {_rotulo_ativacoes(resultado.get('max_ativacoes', 1))}")
        print(f"    Identificador ... {resultado['identificador']}")
    else:
        print(f"  [INVALIDO]  - {resultado.get('erro')}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Gerador de seriais do ToschiBook")
    parser.add_argument(
        "--tipo",
        choices=list(licenca.TIPOS_LICENCA),
        default="perpetua",
        help="Tipo de licença (padrão: perpetua).",
    )
    parser.add_argument(
        "--quantidade", "-q", type=int, default=1,
        help="Quantidade de seriais a gerar (padrão: 1).",
    )
    parser.add_argument(
        "--dias", type=int, default=None,
        help="Validade em dias (sobrescreve o padrão do tipo).",
    )
    parser.add_argument(
        "--ativacoes", "-a", type=int, default=None,
        help="Limite de ativações/máquinas (0 = ilimitado). "
             "Sobrescreve o padrão do tipo.",
    )
    parser.add_argument(
        "--listar-tipos", action="store_true",
        help="Lista os tipos de licença e sai.",
    )
    parser.add_argument(
        "--validar", metavar="SERIAL",
        help="Valida um serial em vez de gerar.",
    )
    args = parser.parse_args()

    # Avisa o administrador se estiver assinando com a chave padrão insegura.
    try:
        import seguranca
        if seguranca.usando_chave_insegura():
            print("\n[AVISO] Gerando seriais com a CHAVE PADRAO (insegura).")
            print("        Defina TOSCHIBOOK_LICENSE_KEY (a mesma no produto) "
                  "antes de emitir seriais reais.\n")
    except Exception:
        pass

    if args.listar_tipos:
        listar_tipos()
        return 0

    if args.validar:
        validar(args.validar)
        return 0

    if args.quantidade < 1:
        print("A quantidade deve ser >= 1.", file=sys.stderr)
        return 1

    if args.ativacoes is not None and args.ativacoes < 0:
        print("O limite de ativações deve ser >= 0 (0 = ilimitado).", file=sys.stderr)
        return 1

    gerar(args.tipo, args.quantidade, args.dias, args.ativacoes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
