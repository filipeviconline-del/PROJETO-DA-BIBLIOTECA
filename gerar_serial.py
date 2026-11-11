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

    # Valida um serial existente
    python gerar_serial.py --validar ABCDE-FGHJK-LMNPQ-RSTUV-WXYZ2
"""
import argparse
import sys

import licenca


def gerar(tipo: str, quantidade: int, dias: int | None) -> None:
    print(f"\n== Gerando {quantidade} serial(is) do tipo '{tipo}' ==\n")
    for i in range(1, quantidade + 1):
        serial = licenca.gerar_serial(tipo=tipo, dias_validade=dias)
        validade = dias if dias is not None else licenca.TIPOS_LICENCA[tipo]
        rotulo = "perpétua" if validade == 0 else f"{validade} dias"
        print(f"  {i:>3}. {serial}   ({rotulo})")
    print()


def validar(serial: str) -> None:
    resultado = licenca.validar_serial(serial)
    print()
    if resultado["valido"]:
        print("  [VALIDO]")
        print(f"    Tipo ............ {resultado['tipo']}")
        print(f"    Validade (dias).. {resultado['dias_validade'] or 'perpetua'}")
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
        "--validar", metavar="SERIAL",
        help="Valida um serial em vez de gerar.",
    )
    args = parser.parse_args()

    if args.validar:
        validar(args.validar)
        return 0

    if args.quantidade < 1:
        print("A quantidade deve ser >= 1.", file=sys.stderr)
        return 1

    gerar(args.tipo, args.quantidade, args.dias)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
