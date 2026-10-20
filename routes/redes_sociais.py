from flask import Blueprint, render_template, request, redirect, url_for, flash

from models import redes_sociais as redes_model

bp = Blueprint("redes_sociais", __name__, url_prefix="/redes-sociais")


@bp.route("/")
def listar():
    return render_template("redes_sociais.html", redes=redes_model.listar_redes())


@bp.route("/nova", methods=["POST"])
def nova():
    redes_model.criar_rede(
        nome=request.form.get("nome", "").strip(),
        url=request.form.get("url", "").strip(),
        icone_url=request.form.get("icone_url", "").strip(),
        ordem=int(request.form.get("ordem") or 0),
        ativo=request.form.get("ativo") == "on",
    )
    flash("Rede social adicionada.", "success")
    return redirect(url_for("redes_sociais.listar"))


@bp.route("/<int:rede_id>/editar", methods=["POST"])
def editar(rede_id):
    redes_model.atualizar_rede(
        rede_id,
        nome=request.form.get("nome", "").strip(),
        url=request.form.get("url", "").strip(),
        icone_url=request.form.get("icone_url", "").strip(),
        ordem=int(request.form.get("ordem") or 0),
        ativo=request.form.get("ativo") == "on",
    )
    flash("Rede social atualizada.", "success")
    return redirect(url_for("redes_sociais.listar"))


@bp.route("/<int:rede_id>/excluir", methods=["POST"])
def excluir(rede_id):
    redes_model.excluir_rede(rede_id)
    flash("Rede social removida.", "success")
    return redirect(url_for("redes_sociais.listar"))
