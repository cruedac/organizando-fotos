from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, current_app
from sqlalchemy import func, text
from app.models.database import (
    db,
    FileType,
    TipoSoporte,
    DynamicTable,
    init_existing_tables,
    ensure_photos_scan_table,
    ensure_photos_scan_summary_table,
)
from app.services.media_metadata import format_size
from app.services.file_type_cache import clear_extensions_cache
from app.services.support_type_cache import clear_support_types_cache
from app.models.movie import Movie
from sqlalchemy import inspect
from pathlib import Path
import shutil
import datetime
import os
import tempfile
import sqlite3
from urllib.parse import quote
from markupsafe import Markup, escape
import csv
import io
import json
import traceback

bp = Blueprint('maintenance', __name__, url_prefix='/maintenance')


def _get_database_info():
    """Construye un resumen del estado actual de la base de datos SQLite."""
    engine = db.engine
    inspector = inspect(engine)
    db_uri = engine.url.database
    db_path = Path(db_uri)
    db_name = db_path.name
    size_bytes = db_path.stat().st_size if db_path.exists() else 0
    dynamic_tables = {table.name: table.description for table in DynamicTable.query.all()}

    tables = inspector.get_table_names()
    table_info = []
    with engine.connect() as conn:
        for table_name in tables:
            result = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
            count = result.scalar() or 0
            actions = _resolve_table_actions(table_name)
            table_info.append({
                'name': table_name,
                'description': dynamic_tables.get(table_name),
                'count': count,
                'actions': actions
            })

    return {
        'db_name': db_name,
        'db_path': str(db_path),
    'db_size': size_bytes,
        'db_size_human': format_size(size_bytes),
        'table_count': len(tables),
        'tables': table_info,
        'backup_suggestion': str(db_path.with_suffix('.bk'))
    }


def _resolve_table_actions(table_name: str) -> dict:
    system_tables = {'sqlite_sequence', 'dynamic_table', 'table_field'}

    if table_name in system_tables:
        return {
            'has_action': True,
            'label': 'Ver',
            'url': url_for('maintenance.view_table', table_name=table_name),
            'can_drop': False
        }

    operational = {
        'movies': 'videos.manage',
        'tipo_soporte': 'maintenance.support_types',
        'file_type': 'maintenance.file_types'
    }

    if table_name in operational:
        return {
            'has_action': True,
            'label': 'Operar',
            'url': url_for(operational[table_name]),
            'can_drop': True
        }

    dynamic = DynamicTable.query.filter_by(name=table_name).first()
    if dynamic:
        return {
            'has_action': True,
            'label': 'Operar',
            'url': url_for('tables.manage_records', table_id=dynamic.id),
            'can_drop': True
        }

    return {'has_action': False, 'label': None, 'url': None, 'can_drop': True}


def _serialize_sql_value(value) -> str:
    """Convierte un valor de Python a su representación SQL segura."""
    if value is None:
        return 'NULL'
    if isinstance(value, bool):
        return '1' if value else '0'
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (bytes, bytearray)):
        return "X'" + value.hex() + "'"
    return "'" + str(value).replace("'", "''") + "'"


def _export_table_sql(table_name: str):
    """Genera un fichero SQL plano con la definicion y datos de la tabla."""
    engine = db.engine
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        raise ValueError(f'La tabla "{table_name}" no existe.')

    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    with engine.connect() as conn:
        create_stmt = conn.execute(
            text("SELECT sql FROM sqlite_master WHERE type='table' AND name=:name"),
            {'name': table_name}
        ).scalar() or f'-- No se encontro la definicion de la tabla {table_name}'
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        rows = conn.execute(text(f'SELECT * FROM "{table_name}"')).fetchall()

    lines = [
        f'-- Exportacion generada el {datetime.datetime.now().isoformat(timespec="seconds")}',
        f'-- Tabla: "{table_name}"',
        ''
    ]

    normalized_stmt = create_stmt if create_stmt.strip().endswith(';') else create_stmt + ';'
    lines.append(normalized_stmt)
    lines.append('')

    if rows:
        quoted_columns = ', '.join(f'"{col}"' for col in columns)
        insert_prefix = f'INSERT INTO "{table_name}" ({quoted_columns}) VALUES '
        for row in rows:
            mapping = row._mapping if hasattr(row, '_mapping') else dict(zip(columns, row))
            serialized = [_serialize_sql_value(mapping[column]) for column in columns]
            lines.append(f'{insert_prefix}({", ".join(serialized)});')
    else:
        lines.append('-- La tabla no contiene registros.')

    buffer = io.BytesIO('\n'.join(lines).encode('utf-8'))
    buffer.seek(0)
    filename = f'{table_name}_{timestamp}.txt'
    return buffer, 'text/plain', filename


