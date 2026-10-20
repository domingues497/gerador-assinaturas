from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from io import BytesIO
from openpyxl import Workbook

from models import colaborador as colaborador_model
from services.colaborador_import_service import importar_xlsx
from services.assinatura_service import gerar_html_assinatura
from models import assinatura as assinatura_model

bp = Blueprint("colaboradores", __name__, url_prefix="/colaboradores")


@bp.route("/")
def listar():
    colaboradores = colaborador_model.listar_colaboradores()
    assinaturas_por_colaborador = {
        c["id"]: colaborador_signature for c in colaboradores
        if (colaborador_signature := assinatura_model.obter_assinatura_por_colaborador(c["id"]))
    }
    return render_template("colaboradores.html", colaboradores=colaboradores, assinaturas_por_colaborador=assinaturas_por_colaborador)


@bp.route("/novo", methods=["GET", "POST"])
def novo():
    if request.method == "POST":
        dados = {campo: request.form.get(campo, "").strip() for campo in colaborador_model.CAMPOS if campo != "ativo"}
        dados["ativo"] = request.form.get("ativo") == "on"
        if not dados.get("nome"):
            flash("O campo Nome é obrigatório.", "danger")
            return render_template("colaborador_form.html", colaborador=dados, modo="novo")
        colaborador_model.criar_colaborador(dados)
        flash("Colaborador cadastrado com sucesso.", "success")
        return redirect(url_for("colaboradores.listar"))
    return render_template("colaborador_form.html", colaborador={}, modo="novo")


@bp.route("/<int:colaborador_id>/editar", methods=["GET", "POST"])
def editar(colaborador_id):
    colaborador = colaborador_model.obter_colaborador(colaborador_id)
    if not colaborador:
        flash("Colaborador não encontrado.", "danger")
        return redirect(url_for("colaboradores.listar"))

    if request.method == "POST":
        dados = {campo: request.form.get(campo, "").strip() for campo in colaborador_model.CAMPOS if campo != "ativo"}
        dados["ativo"] = request.form.get("ativo") == "on"
        if not dados.get("nome"):
            flash("O campo Nome é obrigatório.", "danger")
            return render_template("colaborador_form.html", colaborador=dados, modo="editar", colaborador_id=colaborador_id)
        colaborador_model.atualizar_colaborador(colaborador_id, dados)
        # Atualiza o HTML salvo para que alterações de nome, cargo, telefone etc. apareçam na assinatura.
        atualizadas = 0
        for assinatura in assinatura_model.listar_assinaturas_por_colaborador(colaborador_id):
            resultado = gerar_html_assinatura(
                colaborador_id, assinatura["modelo_id"], assinatura_model.overrides_da_assinatura(assinatura)
            )
            if not resultado.get("erro") and resultado.get("html_preview"):
                assinatura_model.atualizar_assinatura(
                    assinatura["id"], assinatura["nome"], colaborador_id, assinatura["modelo_id"],
                    assinatura_model.overrides_da_assinatura(assinatura), resultado["html_preview"]
                )
                atualizadas += 1
        mensagem = "Colaborador atualizado com sucesso."
        if atualizadas:
            mensagem += f" {atualizadas} assinatura(s) também foram atualizadas."
        flash(mensagem, "success")
        return redirect(url_for("colaboradores.listar"))

    return render_template("colaborador_form.html", colaborador=colaborador, modo="editar", colaborador_id=colaborador_id)


@bp.route("/<int:colaborador_id>/excluir", methods=["POST"])
def excluir(colaborador_id):
    colaborador_model.excluir_colaborador(colaborador_id)
    flash("Colaborador removido.", "success")
    return redirect(url_for("colaboradores.listar"))

@bp.route("/importar", methods=["POST"])
def importar():
    arquivo = request.files.get("arquivo")
    if not arquivo or not arquivo.filename:
        flash("Selecione uma planilha Excel (.xlsx) para importar.", "warning")
        return redirect(url_for("colaboradores.listar"))

    if not arquivo.filename.lower().endswith(".xlsx"):
        flash("Formato inválido. Envie uma planilha Excel com extensão .xlsx.", "danger")
        return redirect(url_for("colaboradores.listar"))

    resultado = importar_xlsx(arquivo.read())
    if resultado.get("ok"):
        flash(f"Importação concluída: {resultado.get('importados', 0)} colaborador(es) importado(s).", "success")
    elif resultado.get("erro"):
        flash(resultado["erro"], "danger")

    erros = resultado.get("erros_linha", [])
    for item in erros[:10]:
        flash(f"Linha {item.get('linha')}: {'; '.join(item.get('erros', []))}", "warning")
    if len(erros) > 10:
        flash(f"Há mais {len(erros) - 10} linha(s) com erro; corrija a planilha e importe novamente.", "warning")
    return redirect(url_for("colaboradores.listar"))


@bp.route("/modelo-importacao.xlsx")
def modelo_importacao():
    wb = Workbook()
    ws = wb.active
    ws.title = "Colaboradores"
    cabecalhos = [
        "Nome", "Sobrenome", "Cargo", "Departamento", "Setor", "E-mail",
        "Telefone", "Ramal", "Celular", "WhatsApp", "Endereço", "Cidade",
        "Estado", "Foto URL",
    ]
    ws.append(cabecalhos)
    ws.append(["Maria", "Silva", "Analista", "TI", "Sistemas", "maria@empresa.com", "", "", "", "", "", "", "PR", ""])
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:N2"
    for col in ws.columns:
        letra = col[0].column_letter
        largura = max(len(str(c.value or "")) for c in col) + 2
        ws.column_dimensions[letra].width = min(max(largura, 12), 28)
    arquivo = BytesIO()
    wb.save(arquivo)
    arquivo.seek(0)
    return send_file(arquivo, as_attachment=True, download_name="modelo_colaboradores.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

