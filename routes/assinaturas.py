import json

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash,
    jsonify, Response, send_file
)

from models import colaborador as colaborador_model
from models import modelo as modelo_model
from models import assinatura as assinatura_model
from services.assinatura_service import gerar_html_assinatura
from services.html_service import html_para_exportacao
from services.upload_service import salvar_banner_upload

bp = Blueprint("assinaturas", __name__, url_prefix="/assinaturas")


def _overrides_do_form(form) -> dict:
    """Lê os toggles/overrides específicos da assinatura enviados no formulário."""
    overrides = {}
    if form.get("banner_ativo") == "on":
        overrides["banner_ativo"] = True
        overrides["banner_url"] = form.get("banner_url", "").strip()
        overrides["banner_link"] = form.get("banner_link", "").strip()
        overrides["banner_alt"] = form.get("banner_alt", "").strip()
        overrides["banner_largura"] = form.get("banner_largura", "300").strip() or "300"
    overrides["opcoes"] = {
        "telefone_clicavel": form.get("telefone_clicavel", "on") == "on",
        "endereco_clicavel": form.get("endereco_clicavel") == "on",
    }
    return overrides


@bp.route("/")
def listar():
    return render_template("assinaturas.html", assinaturas=assinatura_model.listar_assinaturas())


@bp.route("/gerar-todas", methods=["GET", "POST"])
def gerar_todas():
    """Gera uma assinatura para cada colaborador ativo; atualizações existentes são opcionais."""
    colaboradores = colaborador_model.listar_colaboradores(apenas_ativos=True)
    modelos = modelo_model.listar_modelos(apenas_ativos=True)
    modelo_padrao = modelo_model.obter_modelo_padrao()

    if request.method == "POST":
        modelo_id = request.form.get("modelo_id", type=int)
        atualizar_existentes = request.form.get("atualizar_existentes") == "on"
        # Aplicar às assinaturas em lote as mesmas opções disponíveis na geração individual.
        overrides_lote = _overrides_do_form(request.form)
        banner_arquivo = request.files.get("banner_arquivo")
        if banner_arquivo and banner_arquivo.filename:
            upload = salvar_banner_upload(banner_arquivo)
            if not upload.get("ok"):
                flash(upload.get("erro") or "Não foi possível carregar o banner.", "danger")
                return redirect(url_for("assinaturas.gerar_todas"))
            overrides_lote["banner_ativo"] = True
            overrides_lote["banner_url"] = upload["url_local"]
        modelo = modelo_model.obter_modelo(modelo_id) if modelo_id else None
        if not modelo or not modelo.get("ativo"):
            flash("Selecione um modelo ativo para gerar as assinaturas.", "danger")
            return redirect(url_for("assinaturas.gerar_todas"))

        criadas = atualizadas = ignoradas = erros = 0
        for colaborador in colaboradores:
            colaborador_id = colaborador["id"]
            existente = assinatura_model.obter_assinatura_por_colaborador(colaborador_id)
            if existente and not atualizar_existentes:
                ignoradas += 1
                continue

            # As opções escolhidas neste formulário são aplicadas de forma uniforme
            # a todas as assinaturas criadas ou atualizadas nesta execução.
            overrides = dict(overrides_lote)
            resultado = gerar_html_assinatura(colaborador_id, modelo_id, overrides)
            if resultado.get("erro") or not resultado.get("html_preview"):
                erros += 1
                continue

            nome = (existente or {}).get("nome") or "Assinatura " + " ".join(
                filter(None, [colaborador.get("nome"), colaborador.get("sobrenome")])
            )
            if existente:
                assinatura_model.atualizar_assinatura(
                    existente["id"], nome, colaborador_id, modelo_id, overrides, resultado["html_preview"]
                )
                atualizadas += 1
            else:
                assinatura_model.criar_assinatura(
                    nome, colaborador_id, modelo_id, overrides, resultado["html_preview"]
                )
                criadas += 1

        resumo = f"Geração concluída: {criadas} criada(s), {atualizadas} atualizada(s), {ignoradas} já existente(s) mantida(s)."
        flash(resumo, "success")
        if erros:
            flash(f"Não foi possível gerar {erros} assinatura(s). Confira os dados dos colaboradores e o modelo.", "warning")
        return redirect(url_for("assinaturas.listar"))

    return render_template(
        "assinaturas_gerar_todas.html", colaboradores=colaboradores, modelos=modelos,
        modelo_padrao=modelo_padrao,
        existentes=sum(1 for c in colaboradores if assinatura_model.obter_assinatura_por_colaborador(c["id"])),
    )


