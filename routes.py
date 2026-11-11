"""Rotas da API do sistema de biblioteca escolar."""
import os
import uuid
from pathlib import Path
from flask import Blueprint, jsonify, request, send_from_directory
from database import get_connection, DIR_DADOS
from models import Emprestimo, Livro, Usuario

api = Blueprint("api", __name__, url_prefix="/api")

UPLOAD_DIR = DIR_DADOS / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

EXTENSOES_PERMITIDAS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def campos_obrigatorios(dados, campos):
    """Valida que os campos obrigatórios existem e não estão vazios."""
    ausentes = [c for c in campos if not str(dados.get(c, "")).strip()]
    if ausentes:
        return {"erro": f"Campos obrigatórios ausentes: {', '.join(ausentes)}"}
    return None


def salvar_capa(arquivo):
    """Salva o arquivo de capa e retorna o nome do arquivo."""
    if not arquivo or not arquivo.filename:
        return None

    ext = Path(arquivo.filename).suffix.lower()
    if ext not in EXTENSOES_PERMITIDAS:
        return None

    nome_arquivo = f"{uuid.uuid4().hex}{ext}"
    arquivo.save(str(UPLOAD_DIR / nome_arquivo))
    return nome_arquivo


# ---------- Upload de capas ----------


@api.get("/uploads/<path:nome_arquivo>")
def servir_upload(nome_arquivo):
    """Serve as capas de livros da pasta uploads/."""
    return send_from_directory(str(UPLOAD_DIR), nome_arquivo)


# ---------- Livros ----------


@api.get("/livros")
def listar_livros():
    termo = request.args.get("termo")
    return jsonify(Livro.listar(termo))


@api.post("/livros")
def criar_livro():
    # Aceita multipart (com capa) ou JSON
    if request.content_type and "multipart" in request.content_type:
        dados = {
            "titulo": request.form.get("titulo", "").strip(),
            "autor": request.form.get("autor", "").strip(),
            "ano": request.form.get("ano") or None,
            "categoria": request.form.get("categoria", "").strip(),
            "quantidade": request.form.get("quantidade", "1"),
        }

        if not dados["titulo"] or not dados["autor"]:
            return jsonify({"erro": "Campos obrigatórios ausentes: titulo, autor"}), 400

        if dados["ano"]:
            dados["ano"] = int(dados["ano"])
        dados["quantidade"] = int(dados["quantidade"]) if dados["quantidade"] else 1

        # Salva a capa se enviada
        capa = request.files.get("capa")
        dados["capa"] = salvar_capa(capa)

    else:
        dados = request.get_json(silent=True) or {}
        erro = campos_obrigatorios(dados, ["titulo", "autor"])
        if erro:
            return jsonify(erro), 400

    novo_id = Livro.criar(dados)
    return jsonify({"id": novo_id, "mensagem": "Livro cadastrado com sucesso"}), 201


@api.put("/livros/<int:livro_id>")
def atualizar_livro(livro_id):
    if not Livro.buscar(livro_id):
        return jsonify({"erro": "Livro não encontrado"}), 404

    if request.content_type and "multipart" in request.content_type:
        dados = {
            "titulo": request.form.get("titulo", "").strip(),
            "autor": request.form.get("autor", "").strip(),
            "ano": request.form.get("ano") or None,
            "categoria": request.form.get("categoria", "").strip(),
            "quantidade": request.form.get("quantidade", "1"),
        }

        if not dados["titulo"] or not dados["autor"]:
            return jsonify({"erro": "Campos obrigatórios ausentes: titulo, autor"}), 400

        if dados["ano"]:
            dados["ano"] = int(dados["ano"])
        dados["quantidade"] = int(dados["quantidade"]) if dados["quantidade"] else 1

        capa = request.files.get("capa")
        nome_capa = salvar_capa(capa)
        if nome_capa:
            dados["capa"] = nome_capa

    else:
        dados = request.get_json(silent=True) or {}
        erro = campos_obrigatorios(dados, ["titulo", "autor"])
        if erro:
            return jsonify(erro), 400

    Livro.atualizar(livro_id, dados)
    return jsonify({"mensagem": "Livro atualizado com sucesso"})


