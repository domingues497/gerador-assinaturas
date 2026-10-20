"""
Resolve a configuração final de uma assinatura aplicando a regra de
prioridade do Requisito 54:

    Configuração específica da assinatura
            > Configuração do modelo
            > Configuração do colaborador
            > Configuração da empresa
            > Configuração padrão do sistema

O resultado é um único dicionário "achatado" com todos os campos que os
templates Jinja das assinaturas podem usar.
"""

import json
from models import empresa as empresa_model
from models import config as config_model


def _parse_overrides(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}


def resolver_contexto(colaborador: dict, modelo: dict, overrides_assinatura: dict | None = None) -> dict:
    """
    Monta o dicionário final de variáveis para renderizar o template Jinja
    da assinatura, respeitando a prioridade especificada.
    """
    cfg_sistema = config_model.get_all_config()
    dados_empresa = empresa_model.get_empresa()
    overrides_modelo = _parse_overrides(modelo.get("overrides_json") if modelo else None)
    overrides_assinatura = overrides_assinatura or {}

    contexto = {}

    # 5. Configuração padrão do sistema (base)
    contexto["cor_principal"] = cfg_sistema.get("cor_padrao") or "#003366"
    contexto["fonte"] = cfg_sistema.get("fonte_padrao") or "Arial, Helvetica, sans-serif"
    contexto["tamanho_fonte"] = cfg_sistema.get("tamanho_padrao") or "14px"
    contexto["logo_url"] = cfg_sistema.get("logo_padrao_url") or ""
    contexto["whatsapp_icone_url"] = (
        cfg_sistema.get("whatsapp_icone_url") or "https://cdn.simpleicons.org/whatsapp/25D366"
    )

    # 4. Configuração da empresa
    contexto.update({
        "empresa": dados_empresa.get("nome") or "",
        "empresa_fantasia": dados_empresa.get("nome_fantasia") or "",
        "site": dados_empresa.get("site") or "",
        "empresa_telefone": dados_empresa.get("telefone") or "",
        "empresa_endereco": dados_empresa.get("endereco") or "",
        "empresa_cidade": dados_empresa.get("cidade") or "",
        "empresa_estado": dados_empresa.get("estado") or "",
    })
    if dados_empresa.get("logo_url"):
        contexto["logo_url"] = dados_empresa["logo_url"]
    if dados_empresa.get("logo_secundaria_url"):
        contexto["logo_secundaria_url"] = dados_empresa["logo_secundaria_url"]
    for campo, chave_ctx in [
        ("cor_principal", "cor_principal"), ("cor_secundaria", "cor_secundaria"),
        ("cor_texto", "cor_texto"), ("cor_titulos", "cor_titulos"), ("fonte", "fonte"),
    ]:
        if dados_empresa.get(campo):
            contexto[chave_ctx] = dados_empresa[campo]

    # 3. Configuração do colaborador (dados pessoais, sempre do colaborador)
    colaborador = colaborador or {}
    contexto.update({
        "nome": " ".join(filter(None, [colaborador.get("nome"), colaborador.get("sobrenome")])),
        "cargo": colaborador.get("cargo") or "",
        "departamento": colaborador.get("departamento") or "",
        "setor": colaborador.get("setor") or "",
        "email": colaborador.get("email") or "",
        "telefone": colaborador.get("telefone") or "",
        "ramal": colaborador.get("ramal") or "",
        "celular": colaborador.get("celular") or "",
        "whatsapp": colaborador.get("whatsapp") or "",
        "endereco": colaborador.get("endereco") or contexto.get("empresa_endereco", ""),
        "cidade": colaborador.get("cidade") or contexto.get("empresa_cidade", ""),
        "estado": colaborador.get("estado") or contexto.get("empresa_estado", ""),
        "foto_url": colaborador.get("foto_url") or "",
    })

    # 2. Configuração do modelo (pode sobrescrever identidade visual)
    contexto.update(overrides_modelo)

    # 1. Configuração específica da assinatura (maior prioridade)
    contexto.update(overrides_assinatura)

    return contexto
