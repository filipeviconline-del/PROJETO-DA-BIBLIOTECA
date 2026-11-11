"""Conexão com o banco de dados SQLite do sistema de biblioteca escolar."""
import sqlite3
import sys
from pathlib import Path


def _diretorio_dados() -> Path:
    """Diretório gravável para o banco e uploads.

    Quando empacotado (PyInstaller), usa a pasta do executável — que é
    gravável — em vez do bundle temporário read-only. Em execução normal,
    usa a pasta do projeto.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


DIR_DADOS = _diretorio_dados()
DB_PATH = DIR_DADOS / "biblioteca.db"


def get_connection():
    """Retorna uma conexão com o banco, habilitando chaves estrangeiras."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Cria as tabelas do banco caso ainda não existam."""
    conn = get_connection()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS livros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                autor TEXT NOT NULL,
                ano INTEGER,
                categoria TEXT,
                quantidade INTEGER DEFAULT 1,
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                matricula TEXT UNIQUE NOT NULL,
                turma TEXT,
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS emprestimos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                livro_id INTEGER NOT NULL,
                usuario_id INTEGER NOT NULL,
                data_emprestimo TEXT DEFAULT CURRENT_TIMESTAMP,
                data_devolucao TEXT,
                status TEXT DEFAULT 'ativo',
                FOREIGN KEY (livro_id) REFERENCES livros (id) ON DELETE CASCADE,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS contas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                usuario TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                matricula TEXT,
                senha_hash TEXT NOT NULL,
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # Adiciona coluna capa se não existir (migração segura)
        try:
            conn.execute("ALTER TABLE livros ADD COLUMN capa TEXT")
        except Exception:
            pass  # Coluna já existe

        conn.commit()
    finally:
        conn.close()
