"""
Serviço de upload de arquivos: banners, fotos, etc.

Regras:
- Apenas imagens (jpg, jpeg, png, gif, webp)
- Tamanho máximo controlado por MAX_CONTENT_LENGTH no app.py
- Arquivos salvos em static/uploads/banners/ (para banners)
- Nomes de arquivo são randomizados para evitar conflitos
"""

import os
import uuid
import base64
from pathlib import Path

from flask import current_app


EXTENSOES_PERMITIDAS = {"jpg", "jpeg", "png", "gif", "webp"}
TIPOS_MIME_PERMITIDOS = {
    "image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp",
}


def _pasta_uploads_banners() -> Path:
    base = Path(current_app.static_folder) if current_app else Path(__file__).resolve().parent.parent / "static"
    pasta = base / "uploads" / "banners"
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def _pasta_uploads_logos() -> Path:
    base = Path(current_app.static_folder) if current_app else Path(__file__).resolve().parent.parent / "static"
    pasta = base / "uploads" / "logos"
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def extensao_permitida(nome_arquivo: str) -> bool:
    if "." not in nome_arquivo:
        return False
    ext = nome_arquivo.rsplit(".", 1)[1].lower()
    return ext in EXTENSOES_PERMITIDAS


def _arquivo_eh_imagem_valida(caminho: Path, ext: str) -> bool:
    """
    Validação simples baseada em magic bytes (assinatura dos primeiros bytes).
    É uma segurança extra para evitar que arquivos não-imagem sejam aceitos
    mesmo tendo extensão .jpg/.png etc.
    """
    try:
        with open(caminho, "rb") as f:
            head = f.read(16)
        if len(head) < 4:
            return False
        if ext in ("jpg", "jpeg"):
            return head[:3] == b"\xff\xd8\xff"
        if ext == "png":
            return head[:8] == b"\x89PNG\r\n\x1a\n"
        if ext == "gif":
            return head[:6] in (b"GIF87a", b"GIF89a")
        if ext == "webp":
            return head[:4] == b"RIFF" and head[8:12] == b"WEBP"
    except OSError:
        return False
    return False


def _salvar_upload(arquivo, pasta: Path, url_prefix: str) -> dict:
    if not arquivo or not arquivo.filename:
        return {"ok": False, "url_local": "", "caminho_absoluto": "", "erro": "Nenhum arquivo enviado."}

    if not extensao_permitida(arquivo.filename):
        return {
            "ok": False, "url_local": "", "caminho_absoluto": "",
            "erro": f"Tipo de arquivo não permitido. Use: {', '.join(sorted(EXTENSOES_PERMITIDAS))}.",
        }

    ext = arquivo.filename.rsplit(".", 1)[1].lower()
    nome_unico = f"{uuid.uuid4().hex}.{ext}"

    caminho_absoluto = pasta / nome_unico
    arquivo.save(caminho_absoluto)

    if not _arquivo_eh_imagem_valida(caminho_absoluto, ext):
        caminho_absoluto.unlink(missing_ok=True)
        return {
            "ok": False, "url_local": "", "caminho_absoluto": "",
            "erro": "Arquivo enviado não parece ser uma imagem válida.",
        }

    url_local = f"{url_prefix}/{nome_unico}"
    return {"ok": True, "url_local": url_local, "caminho_absoluto": str(caminho_absoluto), "erro": None}


def salvar_banner_upload(arquivo) -> dict:
    """
    Salva um arquivo de banner enviado via formulário.
    Retorna dict com {ok, url_local, caminho_absoluto, erro}.
    url_local é algo como '/static/uploads/banners/<uuid>.ext' e pode ser
    usada tanto no preview quanto no HTML salvo (esse caminho é depois
    convertido para Base64 na hora de exportar/copiar).
    """
    return _salvar_upload(arquivo, _pasta_uploads_banners(), "/static/uploads/banners")


def salvar_logo_upload(arquivo) -> dict:
    """
    Salva um arquivo de logo enviado via formulário.
    Retorna dict com {ok, url_local, caminho_absoluto, erro}.
    """
    return _salvar_upload(arquivo, _pasta_uploads_logos(), "/static/uploads/logos")


def arquivo_para_base64(caminho_absoluto: str) -> str:
    """
    Lê um arquivo de imagem do disco e retorna um data URL em Base64
    pronto para ser usado no atributo 'src' de uma tag <img>.
    """
    path = Path(caminho_absoluto)
    if not path.is_file():
        return ""

    ext = path.suffix.lstrip(".").lower() or "png"
    mime = {
        "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "png": "image/png", "gif": "image/gif",
        "webp": "image/webp",
    }.get(ext, "image/png")

    with open(path, "rb") as f:
        dados = f.read()
    b64 = base64.b64encode(dados).decode("ascii")
    return f"data:{mime};base64,{b64}"


def url_local_para_absoluto(url_local: str) -> str:
    """
    Converte uma URL relativa como '/static/uploads/banners/x.png' para o
    caminho absoluto no disco, se existir. Se não for local, retorna ''.
    """
    if not url_local or not url_local.startswith("/static/"):
        return ""
    try:
        rel = url_local[len("/static/"):]
        caminho = Path(current_app.static_folder) / rel
        return str(caminho) if caminho.is_file() else ""
    except Exception:
        return ""
