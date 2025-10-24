from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.models.database import db, DynamicTable, TableField
from sqlalchemy import inspect, text
import re
from typing import Dict, Any, List
import os
from pathlib import Path

bp = Blueprint('tables', __name__, url_prefix='/tables')


SQL_TYPE_MAP = {
    TableField.FieldTypes.TEXT: 'TEXT',
    TableField.FieldTypes.INTEGER: 'INTEGER',
    TableField.FieldTypes.REAL: 'REAL',
    TableField.FieldTypes.DATE: 'TEXT',
    TableField.FieldTypes.DATETIME: 'TEXT',
    TableField.FieldTypes.BOOLEAN: 'INTEGER'
}


def _is_valid_identifier(name: str) -> bool:
    return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name))


def _create_physical_table(table: DynamicTable) -> None:
    engine = db.engine
    columns = ['"id" INTEGER PRIMARY KEY AUTOINCREMENT']
    create_stmt = f'CREATE TABLE "{table.name}" ({", ".join(columns)})'
    with engine.begin() as connection:
        connection.execute(text(create_stmt))


def _add_column_to_table(table: DynamicTable, field: TableField) -> None:
    if field.name == 'id':
        return
    sql_type = SQL_TYPE_MAP.get(field.field_type, 'TEXT')
    default_clause = ''
    if field.default_value not in (None, ''):
        default_value = _prepare_default_value(field)
        default_clause = f' DEFAULT {default_value}'
    alter_stmt = text(
        f'ALTER TABLE "{table.name}" ADD COLUMN "{field.name}" {sql_type}{default_clause}'
    )
    with db.engine.begin() as connection:
        connection.execute(alter_stmt)


def _prepare_default_value(field: TableField) -> str:
    value = field.default_value
    if field.field_type == TableField.FieldTypes.BOOLEAN:
        return '1' if str(value).lower() in ('1', 'true', 'yes', 'on') else '0'
    if field.field_type == TableField.FieldTypes.INTEGER:
        return str(int(value))
    if field.field_type == TableField.FieldTypes.REAL:
        return str(float(value))
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


def _collect_table_fields(table: DynamicTable) -> List[TableField]:
    return sorted(table.fields, key=lambda f: (0 if f.name == 'id' else 1, f.id))


def _field_display_name(field: TableField) -> str:
    return field.description or field.name


def _to_python_value(field: TableField, raw: str) -> Any:
    if raw is None:
        return None
    raw = raw.strip()
    if raw == '':
        return None
    try:
        if field.field_type == TableField.FieldTypes.INTEGER:
            return int(raw)
        if field.field_type == TableField.FieldTypes.REAL:
            return float(raw)
        if field.field_type == TableField.FieldTypes.BOOLEAN:
            return 1 if raw in ('1', 'true', 'on') else 0
        return raw
    except ValueError:
        raise ValueError(f'El campo "{_field_display_name(field)}" no tiene un valor válido.')


def _present_value(field: TableField, value: Any) -> str:
    if value is None:
        return ''
    if field.field_type == TableField.FieldTypes.BOOLEAN:
        return 'Sí' if int(value or 0) else 'No'
    return str(value)


def _form_value(field: TableField, value: Any) -> Any:
    if value is None:
        return ''
    if field.field_type == TableField.FieldTypes.BOOLEAN:
        return bool(int(value))
    return value

@bp.route('/')
def index():
    """Lista todas las tablas dinámicas"""
    # Obtener todas las tablas registradas
    tables = DynamicTable.query.all()
    
    # Obtener información real de las tablas desde la base de datos
    inspector = inspect(db.engine)
    existing_tables = inspector.get_table_names()
    
    # Añadir información sobre el número real de registros
    for table in tables:
        if table.name in existing_tables:
            result = db.session.execute(text(f'SELECT COUNT(*) FROM "{table.name}"')).scalar()
            table.record_count = result
        else:
            table.record_count = 0
    
    return render_template('tables/index.html', tables=tables)

