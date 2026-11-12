"""Sistema de licenciamento e serial do ToschiBook.

Este módulo é responsável por:
  * Gerar números de série (seriais) assinados criptograficamente;
  * Validar seriais informados pelo usuário;
  * Vincular a ativação ao hardware da máquina (fingerprint);
  * Persistir o estado de ativação no banco de dados.

O serial tem o formato amigável ``XXXXX-XXXXX-XXXXX-XXXXX-XXXXX`` e carrega,
de forma embutida e assinada, os metadados da licença (tipo, data de validade,
limite de ativações e identificador). Assim é possível validar um serial
OFFLINE, sem servidor.

Formatos de payload suportados:
  * ``TB1`` (legado): tipo + validade + id. Limite de ativações = 1.
  * ``TB2`` (atual):  tipo + validade + limite de ativações + id.

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
import time
import uuid
from datetime import date, datetime, timedelta

from database import get_connection
import seguranca

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

# A chave mestra agora vem do módulo de segurança, que a carrega de fora do
# código-fonte (variável de ambiente ou arquivo) e avisa se estiver usando a
# chave padrão insegura. Os seriais são assinados com uma SUB-CHAVE derivada
# (domain separation), de modo que a assinatura do serial é isolada das demais
# finalidades (estado no banco, relógio).
CHAVE_SECRETA = seguranca.chave_serial()

# Alfabeto usado nos seriais (sem caracteres ambíguos: 0/O, 1/I).
ALFABETO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
BASE = len(ALFABETO)

# Tipos de licença suportados e a duração padrão (em dias). 0 = perpétua.
# A ORDEM importa: o índice é gravado no serial. Só ACRESCENTE no final;
# não reordene nem remova itens, para não invalidar seriais já emitidos.
TIPOS_LICENCA = {
    "trial": 30,
    "mensal": 30,
    "trimestral": 90,
    "semestral": 180,
    "anual": 365,
    "bienal": 730,
    "perpetua": 0,
    "vitalicia": 0,     # alias comercial de "perpetua"
    "educacional": 365,
    "corporativa": 365,
}

# Limite de ativações padrão por tipo (quantas máquinas podem ativar o serial).
# 0 = ilimitado.
ATIVACOES_PADRAO = {
    "trial": 1,
    "mensal": 1,
    "trimestral": 1,
    "semestral": 2,
    "anual": 3,
    "bienal": 3,
    "perpetua": 1,
    "vitalicia": 1,
    "educacional": 30,
    "corporativa": 100,
}

PREFIXO_PAYLOAD = b"TB2"           # versão atual do formato do payload
PREFIXO_PAYLOAD_LEGADO = b"TB1"    # formato antigo (sem limite de ativações)


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
                 max_ativacoes: int | None = None,
                 identificador: int | None = None) -> str:
    """Gera um serial assinado (formato TB2).

    Args:
        tipo: um dos valores de ``TIPOS_LICENCA``.
        dias_validade: sobrescreve a duração padrão do tipo (opcional).
        max_ativacoes: nº de máquinas que podem ativar (0 = ilimitado).
            Se omitido, usa o padrão do tipo em ``ATIVACOES_PADRAO``.
        identificador: número sequencial/aleatório embutido no serial.

    Returns:
        Serial no formato ``XXXXX-XXXXX-...``.
    """
    if tipo not in TIPOS_LICENCA:
        raise ValueError(f"Tipo de licença inválido: {tipo}")

    if dias_validade is None:
        dias_validade = TIPOS_LICENCA[tipo]

    if max_ativacoes is None:
        max_ativacoes = ATIVACOES_PADRAO.get(tipo, 1)

    if identificador is None:
        identificador = struct.unpack(">H", os.urandom(2))[0]

    cod_tipo = list(TIPOS_LICENCA).index(tipo)  # 0..255

    # Payload TB2: versão(3) + tipo(1) + validade_dias(2) + ativacoes(1) + id(2) = 9 bytes
    payload = PREFIXO_PAYLOAD + struct.pack(
        ">BHBH",
        cod_tipo,
        min(dias_validade, 65535),
        min(max_ativacoes, 255),
        identificador & 0xFFFF,
    )

    assinatura = hmac.new(CHAVE_SECRETA, payload, hashlib.sha256).digest()[:5]
    bruto = payload + assinatura  # 14 bytes

    texto = _bytes_para_texto(bruto).rjust(25, ALFABETO[0])
    return _formatar_grupos(texto[:25])


def _tentar_formato(limpo: str, tamanho: int, prefixo: bytes,
                    payload_len: int) -> dict | None:
    """Tenta decodificar o serial assumindo um formato (TB1 ou TB2)."""
    try:
        bruto = _texto_para_bytes(limpo, tamanho)
    except (ValueError, OverflowError):
        return None

    payload, assinatura = bruto[:payload_len], bruto[payload_len:]

    if payload[:3] != prefixo:
        return None

    esperada = hmac.new(CHAVE_SECRETA, payload, hashlib.sha256).digest()[:5]
    if not hmac.compare_digest(esperada, assinatura):
        return None

    tipos = list(TIPOS_LICENCA)

    if prefixo == PREFIXO_PAYLOAD:  # TB2: tipo + validade + ativacoes + id
        cod_tipo, dias, ativacoes, identificador = struct.unpack(">BHBH", payload[3:])
    else:  # TB1 (legado): tipo + validade + id, limite implícito = 1
        cod_tipo, dias, identificador = struct.unpack(">BHH", payload[3:])
        ativacoes = 1

    if cod_tipo >= len(tipos):
        return None

    return {
        "tipo": tipos[cod_tipo],
        "dias_validade": dias,
        "max_ativacoes": ativacoes,
        "identificador": identificador,
    }


def _decodificar_serial(serial: str) -> dict | None:
    """Decodifica e valida a assinatura de um serial. Retorna metadados.

    Tenta o formato atual (TB2) e, em seguida, o legado (TB1).
    """
    limpo = serial.strip().upper().replace("-", "").replace(" ", "")
    if not re.fullmatch(f"[{ALFABETO}]{{25}}", limpo):
        return None

    # TB2: 9 bytes de payload + 5 de assinatura = 14 bytes
    info = _tentar_formato(limpo, 14, PREFIXO_PAYLOAD, 9)
    if info is not None:
        return info

    # TB1 (legado): 8 bytes de payload + 5 de assinatura = 13 bytes
    return _tentar_formato(limpo, 13, PREFIXO_PAYLOAD_LEGADO, 8)


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
    # Licença atualmente ativa nesta instalação.
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS licenca (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            serial TEXT NOT NULL,
            tipo TEXT NOT NULL,
            id_maquina TEXT NOT NULL,
            ativado_em TEXT NOT NULL,
            expira_em TEXT,
            max_ativacoes INTEGER DEFAULT 1,
            assinatura TEXT
        )
        """
    )
    # Migrações seguras: adicionam colunas em bancos antigos.
    for coluna, ddl in [
        ("max_ativacoes", "ALTER TABLE licenca ADD COLUMN max_ativacoes INTEGER DEFAULT 1"),
        ("assinatura", "ALTER TABLE licenca ADD COLUMN assinatura TEXT"),
    ]:
        try:
            conn.execute(ddl)
        except Exception:
            pass  # coluna já existe

    # Histórico de ativações: cada (serial, máquina) distinto conta 1 ativação.
    # A coluna 'assinatura' protege cada registro contra inserção/edição manual.
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ativacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            serial TEXT NOT NULL,
            id_maquina TEXT NOT NULL,
            ativado_em TEXT NOT NULL,
            assinatura TEXT,
            UNIQUE (serial, id_maquina)
        )
        """
    )
    try:
        conn.execute("ALTER TABLE ativacoes ADD COLUMN assinatura TEXT")
    except Exception:
        pass

    # Auditoria de relógio (anti clock-rollback): guarda o maior horário já
    # visto, assinado, para detectar quando o usuário atrasa o relógio.
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS relogio_auditoria (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            ultimo_epoch INTEGER NOT NULL,
            assinatura TEXT NOT NULL
        )
        """
    )


