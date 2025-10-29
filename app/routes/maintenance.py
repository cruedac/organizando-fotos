from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from sqlalchemy import func, text
from app.models.database import db, FileType, TipoSoporte, DynamicTable
from app.services.media_metadata import format_size
from app.services.file_type_cache import clear_extensions_cache
from app.services.support_type_cache import clear_support_types_cache
from app.models.movie import Movie
from sqlalchemy import inspect
from pathlib import Path
import shutil
import datetime
import os
from markupsafe import Markup, escape
import csv
import io

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