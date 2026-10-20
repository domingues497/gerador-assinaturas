"""
Gerador de Assinaturas de E-mail
---------------------------------
Ponto de entrada da aplicação. Responsável por:
- Configurar logging persistente em %APPDATA%\\GeradorAssinaturas\\logs.
- Inicializar o banco SQLite (fora da pasta temporária do PyInstaller).
- Registrar os blueprints (rotas).
- Escolher uma porta local livre (com fallback automático).
- Abrir o navegador padrão automaticamente.
- Tratar erros de forma amigável (sem exibir traceback ao usuário final).
"""

import os
import sys
import socket
import logging
import threading
import webbrowser
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template

# Garante que os módulos do projeto sejam encontrados tanto em modo
# desenvolvimento quanto quando empacotado pelo PyInstaller.
if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS  # pasta temporária somente leitura do PyInstaller
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from database.database import init_db, get_app_data_dir  # noqa: E402
from services.seeds import seed_modelo_padrao, migrar_icone_whatsapp  # noqa: E402
from routes import main, empresa, colaboradores, modelos, redes_sociais, assinaturas, configuracoes  # noqa: E402
from routes import outlook_api, distribuicao_outlook  # noqa: E402

PORTA_INICIAL = 5000
TENTATIVAS_PORTA = 10


def configurar_logging():
    log_dir = os.path.join(get_app_data_dir(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "app.log")

    handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))

    logger = logging.getLogger("GeradorAssinaturas")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    # Também loga erros do próprio Flask/Werkzeug
    logging.getLogger("werkzeug").addHandler(handler)
    return logger


def criar_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, "templates"),
        static_folder=os.path.join(BASE_DIR, "static"),
    )
    app.secret_key = os.environ.get("GERADOR_SECRET_KEY", "chave-local-nao-sensivel-troque-se-desejar")
    app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB (uploads de backup)

    app.register_blueprint(main.bp)
    app.register_blueprint(empresa.bp)
    app.register_blueprint(colaboradores.bp)
    app.register_blueprint(modelos.bp)
    app.register_blueprint(redes_sociais.bp)
    app.register_blueprint(assinaturas.bp)
    app.register_blueprint(configuracoes.bp)
    app.register_blueprint(outlook_api.bp)
    app.register_blueprint(distribuicao_outlook.bp)

    @app.errorhandler(404)
    def nao_encontrado(_e):
        return render_template("erro.html", titulo="Página não encontrada",
                                mensagem="A página solicitada não existe."), 404

    @app.errorhandler(500)
    def erro_interno(e):
        logging.getLogger("GeradorAssinaturas").exception("Erro interno não tratado")
        return render_template("erro.html", titulo="Ocorreu um erro",
                                mensagem="Não foi possível concluir a operação. "
                                         "Verifique os dados informados e tente novamente."), 500

    return app


def _porta_livre(porta: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", porta)) != 0


def escolher_porta() -> int:
    for i in range(TENTATIVAS_PORTA):
        candidata = PORTA_INICIAL + i
        if _porta_livre(candidata):
            return candidata
    return PORTA_INICIAL  # fallback final; o Flask acusará erro claro se indisponível


def abrir_navegador(porta: int):
    webbrowser.open(f"http://127.0.0.1:{porta}")


def main_entry():
    logger = configurar_logging()
    logger.info("Inicializando Gerador de Assinaturas...")

    try:
        init_db()
        seed_modelo_padrao()
        migrar_icone_whatsapp()
    except Exception:
        logger.exception("Erro ao inicializar o banco de dados")
        raise

    app = criar_app()
    porta = escolher_porta()
    host_log = os.environ.get("GERADOR_HOST", "127.0.0.1").strip() or "127.0.0.1"
    logger.info("Servidor iniciado em %s:%s", host_log, porta)

    # Abre o navegador após um pequeno delay, dando tempo do servidor subir.
    threading.Timer(1.0, abrir_navegador, args=(porta,)).start()

    try:
        # use_reloader=False evita duas instâncias do servidor/duas abas do navegador.
        host = os.environ.get("GERADOR_HOST", "127.0.0.1").strip() or "127.0.0.1"
        app.run(host=host, port=porta, debug=False, use_reloader=False)
    finally:
        logger.info("Servidor encerrado.")


if __name__ == "__main__":
    main_entry()
