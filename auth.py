"""Rotas de autenticação do sistema ToschiBook."""
from flask import Blueprint, jsonify, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_connection

auth = Blueprint("auth", __name__, url_prefix="/api/auth")


def _normalizar_resposta(texto: str) -> str:
    """Normaliza a resposta de segurança (sem caixa/espaços extras).

    Assim 'Rex', ' rex ' e 'REX' são equivalentes na recuperação.
    """
    return " ".join(str(texto or "").strip().lower().split())


@auth.post("/cadastro")
def cadastro():
    """Cria uma nova conta de usuário."""
    dados = request.get_json(silent=True) or {}

    campos = ["nome", "usuario", "email", "senha"]
    ausentes = [c for c in campos if not str(dados.get(c, "")).strip()]
    if ausentes:
        return jsonify({"erro": f"Campos obrigatórios: {', '.join(ausentes)}"}), 400

    nome = dados["nome"].strip()
    usuario = dados["usuario"].strip().lower()
    email = dados["email"].strip().lower()
    matricula = dados.get("matricula", "").strip()
    senha = dados["senha"]
    pergunta = str(dados.get("pergunta_seguranca", "")).strip()
    resposta = str(dados.get("resposta_seguranca", "")).strip()

    if len(senha) < 6:
        return jsonify({"erro": "A senha deve ter pelo menos 6 caracteres."}), 400

    # Pergunta/resposta de segurança são opcionais, mas vêm em par.
    if pergunta and not resposta:
        return jsonify({"erro": "Informe a resposta da pergunta de segurança."}), 400

    senha_hash = generate_password_hash(senha)
    resposta_hash = (generate_password_hash(_normalizar_resposta(resposta))
                     if pergunta and resposta else None)

    conn = get_connection()
    try:
        # Verifica se já existe conta com mesmo e-mail ou usuário
        existente = conn.execute(
            "SELECT id FROM contas WHERE email = ? OR usuario = ?",
            (email, usuario),
        ).fetchone()

        if existente:
            return jsonify({"erro": "E-mail ou usuário já cadastrado."}), 409

        cur = conn.execute(
            """
            INSERT INTO contas
                (nome, usuario, email, matricula, senha_hash,
                 pergunta_seguranca, resposta_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (nome, usuario, email, matricula, senha_hash,
             pergunta or None, resposta_hash),
        )
        conn.commit()
        conta_id = cur.lastrowid

        # Já loga o usuário após o cadastro
        session["conta_id"] = conta_id
        session["nome"] = nome
        session["usuario"] = usuario
        session["email"] = email

        return jsonify({
            "mensagem": "Conta criada com sucesso!",
            "conta": {
                "id": conta_id,
                "nome": nome,
                "usuario": usuario,
                "email": email,
            },
        }), 201

    except Exception:
        return jsonify({"erro": "Erro interno ao criar conta."}), 500
    finally:
        conn.close()


@auth.post("/login")
def login():
    """Autentica o usuário com e-mail/usuário e senha."""
    dados = request.get_json(silent=True) or {}
    identificador = str(dados.get("identificador", "")).strip().lower()
    senha = str(dados.get("senha", ""))

    if not identificador or not senha:
        return jsonify({"erro": "Informe seu e-mail/usuário e senha."}), 400

    conn = get_connection()
    try:
        # Busca por e-mail OU por nome de usuário
        conta = conn.execute(
            "SELECT * FROM contas WHERE email = ? OR usuario = ?",
            (identificador, identificador),
        ).fetchone()

        if not conta:
            return jsonify({"erro": "Credenciais inválidas."}), 401

        if not check_password_hash(conta["senha_hash"], senha):
            return jsonify({"erro": "Credenciais inválidas."}), 401

        # Salva na sessão
        session["conta_id"] = conta["id"]
        session["nome"] = conta["nome"]
        session["usuario"] = conta["usuario"]
        session["email"] = conta["email"]

        return jsonify({
            "mensagem": "Login realizado com sucesso!",
            "conta": {
                "id": conta["id"],
                "nome": conta["nome"],
                "usuario": conta["usuario"],
                "email": conta["email"],
            },
        })

    finally:
        conn.close()


@auth.get("/sessao")
def sessao():
    """Retorna os dados da sessão ativa ou 401 se não estiver logado."""
    conta_id = session.get("conta_id")
    if not conta_id:
        return jsonify({"erro": "Não autenticado."}), 401

    return jsonify({
        "conta": {
            "id": conta_id,
            "nome": session.get("nome"),
            "usuario": session.get("usuario"),
            "email": session.get("email"),
        }
    })


@auth.post("/logout")
def logout():
    """Encerra a sessão do usuário."""
    session.clear()
    return jsonify({"mensagem": "Sessão encerrada com sucesso."})


# ---------------------------------------------------------------------------
# Recuperação de senha (offline, por pergunta de segurança)
# ---------------------------------------------------------------------------

@auth.post("/recuperar/pergunta")
def recuperar_pergunta():
    """Dado o e-mail/usuário, retorna a pergunta de segurança da conta."""
    dados = request.get_json(silent=True) or {}
    identificador = str(dados.get("identificador", "")).strip().lower()
    if not identificador:
        return jsonify({"erro": "Informe seu e-mail ou usuário."}), 400

    conn = get_connection()
    try:
        conta = conn.execute(
            "SELECT pergunta_seguranca FROM contas WHERE email = ? OR usuario = ?",
            (identificador, identificador),
        ).fetchone()
    finally:
        conn.close()

    # Mensagem neutra para não revelar se a conta existe.
    if not conta or not conta["pergunta_seguranca"]:
        return jsonify({
            "erro": ("Não há recuperação por pergunta de segurança para esta "
                     "conta. Contate o administrador da biblioteca."),
        }), 404

    return jsonify({"pergunta": conta["pergunta_seguranca"]})


@auth.post("/recuperar/redefinir")
def recuperar_redefinir():
    """Valida a resposta de segurança e define uma nova senha."""
    dados = request.get_json(silent=True) or {}
    identificador = str(dados.get("identificador", "")).strip().lower()
    resposta = str(dados.get("resposta", ""))
    nova_senha = str(dados.get("nova_senha", ""))

    if not identificador or not resposta or not nova_senha:
        return jsonify({"erro": "Preencha todos os campos."}), 400

    if len(nova_senha) < 6:
        return jsonify({"erro": "A nova senha deve ter pelo menos 6 caracteres."}), 400

    conn = get_connection()
    try:
        conta = conn.execute(
            "SELECT id, resposta_hash FROM contas WHERE email = ? OR usuario = ?",
            (identificador, identificador),
        ).fetchone()

        if not conta or not conta["resposta_hash"]:
            return jsonify({"erro": "Não foi possível redefinir a senha."}), 404

        if not check_password_hash(conta["resposta_hash"],
                                   _normalizar_resposta(resposta)):
            return jsonify({"erro": "Resposta de segurança incorreta."}), 401

        conn.execute(
            "UPDATE contas SET senha_hash = ? WHERE id = ?",
            (generate_password_hash(nova_senha), conta["id"]),
        )
        conn.commit()
    finally:
        conn.close()

    return jsonify({"mensagem": "Senha redefinida com sucesso! Faça login."})