# --- assinaturas de registro (anti-adulteração do banco) ---

def _assinatura_licenca(serial, tipo, id_maquina, ativado_em, expira_em,
                        max_ativacoes) -> str:
    return seguranca.assinar_registro(
        (serial, tipo, id_maquina, ativado_em, expira_em, max_ativacoes)
    )


def _assinatura_ativacao(serial, id_maquina, ativado_em) -> str:
    return seguranca.assinar_registro((serial, id_maquina, ativado_em))


def _contar_ativacoes(conn, serial: str) -> int:
    """Nº de máquinas distintas (com registro ÍNTEGRO) que ativaram o serial.

    Registros cuja assinatura não confere (inseridos/editados manualmente no
    banco) são ignorados na contagem — não valem como ativação.
    """
    rows = conn.execute(
        "SELECT id_maquina, ativado_em, assinatura FROM ativacoes WHERE serial = ?",
        (serial,),
    ).fetchall()
    validos = 0
    for r in rows:
        if seguranca.verificar_registro(
            (serial, r["id_maquina"], r["ativado_em"]), r["assinatura"]
        ):
            validos += 1
    return validos


# --- anti clock-rollback ---

def _checar_relogio(conn) -> bool:
    """Atualiza/verifica o 'último horário visto'. Retorna False se detectar
    retrocesso significativo do relógio (possível fraude de validade)."""
    agora = int(time.time())

    row = conn.execute(
        "SELECT ultimo_epoch, assinatura FROM relogio_auditoria WHERE id = 1"
    ).fetchone()

    ok = True
    if row:
        ultimo = int(row["ultimo_epoch"])
        # Se a assinatura não bate, o registro foi adulterado.
        if not seguranca.verificar_relogio(ultimo, row["assinatura"]):
            ok = False
        # Tolerância de 1 dia para fusos/ajustes legítimos.
        elif agora < ultimo - 86400:
            ok = False

    # Guarda sempre o MAIOR horário já visto (monotônico).
    novo = max(agora, int(row["ultimo_epoch"]) if row else agora)
    conn.execute(
        "INSERT OR REPLACE INTO relogio_auditoria (id, ultimo_epoch, assinatura) "
        "VALUES (1, ?, ?)",
        (novo, seguranca.assinar_relogio(novo)),
    )
    return ok


