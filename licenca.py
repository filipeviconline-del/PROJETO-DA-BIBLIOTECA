"""Sistema de licenciamento e serial do ToschiBook.

Este módulo é responsável por:
  * Gerar números de série (seriais) assinados criptograficamente;
  * Validar seriais informados pelo usuário;
  * Vincular a ativação ao hardware da máquina (fingerprint);
  * Persistir o estado de ativação no banco de dados.

O serial tem o formato amigável ``XXXXX-XXXXX-XXXXX-XXXXX-XXXXX`` e carrega,
de forma embutida e assinada, os metadados da licença (tipo, data de validade
e identificador). Assim é possível validar um serial OFFLINE, sem servidor.

IMPORTANTE: a segurança depende de manter a ``CHAVE_SECRETA`` em segredo.
Em produção, defina a variável de ambiente ``TOSCHIBOOK_LICENSE_KEY``.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import platform
import re
import struct
import subprocess
import uuid
from datetime import date, datetime, timedelta

from database import get_connection

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

# Chave mestra usada para assinar/validar os seriais. Deve ser a MESMA no
# gerador de seriais (fábrica) e no produto instalado. Troque por um valor
# forte e secreto em produção através da variável de ambiente.
CHAVE_SECRETA = os.environ.get(
    "TOSCHIBOOK_LICENSE_KEY",
    "ToschiBook-Chave-Mestra-2026-NAO-COMPARTILHAR",
).encode("utf-8")

# Alfabeto usado nos seriais (sem caracteres ambíguos: 0/O, 1/I).
ALFABETO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
BASE = len(ALFABETO)

# Tipos de licença suportados e a duração padrão (em dias). 0 = perpétua.
TIPOS_LICENCA = {
    "trial": 30,
    "anual": 365,
    "perpetua": 0,
}

PREFIXO_PAYLOAD = b"TB1"  # versão do formato do payload


# ---------------------------------------------------------------------------
# Identificação da máquina (fingerprint)
# ---------------------------------------------------------------------------

def obter_id_maquina() -> str:
    """Gera um identificador estável e anônimo da máquina atual.

    Combina informações do sistema e o MAC/UUID da placa. O resultado é um
    hash curto, não reversível, usado apenas para amarrar a ativação ao
    equipamento onde o serial foi ativado.
    """
    partes = [platform.node(), platform.machine(), platform.system()]

    # Tenta capturar o UUID da placa-mãe (varia por SO).
    try:
        sistema = platform.system()
        if sistema == "Windows":
            saida = subprocess.check_output(
                "wmic csproduct get uuid", shell=True, timeout=5
            ).decode(errors="ignore")
            partes.append(saida.strip().splitlines()[-1].strip())
        elif sistema == "Darwin":
            saida = subprocess.check_output(
                "ioreg -rd1 -c IOPlatformExpertDevice", shell=True, timeout=5
            ).decode(errors="ignore")
            m = re.search(r'"IOPlatformUUID" = "([^"]+)"', saida)
            if m:
                partes.append(m.group(1))
        else:  # Linux e outros
            for caminho in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
                if os.path.exists(caminho):
                    with open(caminho, "r", encoding="utf-8") as f:
                        partes.append(f.read().strip())
                    break
    except Exception:
        # Falhou a coleta específica: usa o MAC como fallback.
        partes.append(str(uuid.getnode()))

    bruto = "|".join(p for p in partes if p)
    return hashlib.sha256(bruto.encode("utf-8")).hexdigest()[:16].upper()


# ---------------------------------------------------------------------------
# Codificação base32 customizada (alfabeto sem ambiguidade)
# ---------------------------------------------------------------------------

def _bytes_para_texto(dados: bytes) -> str:
    """Converte bytes para texto usando o ALFABETO (base32 custom)."""
    numero = int.from_bytes(dados, "big")
    if numero == 0:
        return ALFABETO[0]
    saida = []
    while numero > 0:
        numero, resto = divmod(numero, BASE)
        saida.append(ALFABETO[resto])
    return "".join(reversed(saida))


def _texto_para_bytes(texto: str, tamanho: int) -> bytes:
    """Converte o texto do ALFABETO de volta para bytes (tamanho fixo)."""
    numero = 0
    for ch in texto:
        numero = numero * BASE + ALFABETO.index(ch)
    return numero.to_bytes(tamanho, "big")


def _formatar_grupos(texto: str) -> str:
    """Quebra o texto em grupos de 5 separados por hífen."""
    return "-".join(texto[i:i + 5] for i in range(0, len(texto), 5))


# ---------------------------------------------------------------------------
# Geração e validação dos seriais
# ---------------------------------------------------------------------------

def gerar_serial(tipo: str = "perpetua", dias_validade: int | None = None,
                 identificador: int | None = None) -> str:
    """Gera um serial assinado.

    Args:
        tipo: um dos valores de ``TIPOS_LICENCA``.
        dias_validade: sobrescreve a duração padrão do tipo (opcional).
        identificador: número sequencial/aleatório embutido no serial.

    Returns:
        Serial no formato ``XXXXX-XXXXX-...``.
    """
    if tipo not in TIPOS_LICENCA:
        raise ValueError(f"Tipo de licença inválido: {tipo}")

    if dias_validade is None:
        dias_validade = TIPOS_LICENCA[tipo]

    if identificador is None:
        identificador = struct.unpack(">H", os.urandom(2))[0]

    cod_tipo = list(TIPOS_LICENCA).index(tipo)  # 0..255

    # Payload: versão(3) + tipo(1) + validade_dias(2) + id(2) = 8 bytes
    payload = PREFIXO_PAYLOAD + struct.pack(">BHH", cod_tipo,
                                            min(dias_validade, 65535),
                                            identificador & 0xFFFF)

    assinatura = hmac.new(CHAVE_SECRETA, payload, hashlib.sha256).digest()[:5]
    bruto = payload + assinatura  # 13 bytes

    texto = _bytes_para_texto(bruto).rjust(25, ALFABETO[0])
    return _formatar_grupos(texto[:25])


def _decodificar_serial(serial: str) -> dict | None:
    """Decodifica e valida a assinatura de um serial. Retorna metadados."""
    limpo = serial.strip().upper().replace("-", "").replace(" ", "")
    if not re.fullmatch(f"[{ALFABETO}]{{25}}", limpo):
        return None

    try:
        bruto = _texto_para_bytes(limpo, 13)
    except (ValueError, OverflowError):
        return None

    payload, assinatura = bruto[:8], bruto[8:]

    if payload[:3] != PREFIXO_PAYLOAD:
        return None

    esperada = hmac.new(CHAVE_SECRETA, payload, hashlib.sha256).digest()[:5]
    if not hmac.compare_digest(esperada, assinatura):
        return None

    cod_tipo, dias, identificador = struct.unpack(">BHH", payload[3:])
    tipos = list(TIPOS_LICENCA)
    if cod_tipo >= len(tipos):
        return None

    return {
        "tipo": tipos[cod_tipo],
        "dias_validade": dias,
        "identificador": identificador,
    }


def validar_serial(serial: str) -> dict:
    """Valida um serial e retorna o resultado detalhado.

    Returns:
        dict com chave ``valido`` (bool) e, quando válido, os metadados.
    """
    info = _decodificar_serial(serial)
    if info is None:
        return {"valido": False, "erro": "Serial inválido ou corrompido."}
    return {"valido": True, **info}


# ---------------------------------------------------------------------------
# Persistência da ativação
# ---------------------------------------------------------------------------

def _garantir_tabela(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS licenca (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            serial TEXT NOT NULL,
            tipo TEXT NOT NULL,
            id_maquina TEXT NOT NULL,
            ativado_em TEXT NOT NULL,
            expira_em TEXT
        )
        """
    )


