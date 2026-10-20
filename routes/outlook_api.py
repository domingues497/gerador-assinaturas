"""API autenticada consumida pelo suplemento do Outlook.

A API aceita apenas access tokens emitidos pelo Microsoft Entra ID para o
aplicativo configurado no servidor. Nunca coloque uma chave compartilhada no
JavaScript do suplemento.
"""

import logging
import os
from functools import lru_cache

from flask import Blueprint, jsonify, request

from models import colaborador as colaborador_model
from models import assinatura as assinatura_model
from services.assinatura_service import gerar_html_assinatura

bp = Blueprint("outlook_api", __name__, url_prefix="/api/outlook")
logger = logging.getLogger("GeradorAssinaturas")


def _config_entra():
    tenant_id = os.environ.get("GERADOR_ENTRA_TENANT_ID", "").strip()
    client_id = os.environ.get("GERADOR_ENTRA_CLIENT_ID", "").strip()
    audience_raw = os.environ.get("GERADOR_ENTRA_AUDIENCE", "").strip()
    issuer = os.environ.get("GERADOR_ENTRA_ISSUER", "").strip()
    if not tenant_id or not client_id or not audience_raw:
        return None
    if not issuer:
        issuer = f"https://login.microsoftonline.com/{tenant_id}/v2.0"
    audiences = [item.strip() for item in audience_raw.split(",") if item.strip()]
    return {
        "tenant_id": tenant_id,
        "client_id": client_id,
        "audiences": audiences,
        "issuer": issuer,
        "jwks_url": f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys",
    }


@lru_cache(maxsize=8)
def _jwks_client(jwks_url: str):
    import jwt
    return jwt.PyJWKClient(jwks_url, cache_keys=True, lifespan=3600)


def _identidade_do_token(token: str):
    """Valida assinatura, emissor, audiência e tenant do access token SSO."""
    config = _config_entra()
    if not config:
        raise RuntimeError("Integração Microsoft Entra ID não configurada no servidor.")

    import jwt

    signing_key = _jwks_client(config["jwks_url"]).get_signing_key_from_jwt(token)
    claims = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        audience=config["audiences"],
        issuer=config["issuer"],
        options={"require": ["exp", "iat", "iss", "aud"]},
    )
    if claims.get("tid", "").lower() != config["tenant_id"].lower():
        raise jwt.InvalidTokenError("Tenant do token não corresponde ao configurado.")

    email = (claims.get("preferred_username") or claims.get("upn") or claims.get("email") or "").strip()
    if not email or "@" not in email:
        raise jwt.InvalidTokenError("O token não contém um endereço de e-mail utilizável.")
    return email.lower()


def _extrair_bearer():
    cabecalho = request.headers.get("Authorization", "")
    esquema, _, token = cabecalho.partition(" ")
    if esquema.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


@bp.get("/health")
def health():
    """Diagnóstico sem revelar dados de colaboradores ou configurações sensíveis."""
    config = _config_entra()
    return jsonify({
        "status": "ok" if config else "configuration_required",
        "authentication": "Microsoft Entra ID SSO",
        "entra_configured": bool(config),
    })


@bp.get("/signature")
def signature():
    token = _extrair_bearer()
    if not token:
        return jsonify({"error": "unauthorized", "message": "Token Microsoft 365 ausente."}), 401

    try:
        email = _identidade_do_token(token)
    except RuntimeError as exc:
        logger.warning("API Outlook chamada sem configuração Entra ID: %s", exc)
        return jsonify({"error": "server_not_configured", "message": "A integração Microsoft 365 ainda não foi configurada pela TI."}), 503
    except Exception as exc:
        logger.info("Token SSO do Outlook rejeitado: %s", type(exc).__name__)
        return jsonify({"error": "unauthorized", "message": "Não foi possível validar a identidade Microsoft 365."}), 401

    try:
        assinatura = assinatura_model.obter_assinatura_ativa_por_email(email)
        if not assinatura:
            return jsonify({
                "error": "signature_not_found",
                "message": "Não há assinatura ativa vinculada a este e-mail no Gerador de Assinaturas.",
            }), 404

        resultado = gerar_html_assinatura(
            assinatura["colaborador_id"],
            assinatura["modelo_id"],
            assinatura_model.overrides_da_assinatura(assinatura),
        )
        if resultado.get("erro") or not resultado.get("html_preview"):
            logger.error("Falha ao regenerar assinatura para colaborador_id=%s", assinatura["colaborador_id"])
            return jsonify({"error": "signature_generation_failed", "message": "Não foi possível gerar a assinatura atual."}), 500

        html = str(resultado["html_preview"])
        # Outlook Body.setSignatureAsync aceita no máximo 30.000 caracteres.
        if len(html) > 30000:
            return jsonify({
                "error": "signature_too_large",
                "message": "A assinatura ultrapassa o limite de 30.000 caracteres do Outlook. Reduza o HTML do modelo.",
            }), 422

        return jsonify({
            "email": email,
            "signatureId": assinatura["id"],
            "updatedAt": assinatura.get("atualizado_em"),
            "html": html,
        }), 200, {"Cache-Control": "no-store, private"}
    except Exception:
        logger.exception("Erro ao fornecer assinatura pela API Outlook")
        return jsonify({"error": "internal_error", "message": "Não foi possível obter a assinatura."}), 500