@api.delete("/livros/<int:livro_id>")
def excluir_livro(livro_id):
    if not Livro.excluir(livro_id):
        return jsonify({"erro": "Livro não encontrado"}), 404
    return jsonify({"mensagem": "Livro excluído com sucesso"})


# ---------- Usuários ----------


@api.get("/usuarios")
def listar_usuarios():
    termo = request.args.get("termo")
    return jsonify(Usuario.listar(termo))


@api.post("/usuarios")
def criar_usuario():
    dados = request.get_json(silent=True) or {}
    erro = campos_obrigatorios(dados, ["nome", "email", "matricula"])
    if erro:
        return jsonify(erro), 400
    try:
        novo_id = Usuario.criar(dados)
    except Exception:
        return jsonify({"erro": "E-mail ou matrícula já cadastrados"}), 409
    return jsonify({"id": novo_id, "mensagem": "Usuário cadastrado com sucesso"}), 201


@api.put("/usuarios/<int:usuario_id>")
def atualizar_usuario(usuario_id):
    if not Usuario.buscar(usuario_id):
        return jsonify({"erro": "Usuário não encontrado"}), 404
    dados = request.get_json(silent=True) or {}
    erro = campos_obrigatorios(dados, ["nome", "email", "matricula"])
    if erro:
        return jsonify(erro), 400
    try:
        Usuario.atualizar(usuario_id, dados)
    except Exception:
        return jsonify({"erro": "E-mail ou matrícula já cadastrados"}), 409
    return jsonify({"mensagem": "Usuário atualizado com sucesso"})


@api.delete("/usuarios/<int:usuario_id>")
def excluir_usuario(usuario_id):
    if not Usuario.excluir(usuario_id):
        return jsonify({"erro": "Usuário não encontrado"}), 404
    return jsonify({"mensagem": "Usuário excluído com sucesso"})


# ---------- Empréstimos ----------


@api.get("/emprestimos")
def listar_emprestimos():
    return jsonify(Emprestimo.listar_ativos())


@api.post("/emprestimos")
def criar_emprestimo():
    dados = request.get_json(silent=True) or {}
    erro = campos_obrigatorios(dados, ["livro_id", "usuario_id"])
    if erro:
        return jsonify(erro), 400
    if not Livro.buscar(dados["livro_id"]):
        return jsonify({"erro": "Livro não encontrado"}), 404
    if not Usuario.buscar(dados["usuario_id"]):
        return jsonify({"erro": "Usuário não encontrado"}), 404
    novo_id = Emprestimo.criar(dados["livro_id"], dados["usuario_id"])
    if not novo_id:
        return jsonify({"erro": "Nenhum exemplar disponível deste livro"}), 409
    return jsonify({"id": novo_id, "mensagem": "Empréstimo registrado com sucesso"}), 201


@api.post("/emprestimos/<int:emprestimo_id>/devolver")
def devolver_emprestimo(emprestimo_id):
    if not Emprestimo.devolver(emprestimo_id):
        return jsonify({"erro": "Empréstimo não encontrado ou já devolvido"}), 404
    return jsonify({"mensagem": "Livro devolvido com sucesso"})


# ---------- Estatísticas ----------


@api.get("/estatisticas")
def estatisticas():
    conn = get_connection()
    try:
        total_livros = conn.execute(
            "SELECT COALESCE(SUM(quantidade), 0) FROM livros"
        ).fetchone()[0]
        total_usuarios = conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
        emprestimos_ativos = conn.execute(
            "SELECT COUNT(*) FROM emprestimos WHERE status = 'ativo'"
        ).fetchone()[0]
    finally:
        conn.close()
    return jsonify(
        {
            "total_livros": total_livros,
            "total_usuarios": total_usuarios,
            "emprestimos_ativos": emprestimos_ativos,
        }
    )
