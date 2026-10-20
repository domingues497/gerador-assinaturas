"""Ponto de entrada WSGI para Gunicorn no Linux/Ubuntu.

Uso: gunicorn --workers 1 --bind 127.0.0.1:8017 wsgi:app
"""
from app import criar_app
from database.database import init_db
from services.seeds import seed_modelo_padrao, migrar_icone_whatsapp

# Inicializa o banco e os dados padrão antes de atender requisições.
init_db()
seed_modelo_padrao()
migrar_icone_whatsapp()

app = criar_app()