@bp.route('/create', methods=['GET', 'POST'])
def create_table():
    """Crear una nueva tabla"""
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip().lower()
        description = request.form.get('description')
        
        if not _is_valid_identifier(name):
            flash('El nombre de la tabla solo puede contener letras, números y guiones bajos y debe comenzar con una letra.', 'error')
            return redirect(url_for('tables.create_table'))

        # Verificar si ya existe la tabla
        if DynamicTable.query.filter_by(name=name).first():
            flash('Ya existe una tabla con ese nombre.', 'error')
            return redirect(url_for('tables.create_table'))
        
        table = DynamicTable(name=name, description=description)
        db.session.add(table)
        db.session.commit()

        # Añadir campo ID por defecto para nuevas tablas dinámicas
        id_field = TableField(
            table_id=table.id,
            name='id',
            field_type=TableField.FieldTypes.INTEGER,
            is_required=True,
            is_primary_key=True,
            is_auto_increment=True,
            description='Identificador único autoincremental'
        )
        db.session.add(id_field)
        db.session.commit()

        try:
            _create_physical_table(table)
        except Exception as exc:
            db.session.delete(id_field)
            db.session.delete(table)
            db.session.commit()
            flash(f'No se pudo crear la tabla física: {exc}', 'error')
            return redirect(url_for('tables.create_table'))
        
        flash('Tabla creada correctamente. Ahora puedes añadir campos.', 'success')
        return redirect(url_for('tables.edit_table', table_id=table.id))
    
    return render_template('tables/create.html')

@bp.route('/<int:table_id>/edit', methods=['GET', 'POST'])
def edit_table(table_id):
    """Editar una tabla existente y sus campos"""
    table = DynamicTable.query.get_or_404(table_id)
    
    if request.method == 'POST':
        # Actualizar descripción de la tabla
        table.description = request.form.get('description')
        db.session.commit()
        flash('Tabla actualizada correctamente.', 'success')
        return redirect(url_for('tables.index'))
    
    return render_template('tables/edit.html', table=table)

@bp.route('/<int:table_id>/fields/add', methods=['GET', 'POST'])
def add_field(table_id):
    """Añadir un campo a una tabla"""
    table = DynamicTable.query.get_or_404(table_id)
    
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip().lower()
        field_type = request.form.get('field_type')
        is_required = 'is_required' in request.form
        is_primary_key = 'is_primary_key' in request.form
        is_auto_increment = 'is_auto_increment' in request.form
        default_value = request.form.get('default_value')

        if not _is_valid_identifier(name):
            flash('El nombre del campo solo puede contener letras, números y guiones bajos y debe comenzar con una letra.', 'error')
            return redirect(url_for('tables.add_field', table_id=table_id))
        
        # Verificar si ya existe el campo en esta tabla
        if any(field.name == name for field in table.fields):
            flash('Ya existe un campo con ese nombre en esta tabla.', 'error')
            return redirect(url_for('tables.add_field', table_id=table_id))
        
        description = (request.form.get('description') or '').strip() or None

        field = TableField(
            table_id=table_id,
            name=name,
            field_type=field_type,
            is_required=is_required,
            is_primary_key=is_primary_key,
            is_auto_increment=is_auto_increment,
            default_value=default_value,
            description=description
        )
        
        db.session.add(field)
        db.session.commit()

        try:
            _add_column_to_table(table, field)
        except Exception as exc:
            db.session.delete(field)
            db.session.commit()
            flash(f'No se pudo crear el campo físico: {exc}', 'error')
            return redirect(url_for('tables.add_field', table_id=table_id))
        
        flash('Campo añadido correctamente.', 'success')
        return redirect(url_for('tables.edit_table', table_id=table_id))
    
    field_types = TableField.FieldTypes.choices()
    return render_template('tables/field_form.html', table=table, field_types=field_types, field=None)