def ativar(serial: str) -> dict:
    """Ativa o produto com o serial informado, vinculando à máquina atual."""
    resultado = validar_serial(serial)
    if not resultado["valido"]:
        return {"sucesso": False, "erro": resultado.get("erro", "Serial inválido.")}

    tipo = resultado["tipo"]
    dias = resultado["dias_validade"]

    ativado_em = datetime.now()
    expira_em = None
    if dias and dias > 0:
        expira_em = (ativado_em + timedelta(days=dias)).date().isoformat()

    conn = get_connection()
    try:
        _garantir_tabela(conn)
        conn.execute("DELETE FROM licenca")
        conn.execute(
            """
            INSERT INTO licenca (id, serial, tipo, id_maquina, ativado_em, expira_em)
            VALUES (1, ?, ?, ?, ?, ?)
            """,
            (
                serial.strip().upper(),
                tipo,
                obter_id_maquina(),
                ativado_em.isoformat(timespec="seconds"),
                expira_em,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return {
        "sucesso": True,
        "tipo": tipo,
        "expira_em": expira_em,
        "mensagem": "Produto ativado com sucesso!",
    }


def status() -> dict:
    """Retorna o status atual da licença instalada."""
    conn = get_connection()
    try:
        _garantir_tabela(conn)
        row = conn.execute("SELECT * FROM licenca WHERE id = 1").fetchone()
    finally:
        conn.close()

    if not row:
        return {"ativado": False, "motivo": "nao_ativado"}

    dados = dict(row)

    # A licença precisa ter sido ativada NESTA máquina.
    if dados["id_maquina"] != obter_id_maquina():
        return {
            "ativado": False,
            "motivo": "maquina_diferente",
            "mensagem": "Esta licença foi ativada em outro computador.",
        }

    expira_em = dados.get("expira_em")
    if expira_em:
        try:
            if date.fromisoformat(expira_em) < date.today():
                return {
                    "ativado": False,
                    "motivo": "expirada",
                    "expira_em": expira_em,
                    "mensagem": "A licença expirou. Informe um novo serial.",
                }
        except ValueError:
            pass

    return {
        "ativado": True,
        "tipo": dados["tipo"],
        "ativado_em": dados["ativado_em"],
        "expira_em": expira_em,
        "dias_restantes": _dias_restantes(expira_em),
    }


def _dias_restantes(expira_em: str | None) -> int | None:
    if not expira_em:
        return None
    try:
        return (date.fromisoformat(expira_em) - date.today()).days
    except ValueError:
        return None


def esta_ativado() -> bool:
    """Atalho booleano para o middleware de rotas."""
    return bool(status().get("ativado"))


def desativar() -> None:
    """Remove a ativação local (uso administrativo/testes)."""
    conn = get_connection()
    try:
        _garantir_tabela(conn)
        conn.execute("DELETE FROM licenca")
        conn.commit()
    finally:
        conn.close()