def _export_table_csv(table_name: str):
    """Genera un CSV UTF-8 con los datos de la tabla."""
    engine = db.engine
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        raise ValueError(f'La tabla "{table_name}" no existe.')

    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    with engine.connect() as conn:
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        rows = conn.execute(text(f'SELECT * FROM "{table_name}"')).fetchall()

    string_buffer = io.StringIO()
    writer = csv.writer(string_buffer)
    writer.writerow(columns)
    for row in rows:
        mapping = row._mapping if hasattr(row, '_mapping') else dict(zip(columns, row))
        writer.writerow([mapping[column] if mapping[column] is not None else '' for column in columns])

    buffer = io.BytesIO(string_buffer.getvalue().encode('utf-8'))
    buffer.seek(0)
    filename = f'{table_name}_{timestamp}.csv'
    return buffer, 'text/csv', filename


@bp.route('/')
def index():
    """Página principal de mantenimiento"""
    info = _get_database_info()
    return render_template('maintenance/index.html', **info)

@bp.route('/file-types')
def file_types():
    """Lista de tipos de archivo"""
    extensions = FileType.query.order_by(FileType.type, FileType.extension).all()
    return render_template('maintenance/file_types.html', extensions=extensions)

@bp.route('/file-types/add', methods=['GET', 'POST'])
def add_file_type():
    """Añadir nuevo tipo de archivo"""
    if request.method == 'POST':
        extension = request.form.get('extension', '').lower()
        if not extension.startswith('.'):
            extension = '.' + extension
        file_type = request.form.get('type')
        
        if FileType.query.filter_by(extension=extension).first():
            flash('Esta extensión ya existe.', 'error')
        else:
            new_type = FileType(extension=extension, type=file_type)
            db.session.add(new_type)
            db.session.commit()
            clear_extensions_cache()  # Limpiar cache después de añadir
            flash('Extensión añadida correctamente.', 'success')
            return redirect(url_for('maintenance.file_types'))
    
    return render_template('maintenance/file_type_form.html')

@bp.route('/file-types/<int:id>/edit', methods=['GET', 'POST'])
def edit_file_type(id):
    """Editar tipo de archivo existente"""
    file_type = FileType.query.get_or_404(id)
    
    if request.method == 'POST':
        file_type.type = request.form.get('type')
        db.session.commit()
        clear_extensions_cache()  # Limpiar cache después de editar
        flash('Tipo de archivo actualizado correctamente.', 'success')
        return redirect(url_for('maintenance.file_types'))
    
    return render_template('maintenance/file_type_form.html', file_type=file_type)

@bp.route('/file-types/<int:id>/delete', methods=['POST'])
def delete_file_type(id):
    """Eliminar tipo de archivo"""
    file_type = FileType.query.get_or_404(id)
    db.session.delete(file_type)
    db.session.commit()
    clear_extensions_cache()  # Limpiar cache después de eliminar
    flash('Tipo de archivo eliminado correctamente.', 'success')
    return redirect(url_for('maintenance.file_types'))


@bp.route('/support-types')
def support_types():
    """Listado de tipos de soporte disponibles."""
    supports = TipoSoporte.query.order_by(TipoSoporte.tipo).all()
    return render_template('maintenance/support_types.html', supports=supports)


@bp.route('/support-types/add', methods=['GET', 'POST'])
def add_support_type():
    """Crear un nuevo tipo de soporte."""
    form_data = {}
    if request.method == 'POST':
        tipo = (request.form.get('tipo') or '').strip()
        form_data['tipo'] = tipo

        if not tipo:
            flash('El nombre del tipo de soporte es obligatorio.', 'error')
        else:
            existing = TipoSoporte.query.filter(func.lower(TipoSoporte.tipo) == tipo.lower()).first()
            if existing:
                flash('Ya existe un tipo de soporte con ese nombre.', 'error')
            else:
                support = TipoSoporte(tipo=tipo)
                db.session.add(support)
                db.session.commit()
                clear_support_types_cache()  # Limpiar cache después de añadir
                flash('Tipo de soporte añadido correctamente.', 'success')
                return redirect(url_for('maintenance.support_types'))

    return render_template('maintenance/support_type_form.html', form_data=form_data or None)


