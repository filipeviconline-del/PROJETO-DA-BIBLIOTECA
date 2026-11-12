"""Rotas de ativação/licenciamento do ToschiBook.

Expõe uma API para:
  * consultar o status da licença (``GET /api/licenca/status``);
  * ativar o produto com um serial (``POST /api/licenca/ativar``);
  * obter o identificador da máquina (``GET /api/licenca/maquina``).

Também registra um ``before_request`` que BLOQUEIA o uso do sistema enquanto
o produto não estiver ativado, redirecionando o usuário para a tela de
ativação.
"""
from flask import Blueprint, jsonify, redirect, request, session

import licenca

ativacao = Blueprint("ativacao", __name__)

# Caminhos liberados mesmo sem ativação (tela/arquivos de ativação e a API dela).
ROTAS_LIVRES = {
    "/ativacao.html",
    "/html/ativacao.html",
    "/favicon.ico",
}
PREFIXOS_LIVRES = (
    "/api/licenca",
    "/css/",
    "/javascript/",
)


@ativacao.get("/api/licenca/status")
def licenca_status():
    """Retorna o estado atual da licença."""
    return jsonify(licenca.status())


@ativacao.get("/api/licenca/maquina")
def licenca_maquina():
    """Retorna o identificador desta máquina (para suporte/geração)."""
    return jsonify({"id_maquina": licenca.obter_id_maquina()})


@ativacao.post("/api/licenca/ativar")
def licenca_ativar():
    """Ativa o produto com o serial informado."""
    dados = request.get_json(silent=True) or {}
    serial = str(dados.get("serial", "")).strip()
    if not serial:
        return jsonify({"sucesso": False, "erro": "Informe o número de série."}), 400

    resultado = licenca.ativar(serial)
    if not resultado.get("sucesso"):
        return jsonify(resultado), 400
    return jsonify(resultado)


@ativacao.post("/api/licenca/diagnosticar")
def licenca_diagnosticar():
    """Analisa um serial/código e explica por que não ativa (sem ativar)."""
    dados = request.get_json(silent=True) or {}
    serial = str(dados.get("serial", "")).strip()
    return jsonify(licenca.diagnosticar(serial))


# ---------- Painel administrativo de ativações ----------

def _exige_login():
    """Retorna uma resposta 401 se não houver sessão de usuário logada."""
    if not session.get("conta_id"):
        return jsonify({"erro": "Faça login para acessar o painel administrativo."}), 401
    return None


@ativacao.get("/api/licenca/ativacoes")
def licenca_ativacoes():
    """Lista as ativações registradas e um resumo por serial (requer login)."""
    bloqueio = _exige_login()
    if bloqueio:
        return bloqueio

    return jsonify({
        "licenca": licenca.status(),
        "id_maquina": licenca.obter_id_maquina(),
        "resumo_seriais": licenca.resumo_seriais(),
        "ativacoes": licenca.listar_ativacoes(),
    })


@ativacao.delete("/api/licenca/ativacoes/<int:ativacao_id>")
def licenca_revogar(ativacao_id):
    """Revoga uma ativação específica, liberando a vaga (requer login)."""
    bloqueio = _exige_login()
    if bloqueio:
        return bloqueio

    if not licenca.revogar_ativacao(ativacao_id):
        return jsonify({"erro": "Ativação não encontrada."}), 404
    return jsonify({"mensagem": "Ativação revogada com sucesso."})


def registrar_bloqueio(app):
    """Instala o middleware que exige ativação para usar o sistema."""

    @app.before_request
    def exigir_ativacao():
        caminho = request.path

        # Libera requisições de pré-voo CORS.
        if request.method == "OPTIONS":
            return None

        if caminho in ROTAS_LIVRES:
            return None
        if any(caminho.startswith(p) for p in PREFIXOS_LIVRES):
            return None

        if licenca.esta_ativado():
            return None

        # Não ativado: APIs recebem 403; páginas são redirecionadas.
        if caminho.startswith("/api/"):
            estado = licenca.status()
            return jsonify({
                "erro": "Produto não ativado.",
                "licenca": estado,
            }), 403

        return redirect("/html/ativacao.html")
