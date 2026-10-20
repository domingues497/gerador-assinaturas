"""
Orquestra a geração de uma assinatura: resolve o contexto (prioridades),
injeta as redes sociais ativas e renderiza o template do modelo.
"""

from models import colaborador as colaborador_model
from models import modelo as modelo_model
from models import redes_sociais as redes_model
from services import config_resolver
from services import html_service


def gerar_html_assinatura(colaborador_id: int, modelo_id: int, overrides: dict | None = None) -> dict:
    """
    Retorna dict com:
      - html_preview: HTML renderizado (para exibir em preview / copiar / exportar)
      - contexto: contexto final usado (útil para depuração)
      - erro: mensagem amigável em caso de falha (ou None)
    """
    colaborador = colaborador_model.obter_colaborador(colaborador_id)
    modelo = modelo_model.obter_modelo(modelo_id)

    if not colaborador:
        return {"html_preview": "", "contexto": {}, "erro": "Colaborador não encontrado."}
    if not modelo:
        return {"html_preview": "", "contexto": {}, "erro": "Modelo não encontrado."}

    try:
        contexto = config_resolver.resolver_contexto(colaborador, modelo, overrides)
        opcoes = (overrides or {}).get("opcoes", {})
        contexto = html_service.preparar_contexto_html(contexto, opcoes)
        contexto["redes_sociais"] = redes_model.listar_redes(apenas_ativas=True)

        # Banner (opcional, configurável por override de assinatura/modelo)
        contexto.setdefault("banner_ativo", False)
        contexto.setdefault("banner_url", "")
        contexto.setdefault("banner_link", "")
        contexto.setdefault("banner_alt", "")
        contexto.setdefault("banner_largura", 300)

        html_renderizado = html_service.renderizar_assinatura(modelo["html_template"], contexto)
        return {"html_preview": str(html_renderizado), "contexto": contexto, "erro": None}
    except Exception as exc:  # nunca expor traceback ao usuário (Requisito 48)
        import logging
        logging.getLogger("GeradorAssinaturas").exception("Erro ao gerar assinatura")
        return {
            "html_preview": "",
            "contexto": {},
            "erro": "Não foi possível gerar a assinatura. Verifique os dados informados e tente novamente.",
        }