@bp.route('/<int:table_id>/fields/<int:field_id>/edit', methods=['GET', 'POST'])
def edit_field(table_id, field_id):
    """Editar un campo existente"""
    field = TableField.query.get_or_404(field_id)
    
    if request.method == 'POST':
        field.field_type = request.form.get('field_type')
        field.is_required = 'is_required' in request.form
        field.is_primary_key = 'is_primary_key' in request.form
        field.is_auto_increment = 'is_auto_increment' in request.form
        field.default_value = request.form.get('default_value')
        field.description = (request.form.get('description') or '').strip() or None
        
        db.session.commit()
        flash('Campo actualizado correctamente.', 'success')
        return redirect(url_for('tables.edit_table', table_id=table_id))
    
    field_types = TableField.FieldTypes.choices()
    return render_template('tables/field_form.html', table=field.table, field=field, field_types=field_types)

@bp.route('/<int:table_id>/fields/<int:field_id>/delete', methods=['POST'])
def delete_field(table_id, field_id):
    """Eliminar un campo"""
    field = TableField.query.get_or_404(field_id)
    db.session.delete(field)
    db.session.commit()
    
    flash('Campo eliminado correctamente.', 'success')
    return redirect(url_for('tables.edit_table', table_id=table_id))

@bp.route('/<int:table_id>/delete', methods=['POST'])
def delete_table(table_id):
    """Eliminar una tabla"""
    table = DynamicTable.query.get_or_404(table_id)
    table_name = table.name

    engine = db.engine
    inspector = inspect(engine)

    if table_name not in inspector.get_table_names():
        # Solo eliminar el registro meta si la tabla ya no existe físicamente
        db.session.delete(table)
        db.session.commit()
        flash('Registro de tabla eliminado. La tabla física ya no existía.', 'info')
        return redirect(url_for('tables.index'))

    # Verificar dependencias referenciales
    fk_constraints = inspector.get_foreign_keys(table_name)
    if fk_constraints:
        flash('No se puede eliminar la tabla porque tiene claves foráneas definidas.', 'error')
        return redirect(url_for('tables.edit_table', table_id=table_id))

    # Revisar si otras tablas referencian a esta tabla
    referencing = []
    for other_table in inspector.get_table_names():
        if other_table == table_name:
            continue
        foreign_keys = inspector.get_foreign_keys(other_table)
        for fk in foreign_keys:
            if fk.get('referred_table') == table_name:
                referencing.append(other_table)
                break

    if referencing:
        ref_list = ', '.join(referencing)
        flash(f'No se puede eliminar la tabla porque está referenciada por: {ref_list}.', 'error')
        return redirect(url_for('tables.edit_table', table_id=table_id))

    # Comprobar registros existentes
    count = db.session.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar()
    if count and count > 0:
        flash(f'La tabla contiene {count} registros. Vacíala antes de eliminarla.', 'error')
        return redirect(url_for('tables.edit_table', table_id=table_id))

    try:
        with engine.connect() as conn:
            conn.execute(text(f'DROP TABLE "{table_name}"'))
            conn.commit()
    except Exception as exc:
        flash(f'No se pudo eliminar la tabla física: {exc}', 'error')
        return redirect(url_for('tables.edit_table', table_id=table_id))

    db.session.delete(table)
    db.session.commit()
    flash(f'Tabla "{table_name}" eliminada correctamente.', 'success')
    return redirect(url_for('tables.index'))


