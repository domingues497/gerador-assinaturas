"""Acesso a dados da tabela modelos (modelos/layouts de assinatura)."""

import json
from database.database import get_connection


def listar_modelos(apenas_ativos: bool = False) -> list:
    with get_connection() as conn:
        query = "SELECT * FROM modelos"
        if apenas_ativos:
            query += " WHERE ativo = 1"
        query += " ORDER BY nome"
        return [dict(r) for r in conn.execute(query).fetchall()]


def obter_modelo(modelo_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM modelos WHERE id = ?", (modelo_id,)).fetchone()
        return dict(row) if row else None


def obter_modelo_padrao() -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM modelos WHERE padrao = 1 AND ativo = 1 LIMIT 1"
        ).fetchone()
        if row:
            return dict(row)
        row = conn.execute("SELECT * FROM modelos WHERE ativo = 1 LIMIT 1").fetchone()
        return dict(row) if row else None


def criar_modelo(nome: str, descricao: str, html_template: str,
                  overrides: dict | None = None, padrao: bool = False) -> int:
    with get_connection() as conn:
        if padrao:
            conn.execute("UPDATE modelos SET padrao = 0")
        cursor = conn.execute(
            "INSERT INTO modelos (nome, descricao, html_template, overrides_json, padrao) "
            "VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, html_template, json.dumps(overrides or {}), 1 if padrao else 0),
        )
        return cursor.lastrowid


def atualizar_modelo(modelo_id: int, nome: str, descricao: str, html_template: str,
                      overrides: dict | None = None, padrao: bool = False,
                      ativo: bool = True) -> None:
    with get_connection() as conn:
        if padrao:
            conn.execute("UPDATE modelos SET padrao = 0")
        conn.execute(
            "UPDATE modelos SET nome = ?, descricao = ?, html_template = ?, "
            "overrides_json = ?, padrao = ?, ativo = ?, atualizado_em = datetime('now') "
            "WHERE id = ?",
            (nome, descricao, html_template, json.dumps(overrides or {}),
             1 if padrao else 0, 1 if ativo else 0, modelo_id),
        )


def excluir_modelo(modelo_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM modelos WHERE id = ?", (modelo_id,))
