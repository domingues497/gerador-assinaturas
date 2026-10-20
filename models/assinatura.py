"""Acesso a dados da tabela assinaturas (assinaturas salvas)."""

import json
from database.database import get_connection


def listar_assinaturas() -> list:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT a.*, c.nome AS colaborador_nome, m.nome AS modelo_nome
            FROM assinaturas a
            JOIN colaboradores c ON c.id = a.colaborador_id
            JOIN modelos m ON m.id = a.modelo_id
            WHERE a.ativo = 1
            ORDER BY a.atualizado_em DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]


def obter_assinatura(assinatura_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM assinaturas WHERE id = ?", (assinatura_id,)
        ).fetchone()
        return dict(row) if row else None




def obter_assinatura_por_colaborador(colaborador_id: int) -> dict | None:
    """Retorna a assinatura ativa mais recente associada ao colaborador."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM assinaturas WHERE colaborador_id = ? AND ativo = 1 "
            "ORDER BY atualizado_em DESC, id DESC LIMIT 1",
            (colaborador_id,),
        ).fetchone()
        return dict(row) if row else None


def listar_assinaturas_por_colaborador(colaborador_id: int) -> list:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM assinaturas WHERE colaborador_id = ? AND ativo = 1 ORDER BY id DESC",
            (colaborador_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def criar_assinatura(nome: str, colaborador_id: int, modelo_id: int,
                      overrides: dict | None, html_gerado: str) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO assinaturas (nome, colaborador_id, modelo_id, overrides_json, html_gerado) "
            "VALUES (?, ?, ?, ?, ?)",
            (nome, colaborador_id, modelo_id, json.dumps(overrides or {}), html_gerado),
        )
        return cursor.lastrowid


def atualizar_assinatura(assinatura_id: int, nome: str, colaborador_id: int, modelo_id: int,
                          overrides: dict | None, html_gerado: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE assinaturas SET nome = ?, colaborador_id = ?, modelo_id = ?, "
            "overrides_json = ?, html_gerado = ?, atualizado_em = datetime('now'), "
            "atualizada = 0, atualizada_em = NULL WHERE id = ?",
            (nome, colaborador_id, modelo_id, json.dumps(overrides or {}), html_gerado, assinatura_id),
        )



def definir_status_atualizada(assinatura_id: int, atualizada: bool) -> bool:
    """Atualiza o status individual de uma assinatura salva."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE assinaturas
            SET atualizada = ?, atualizada_em = CASE
                WHEN ? = 1 THEN datetime('now')
                ELSE NULL
            END
            WHERE id = ? AND ativo = 1
            """,
            (1 if atualizada else 0, 1 if atualizada else 0, assinatura_id),
        )
        return cursor.rowcount > 0

def duplicar_assinatura(assinatura_id: int) -> int | None:
    original = obter_assinatura(assinatura_id)
    if not original:
        return None
    novo_nome = f"{original['nome']} 2"
    with get_connection() as conn:
        existentes = {
            r["nome"] for r in conn.execute(
                "SELECT nome FROM assinaturas WHERE nome LIKE ?",
                (f"{original['nome']}%",),
            ).fetchall()
        }
        contador = 2
        while novo_nome in existentes:
            contador += 1
            novo_nome = f"{original['nome']} {contador}"
        cursor = conn.execute(
            "INSERT INTO assinaturas (nome, colaborador_id, modelo_id, overrides_json, html_gerado) "
            "VALUES (?, ?, ?, ?, ?)",
            (novo_nome, original["colaborador_id"], original["modelo_id"],
             original["overrides_json"], original["html_gerado"]),
        )
        return cursor.lastrowid


def excluir_assinatura(assinatura_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM assinaturas WHERE id = ?", (assinatura_id,))


def obter_assinatura_ativa_por_email(email: str) -> dict | None:
    """Retorna a assinatura ativa mais recentemente atualizada para um e-mail."""
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT a.*, c.email AS colaborador_email, c.ativo AS colaborador_ativo
            FROM assinaturas a
            JOIN colaboradores c ON c.id = a.colaborador_id
            WHERE a.ativo = 1 AND c.ativo = 1
              AND lower(trim(c.email)) = lower(trim(?))
            ORDER BY a.atualizado_em DESC, a.id DESC
            LIMIT 1
            """,
            (email,),
        ).fetchone()
        return dict(row) if row else None


def overrides_da_assinatura(assinatura: dict) -> dict:
    """Decodifica os overrides salvos, com fallback seguro para JSON inválido."""
    try:
        valor = json.loads(assinatura.get("overrides_json") or "{}")
        return valor if isinstance(valor, dict) else {}
    except (TypeError, json.JSONDecodeError):
        return {}
