"""Exportação/Importação de backup (Requisitos 55 e 56).

O backup contém o banco SQLite completo (empresa, colaboradores, modelos,
redes sociais, assinaturas e configurações). Como as imagens são hospedadas
externamente, elas não fazem parte do backup.
"""

import os
import shutil
import tempfile
import zipfile
from datetime import datetime

from database.database import get_db_path


def exportar_backup() -> str:
    """Gera um arquivo zip de backup e retorna o caminho do arquivo temporário."""
    db_path = get_db_path()
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    tmp_dir = tempfile.mkdtemp(prefix="backup-assinaturas-")
    zip_path = os.path.join(tmp_dir, f"backup-assinaturas-{timestamp}.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        if os.path.exists(db_path):
            zf.write(db_path, arcname="assinaturas.db")
        zf.writestr("backup_info.txt",
                     f"Backup gerado em {datetime.now().isoformat()}\n"
                     "Contém: banco SQLite (empresa, colaboradores, modelos, "
                     "redes sociais, assinaturas e configurações).\n"
                     "As imagens não estão incluídas (hospedadas externamente).")
    return zip_path


def importar_backup(arquivo_zip_path: str) -> dict:
    """Restaura um backup, substituindo o banco atual. Retorna dict com sucesso/mensagem."""
    db_path = get_db_path()
    try:
        with zipfile.ZipFile(arquivo_zip_path, "r") as zf:
            if "assinaturas.db" not in zf.namelist():
                return {"sucesso": False, "mensagem": "Arquivo de backup inválido: banco de dados não encontrado."}
            tmp_dir = tempfile.mkdtemp(prefix="restore-assinaturas-")
            zf.extract("assinaturas.db", tmp_dir)
            extraido = os.path.join(tmp_dir, "assinaturas.db")

            # Backup de segurança do banco atual antes de sobrescrever
            if os.path.exists(db_path):
                shutil.copy2(db_path, db_path + ".antes-restauracao.bak")

            shutil.copy2(extraido, db_path)
        return {"sucesso": True, "mensagem": "Configurações restauradas com sucesso."}
    except zipfile.BadZipFile:
        return {"sucesso": False, "mensagem": "Arquivo de backup inválido ou corrompido."}
    except Exception:
        import logging
        logging.getLogger("GeradorAssinaturas").exception("Erro ao importar backup")
        return {"sucesso": False, "mensagem": "Não foi possível importar o backup. Tente novamente."}