@bp.route('/<int:table_id>/records')
def manage_records(table_id):
    table = DynamicTable.query.get_or_404(table_id)
    fields = _collect_table_fields(table)

    if len(fields) <= 1:
        flash('Añade campos a la tabla antes de gestionar sus registros.', 'warning')
        return redirect(url_for('tables.edit_table', table_id=table_id))

    select_order = ['id'] + [f.name for f in fields]
    seen = set()
    columns = []
    for name in select_order:
        if name and name not in seen:
            columns.append(f'"{name}"')
            seen.add(name)
    field_names = ', '.join(columns)
    try:
        result = db.session.execute(text(f'SELECT {field_names} FROM "{table.name}" ORDER BY "id" DESC')).mappings().all()
    except Exception as exc:
        flash(f'No se pudieron obtener los registros: {exc}', 'error')
        return redirect(url_for('tables.edit_table', table_id=table_id))

    rows = []
    for item in result:
        row = {'__record_id': item.get('id')}
        for field in fields:
            row[field.name] = _present_value(field, item.get(field.name))
        rows.append(row)

    return render_template('tables/records_list.html', table=table, fields=fields, rows=rows)


@bp.route('/<int:table_id>/records/delete-all', methods=['POST'])
def delete_all_records(table_id: int):
    """Elimina todos los registros de la tabla dinámica seleccionada."""
    table = DynamicTable.query.get_or_404(table_id)

    try:
        with db.engine.begin() as connection:
            connection.execute(text(f'DELETE FROM "{table.name}"'))
        flash('Se eliminaron todos los registros de la tabla seleccionada.', 'success')
    except Exception as exc:
        flash(f'No se pudo eliminar el contenido de la tabla: {exc}', 'error')

    return redirect(url_for('tables.manage_records', table_id=table_id))


@bp.route('/open-folder', methods=['POST'])
def open_parent_folder():
    """Abre el explorador de archivos apuntando a la ruta indicada."""
    payload = request.get_json(silent=True) or {}
    raw_path = (payload.get('path') or '').strip()

    if not raw_path:
        return jsonify({'error': 'No se proporcionó la ruta a abrir.'}), 400

    path_obj = Path(raw_path)
    if not path_obj.exists():
        return jsonify({'error': 'La ruta solicitada no existe.'}), 404

    target = path_obj if path_obj.is_dir() else path_obj.parent

    try:
        if os.name == 'nt':
            os.startfile(str(target))  # type: ignore[attr-defined]
        else:
            raise RuntimeError('Solo disponible en Windows.')
    except Exception as exc:
        return jsonify({'error': f'No se pudo abrir el explorador: {exc}'}), 500

    return jsonify({'status': 'ok'})


@bp.route('/<int:table_id>/records/add', methods=['GET', 'POST'])
def add_record(table_id):
    table = DynamicTable.query.get_or_404(table_id)
    fields = [f for f in _collect_table_fields(table) if not f.is_auto_increment]

    if not fields:
        flash('No hay campos disponibles para crear registros.', 'warning')
        return redirect(url_for('tables.manage_records', table_id=table_id))

    form_data: Dict[str, Any] = {}
    errors: List[str] = []

    if request.method == 'POST':
        for field in fields:
            raw_value = request.form.get(field.name)
            if field.field_type == TableField.FieldTypes.BOOLEAN:
                raw_value = '1' if request.form.get(field.name) else '0'

            if field.is_required and (raw_value is None or str(raw_value).strip() == ''):
                errors.append(f'El campo "{_field_display_name(field)}" es obligatorio.')
                form_data[field.name] = raw_value
                continue

            try:
                value = _to_python_value(field, raw_value)
            except ValueError as exc:
                errors.append(str(exc))
                form_data[field.name] = raw_value
                continue

            form_data[field.name] = raw_value if field.field_type != TableField.FieldTypes.BOOLEAN else ('1' if value else '0')

        if not errors:
            payload = {
                field.name: _to_python_value(field, form_data[field.name])
                for field in fields
            }
            columns = ', '.join(f'"{name}"' for name in payload.keys())
            placeholders = ', '.join(f':{name}' for name in payload.keys())
            stmt = text(f'INSERT INTO "{table.name}" ({columns}) VALUES ({placeholders})')
            try:
                with db.engine.begin() as connection:
                    connection.execute(stmt, payload)
                flash('Registro creado correctamente.', 'success')
                return redirect(url_for('tables.manage_records', table_id=table_id))
            except Exception as exc:
                errors.append(f'No se pudo crear el registro: {exc}')

    else:
        for field in fields:
            if field.field_type == TableField.FieldTypes.BOOLEAN:
                form_data[field.name] = '0'
            else:
                form_data[field.name] = ''

    return render_template('tables/record_form.html', table=table, fields=fields, form_data=form_data, errors=errors, mode='create')


