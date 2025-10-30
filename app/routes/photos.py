from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for
from app.models.photo_scan_summary import PhotoScanSummary
from app.models.database import FileType
from app.services.file_scanner import scan_for_media_recursive
from app import db
from datetime import datetime
from pathlib import Path

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

@bp.route('/api/browse-folders', methods=['POST'])
def browse_folders():
    """API endpoint para explorar carpetas del sistema"""
    import os
    from pathlib import Path
    
    data = request.json
    current_path = data.get('path', str(Path.home()))
    
    try:
        path_obj = Path(current_path)
        
        # Validar que el path existe y es un directorio
        if not path_obj.exists():
            return jsonify({'error': 'La ruta no existe'}), 404
        
        if not path_obj.is_dir():
            return jsonify({'error': 'La ruta no es un directorio'}), 400
        
        # Obtener directorios
        directories = []
        try:
            for item in sorted(path_obj.iterdir()):
                if item.is_dir() and not item.name.startswith('.'):
                    try:
                        # Verificar si tenemos permisos de lectura
                        item.stat()
                        directories.append({
                            'name': item.name,
                            'path': str(item),
                            'parent': str(item.parent)
                        })
                    except PermissionError:
                        # Saltar directorios sin permisos
                        pass
        except PermissionError:
            return jsonify({'error': 'Sin permisos para acceder a esta carpeta'}), 403
        
        # Información del directorio actual
        parent_path = str(path_obj.parent) if path_obj.parent != path_obj else None
        
        return jsonify({
            'current_path': str(path_obj),
            'parent_path': parent_path,
            'directories': directories
        })
        
    except Exception as e:
        current_app.logger.error(f"Error browsing folders: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/get-home-directory', methods=['GET'])
def get_home_directory():
    """Obtiene el directorio home del usuario"""
    from pathlib import Path
    return jsonify({'path': str(Path.home())})

@bp.route('/api/get-drives', methods=['GET'])
def get_drives():
    """Obtiene todas las unidades/drives disponibles en el sistema"""
    import os
    import platform
    from pathlib import Path
    
    drives = []
    system = platform.system()
    
    try:
        if system == 'Windows':
            # En Windows, listar todas las unidades de A: a Z:
            import string
            for letter in string.ascii_uppercase:
                drive = f'{letter}:\\'
                if os.path.exists(drive):
                    try:
                        # Intentar obtener información de la unidad
                        total, used, free = 0, 0, 0
                        try:
                            import shutil
                            usage = shutil.disk_usage(drive)
                            total = usage.total
                            used = usage.used
                            free = usage.free
                        except:
                            pass
                        
                        drives.append({
                            'name': f'Unidad {letter}:',
                            'path': drive,
                            'type': 'drive',
                            'total': total,
                            'used': used,
                            'free': free
                        })
                    except:
                        pass
        else:
            # En Linux/Mac, mostrar puntos de montaje comunes
            common_mounts = [
                ('/', 'Raíz del Sistema'),
                (str(Path.home()), 'Carpeta Personal'),
                ('/media', 'Medios Extraíbles'),
                ('/mnt', 'Puntos de Montaje'),
            ]
            
            for mount_path, name in common_mounts:
                if os.path.exists(mount_path):
                    try:
                        # Verificar si es accesible
                        os.listdir(mount_path)
                        drives.append({
                            'name': name,
                            'path': mount_path,
                            'type': 'mount'
                        })
                    except PermissionError:
                        # Añadir aunque no tenga permisos, el usuario puede necesitarlo
                        drives.append({
                            'name': f'{name} (sin permisos)',
                            'path': mount_path,
                            'type': 'mount'
                        })
            
            # Buscar unidades montadas en /media y /mnt
            for base_path in ['/media', '/mnt']:
                if os.path.exists(base_path):
                    try:
                        for item in os.listdir(base_path):
                            item_path = os.path.join(base_path, item)
                            if os.path.isdir(item_path):
                                drives.append({
                                    'name': item,
                                    'path': item_path,
                                    'type': 'external'
                                })
                    except:
                        pass
        
        return jsonify({'drives': drives})
        
    except Exception as e:
        current_app.logger.error(f"Error getting drives: {str(e)}")
        return jsonify({'error': str(e), 'drives': []}), 500

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

@bp.route('/api/scan-folder', methods=['POST'])
def scan_folder():
    """API endpoint para escanear una carpeta y devolver resultados"""
    data = request.json
    folder_path = data.get('folder_path')
    scan_subdirs = data.get('scan_subdirs', True)
    file_types = data.get('file_types', ['images', 'videos', 'audio'])
    
    if not folder_path:
        return jsonify({'error': 'Se requiere folder_path'}), 400
    
    path_obj = Path(folder_path)
    if not path_obj.exists():
        return jsonify({'error': 'La ruta no existe'}), 404
    
    if not path_obj.is_dir():
        return jsonify({'error': 'La ruta no es un directorio'}), 400
    
    try:
        # Obtener extensiones de la base de datos
        image_extensions = set()
        video_extensions = set()
        audio_extensions = set()
        
        if 'images' in file_types:
            image_types = FileType.query.filter_by(type='image').all()
            image_extensions = {ft.extension for ft in image_types}
        
        if 'videos' in file_types:
            video_types = FileType.query.filter_by(type='video').all()
            video_extensions = {ft.extension for ft in video_types}
        
        if 'audio' in file_types:
            audio_types = FileType.query.filter_by(type='audio').all()
            audio_extensions = {ft.extension for ft in audio_types}
        
        # Ejecutar escaneo
        scan_results = scan_for_media_recursive(
            folder_path=str(path_obj),
            image_extensions=image_extensions,
            video_extensions=video_extensions,
            audio_extensions=audio_extensions,
            scan_subdirs=scan_subdirs
        )
        
        # Calcular totales
        totals = scan_results.get('totals', {})
        total_files = sum(totals.values())
        
        return jsonify({
            'status': 'ok',
            'folder_path': str(path_obj),
            'totals': totals,
            'by_extension': scan_results.get('by_extension', {}),
            'total_files': total_files,
            'total_size': scan_results.get('total_size', 0),
            'directories': scan_results.get('directories', [])
        })
    
    except Exception as e:
        current_app.logger.error(f"Error scanning folder: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/save-scan-summary', methods=['POST'])
def save_scan_summary():
    """API endpoint para guardar el resumen de un escaneo en la base de datos"""
    data = request.json
    
    folder_path = data.get('folder_path')
    totals = data.get('totals', {})
    total_files = data.get('total_files', 0)
    total_size = data.get('total_size', 0)
    
    if not folder_path:
        return jsonify({'error': 'Se requiere folder_path'}), 400
    
    try:
        # Crear el resumen
        summary = PhotoScanSummary(
            path=folder_path,
            directory=folder_path,
            directories_count=1,  # Por ahora, podemos mejorar esto después
            num_images=totals.get('image', 0),
            num_videos=totals.get('video', 0),
            total_files=total_files,
            total_size=total_size,
            processed_files=total_files,
            failed_files=0,
            status='completed',
            scan_date=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        
        db.session.add(summary)
        db.session.commit()
        
        current_app.logger.info(f'Resumen de escaneo guardado para: {folder_path}')
        
        return jsonify({
            'status': 'ok',
            'summary_id': summary.id,
            'message': 'Resumen guardado correctamente'
        }), 201
    
    except Exception as e:
        current_app.logger.error(f"Error saving scan summary: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