def ativar(serial: str) -> dict:
    """Ativa o produto com o serial informado, vinculando à máquina atual.

    Respeita o limite de ativações (nº de máquinas distintas) embutido no
    serial. Reativar na MESMA máquina não consome uma nova ativação.
    """
    resultado = validar_serial(serial)
    if not resultado["valido"]:
        return {"sucesso": False, "erro": resultado.get("erro", "Serial inválido.")}

    tipo = resultado["tipo"]
    dias = resultado["dias_validade"]
    max_ativacoes = resultado.get("max_ativacoes", 1)
    serial_norm = serial.strip().upper()
    id_maquina = obter_id_maquina()

    ativado_em = datetime.now()
    expira_em = None
    if dias and dias > 0:
        expira_em = (ativado_em + timedelta(days=dias)).date().isoformat()

    conn = get_connection()
    try:
        _garantir_tabela(conn)

        # Esta máquina já ativou este serial antes?
        ja_ativou = conn.execute(
            "SELECT 1 FROM ativacoes WHERE serial = ? AND id_maquina = ?",
            (serial_norm, id_maquina),
        ).fetchone()

        # Verifica o limite apenas se for uma máquina NOVA e o limite não for 0.
        if not ja_ativou and max_ativacoes and max_ativacoes > 0:
            usadas = _contar_ativacoes(conn, serial_norm)
            if usadas >= max_ativacoes:
                return {
                    "sucesso": False,
                    "erro": (
                        f"Limite de ativações atingido "
                        f"({usadas}/{max_ativacoes} máquinas). "
                        f"Use outro serial ou contate o suporte."
                    ),
                    "max_ativacoes": max_ativacoes,
                    "ativacoes_usadas": usadas,
                }

        ts = ativado_em.isoformat(timespec="seconds")

        # Registra a ativação desta máquina (idempotente por UNIQUE), ASSINADA.
        assinatura_ativ = _assinatura_ativacao(serial_norm, id_maquina, ts)
        conn.execute(
            """
            INSERT OR IGNORE INTO ativacoes (serial, id_maquina, ativado_em, assinatura)
            VALUES (?, ?, ?, ?)
            """,
            (serial_norm, id_maquina, ts, assinatura_ativ),
        )

        # Define a licença ativa desta instalação, com assinatura de integridade.
        assinatura_lic = _assinatura_licenca(
            serial_norm, tipo, id_maquina, ts, expira_em, max_ativacoes)
        conn.execute("DELETE FROM licenca")
        conn.execute(
            """
            INSERT INTO licenca
                (id, serial, tipo, id_maquina, ativado_em, expira_em,
                 max_ativacoes, assinatura)
            VALUES (1, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                serial_norm, tipo, id_maquina, ts, expira_em,
                max_ativacoes, assinatura_lic,
            ),
        )
        _checar_relogio(conn)  # registra o horário de referência
        conn.commit()

        usadas = _contar_ativacoes(conn, serial_norm)
    finally:
        conn.close()

    return {
        "sucesso": True,
        "tipo": tipo,
        "expira_em": expira_em,
        "max_ativacoes": max_ativacoes,
        "ativacoes_usadas": usadas,
        "ativacoes_restantes": (
            None if not max_ativacoes else max(max_ativacoes - usadas, 0)
        ),
        "mensagem": "Produto ativado com sucesso!",
    }


def status() -> dict:
    """Retorna o status atual da licença instalada."""
    conn = get_connection()
    try:
        _garantir_tabela(conn)
        row = conn.execute("SELECT * FROM licenca WHERE id = 1").fetchone()
        relogio_ok = _checar_relogio(conn)
        conn.commit()
    finally:
        conn.close()

    if not row:
        return {"ativado": False, "motivo": "nao_ativado"}

    dados = dict(row)

    # 1) Integridade: o registro da licença não pode ter sido editado no banco.
    if not seguranca.verificar_registro(
        (dados["serial"], dados["tipo"], dados["id_maquina"],
         dados["ativado_em"], dados.get("expira_em"), dados.get("max_ativacoes")),
        dados.get("assinatura"),
    ):
        return {
            "ativado": False,
            "motivo": "adulterada",
            "mensagem": "Os dados de licença foram adulterados. Reative o produto.",
        }

    # 2) A licença precisa ter sido ativada NESTA máquina.
    if dados["id_maquina"] != obter_id_maquina():
        return {
            "ativado": False,
            "motivo": "maquina_diferente",
            "mensagem": "Esta licença foi ativada em outro computador.",
        }

    # 3) Anti clock-rollback: relógio atrasado para burlar a validade.
    if not relogio_ok:
        return {
            "ativado": False,
            "motivo": "relogio_alterado",
            "mensagem": ("Detectamos uma alteração suspeita no relógio do "
                         "sistema. Ajuste a data/hora e reative o produto."),
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

    max_ativacoes = dados.get("max_ativacoes") or 0
    conn = get_connection()
    try:
        usadas = _contar_ativacoes(conn, dados["serial"])
    finally:
        conn.close()

    return {
        "ativado": True,
        "tipo": dados["tipo"],
        "ativado_em": dados["ativado_em"],
        "expira_em": expira_em,
        "dias_restantes": _dias_restantes(expira_em),
        "max_ativacoes": max_ativacoes,
        "ativacoes_usadas": usadas,
        "ativacoes_restantes": (
            None if not max_ativacoes else max(max_ativacoes - usadas, 0)
        ),
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


def desativar(limpar_historico: bool = False) -> None:
    """Remove a ativação local (uso administrativo/testes).

    Args:
        limpar_historico: se True, também apaga o histórico de ativações
            (zera o contador de máquinas). Por padrão o histórico é mantido,
            de modo que reativar na mesma máquina não consome nova ativação.
    """
    conn = get_connection()
    try:
        _garantir_tabela(conn)
        conn.execute("DELETE FROM licenca")
        if limpar_historico:
            conn.execute("DELETE FROM ativacoes")
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Consultas administrativas (painel de ativações)
# ---------------------------------------------------------------------------

def listar_ativacoes() -> list[dict]:
    """Lista todas as ativações registradas nesta instalação.

    Cada item traz o serial, o ID da máquina, quando foi ativado e um
    indicador de ser (ou não) a máquina atual.
    """
    atual = obter_id_maquina()
    conn = get_connection()
    try:
        _garantir_tabela(conn)
        rows = conn.execute(
            """
            SELECT id, serial, id_maquina, ativado_em, assinatura
            FROM ativacoes
            ORDER BY ativado_em DESC, id DESC
            """
        ).fetchall()
    finally:
        conn.close()

    return [
        {
            "id": r["id"],
            "serial": r["serial"],
            "id_maquina": r["id_maquina"],
            "ativado_em": r["ativado_em"],
            "maquina_atual": r["id_maquina"] == atual,
            # Registro íntegro? (assinatura confere). Falso = inserido/editado
            # manualmente no banco -> não conta como ativação legítima.
            "integra": seguranca.verificar_registro(
                (r["serial"], r["id_maquina"], r["ativado_em"]), r["assinatura"]
            ),
        }
        for r in rows
    ]


def resumo_seriais() -> list[dict]:
    """Agrupa as ativações por serial, com contagem de máquinas por serial."""
    conn = get_connection()
    try:
        _garantir_tabela(conn)
        rows = conn.execute(
            """
            SELECT serial,
                   MIN(ativado_em) AS primeira_ativacao,
                   MAX(ativado_em) AS ultima_ativacao
            FROM ativacoes
            GROUP BY serial
            ORDER BY ultima_ativacao DESC
            """
        ).fetchall()

        resultado = []
        for r in rows:
            info = _decodificar_serial(r["serial"])
            limite = info.get("max_ativacoes") if info else None
            tipo = info.get("tipo") if info else None
            # Conta apenas máquinas com registro ÍNTEGRO (assinatura válida).
            maquinas = _contar_ativacoes(conn, r["serial"])
            resultado.append({
                "serial": r["serial"],
                "tipo": tipo,
                "maquinas": maquinas,
                "max_ativacoes": limite,
                "restantes": (
                    None if not limite else max(limite - maquinas, 0)
                ),
                "primeira_ativacao": r["primeira_ativacao"],
                "ultima_ativacao": r["ultima_ativacao"],
            })
        return resultado
    finally:
        conn.close()


def revogar_ativacao(ativacao_id: int) -> bool:
    """Remove uma ativação específica (libera uma vaga daquele serial).

    Se a ativação removida for a desta máquina, a licença ativa local também
    é desativada, forçando nova ativação.
    """
    conn = get_connection()
    try:
        _garantir_tabela(conn)
        alvo = conn.execute(
            "SELECT serial, id_maquina FROM ativacoes WHERE id = ?",
            (ativacao_id,),
        ).fetchone()
        if not alvo:
            return False

        conn.execute("DELETE FROM ativacoes WHERE id = ?", (ativacao_id,))

        # Se removemos a ativação da máquina atual, desativa a licença local.
        if alvo["id_maquina"] == obter_id_maquina():
            conn.execute(
                "DELETE FROM licenca WHERE id = 1 AND serial = ?",
                (alvo["serial"],),
            )
        conn.commit()
        return True
    finally:
        conn.close()
