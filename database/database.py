"""
Camada de acesso ao banco de dados SQLite.

Responsável por:
- Descobrir o diretório persistente de dados do usuário (%APPDATA%),
  garantindo que o banco NUNCA fique dentro da pasta temporária
  criada pelo PyInstaller (sys._MEIPASS).
- Criar o schema inicial (se não existir).
- Controlar a versão do banco (DB_VERSION) e aplicar migrações simples.
- Fornecer uma conexão sqlite3 configurada (row_factory, foreign_keys).
"""

import os
import sys
import sqlite3
import logging
from contextlib import contextmanager

APP_NAME = "GeradorAssinaturas"
DB_VERSION = 3
DB_FILENAME = "assinaturas.db"

logger = logging.getLogger(APP_NAME)


def get_app_data_dir() -> str:
    """
    Retorna a pasta persistente de dados do usuário.

    Windows -> %APPDATA%\\GeradorAssinaturas
    Outros SOs (uso em desenvolvimento/testes) -> ~/.gerador_assinaturas

    Esta pasta é sempre externa à área temporária do PyInstaller
    (sys._MEIPASS), garantindo que os dados sobrevivam a atualizações
    do executável.
    """
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        data_dir = os.path.join(base, APP_NAME)
    else:
        # Fallback para desenvolvimento em Linux/Mac
        data_dir = os.path.join(os.path.expanduser("~"), f".{APP_NAME.lower()}")

    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(os.path.join(data_dir, "logs"), exist_ok=True)
    return data_dir


def get_db_path() -> str:
    return os.path.join(get_app_data_dir(), DB_FILENAME)


@contextmanager
def get_connection():
    """Fornece uma conexão sqlite3 com row_factory configurado."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS empresa (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    nome TEXT,
    nome_fantasia TEXT,
    cnpj TEXT,
    site TEXT,
    telefone TEXT,
    endereco TEXT,
    cidade TEXT,
    estado TEXT,
    cep TEXT,
    logo_url TEXT,
    logo_secundaria_url TEXT,
    cor_principal TEXT DEFAULT '#003366',
    cor_secundaria TEXT DEFAULT '#666666',
    cor_texto TEXT DEFAULT '#333333',
    cor_titulos TEXT DEFAULT '#003366',
    fonte TEXT DEFAULT 'Arial, Helvetica, sans-serif',
    criado_em TEXT DEFAULT (datetime('now')),
    atualizado_em TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS colaboradores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    sobrenome TEXT,
    cargo TEXT,
    departamento TEXT,
    setor TEXT,
    email TEXT,
    telefone TEXT,
    ramal TEXT,
    celular TEXT,
    whatsapp TEXT,
    endereco TEXT,
    cidade TEXT,
    estado TEXT,
    foto_url TEXT,
    ativo INTEGER DEFAULT 1,
    criado_em TEXT DEFAULT (datetime('now')),
    atualizado_em TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS modelos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    descricao TEXT,
    html_template TEXT NOT NULL,
    overrides_json TEXT,
    ativo INTEGER DEFAULT 1,
    padrao INTEGER DEFAULT 0,
    criado_em TEXT DEFAULT (datetime('now')),
    atualizado_em TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS redes_sociais (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    url TEXT,
    icone_url TEXT,
    ordem INTEGER DEFAULT 0,
    ativo INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS assinaturas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    colaborador_id INTEGER NOT NULL REFERENCES colaboradores(id) ON DELETE CASCADE,
    modelo_id INTEGER NOT NULL REFERENCES modelos(id) ON DELETE RESTRICT,
    overrides_json TEXT,
    html_gerado TEXT,
    ativo INTEGER DEFAULT 1,
    criado_em TEXT DEFAULT (datetime('now')),
    atualizado_em TEXT DEFAULT (datetime('now')),
    atualizada INTEGER NOT NULL DEFAULT 0,
    atualizada_em TEXT
);

CREATE TABLE IF NOT EXISTS configuracoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chave TEXT UNIQUE NOT NULL,
    valor TEXT,
    tipo TEXT DEFAULT 'texto',
    atualizado_em TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS schema_info (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    db_version INTEGER NOT NULL
);
"""


def init_db():
    """Cria as tabelas caso não existam e aplica migrações necessárias."""
    with get_connection() as conn:
        conn.executescript(SCHEMA)
        row = conn.execute("SELECT db_version FROM schema_info WHERE id = 1").fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO schema_info (id, db_version) VALUES (1, ?)", (DB_VERSION,)
            )
            logger.info("Banco de dados criado. DB_VERSION=%s", DB_VERSION)
        else:
            current = row["db_version"]
            if current < DB_VERSION:
                _run_migrations(conn, current, DB_VERSION)
                conn.execute(
                    "UPDATE schema_info SET db_version = ? WHERE id = 1", (DB_VERSION,)
                )
                logger.info("Banco migrado de v%s para v%s", current, DB_VERSION)


def _run_migrations(conn, from_version: int, to_version: int):
    """Aplica migrações incrementais sem perder as assinaturas existentes."""
    if from_version < 3 <= to_version:
        # Verifica as colunas independentemente do estado anterior do banco.
        # Isso também corrige bases já marcadas como versão 2, mas sem as colunas.
        colunas = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(assinaturas)").fetchall()
        }
        if "atualizada" not in colunas:
            conn.execute(
                "ALTER TABLE assinaturas ADD COLUMN atualizada INTEGER NOT NULL DEFAULT 0"
            )
        if "atualizada_em" not in colunas:
            conn.execute("ALTER TABLE assinaturas ADD COLUMN atualizada_em TEXT")