@bp.route('/<int:table_id>/records/<int:record_id>/edit', methods=['GET', 'POST'])
def edit_record(table_id, record_id):
    table = DynamicTable.query.get_or_404(table_id)
    fields = [f for f in _collect_table_fields(table) if not f.is_auto_increment]

    if not fields:
        flash('No hay campos disponibles para editar registros.', 'warning')
        return redirect(url_for('tables.manage_records', table_id=table_id))

    select_fields = ', '.join(['"id"'] + [f'"{field.name}"' for field in fields])
    stmt = text(f'SELECT {select_fields} FROM "{table.name}" WHERE "id" = :id')
    record = db.session.execute(stmt, {'id': record_id}).mappings().first()
    if not record:
        flash('Registro no encontrado.', 'error')
        return redirect(url_for('tables.manage_records', table_id=table_id))

    form_data: Dict[str, Any] = {
        field.name: '1' if _form_value(field, record.get(field.name)) else '0'
        if field.field_type == TableField.FieldTypes.BOOLEAN
        else record.get(field.name, '')
        for field in fields
    }

    errors: List[str] = []

    if request.method == 'POST':
        for field in fields:
            raw_value = request.form.get(field.name)
            if field.field_type == TableField.FieldTypes.BOOLEAN:
                raw_value = '1' if request.form.get(field.name) else '0'

            if field.is_required and (raw_value is None or str(raw_value).strip() == ''):
                errors.append(f'El campo "{field.name}" es obligatorio.')
                form_data[field.name] = raw_value
                continue

            try:
                value = _to_python_value(field, raw_value)
            except ValueError as exc:
                errors.append(str(exc))
                form_data[field.name] = raw_value
                continue

            form_data[field.name] = raw_value if field.field_type != TableField.FieldTypes.BOOLEAN else ('1' if value else '0')

        if not errors:
            payload = {
                field.name: _to_python_value(field, form_data[field.name])
                for field in fields
            }
            payload['id'] = record_id
            set_clause = ', '.join([f'"{name}" = :{name}' for name in payload if name != 'id'])
            stmt = text(f'UPDATE "{table.name}" SET {set_clause} WHERE "id" = :id')
            try:
                with db.engine.begin() as connection:
                    connection.execute(stmt, payload)
                flash('Registro actualizado correctamente.', 'success')
                return redirect(url_for('tables.manage_records', table_id=table_id))
            except Exception as exc:
                errors.append(f'No se pudo actualizar el registro: {exc}')

    return render_template('tables/record_form.html', table=table, fields=fields, form_data=form_data, errors=errors, mode='edit', record_id=record_id)


@bp.route('/<int:table_id>/records/<int:record_id>/delete', methods=['POST'])
def delete_record(table_id, record_id):
    table = DynamicTable.query.get_or_404(table_id)
    stmt = text(f'DELETE FROM "{table.name}" WHERE "id" = :id')
    try:
        with db.engine.begin() as connection:
            result = connection.execute(stmt, {'id': record_id})
        if result.rowcount:
            flash('Registro eliminado correctamente.', 'success')
        else:
            flash('No se encontró el registro a eliminar.', 'warning')
    except Exception as exc:
        flash(f'No se pudo eliminar el registro: {exc}', 'error')
    return redirect(url_for('tables.manage_records', table_id=table_id))