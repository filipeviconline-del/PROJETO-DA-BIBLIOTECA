"""Gera o ícone do ToschiBook (PNG) usando apenas a biblioteca padrão.

Desenha um "livro" estilizado em fundo verde (identidade do ToschiBook) e
salva em assets/toschibook.png. Não requer Pillow nem dependências externas.

Uso:
    python3 criar_icone.py
"""
import struct
import zlib
from pathlib import Path

TAM = 256  # ícone 256x256

# Cores (R, G, B)
VERDE = (22, 115, 74)
VERDE_ESCURO = (13, 79, 53)
BRANCO = (245, 251, 247)
CLARO = (233, 246, 238)


def _novo_canvas(cor):
    return [[list(cor) for _ in range(TAM)] for _ in range(TAM)]


def _ret(px, x0, y0, x1, y1, cor):
    for y in range(max(0, y0), min(TAM, y1)):
        for x in range(max(0, x0), min(TAM, x1)):
            px[y][x] = list(cor)


def _ret_borda(px, x0, y0, x1, y1, cor, esp):
    _ret(px, x0, y0, x1, y0 + esp, cor)          # topo
    _ret(px, x0, y1 - esp, x1, y1, cor)          # base
    _ret(px, x0, y0, x0 + esp, y1, cor)          # esquerda
    _ret(px, x1 - esp, y0, x1, y1, cor)          # direita


def desenhar():
    px = _novo_canvas(VERDE)

    # Cantos arredondados simples: apaga os 4 cantos para transparência? Mantemos
    # fundo quadrado verde com um leve degrade (faixa mais escura embaixo).
    _ret(px, 0, int(TAM * 0.78), TAM, TAM, VERDE_ESCURO)

    # Livro: capa (retângulo branco) com lombada central
    x0, y0, x1, y1 = 60, 55, 196, 201
    _ret_borda(px, x0, y0, x1, y1, BRANCO, 7)
    # lombada central
    _ret(px, (x0 + x1) // 2 - 3, y0, (x0 + x1) // 2 + 3, y1, BRANCO)

    # "linhas" de texto (páginas) em cada lado
    for ly in (90, 112, 134):
        _ret(px, 78, ly, 118, ly + 5, CLARO)      # página esquerda
        _ret(px, 140, ly, 180, ly + 5, CLARO)     # página direita

    return px


def salvar_png(px, caminho):
    # Monta os bytes do PNG (RGB, sem filtro por linha).
    linhas = bytearray()
    for y in range(TAM):
        linhas.append(0)  # filtro "None" para a linha
        for x in range(TAM):
            linhas.extend(px[y][x])

    def _chunk(tipo, dados):
        c = struct.pack(">I", len(dados)) + tipo + dados
        crc = zlib.crc32(tipo + dados) & 0xFFFFFFFF
        return c + struct.pack(">I", crc)

    cabecalho = struct.pack(">IIBBBBB", TAM, TAM, 8, 2, 0, 0, 0)  # 8 bits, RGB
    png = (b"\x89PNG\r\n\x1a\n"
           + _chunk(b"IHDR", cabecalho)
           + _chunk(b"IDAT", zlib.compress(bytes(linhas), 9))
           + _chunk(b"IEND", b""))

    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    Path(caminho).write_bytes(png)


def main():
    destino = Path(__file__).resolve().parent / "assets" / "toschibook.png"
    salvar_png(desenhar(), destino)
    print(f"[OK] Ícone gerado em: {destino}")


if __name__ == "__main__":
    main()
