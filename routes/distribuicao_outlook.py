"""Tela administrativa de diagnóstico e implantação do suplemento Outlook."""

import os
from flask import Blueprint, render_template

bp = Blueprint("distribuicao_outlook", __name__, url_prefix="/distribuicao-outlook")


@bp.route("/")
def index():
    tenant_id = os.environ.get("GERADOR_ENTRA_TENANT_ID", "").strip()
    client_id = os.environ.get("GERADOR_ENTRA_CLIENT_ID", "").strip()
    audience = os.environ.get("GERADOR_ENTRA_AUDIENCE", "").strip()
    issuer = os.environ.get("GERADOR_ENTRA_ISSUER", "").strip()
    return render_template(
        "distribuicao_outlook.html",
        entra_configurado=bool(tenant_id and client_id and audience),
        tenant_id=tenant_id,
        client_id=client_id,
        audience=audience,
        issuer=issuer or (f"https://login.microsoftonline.com/{tenant_id}/v2.0" if tenant_id else ""),
        api_url="/api/outlook/signature",
        manifest_template="outlook_addin/manifest.xml.template",
    )