@bp.route("/nova", methods=["GET", "POST"])
def nova():
    colaboradores = colaborador_model.listar_colaboradores(apenas_ativos=True)
    modelos = modelo_model.listar_modelos(apenas_ativos=True)
    colaborador_preselecionado = request.args.get("colaborador_id", type=int)
    modelo_padrao = modelo_model.obter_modelo_padrao()

    if request.method == "POST":
        try:
            colaborador_id = int(request.form.get("colaborador_id"))
            modelo_id = int(request.form.get("modelo_id"))
        except (TypeError, ValueError):
            flash("Selecione um colaborador e um modelo.", "danger")
            return render_template("assinatura_form.html", colaboradores=colaboradores, modelos=modelos, modo="novo", assinatura={}, overrides={}, colaborador_preselecionado=colaborador_preselecionado, modelo_padrao=modelo_padrao)
        nome = request.form.get("nome", "").strip()
        overrides = _overrides_do_form(request.form)

        resultado = gerar_html_assinatura(colaborador_id, modelo_id, overrides)
        if resultado["erro"]:
            flash(resultado["erro"], "danger")
            return render_template("assinatura_form.html", colaboradores=colaboradores, modelos=modelos, modo="novo", assinatura={"nome": nome}, overrides=overrides, colaborador_preselecionado=colaborador_id, modelo_padrao=modelo_padrao)

        if not nome:
            colaborador = colaborador_model.obter_colaborador(colaborador_id)
            nome = f"Assinatura {colaborador['nome']}" if colaborador else "Assinatura"

        assinatura_model.criar_assinatura(nome, colaborador_id, modelo_id, overrides, resultado["html_preview"])
        flash("Assinatura salva com sucesso.", "success")
        return redirect(url_for("assinaturas.listar"))

    return render_template("assinatura_form.html", colaboradores=colaboradores, modelos=modelos, modo="novo", assinatura={}, overrides={}, colaborador_preselecionado=colaborador_preselecionado, modelo_padrao=modelo_padrao)


@bp.route("/<int:assinatura_id>/editar", methods=["GET", "POST"])
def editar(assinatura_id):
    assinatura = assinatura_model.obter_assinatura(assinatura_id)
    if not assinatura:
        flash("Assinatura não encontrada.", "danger")
        return redirect(url_for("assinaturas.listar"))

    colaboradores = colaborador_model.listar_colaboradores(apenas_ativos=True)
    modelos = modelo_model.listar_modelos(apenas_ativos=True)
    overrides = assinatura_model.overrides_da_assinatura(assinatura)

    if request.method == "POST":
        try:
            colaborador_id = int(request.form.get("colaborador_id"))
            modelo_id = int(request.form.get("modelo_id"))
        except (TypeError, ValueError):
            flash("Selecione um colaborador e um modelo.", "danger")
            return render_template("assinatura_form.html", colaboradores=colaboradores, modelos=modelos, modo="editar", assinatura=assinatura, overrides=overrides, colaborador_preselecionado=assinatura["colaborador_id"], modelo_padrao=None)
        nome = request.form.get("nome", "").strip() or assinatura["nome"]
        overrides = _overrides_do_form(request.form)
        resultado = gerar_html_assinatura(colaborador_id, modelo_id, overrides)
        if resultado.get("erro"):
            flash(resultado["erro"], "danger")
            return render_template("assinatura_form.html", colaboradores=colaboradores, modelos=modelos, modo="editar", assinatura=assinatura, overrides=overrides, colaborador_preselecionado=colaborador_id, modelo_padrao=None)
        assinatura_model.atualizar_assinatura(assinatura_id, nome, colaborador_id, modelo_id, overrides, resultado["html_preview"])
        flash("Assinatura atualizada com sucesso.", "success")
        return redirect(url_for("colaboradores.listar"))

    return render_template("assinatura_form.html", colaboradores=colaboradores, modelos=modelos, modo="editar", assinatura=assinatura, overrides=overrides, colaborador_preselecionado=assinatura["colaborador_id"], modelo_padrao=None)


