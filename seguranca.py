"""Camada de segurança do licenciamento do ToschiBook.

Reúne mecanismos para dificultar a adulteração/cracking das licenças, usando
apenas a biblioteca padrão (hmac/hashlib) — sem dependências externas:

  * carregamento seguro da chave mestra (fora do código-fonte);
  * assinatura de registros (licença e ativações) para detectar adulteração
    direta do banco de dados (biblioteca.db);
  * detecção de retrocesso do relógio do sistema ("clock rollback"), que
    burlaria licenças com validade.

IMPORTANTE: nenhuma proteção client-side é 100% inviolável contra um atacante
que controla totalmente a máquina. O objetivo aqui é elevar bastante o custo
do ataque (edição de banco, falsificação de serial e manipulação de relógio
deixam de funcionar com edições triviais).
"""
from __future__ import annotations

import hashlib
import hmac
import os
import warnings
from pathlib import Path

# Chave padrão (INSEGURA) — apenas para desenvolvimento. Em produção, defina
# TOSCHIBOOK_LICENSE_KEY ou crie o arquivo de chave (ver _carregar_chave).
_CHAVE_PADRAO = "ToschiBook-Chave-Mestra-2026-NAO-COMPARTILHAR"

# Nome do arquivo opcional que guarda a chave fora do código-fonte.
_ARQUIVO_CHAVE = os.environ.get("TOSCHIBOOK_LICENSE_KEY_FILE", "")

# Arquivo de chave padrão, procurado ao lado deste módulo (licenca.key).
# É o MESMO arquivo que a central de emissão (gerador_serial) cria, de modo
# que o gerador e o produto usem automaticamente a mesma chave — sem o usuário
# precisar definir variáveis de ambiente.
_ARQUIVO_CHAVE_LOCAL = Path(__file__).resolve().parent / "licenca.key"


def _ler_arquivo(caminho) -> str | None:
    try:
        dados = Path(caminho).read_text(encoding="utf-8").strip()
        return dados or None
    except OSError:
        return None


def _carregar_chave() -> tuple[bytes, bool]:
    """Carrega a chave mestra e informa se está usando o padrão inseguro.

    Ordem de prioridade:
      1. variável de ambiente TOSCHIBOOK_LICENSE_KEY;
      2. arquivo apontado por TOSCHIBOOK_LICENSE_KEY_FILE;
      3. arquivo ``licenca.key`` ao lado do código (criado pela central);
      4. chave padrão de desenvolvimento (emite aviso).
    """
    valor = os.environ.get("TOSCHIBOOK_LICENSE_KEY")
    if valor:
        return valor.encode("utf-8"), False

    if _ARQUIVO_CHAVE:
        dados = _ler_arquivo(_ARQUIVO_CHAVE)
        if dados:
            return dados.encode("utf-8"), False

    dados = _ler_arquivo(_ARQUIVO_CHAVE_LOCAL)
    if dados:
        return dados.encode("utf-8"), False

    return _CHAVE_PADRAO.encode("utf-8"), True


CHAVE_SECRETA, _USANDO_CHAVE_PADRAO = _carregar_chave()


def usando_chave_insegura() -> bool:
    """True se o produto está rodando com a chave padrão de desenvolvimento."""
    return _USANDO_CHAVE_PADRAO


def avisar_se_chave_insegura():
    """Emite um aviso (uma vez) se a chave padrão estiver em uso."""
    if _USANDO_CHAVE_PADRAO:
        warnings.warn(
            "ToschiBook: usando a CHAVE DE LICENÇA PADRÃO (insegura). "
            "Em produção, defina a variável de ambiente TOSCHIBOOK_LICENSE_KEY "
            "com um valor forte e secreto.",
            RuntimeWarning,
            stacklevel=2,
        )


# ---------------------------------------------------------------------------
# Derivação de sub-chaves (domain separation)
# ---------------------------------------------------------------------------
# Cada finalidade usa uma sub-chave distinta derivada da chave mestra, para que
# o vazamento/uso de uma não enfraqueça as demais.

def _subchave(dominio: str) -> bytes:
    return hmac.new(CHAVE_SECRETA, b"toschibook:" + dominio.encode(),
                    hashlib.sha256).digest()


_SK_SERIAL = _subchave("serial")        # assinatura dos seriais
_SK_REGISTRO = _subchave("registro")    # assinatura do estado no banco
_SK_RELOGIO = _subchave("relogio")      # assinatura do "último horário visto"


def chave_serial() -> bytes:
    """Sub-chave usada para assinar/validar os seriais."""
    return _SK_SERIAL


# ---------------------------------------------------------------------------
# Assinatura de registros (anti-adulteração do banco)
# ---------------------------------------------------------------------------

def assinar_registro(campos) -> str:
    """Gera um HMAC hex para um conjunto de campos (tupla/lista de valores).

    Usado para detectar edição manual das tabelas de licença e ativações.
    """
    base = "|".join("" if c is None else str(c) for c in campos)
    return hmac.new(_SK_REGISTRO, base.encode("utf-8"),
                    hashlib.sha256).hexdigest()


def verificar_registro(campos, assinatura: str | None) -> bool:
    """Confere se a assinatura corresponde aos campos (comparação constante)."""
    if not assinatura:
        return False
    esperada = assinar_registro(campos)
    return hmac.compare_digest(esperada, assinatura)


# ---------------------------------------------------------------------------
# Proteção contra retrocesso de relógio (clock rollback)
# ---------------------------------------------------------------------------

def assinar_relogio(epoch: int) -> str:
    """Assina um instante (epoch) para gravar o 'último horário visto'."""
    return hmac.new(_SK_RELOGIO, str(int(epoch)).encode(),
                    hashlib.sha256).hexdigest()


def verificar_relogio(epoch: int, assinatura: str | None) -> bool:
    """Confere a assinatura do 'último horário visto'."""
    if not assinatura:
        return False
    return hmac.compare_digest(assinar_relogio(int(epoch)), assinatura)


# ---------------------------------------------------------------------------
# Geração/gestão da chave mestra (uso administrativo)
# ---------------------------------------------------------------------------

def gerar_chave_forte(tamanho_bytes: int = 48) -> str:
    """Gera uma chave mestra forte e aleatória (texto seguro para URL)."""
    import secrets
    return secrets.token_urlsafe(tamanho_bytes)


def impressao_digital_chave() -> str:
    """Retorna uma 'impressão digital' curta da chave mestra em uso.

    Permite conferir, sem expor a chave, se o gerador e o produto usam a MESMA
    chave (as impressões digitais devem ser idênticas).
    """
    return hashlib.sha256(b"fp:" + CHAVE_SECRETA).hexdigest()[:12].upper()
