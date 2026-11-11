"""Aplicação principal do sistema de biblioteca escolar."""
import os
import sys
from flask import Flask, send_from_directory
from database import init_db
from routes import api
from auth import auth
from ativacao import ativacao, registrar_bloqueio


def diretorio_recursos():
    """Diretório-base dos recursos estáticos (html/css/js).

    Quando empacotado pelo PyInstaller, os recursos ficam na pasta temporária
    apontada por ``sys._MEIPASS``. Em execução normal, usa a pasta do projeto.
    """
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


BASE_RECURSOS = diretorio_recursos()


def caminho_recurso(*partes):
    """Monta um caminho absoluto dentro da base de recursos."""
    return os.path.join(BASE_RECURSOS, *partes)


app = Flask(__name__, static_folder=caminho_recurso("html"), static_url_path="")
app.config["JSON_SORT_KEYS"] = False
app.secret_key = os.environ.get("SECRET_KEY", "toschibook-dev-secret-2026")

init_db()
app.register_blueprint(api)
app.register_blueprint(auth)
app.register_blueprint(ativacao)

# Exige ativação por serial antes de liberar o sistema.
registrar_bloqueio(app)


@app.after_request
def adicionar_cors(resposta):
    """Permite que o front aberto pelo Live Server acesse a API Flask."""
    resposta.headers["Access-Control-Allow-Origin"] = "*"
    resposta.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resposta.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    resposta.headers["Access-Control-Allow-Credentials"] = "true"
    return resposta


@app.get("/")
def index():
    return send_from_directory(caminho_recurso("html"), "index.html")


@app.get("/html/<path:nome_arquivo>")
def servir_html(nome_arquivo):
    """Serve as páginas HTML também pelo caminho /html/."""
    return send_from_directory(caminho_recurso("html"), nome_arquivo)


@app.get("/css/<path:nome_arquivo>")
def servir_css(nome_arquivo):
    """Serve os arquivos de estilo da pasta css/."""
    return send_from_directory(caminho_recurso("css"), nome_arquivo)


@app.get("/javascript/<path:nome_arquivo>")
def servir_javascript(nome_arquivo):
    """Serve os arquivos JavaScript da pasta javascript/."""
    return send_from_directory(caminho_recurso("javascript"), nome_arquivo)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
