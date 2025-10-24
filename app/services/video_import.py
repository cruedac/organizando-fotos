import json
import logging
import os
from datetime import datetime

from app import db

logger = logging.getLogger(__name__)

def import_movies_from_txt(app=None):
    """Importa INSERTs desde imports/datos.txt hacia la base de datos.

    Si se pasa la aplicación (`app`), se ejecuta dentro de `with app.app_context()`.
    En caso contrario, intenta obtener el contexto actual (para compatibilidad).
    """
    # Resolvemos la ruta del archivo
    file_path = os.path.join(os.getcwd(), "imports", "datos.txt")
    if not os.path.exists(file_path):
        return 0

    # Importar bajo el contexto correcto
    from app import db
    imported = 0

    def _do_import():
        nonlocal imported
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        for line in lines:
            line = line.strip()
            if line.startswith("INSERT INTO movies"):
                try:
                    db.session.execute(line)
                    imported += 1
                except Exception as e:
                    logger.exception("Error importing line", exc_info=e)
        db.session.commit()

    # Ejecutar con el contexto adecuado
    if app is not None:
        with app.app_context():
            _do_import()
    else:
        # Intentar usar current_app si existe
        try:
            from flask import current_app
            with current_app.app_context():
                _do_import()
        except RuntimeError:
            # No hay contexto disponible
            logger.warning("No hay contexto de aplicación disponible para importar datos.")
            return 0

    logger.info("Importación de películas finalizada. Total importados: %s", imported)
    return imported


def import_sql_file(sql_path=None, app=None):
    """Ejecuta un archivo .sql directamente en la base de datos.

    Usa la conexión raw de la base de datos (DB-API) para llamar a
    cursor.executescript(...) que es la forma más sencilla para ejecutar
    múltiples sentencias SQLite (CREATE/INSERT/..).

    Por defecto busca 'imports/Cintas.sql' en el directorio del proyecto.
    """
    if sql_path is None:
        sql_path = os.path.join(os.getcwd(), 'imports', 'Cintas.sql')

    if not os.path.exists(sql_path):
        logger.warning("Archivo SQL no encontrado: %s", sql_path)
        return 0

    # Controlar ejecución condicional por variable de entorno
    import os as _os
    env_flag = _os.getenv('IMPORT_LEGACY_SQL', '')
    if str(env_flag).lower() not in ['', '1', 'true', 'yes']:
        logger.info('IMPORT_LEGACY_SQL no establecido. Saltando ejecución de SQL legacy.')
        return 0

    # Ejecutar dentro del contexto de la aplicación si se pasa
    def _exec_sql():
        from app import db
        imported_statements = 0
        report = {
            'sql_path': sql_path,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'insert_attempts': 0,
            'insert_executed': 0,
            'errors': []
        }
        # Obtener una conexión DB-API cruda y usar executescript
        raw_conn = db.engine.raw_connection()
        try:
            with open(sql_path, 'r', encoding='utf-8', errors='ignore') as f:
                sql_text = f.read()

            # Evitar fallos por UNIQUE constraint cambiando INSERT INTO por
            # INSERT OR IGNORE para la tabla movies (SQLite). La tabla extras
            # dejó de existir, así que eliminamos cualquier referencia.
            import re
            sql_text_mod = re.sub(r"INSERT\s+INTO\s+movies", "INSERT OR IGNORE INTO movies", sql_text, flags=re.I)
            sql_text_mod = re.sub(r"(?is)CREATE\s+TABLE\s+[\"`]?extras[\"`]?\s*\(.*?\);\s*", "", sql_text_mod)
            sql_text_mod = re.sub(r"(?im)^[^\n]*INSERT\s+INTO\s+[\"`]?extras[\"`]?[^;]*;\s*", "", sql_text_mod)

            cursor = raw_conn.cursor()
            try:
                cursor.executescript(sql_text_mod)
                raw_conn.commit()
                # Contar aproximado de INSERTs para feedback (buscamos ambas formas)
                imported_statements = sql_text_mod.lower().count('insert or ignore into')
                if imported_statements == 0:
                    # fallback: contar cualquier INSERT
                    imported_statements = sql_text_mod.lower().count('insert into')
                report['insert_attempts'] = imported_statements
                report['insert_executed'] = imported_statements  # aproximado
            except Exception as ex_exec:
                try:
                    raw_conn.rollback()
                except Exception:
                    pass
                err = str(ex_exec)
                report['errors'].append(err)
                logger.error("Error ejecutando script SQL: %s", err)
                # re-raise to upper handler
                raise
        except Exception as e:
            try:
                raw_conn.rollback()
            except Exception:
                pass
            err = str(e)
            report.setdefault('errors', []).append(err)
            logger.error("Error ejecutando SQL desde %s: %s", sql_path, err)
        finally:
            try:
                cursor.close()
            except Exception:
                pass
            try:
                raw_conn.close()
            except Exception:
                pass
        # Escribir informe JSON en data/import_reports
        try:
            # Determinar directorio de informes
            base_dir = os.path.dirname(os.getcwd()) if os.getcwd().endswith('src') else os.getcwd()
            reports_dir = os.path.join(base_dir, 'data', 'import_reports')
            os.makedirs(reports_dir, exist_ok=True)
            report_name = f"import_legacy_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json"
            report_path = os.path.join(reports_dir, report_name)
            with open(report_path, 'w', encoding='utf-8') as rf:
                json.dump(report, rf, ensure_ascii=False, indent=2)
            logger.info("Informe de importación guardado en: %s", report_path)
        except Exception as e_rep:
            logger.error("Error escribiendo informe de importación: %s", e_rep)

        return imported_statements

    if app is not None:
        with app.app_context():
            count = _exec_sql()
    else:
        try:
            from flask import current_app
            with current_app.app_context():
                count = _exec_sql()
        except RuntimeError:
            logger.warning('No hay contexto de aplicación disponible para ejecutar SQL.')
            return 0

    logger.info("Ejecución de SQL finalizada. INSERTs aproximados ejecutados: %s", count)
    return count
