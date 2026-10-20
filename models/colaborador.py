"""Acesso a dados da tabela colaboradores."""

from database.database import get_connection

CAMPOS = [
    "nome", "sobrenome", "cargo", "departamento", "setor", "email",
    "telefone", "ramal", "celular", "whatsapp", "endereco", "cidade",
    "estado", "foto_url", "ativo",
]


def listar_colaboradores(apenas_ativos: bool = False) -> list:
    with get_connection() as conn:
        query = "SELECT * FROM colaboradores"
        if apenas_ativos:
            query += " WHERE ativo = 1"
        query += " ORDER BY nome"
        return [dict(r) for r in conn.execute(query).fetchall()]


def obter_colaborador(colaborador_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM colaboradores WHERE id = ?", (colaborador_id,)
        ).fetchone()
        return dict(row) if row else None


def criar_colaborador(dados: dict) -> int:
    valores = {campo: dados.get(campo, "") for campo in CAMPOS}
    valores["ativo"] = 1 if dados.get("ativo", True) else 0
    with get_connection() as conn:
        colunas = ", ".join(CAMPOS)
        placeholders = ", ".join(f":{c}" for c in CAMPOS)
        cursor = conn.execute(
            f"INSERT INTO colaboradores ({colunas}) VALUES ({placeholders})", valores
        )
        return cursor.lastrowid


def atualizar_colaborador(colaborador_id: int, dados: dict) -> None:
    valores = {campo: dados.get(campo, "") for campo in CAMPOS}
    valores["ativo"] = 1 if dados.get("ativo", True) else 0
    valores["id"] = colaborador_id
    with get_connection() as conn:
        set_clause = ", ".join(f"{c} = :{c}" for c in CAMPOS)
        conn.execute(
            f"UPDATE colaboradores SET {set_clause}, atualizado_em = datetime('now') "
            "WHERE id = :id",
            valores,
        )


def excluir_colaborador(colaborador_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM colaboradores WHERE id = ?", (colaborador_id,))
