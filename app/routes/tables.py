from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from app.models.database import db, DynamicTable, TableField
from sqlalchemy import inspect, text
from sqlalchemy.engine import reflection

bp = Blueprint('tables', __name__, url_prefix='/tables')

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
            result = db.session.execute(text(f'SELECT COUNT(*) FROM {table.name}')).scalar()
            table.record_count = result
        else:
            table.record_count = 0
    
    return render_template('tables/index.html', tables=tables)

@bp.route('/create', methods=['GET', 'POST'])
def create_table():
    """Crear una nueva tabla"""
    if request.method == 'POST':
        name = request.form.get('name').lower()
        description = request.form.get('description')
        
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
            is_auto_increment=True
        )
        db.session.add(id_field)
        db.session.commit()
        
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
        name = request.form.get('name').lower()
        field_type = request.form.get('field_type')
        is_required = 'is_required' in request.form
        is_primary_key = 'is_primary_key' in request.form
        is_auto_increment = 'is_auto_increment' in request.form
        default_value = request.form.get('default_value')
        
        # Verificar si ya existe el campo en esta tabla
        if any(field.name == name for field in table.fields):
            flash('Ya existe un campo con ese nombre en esta tabla.', 'error')
            return redirect(url_for('tables.add_field', table_id=table_id))
        
        field = TableField(
            table_id=table_id,
            name=name,
            field_type=field_type,
            is_required=is_required,
            is_primary_key=is_primary_key,
            is_auto_increment=is_auto_increment,
            default_value=default_value
        )
        
        db.session.add(field)
        db.session.commit()
        
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