"""Validação e verificação de URLs de imagens (Requisitos 34, 35, 36)."""

import urllib.request
import urllib.error
import ssl


def url_e_https(url: str) -> bool:
    return bool(url) and url.strip().lower().startswith("https://")


def validar_url_imagem(url: str) -> dict:
    """
    Valida formato da URL. Retorna dict com 'valida' e 'aviso'.
    Não bloqueia http://, apenas alerta (o usuário decide).
    """
    if not url:
        return {"valida": True, "aviso": None}
    url = url.strip()
    if url.lower().startswith("file://") or (len(url) > 1 and url[1] == ":"):
        return {"valida": False, "aviso": "Não utilize caminhos locais (C:\\...) ou file://. "
                                            "A imagem deve estar hospedada em um servidor HTTPS."}
    if not url.lower().startswith(("http://", "https://")):
        return {"valida": False, "aviso": "Informe uma URL completa iniciando com https://"}
    if not url_e_https(url):
        return {"valida": True, "aviso": "A imagem deve estar disponível através de HTTPS "
                                          "para garantir exibição correta no Outlook."}
    return {"valida": True, "aviso": None}


def testar_imagem_acessivel(url: str, timeout: int = 5) -> dict:
    """Faz um HEAD/GET rápido para checar se a imagem responde e tem Content-Type de imagem."""
    if not url:
        return {"acessivel": False, "mensagem": "Nenhuma URL informada."}
    validacao = validar_url_imagem(url)
    if not validacao["valida"]:
        return {"acessivel": False, "mensagem": validacao["aviso"]}
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "GeradorAssinaturas/1.0"})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            content_type = resp.headers.get("Content-Type", "")
            if resp.status == 200 and content_type.startswith("image/"):
                return {"acessivel": True, "mensagem": "Imagem acessível."}
            if resp.status == 200:
                return {"acessivel": True, "mensagem": "URL acessível, mas o Content-Type "
                                                          f"retornado ('{content_type}') não parece ser imagem."}
            return {"acessivel": False, "mensagem": f"Servidor retornou status {resp.status}."}
    except urllib.error.URLError as exc:
        return {"acessivel": False, "mensagem": f"Não foi possível acessar a imagem ({exc.reason})."}
    except Exception as exc:  # pragma: no cover
        return {"acessivel": False, "mensagem": f"Não foi possível acessar a imagem ({exc})."}
