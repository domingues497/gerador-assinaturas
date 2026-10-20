"""Acesso a dados da tabela configuracoes (chave/valor)."""

from database.database import get_connection

DEFAULTS = {
    "modelo_padrao_id": "",
    "logo_padrao_url": "",
    "cor_padrao": "#003366",
    "fonte_padrao": "Arial, Helvetica, sans-serif",
    "tamanho_padrao": "14px",
    "whatsapp_icone_url": "https://cdn.simpleicons.org/whatsapp/25D366",
    "primeiro_acesso_concluido": "0",
}


def get_config(chave: str, padrao: str = "") -> str:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT valor FROM configuracoes WHERE chave = ?", (chave,)
        ).fetchone()
        return row["valor"] if row else padrao


def get_all_config() -> dict:
    with get_connection() as conn:
        rows = conn.execute("SELECT chave, valor FROM configuracoes").fetchall()
        cfg = dict(DEFAULTS)
        cfg.update({r["chave"]: r["valor"] for r in rows})
        return cfg


def set_config(chave: str, valor: str, tipo: str = "texto") -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO configuracoes (chave, valor, tipo, atualizado_em)
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT(chave) DO UPDATE SET
                valor = excluded.valor,
                tipo = excluded.tipo,
                atualizado_em = datetime('now')
            """,
            (chave, valor, tipo),
        )


def set_many(dados: dict) -> None:
    for chave, valor in dados.items():
        set_config(chave, str(valor))
