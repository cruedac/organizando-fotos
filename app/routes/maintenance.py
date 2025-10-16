from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from app.models.database import db, FileType

bp = Blueprint('maintenance', __name__, url_prefix='/maintenance')

@bp.route('/')
def index():
    """Página principal de mantenimiento"""
    return render_template('maintenance/index.html')

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
        flash('Tipo de archivo actualizado correctamente.', 'success')
        return redirect(url_for('maintenance.file_types'))
    
    return render_template('maintenance/file_type_form.html', file_type=file_type)

@bp.route('/file-types/<int:id>/delete', methods=['POST'])
def delete_file_type(id):
    """Eliminar tipo de archivo"""
    file_type = FileType.query.get_or_404(id)
    db.session.delete(file_type)
    db.session.commit()
    flash('Tipo de archivo eliminado correctamente.', 'success')
    return redirect(url_for('maintenance.file_types'))