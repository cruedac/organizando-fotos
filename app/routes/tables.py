from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from app.models.database import db, DynamicTable, TableField
from sqlalchemy import text

bp = Blueprint('tables', __name__, url_prefix='/tables')

@bp.route('/')
def index():
    """Lista todas las tablas dinámicas"""
    tables = DynamicTable.query.all()
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
    
    return render_template('tables/field_form.html', table=table)

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
    
    return render_template('tables/field_form.html', table=field.table, field=field)

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
    db.session.delete(table)
    db.session.commit()
    
    flash('Tabla eliminada correctamente.', 'success')
    return redirect(url_for('tables.index'))