@bp.route("/upload-banner", methods=["POST"])
def upload_banner():
    """Recebe um banner selecionado na tela e retorna a URL local para preview.

    Para uso real em e-mails, a URL resultante precisa estar publicada em HTTPS
    acessível aos destinatários; localhost e caminhos relativos não são públicos.
    """
    arquivo = request.files.get("banner_arquivo")
    resultado = salvar_banner_upload(arquivo)
    if not resultado.get("ok"):
        return jsonify({"ok": False, "erro": resultado.get("erro") or "Falha ao enviar o banner."}), 400
    return jsonify({"ok": True, "url": resultado["url_local"], "mensagem": "Banner enviado. Para uso em e-mails, hospede a imagem em HTTPS acessível aos destinatários."})


@bp.route("/preview", methods=["POST"])
def preview():
    """Endpoint AJAX usado pela tela de criação para atualizar a pré-visualização."""
    colaborador_id = request.form.get("colaborador_id", type=int)
    modelo_id = request.form.get("modelo_id", type=int)
    if not colaborador_id or not modelo_id:
        return jsonify({"html": "", "erro": "Selecione um colaborador e um modelo."})
    overrides = _overrides_do_form(request.form)
    resultado = gerar_html_assinatura(colaborador_id, modelo_id, overrides)
    return jsonify({"html": resultado["html_preview"], "erro": resultado["erro"]})


@bp.route("/<int:assinatura_id>/exportar-html")
def exportar_html(assinatura_id):
    assinatura = assinatura_model.obter_assinatura(assinatura_id)
    if not assinatura:
        flash("Assinatura não encontrada.", "danger")
        return redirect(url_for("assinaturas.listar"))
    conteudo = html_para_exportacao(assinatura["html_gerado"] or "")
    nome_arquivo = f"assinatura-{assinatura['nome'].lower().replace(' ', '-')}.html"
    return Response(
        conteudo,
        mimetype="text/html",
        headers={"Content-Disposition": f"attachment; filename={nome_arquivo}"},
    )


@bp.route("/<int:assinatura_id>/duplicar", methods=["POST"])
def duplicar(assinatura_id):
    novo_id = assinatura_model.duplicar_assinatura(assinatura_id)
    if novo_id:
        flash("Assinatura duplicada com sucesso.", "success")
    else:
        flash("Assinatura não encontrada.", "danger")
    return redirect(url_for("assinaturas.listar"))


@bp.route("/<int:assinatura_id>/excluir", methods=["POST"])
def excluir(assinatura_id):
    assinatura_model.excluir_assinatura(assinatura_id)
    flash("Assinatura removida.", "success")
    return redirect(url_for("assinaturas.listar"))


@bp.route("/<int:assinatura_id>")
def visualizar(assinatura_id):
    assinatura = assinatura_model.obter_assinatura(assinatura_id)
    if not assinatura:
        flash("Assinatura não encontrada.", "danger")
        return redirect(url_for("assinaturas.listar"))
    return render_template("assinatura_visualizar.html", assinatura=assinatura)
