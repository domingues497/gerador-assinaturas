"""Dados iniciais (seed) criados apenas se o banco estiver vazio, e pequenas
migrações de conteúdo para bancos já existentes (sem sobrescrever
personalizações feitas pelo usuário)."""

from database.database import get_connection
from models import modelo as modelo_model
from services.html_service import MODELO_CORPORATIVO_PADRAO

# Trechos antigos (versão sem ícone do WhatsApp) que podem existir em
# modelos já salvos por usuários que geraram o banco antes desta correção.
_TRECHOS_ANTIGOS_WHATSAPP = [
    '<td style="padding-right: 8px;"><a href="{{ whatsapp_link }}" target="_blank">WhatsApp</a></td>',
    '<table cellpadding="0" cellspacing="0" border="0"><tr><td><a href="{{ whatsapp_link }}" target="_blank">WhatsApp</a></td></tr></table>',
]
_TRECHO_NOVO_WHATSAPP = (
    '<td style="padding-right: 8px;"><a href="{{ whatsapp_link }}" target="_blank">'
    '<img src="{{ whatsapp_icone_url }}" alt="WhatsApp" width="24" height="24" style="display:block;"></a></td>'
)


def seed_modelo_padrao():
    modelos = modelo_model.listar_modelos()
    if modelos:
        return
    modelo_model.criar_modelo(
        nome="Assinatura Corporativa",
        descricao="Modelo padrão com foto, cargo, contatos e redes sociais.",
        html_template=MODELO_CORPORATIVO_PADRAO,
        overrides={},
        padrao=True,
    )


def migrar_icone_whatsapp():
    """
    Corrige modelos salvos que ainda usam o texto "WhatsApp" em vez do ícone.
    Só altera o trecho específico do WhatsApp, preservando o restante do
    template (inclusive customizações feitas pelo usuário em outras partes).
    """
    with get_connection() as conn:
        rows = conn.execute("SELECT id, html_template FROM modelos").fetchall()
        for row in rows:
            template = row["html_template"] or ""
            atualizado = template
            for trecho_antigo in _TRECHOS_ANTIGOS_WHATSAPP:
                if trecho_antigo in atualizado:
                    if trecho_antigo.startswith("<table"):
                        # variante "somente whatsapp" (sem outras redes sociais)
                        atualizado = atualizado.replace(
                            trecho_antigo,
                            '<table cellpadding="0" cellspacing="0" border="0"><tr>' + _TRECHO_NOVO_WHATSAPP + "</tr></table>",
                        )
                    else:
                        atualizado = atualizado.replace(trecho_antigo, _TRECHO_NOVO_WHATSAPP)
            if atualizado != template:
                conn.execute(
                    "UPDATE modelos SET html_template = ?, atualizado_em = datetime('now') WHERE id = ?",
                    (atualizado, row["id"]),
                )
