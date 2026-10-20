from flask import Blueprint, render_template, request, redirect, url_for, flash

from models import empresa as empresa_model
from services.url_service import validar_url_imagem

bp = Blueprint("empresa", __name__, url_prefix="/empresa")


@bp.route("/", methods=["GET", "POST"])
def editar():
    if request.method == "POST":
        dados = {campo: request.form.get(campo, "").strip() for campo in empresa_model.CAMPOS}
        aviso_logo = validar_url_imagem(dados.get("logo_url", ""))
        if not aviso_logo["valida"]:
            flash(aviso_logo["aviso"], "danger")
            return render_template("empresa.html", empresa=dados)
        empresa_model.salvar_empresa(dados)
        flash("Dados da empresa salvos com sucesso.", "success")
        return redirect(url_for("empresa.editar"))

    return render_template("empresa.html", empresa=empresa_model.get_empresa())
