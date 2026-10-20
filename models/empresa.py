"""Acesso a dados da tabela empresa (registro único, id=1)."""

from database.database import get_connection

CAMPOS = [
    "nome", "nome_fantasia", "cnpj", "site", "telefone", "endereco",
    "cidade", "estado", "cep", "logo_url", "logo_secundaria_url",
    "cor_principal", "cor_secundaria", "cor_texto", "cor_titulos", "fonte",
]


def get_empresa() -> dict:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM empresa WHERE id = 1").fetchone()
        return dict(row) if row else {}


def empresa_configurada() -> bool:
    empresa = get_empresa()
    return bool(empresa and empresa.get("nome"))


def salvar_empresa(dados: dict) -> None:
    """Insere (id=1) ou atualiza os dados da empresa (upsert)."""
    valores = {campo: dados.get(campo, "") for campo in CAMPOS}
    with get_connection() as conn:
        existe = conn.execute("SELECT 1 FROM empresa WHERE id = 1").fetchone()
        if existe:
            set_clause = ", ".join(f"{c} = :{c}" for c in CAMPOS)
            conn.execute(
                f"UPDATE empresa SET {set_clause}, atualizado_em = datetime('now') WHERE id = 1",
                valores,
            )
        else:
            colunas = ", ".join(CAMPOS)
            placeholders = ", ".join(f":{c}" for c in CAMPOS)
            conn.execute(
                f"INSERT INTO empresa (id, {colunas}) VALUES (1, {placeholders})",
                valores,
            )
