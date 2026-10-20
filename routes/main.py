from flask import Blueprint, render_template, redirect, url_for, request, flash

from models import empresa as empresa_model
from models import colaborador as colaborador_model
from models import modelo as modelo_model
from models import assinatura as assinatura_model
from models import config as config_model

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    if not empresa_model.empresa_configurada():
        return redirect(url_for("main.setup_inicial"))
    return render_template(
        "index.html",
        total_colaboradores=len(colaborador_model.listar_colaboradores(apenas_ativos=True)),
        total_modelos=len(modelo_model.listar_modelos(apenas_ativos=True)),
        total_assinaturas=len(assinatura_model.listar_assinaturas()),
        empresa=empresa_model.get_empresa(),
    )


@bp.route("/configuracao-inicial", methods=["GET", "POST"])
def setup_inicial():
    """Assistente de primeiro acesso (Requisito 42)."""
    if request.method == "POST":
        dados = {campo: request.form.get(campo, "").strip() for campo in empresa_model.CAMPOS}
        empresa_model.salvar_empresa(dados)
        config_model.set_many({
            "cor_padrao": dados.get("cor_principal") or "#003366",
            "logo_padrao_url": dados.get("logo_url") or "",
            "fonte_padrao": dados.get("fonte") or "Arial, Helvetica, sans-serif",
            "primeiro_acesso_concluido": "1",
        })
        flash("Configuração salva com sucesso.", "success")
        return redirect(url_for("main.index"))
    return render_template("setup_inicial.html")
