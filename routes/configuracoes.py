import os
import tempfile

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash,
    jsonify, send_file
)

from models import config as config_model
from models import empresa as empresa_model
from models import modelo as modelo_model
from services.url_service import testar_imagem_acessivel
from services import backup_service

bp = Blueprint("configuracoes", __name__, url_prefix="/configuracoes")


@bp.route("/preferencias", methods=["GET", "POST"])
def preferencias():
    if request.method == "POST":
        config_model.set_many({
            "modelo_padrao_id": request.form.get("modelo_padrao_id", ""),
            "logo_padrao_url": request.form.get("logo_padrao_url", "").strip(),
            "cor_padrao": request.form.get("cor_padrao", "#003366"),
            "fonte_padrao": request.form.get("fonte_padrao", "Arial, Helvetica, sans-serif"),
            "tamanho_padrao": request.form.get("tamanho_padrao", "14px"),
            "whatsapp_icone_url": request.form.get("whatsapp_icone_url", "").strip()
                or "https://cdn.simpleicons.org/whatsapp/25D366",
        })
        flash("Preferências salvas com sucesso.", "success")
        return redirect(url_for("configuracoes.preferencias"))

    return render_template(
        "configuracoes_preferencias.html",
        config=config_model.get_all_config(),
        modelos=modelo_model.listar_modelos(apenas_ativos=True),
    )


@bp.route("/testar-imagem", methods=["POST"])
def testar_imagem():
    url = request.json.get("url", "") if request.is_json else request.form.get("url", "")
    resultado = testar_imagem_acessivel(url)
    return jsonify(resultado)


@bp.route("/backup/exportar")
def backup_exportar():
    zip_path = backup_service.exportar_backup()
    return send_file(zip_path, as_attachment=True, download_name=os.path.basename(zip_path))


@bp.route("/backup/importar", methods=["POST"])
def backup_importar():
    arquivo = request.files.get("arquivo_backup")
    if not arquivo or arquivo.filename == "":
        flash("Selecione um arquivo de backup (.zip).", "danger")
        return redirect(url_for("configuracoes.preferencias"))

    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        arquivo.save(tmp.name)
        caminho_tmp = tmp.name

    resultado = backup_service.importar_backup(caminho_tmp)
    os.unlink(caminho_tmp)

    flash(resultado["mensagem"], "success" if resultado["sucesso"] else "danger")
    return redirect(url_for("configuracoes.preferencias"))