@bp.route('/support-types/<int:support_id>/edit', methods=['GET', 'POST'])
def edit_support_type(support_id):
    """Actualizar un tipo de soporte existente."""
    support = TipoSoporte.query.get_or_404(support_id)
    form_data = {}

    if request.method == 'POST':
        tipo = (request.form.get('tipo') or '').strip()
        form_data['tipo'] = tipo

        if not tipo:
            flash('El nombre del tipo de soporte es obligatorio.', 'error')
        else:
            existing = TipoSoporte.query.filter(
                func.lower(TipoSoporte.tipo) == tipo.lower(),
                TipoSoporte.id != support.id
            ).first()
            if existing:
                flash('Ya existe otro tipo de soporte con ese nombre.', 'error')
            else:
                old_tipo = support.tipo
                if tipo != old_tipo:
                    count_matches = Movie.query.filter(Movie.mediatype == old_tipo).count()
                    if count_matches:
                        flash(f'Se actualizarán {count_matches} registros en la tabla movies al nuevo tipo de soporte "{tipo}".', 'info')
                        Movie.query.filter(Movie.mediatype == old_tipo).update({'mediatype': tipo}, synchronize_session=False)
                support.tipo = tipo
                db.session.commit()
                clear_support_types_cache()  # Limpiar cache después de editar
                flash('Tipo de soporte actualizado correctamente.', 'success')
                return redirect(url_for('maintenance.support_types'))

    return render_template('maintenance/support_type_form.html', support_type=support, form_data=form_data or None)


@bp.route('/support-types/<int:support_id>/delete', methods=['POST'])
def delete_support_type(support_id):
    """Eliminar un tipo de soporte."""
    support = TipoSoporte.query.get_or_404(support_id)
    db.session.delete(support)
    db.session.commit()
    clear_support_types_cache()  # Limpiar cache después de eliminar
    flash('Tipo de soporte eliminado correctamente.', 'success')
    return redirect(url_for('maintenance.support_types'))


@bp.route('/stats.json')
def stats_json():
    """Devuelve la información de la base de datos en formato JSON."""
    return jsonify(_get_database_info())


@bp.route('/table/<string:table_name>')
def view_table(table_name: str):
    """Muestra el contenido de una tabla sin capacidad de edición."""
    engine = db.engine
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        flash(f'La tabla "{table_name}" no existe.', 'error')
        return redirect(url_for('maintenance.index'))

    with engine.connect() as conn:
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        result = conn.execute(text(f'SELECT * FROM "{table_name}" LIMIT 500'))
        rows = result.fetchall()

    actions = _resolve_table_actions(table_name)
    return render_template('maintenance/table_view.html', table_name=table_name, columns=columns, rows=rows, can_drop=actions['can_drop'])


@bp.route('/backup', methods=['POST'])
def backup_database():
    """Realiza una copia de la base de datos en la ruta indicada por el usuario."""
    target_path = request.form.get('target_path')
    if not target_path:
        flash('Debe especificar una ruta de destino para el backup.', 'error')
        return redirect(url_for('maintenance.index'))

    engine = db.engine
    db_uri = engine.url.database
    db_path = Path(db_uri)
    if not db_path.exists():
        flash('La base de datos origen no existe.', 'error')
        return redirect(url_for('maintenance.index'))

    target = Path(target_path)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(db_path, target)
        info = _get_database_info()
        total_records = sum(table['count'] for table in info['tables'])
        summary = (
            f'Copia completada de "{escape(info["db_name"])}" ({escape(info["db_size_human"])}) '
            f'con {info["table_count"]} tablas y {total_records} registros.'
        )
        escaped_target = escape(str(target))
        flash(Markup(f'{summary} Archivo generado: <code>{escaped_target}</code>.'), 'success')
    except Exception as exc:
        flash(f'No se pudo crear el backup: {exc}', 'error')

    return redirect(url_for('maintenance.index'))


