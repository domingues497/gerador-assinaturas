from flask import Blueprint, render_template, request, redirect, url_for, flash

from models import modelo as modelo_model

bp = Blueprint("modelos", __name__, url_prefix="/modelos")


@bp.route("/")
def listar():
    return render_template("modelos.html", modelos=modelo_model.listar_modelos())


@bp.route("/novo", methods=["GET", "POST"])
def novo():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        descricao = request.form.get("descricao", "").strip()
        html_template = request.form.get("html_template", "").strip()
        padrao = request.form.get("padrao") == "on"
        if not nome or not html_template:
            flash("Nome e HTML do modelo são obrigatórios.", "danger")
            return render_template("modelo_form.html", modelo={"nome": nome, "descricao": descricao, "html_template": html_template}, modo="novo")
        modelo_model.criar_modelo(nome, descricao, html_template, overrides={}, padrao=padrao)
        flash("Modelo criado com sucesso.", "success")
        return redirect(url_for("modelos.listar"))
    return render_template("modelo_form.html", modelo={}, modo="novo")


@bp.route("/<int:modelo_id>/editar", methods=["GET", "POST"])
def editar(modelo_id):
    modelo = modelo_model.obter_modelo(modelo_id)
    if not modelo:
        flash("Modelo não encontrado.", "danger")
        return redirect(url_for("modelos.listar"))

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        descricao = request.form.get("descricao", "").strip()
        html_template = request.form.get("html_template", "").strip()
        padrao = request.form.get("padrao") == "on"
        ativo = request.form.get("ativo") == "on"
        if not nome or not html_template:
            flash("Nome e HTML do modelo são obrigatórios.", "danger")
            return render_template("modelo_form.html", modelo=modelo, modo="editar", modelo_id=modelo_id)
        modelo_model.atualizar_modelo(modelo_id, nome, descricao, html_template, overrides={}, padrao=padrao, ativo=ativo)
        flash("Modelo atualizado com sucesso.", "success")
        return redirect(url_for("modelos.listar"))

    return render_template("modelo_form.html", modelo=modelo, modo="editar", modelo_id=modelo_id)


@bp.route("/<int:modelo_id>/excluir", methods=["POST"])
def excluir(modelo_id):
    modelo_model.excluir_modelo(modelo_id)
    flash("Modelo removido.", "success")
    return redirect(url_for("modelos.listar"))
