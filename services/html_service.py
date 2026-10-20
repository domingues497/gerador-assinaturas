"""
Geração do HTML final da assinatura.

Regras (Requisitos 46, 58, 59):
- Layout baseado em <table> (compatibilidade Outlook / Novo Outlook).
- CSS 100% inline (sem <style>, sem classes Bootstrap).
- Sem Flexbox, CSS Grid ou JavaScript no HTML exportado.
- Imagens sempre via URL HTTPS externa (nunca Base64, nunca caminho local).
- Elementos condicionais: campos vazios simplesmente não são renderizados.
- Todo texto vindo do usuário é escapado (Jinja autoescape) para evitar
  HTML/JS arbitrário dentro da assinatura.
"""

import re
from markupsafe import Markup, escape
from jinja2 import Environment, BaseLoader, select_autoescape

_env = Environment(
    loader=BaseLoader(),
    autoescape=select_autoescape(["html"]),
)


def _telefone_para_tel_link(telefone: str) -> str:
    """Converte um telefone formatado em um valor utilizável em tel:+55..."""
    digitos = re.sub(r"\D", "", telefone or "")
    if not digitos:
        return ""
    if not digitos.startswith("55") and len(digitos) <= 11:
        digitos = "55" + digitos
    return f"+{digitos}"


def _telefone_para_whatsapp(numero: str) -> str:
    digitos = re.sub(r"\D", "", numero or "")
    if not digitos:
        return ""
    if not digitos.startswith("55") and len(digitos) <= 11:
        digitos = "55" + digitos
    return digitos


def preparar_contexto_html(contexto: dict, opcoes: dict | None = None) -> dict:
    """
    Enriquece o contexto resolvido (config_resolver) com valores derivados
    prontos para uso direto no template: links mailto/tel/whatsapp/maps.
    'opcoes' controla toggles como telefone_clicavel e endereco_clicavel.
    """
    opcoes = opcoes or {}
    ctx = dict(contexto)

    ctx["email_link"] = f"mailto:{ctx.get('email')}" if ctx.get("email") else ""

    if ctx.get("telefone") and opcoes.get("telefone_clicavel", True):
        ctx["telefone_link"] = f"tel:{_telefone_para_tel_link(ctx['telefone'])}"
    else:
        ctx["telefone_link"] = ""

    if ctx.get("whatsapp"):
        ctx["whatsapp_link"] = f"https://wa.me/{_telefone_para_whatsapp(ctx['whatsapp'])}"
    else:
        ctx["whatsapp_link"] = ""

    endereco_completo = ", ".join(filter(None, [
        ctx.get("endereco"), ctx.get("cidade"), ctx.get("estado")
    ]))
    ctx["endereco_completo"] = endereco_completo
    if endereco_completo and opcoes.get("endereco_clicavel", False):
        ctx["endereco_link"] = "https://maps.google.com/?q=" + endereco_completo.replace(" ", "+")
    else:
        ctx["endereco_link"] = ""

    return ctx


def renderizar_assinatura(html_template: str, contexto: dict) -> Markup:
    """Renderiza o template Jinja do modelo com o contexto resolvido."""
    template = _env.from_string(html_template)
    return template.render(**contexto)


def html_para_exportacao(html_renderizado: str) -> str:
    """
    Monta o arquivo final .html a ser exportado/copiado: um documento HTML
    mínimo contendo apenas a assinatura (sem Bootstrap, sem <script>).
    """
    return (
        "<!DOCTYPE html>\n"
        '<html lang="pt-BR"><head><meta charset="UTF-8">'
        "<title>Assinatura de E-mail</title></head><body>\n"
        f"{html_renderizado}\n"
        "</body></html>\n"
    )


# ---------------------------------------------------------------------------
# Modelo padrão semeado no primeiro acesso (Requisito 18/19): 100% baseado
# em tabelas, CSS inline, variáveis Jinja, nenhuma informação fixa.
# ---------------------------------------------------------------------------
MODELO_CORPORATIVO_PADRAO = """
<table cellpadding="0" cellspacing="0" border="0" style="font-family: {{ fonte }}; font-size: {{ tamanho_fonte }}; color: {{ cor_texto or '#333333' }};">
  <tr>
    {% if foto_url %}
    <td style="padding-right: 16px; vertical-align: top;">
      {% if logo_url %}<a href="{{ site }}" target="_blank" style="text-decoration:none;">{% endif %}
      <img src="{{ foto_url }}" alt="{{ nome }}" width="80" height="80" style="border-radius: 50%; display:block;">
      {% if logo_url %}</a>{% endif %}
    </td>
    {% endif %}
    <td style="border-left: 3px solid {{ cor_principal }}; padding-left: 16px; vertical-align: top;">
      <table cellpadding="0" cellspacing="0" border="0">
        <tr><td style="font-size: 16px; font-weight: bold; color: {{ cor_titulos or cor_principal }}; padding-bottom: 2px;">{{ nome }}</td></tr>
        {% if cargo %}<tr><td style="color: {{ cor_secundaria or '#666666' }}; padding-bottom: 6px;">{{ cargo }}{% if departamento %} &middot; {{ departamento }}{% endif %}</td></tr>{% endif %}
        {% if empresa %}<tr><td style="font-weight:bold; padding-bottom: 8px;">{{ empresa }}</td></tr>{% endif %}
        {% if email %}<tr><td style="padding-bottom: 2px;"><a href="{{ email_link }}" style="color: {{ cor_texto or '#333333' }}; text-decoration:none;">{{ email }}</a></td></tr>{% endif %}
        {% if telefone %}<tr><td style="padding-bottom: 2px;">{% if telefone_link %}<a href="{{ telefone_link }}" style="color: {{ cor_texto or '#333333' }}; text-decoration:none;">{{ telefone }}</a>{% else %}{{ telefone }}{% endif %}{% if ramal %} - Ramal {{ ramal }}{% endif %}</td></tr>{% endif %}
        {% if celular %}<tr><td style="padding-bottom: 2px;">{{ celular }}</td></tr>{% endif %}
        {% if site %}<tr><td style="padding-bottom: 8px;"><a href="{{ site }}" style="color: {{ cor_principal }}; text-decoration:none;">{{ site }}</a></td></tr>{% endif %}
      </table>
      {% if redes_sociais or whatsapp_link %}
      <table cellpadding="0" cellspacing="0" border="0"><tr>
        {% for rede in redes_sociais %}
        <td style="padding-right: 8px;"><a href="{{ rede.url }}" target="_blank"><img src="{{ rede.icone_url }}" alt="{{ rede.nome }}" width="24" height="24" style="display:block;"></a></td>
        {% endfor %}
        {% if whatsapp_link %}<td style="padding-right: 8px;"><a href="{{ whatsapp_link }}" target="_blank"><img src="{{ whatsapp_icone_url }}" alt="WhatsApp" width="24" height="24" style="display:block;"></a></td>{% endif %}
      </table>
      {% endif %}
    </td>
  </tr>
  {% if banner_ativo and banner_url %}
  <tr><td colspan="2" style="padding-top: 12px;">
    {% if banner_link %}<a href="{{ banner_link }}" target="_blank">{% endif %}
    <img src="{{ banner_url }}" alt="{{ banner_alt or 'Banner' }}" width="{{ banner_largura or 300 }}" style="display:block; border:0;">
    {% if banner_link %}</a>{% endif %}
  </td></tr>
  {% endif %}
</table>
""".strip()