def _create_database_backup():
    """Crea un backup automático de la base de datos en la carpeta data/backup/"""
    engine = db.engine
    db_uri = engine.url.database
    db_path = Path(db_uri)
    
    if not db_path.exists():
        raise FileNotFoundError('La base de datos no existe')
    
    # Crear carpeta de backups si no existe
    backup_dir = Path('data/backup')
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Generar nombre con timestamp
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'{db_path.stem}_backup_{timestamp}{db_path.suffix}'
    backup_path = backup_dir / backup_filename
    
    # Copiar archivo
    shutil.copy2(db_path, backup_path)
    
    return str(backup_path)


@bp.route('/export', methods=['POST'])
def export_table():
    """Exporta una tabla a formato SQL plano (.txt) o CSV."""
    table_name = (request.form.get('table_name') or '').strip()
    export_format = (request.form.get('export_format') or '').strip().lower()

    if not table_name:
        flash('Debe seleccionar una tabla para exportar.', 'error')
        return redirect(url_for('maintenance.index'))

    if export_format not in {'sql', 'csv'}:
        flash('Formato de exportacion no valido.', 'error')
        return redirect(url_for('maintenance.index'))

    try:
        if export_format == 'sql':
            buffer, mimetype, filename = _export_table_sql(table_name)
        else:
            buffer, mimetype, filename = _export_table_csv(table_name)
    except ValueError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('maintenance.index'))
    except Exception as exc:  # pylint: disable=broad-except
        flash(f'No se pudo exportar la tabla: {exc}', 'error')
        return redirect(url_for('maintenance.index'))

    return send_file(buffer, mimetype=mimetype, as_attachment=True, download_name=filename)


