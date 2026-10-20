"""Acesso a dados da tabela redes_sociais."""

from database.database import get_connection


def listar_redes(apenas_ativas: bool = False) -> list:
    with get_connection() as conn:
        query = "SELECT * FROM redes_sociais"
        if apenas_ativas:
            query += " WHERE ativo = 1"
        query += " ORDER BY ordem, nome"
        return [dict(r) for r in conn.execute(query).fetchall()]


def obter_rede(rede_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM redes_sociais WHERE id = ?", (rede_id,)).fetchone()
        return dict(row) if row else None


def criar_rede(nome: str, url: str, icone_url: str, ordem: int = 0, ativo: bool = True) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO redes_sociais (nome, url, icone_url, ordem, ativo) "
            "VALUES (?, ?, ?, ?, ?)",
            (nome, url, icone_url, ordem, 1 if ativo else 0),
        )
        return cursor.lastrowid


def atualizar_rede(rede_id: int, nome: str, url: str, icone_url: str,
                    ordem: int = 0, ativo: bool = True) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE redes_sociais SET nome = ?, url = ?, icone_url = ?, ordem = ?, ativo = ? "
            "WHERE id = ?",
            (nome, url, icone_url, ordem, 1 if ativo else 0, rede_id),
        )


def excluir_rede(rede_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM redes_sociais WHERE id = ?", (rede_id,))
