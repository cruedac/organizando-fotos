from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for
from app.models.photo_scan_summary import PhotoScanSummary
from app import db
from datetime import datetime

bp = Blueprint('photos', __name__, url_prefix='/photos')

@bp.route('/')
def index():
    """Página principal de fotos"""
    return render_template('photos/index.html')

@bp.route('/hub')
def hub():
    """Hub central de Fotos con todas las opciones disponibles"""
    return render_template('photos/hub.html')

@bp.route('/scanner')
def scanner():
    """Página de scanner de archivos multimedia"""
    return render_template('photos/scanner.html')

@bp.route('/scan-summary')
def scan_summary():
    """Lista de resúmenes de escaneo"""
    summaries = PhotoScanSummary.query.order_by(PhotoScanSummary.scan_date.desc()).all()
    return render_template('photos/scan_summary.html', summaries=summaries)

@bp.route('/scan-summary/<int:id>/edit', methods=['GET', 'POST'])
def edit_scan_summary(id):
    """Editar un resumen de escaneo"""
    summary = PhotoScanSummary.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            summary.path = request.form.get('path', summary.path)
            summary.directories_count = int(request.form.get('directories_count', summary.directories_count))
            summary.num_images = int(request.form.get('num_images', summary.num_images))
            summary.num_videos = int(request.form.get('num_videos', summary.num_videos))
            summary.year = int(request.form.get('year')) if request.form.get('year') else summary.year
            summary.month_number = int(request.form.get('month_number')) if request.form.get('month_number') else summary.month_number
            summary.month_text = request.form.get('month_text', summary.month_text)
            summary.total_size = int(request.form.get('total_size', summary.total_size))
            summary.directory = request.form.get('directory', summary.directory)
            summary.total_files = int(request.form.get('total_files', summary.total_files))
            summary.processed_files = int(request.form.get('processed_files', summary.processed_files))
            summary.failed_files = int(request.form.get('failed_files', summary.failed_files))
            summary.status = request.form.get('status', summary.status)
            summary.details = request.form.get('details', summary.details)
            
            db.session.commit()
            return redirect(url_for('photos.scan_summary'))
        except Exception as e:
            current_app.logger.error(f"Error updating scan summary: {str(e)}")
            return render_template('photos/edit_scan_summary.html', summary=summary, error=str(e))
    
    return render_template('photos/edit_scan_summary.html', summary=summary)

@bp.route('/api/scan-summary', methods=['GET'])
def get_scan_summaries():
    """API endpoint para obtener resúmenes de escaneo"""
    summaries = PhotoScanSummary.query.order_by(PhotoScanSummary.scan_date.desc()).all()
    return jsonify([summary.to_dict() for summary in summaries])

@bp.route('/api/scan-summary', methods=['POST'])
def create_scan_summary():
    """API endpoint para crear un nuevo resumen de escaneo"""
    data = request.json
    try:
        summary = PhotoScanSummary(
            path=data.get('path', ''),
            directories_count=data.get('directories_count', 0),
            num_images=data.get('num_images', 0),
            num_videos=data.get('num_videos', 0),
            year=data.get('year'),
            month_number=data.get('month_number'),
            month_text=data.get('month_text', ''),
            total_size=data.get('total_size', 0),
            directory=data.get('directory', ''),
            total_files=data.get('total_files', 0),
            processed_files=data.get('processed_files', 0),
            failed_files=data.get('failed_files', 0),
            status=data.get('status', 'pending'),
            details=data.get('details', '')
        )
        db.session.add(summary)
        db.session.commit()
        return jsonify(summary.to_dict()), 201
    except Exception as e:
        current_app.logger.error(f"Error creating scan summary: {str(e)}")
        return jsonify({'error': str(e)}), 400

@bp.route('/api/scan-summary/<int:id>', methods=['PUT'])
def update_scan_summary(id):
    """API endpoint para actualizar un resumen de escaneo"""
    summary = PhotoScanSummary.query.get_or_404(id)
    data = request.json
    try:
        if 'path' in data:
            summary.path = data['path']
        if 'directories_count' in data:
            summary.directories_count = data['directories_count']
        if 'num_images' in data:
            summary.num_images = data['num_images']
        if 'num_videos' in data:
            summary.num_videos = data['num_videos']
        if 'directory' in data:
            summary.directory = data['directory']
        if 'total_files' in data:
            summary.total_files = data['total_files']
        if 'processed_files' in data:
            summary.processed_files = data['processed_files']
        if 'failed_files' in data:
            summary.failed_files = data['failed_files']
        if 'status' in data:
            summary.status = data['status']
        if 'details' in data:
            summary.details = data['details']
        
        db.session.commit()
        return jsonify(summary.to_dict())
    except Exception as e:
        current_app.logger.error(f"Error updating scan summary: {str(e)}")
        return jsonify({'error': str(e)}), 400

@bp.route('/api/scan-summary/<int:id>', methods=['DELETE'])
def delete_scan_summary(id):
    """API endpoint para eliminar un resumen de escaneo"""
    summary = PhotoScanSummary.query.get_or_404(id)
    try:
        db.session.delete(summary)
        db.session.commit()
        return '', 204
    except Exception as e:
        current_app.logger.error(f"Error deleting scan summary: {str(e)}")
        return jsonify({'error': str(e)}), 400