@bp.route('/import-database', methods=['POST'])
def import_database():
    """
    Importa una base de datos desde un archivo SQL o JSON.
    
    Formatos soportados:
    - SQL: Archivo .sql con sentencias INSERT
    - JSON: Archivo .json con estructura de exportación
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No se proporcionó ningún archivo'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
    
    file_ext = Path(file.filename).suffix.lower()

    truthy_values = {'true', '1', 'on', 'yes'}
    raw_create_backup = (request.form.get('create_backup') or 'true').strip().lower()
    raw_replace_existing = (request.form.get('replace_existing') or 'false').strip().lower()

    create_backup = raw_create_backup in truthy_values
    replace_existing = raw_replace_existing in truthy_values
    
    try:
        # Crear backup antes de importar si se solicita
        if create_backup:
            backup_path = _create_database_backup()
            current_app.logger.info(f'Backup creado antes de importar: {backup_path}')
        
        # Leer contenido del archivo
        content_bytes = file.read()

        if not content_bytes:
            return jsonify({'error': 'El archivo de importacion esta vacio'}), 400

        detected_format = 'sql'

        if content_bytes.startswith(b'SQLite format 3\x00'):
            result = _import_sqlite_database(content_bytes)
            detected_format = 'sqlite'
        else:
            try:
                decoded_content = content_bytes.decode('utf-8-sig')
            except UnicodeDecodeError:
                decoded_content = content_bytes.decode('latin-1')

            preferred_format = (file_ext.lstrip('.') if file_ext else '').lower()
            json_payload = None
            json_error_message = None

            try:
                parsed = json.loads(decoded_content)
                if isinstance(parsed, dict):
                    json_payload = parsed
                else:
                    json_error_message = 'La estructura JSON debe ser un objeto con tablas.'
            except json.JSONDecodeError as exc:  # type: ignore[attr-defined]
                json_error_message = str(exc)

            json_parse_success = json_payload is not None

            if preferred_format == 'json' and not json_parse_success and json_error_message:
                current_app.logger.warning('El archivo %s tiene extension JSON pero no se pudo procesar como JSON: %s', file.filename, json_error_message)

            if preferred_format == 'sql' and 'INSERT' in decoded_content.upper():
                chosen_format = 'sql'
            elif preferred_format == 'json' and json_parse_success:
                chosen_format = 'json'
            elif json_parse_success:
                chosen_format = 'json'
            else:
                chosen_format = 'sql'

            if chosen_format == 'json' and json_parse_success and json_payload is not None:
                result = _import_from_json(json_payload, replace_existing)
            else:
                if chosen_format == 'json' and not json_parse_success and json_error_message:
                    current_app.logger.warning('No se pudo interpretar el contenido como JSON (%s); se intentara como SQL.', json_error_message)
                result = _import_from_sql(decoded_content, replace_existing)
                chosen_format = 'sql'

            detected_format = chosen_format

        _refresh_post_import(current_app)
        
        return jsonify({
            'success': True,
            'message': 'Importación completada exitosamente',
            'details': {
                **result,
                'format_used': detected_format
            }
        }), 200
    except ValueError as e:
        current_app.logger.warning('Error de validacion al importar base de datos: %s', str(e))
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f'Error al importar base de datos: {str(e)}')
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': f'Error al importar: {str(e)}'}), 500


def _refresh_post_import(app):
    """Sincroniza metadatos y limpia caches tras la importacion."""
    try:
        init_existing_tables(app)
        ensure_photos_scan_table(app)
        ensure_photos_scan_summary_table(app)
    except Exception as exc:  # pylint: disable=broad-except
        app.logger.warning('No se pudieron sincronizar todas las tablas tras la importacion: %s', exc)

    try:
        clear_extensions_cache()
        clear_support_types_cache()
    except Exception as exc:  # pylint: disable=broad-except
        app.logger.warning('No se pudieron limpiar las caches tras la importacion: %s', exc)


def _import_sqlite_database(content_bytes):
    """Reemplaza la base de datos SQLite por el archivo proporcionado."""
    db_path = Path(db.engine.url.database)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=db_path.suffix)
    temp_path = Path(temp_file.name)
    try:
        temp_file.write(content_bytes)
        temp_file.flush()
    finally:
        temp_file.close()

    try:
        temp_uri = f"file:{quote(temp_path.resolve().as_posix(), safe='/:')}?mode=ro"
        with sqlite3.connect(temp_uri, uri=True) as connection:  # type: ignore[arg-type]
            connection.execute('SELECT name FROM sqlite_master LIMIT 1')
    except sqlite3.Error as exc:
        temp_path.unlink(missing_ok=True)
        raise ValueError(f'El archivo no es una base de datos SQLite valida: {exc}') from exc

    try:
        db.session.commit()
    except Exception:  # pylint: disable=broad-except
        db.session.rollback()
        temp_path.unlink(missing_ok=True)
        raise
    finally:
        db.session.remove()

    db.engine.dispose()

    try:
        temp_path.replace(db_path)
    finally:
        temp_path.unlink(missing_ok=True)

    table_count = 0
    try:
        inspector = inspect(db.engine)
        table_count = len(inspector.get_table_names())
    except Exception:  # pylint: disable=broad-except
        table_count = 0

    return {
        'bytes_written': len(content_bytes),
        'destination': str(db_path),
        'tables_detected': table_count,
        'full_replace': True
    }


def _import_from_sql(sql_content, replace_existing=False):
    """Importa datos desde contenido SQL"""
    from sqlalchemy import text
    
    # Dividir en sentencias individuales
    statements = [s.strip() for s in sql_content.split(';') if s.strip()]
    
    executed = 0
    skipped = 0
    errors = []
    
    for statement in statements:
        # Ignorar comentarios y líneas vacías
        if statement.startswith('--') or statement.startswith('/*') or not statement:
            continue
        
        try:
            # Si replace_existing es False, convertir INSERT a INSERT OR IGNORE
            if not replace_existing and statement.upper().startswith('INSERT'):
                statement = statement.replace('INSERT', 'INSERT OR IGNORE', 1)
            
            db.session.execute(text(statement))
            executed += 1
        except Exception as e:
            skipped += 1
            errors.append(f'Error en sentencia: {str(e)[:100]}')
            if len(errors) > 10:  # Limitar errores reportados
                errors.append('... (más errores omitidos)')
                break
    
    db.session.commit()
    
    return {
        'executed': executed,
        'skipped': skipped,
        'errors': errors[:10]  # Solo primeros 10 errores
    }


def _import_from_json(data, replace_existing=False):
    """Importa datos desde estructura JSON"""
    from sqlalchemy import text, inspect
    
    inspector = inspect(db.engine)
    existing_tables = inspector.get_table_names()
    
    imported_tables = 0
    imported_records = 0
    skipped_records = 0
    errors = []
    
    for table_name, records in data.items():
        if table_name not in existing_tables:
            errors.append(f'Tabla {table_name} no existe en la BD')
            continue
        
        imported_tables += 1
        
        for record in records:
            try:
                # Construir INSERT dinámico
                columns = ', '.join(record.keys())
                placeholders = ', '.join([f':{k}' for k in record.keys()])
                
                if replace_existing:
                    sql = f'INSERT OR REPLACE INTO {table_name} ({columns}) VALUES ({placeholders})'
                else:
                    sql = f'INSERT OR IGNORE INTO {table_name} ({columns}) VALUES ({placeholders})'
                
                db.session.execute(text(sql), record)
                imported_records += 1
            except Exception as e:
                skipped_records += 1
                if len(errors) < 10:
                    errors.append(f'{table_name}: {str(e)[:100]}')
    
    db.session.commit()
    
    return {
        'imported_tables': imported_tables,
        'imported_records': imported_records,
        'skipped_records': skipped_records,
        'errors': errors[:10]
    }


@bp.route('/reset-database', methods=['POST'])
def reset_database():
    """
    Resetea completamente la base de datos.
    
    Proceso:
    1. Crea backup automático (a menos que se especifique skip_backup=true)
    2. Elimina todas las tablas
    3. Recrea todas las tablas desde esquemas
    4. Pobla datos iniciales si seed=true
    
    JSON Request Body:
        {
            "skip_backup": false,  // Opcional: no crear backup (NO RECOMENDADO)
            "seed_data": true,      // Opcional: poblar datos iniciales
            "confirm": "CONFIRMAR"  // Requerido: confirmación explícita
        }
    
    JSON Response:
        {
            "success": true/false,
            "message": "...",
            "backup_path": "...",  // Si se creó backup
            "tables_created": [...],
            "records_seeded": {...}  // Si seed_data=true
        }
    """
    import subprocess
    import json as json_module
    
    try:
        data = request.get_json() or {}
    except Exception:
        return jsonify({
            'success': False,
            'message': 'Datos JSON inválidos'
        }), 400
    
    # Verificar confirmación
    confirm = data.get('confirm', '').strip()
    if confirm != 'CONFIRMAR':
        return jsonify({
            'success': False,
            'message': 'Confirmación requerida. Debe enviar "confirm": "CONFIRMAR"'
        }), 400
    
    skip_backup = data.get('skip_backup', False)
    seed_data = data.get('seed_data', True)
    
    response_data = {
        'success': False,
        'message': '',
        'timestamp': datetime.datetime.now().isoformat()
    }
    
    try:
        # Construir comando para ejecutar init_database.py
        root_dir = Path(__file__).parent.parent.parent
        script_path = root_dir / 'database' / 'init_database.py'
        
        if not script_path.exists():
            return jsonify({
                'success': False,
                'message': f'Script init_database.py no encontrado en: {script_path}'
            }), 500
        
        # Construir argumentos
        cmd = ['python', str(script_path), '--drop']
        
        if seed_data:
            cmd.append('--seed')
        
        if skip_backup:
            cmd.append('--no-backup')
        
        # Ejecutar script en un subprocess
        # Necesitamos simular la confirmación "CONFIRMAR" enviándola al stdin
        result = subprocess.run(
            cmd,
            cwd=str(root_dir),
            capture_output=True,
            text=True,
            input='CONFIRMAR\n',  # Enviar confirmación automáticamente
            timeout=60  # Timeout de 60 segundos
        )
        
        # Analizar resultado
        if result.returncode == 0:
            # Éxito
            response_data['success'] = True
            response_data['message'] = 'Base de datos reseteada exitosamente'
            
            # Extraer información del output
            output_lines = result.stdout.split('\n')
            
            # Buscar backup path
            for line in output_lines:
                if 'Backup guardado en:' in line:
                    backup_path = line.split('Backup guardado en:')[-1].strip()
                    response_data['backup_path'] = backup_path
            
            # Buscar tablas creadas
            tables_created = []
            for line in output_lines:
                if line.strip().startswith('✓ Tabla'):
                    # Ejemplo: "✓ Tabla 'file_types' creada"
                    parts = line.split("'")
                    if len(parts) >= 2:
                        tables_created.append(parts[1])
            
            if tables_created:
                response_data['tables_created'] = tables_created
            
            # Agregar output completo para depuración
            response_data['output'] = result.stdout
            
            return jsonify(response_data), 200
        else:
            # Error
            response_data['success'] = False
            response_data['message'] = 'Error al resetear la base de datos'
            response_data['error'] = result.stderr
            response_data['output'] = result.stdout
            return jsonify(response_data), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'message': 'Timeout: El proceso tardó más de 60 segundos'
        }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error inesperado: {str(e)}'
        }), 500
