from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for, Response
from app.models.database import PhotoScanSummary, FileType
from app.services.file_scanner import scan_for_media_recursive
from app import db
from datetime import datetime
from pathlib import Path
import threading
import queue
import time
import json

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


# Variable global para almacenar el estado del escaneo actual
_scan_progress = {
    'queue': None,
    'active': False,
    'results': None
}


@bp.route('/api/scan-progress')
def scan_progress():
    """SSE endpoint para progreso en tiempo real del escaneo"""
    def generate():
        # Enviar heartbeat inicial
        yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
        
        if not _scan_progress['active']:
            yield f"data: {json.dumps({'type': 'error', 'message': 'No hay escaneo activo'})}\n\n"
            return
        
        q = _scan_progress['queue']
        last_heartbeat = time.time()
        
        while True:
            try:
                # Enviar heartbeat cada 5 segundos para mantener conexión viva
                if time.time() - last_heartbeat > 5:
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                    last_heartbeat = time.time()
                
                # Intentar obtener mensaje de la cola (timeout 1 segundo)
                try:
                    message = q.get(timeout=1)
                except queue.Empty:
                    continue
                
                yield f"data: {json.dumps(message)}\n\n"
                
                # Si es mensaje de finalización, terminar
                if message.get('type') in ['complete', 'error']:
                    break
                    
            except GeneratorExit:
                break
    
    return Response(generate(), mimetype='text/event-stream')


@bp.route('/api/scan-folder-async', methods=['POST'])
def scan_folder_async():
    """Inicia un escaneo asíncrono con progreso en tiempo real"""
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
    
    # Verificar si ya hay un escaneo activo
    if _scan_progress['active']:
        return jsonify({'error': 'Ya hay un escaneo en progreso'}), 409
    
    # Crear nueva cola para este escaneo
    _scan_progress['queue'] = queue.Queue()
    _scan_progress['active'] = True
    _scan_progress['results'] = None
    
    # Función para ejecutar el escaneo en thread separado
    def run_scan():
        # IMPORTANTE: Usar contexto de aplicación Flask para acceso a DB
        with current_app.app_context():
            try:
                # Enviar mensaje de inicio
                _scan_progress['queue'].put({
                    'type': 'start',
                    'folder_path': str(path_obj),
                    'scan_subdirs': scan_subdirs
                })
                
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
                
                # Callback para actualizar progreso
                start_time = time.time()
                def progress_callback(totals):
                    elapsed = time.time() - start_time
                    _scan_progress['queue'].put({
                        'type': 'progress',
                        'totals': totals,
                        'elapsed_seconds': int(elapsed)
                    })
                
                # Ejecutar escaneo con callback
                scan_results = scan_for_media_recursive(
                    folder_path=str(path_obj),
                    image_extensions=image_extensions,
                    video_extensions=video_extensions,
                    audio_extensions=audio_extensions,
                    scan_subdirs=scan_subdirs,
                    progress_callback=progress_callback
                )
                
                # Calcular totales
                totals = scan_results.get('totals', {})
                total_files = sum(totals.values())
                
                # Guardar resultados
                _scan_progress['results'] = {
                    'status': 'ok',
                    'folder_path': str(path_obj),
                    'totals': totals,
                    'by_extension': scan_results.get('by_extension', {}),
                    'total_files': total_files,
                    'total_size': scan_results.get('total_size', 0),
                    'directories': scan_results.get('directories', [])
                }
                
                # Enviar mensaje de finalización
                _scan_progress['queue'].put({
                    'type': 'complete',
                    'results': _scan_progress['results']
                })
                
            except Exception as e:
                current_app.logger.error(f"Error scanning folder: {str(e)}")
                import traceback
                current_app.logger.error(traceback.format_exc())
                _scan_progress['queue'].put({
                    'type': 'error',
                    'error': str(e)
                })
            finally:
                _scan_progress['active'] = False
    
    # Iniciar thread de escaneo
    scan_thread = threading.Thread(target=run_scan)
    scan_thread.daemon = True
    scan_thread.start()
    
    return jsonify({
        'status': 'started',
        'message': 'Escaneo iniciado. Conecta a /api/scan-progress para recibir actualizaciones'
    }), 202


@bp.route('/api/scan-results', methods=['GET'])
def get_scan_results():
    """Obtiene los resultados del último escaneo completado"""
    if _scan_progress['results']:
        return jsonify(_scan_progress['results'])
    else:
        return jsonify({'error': 'No hay resultados disponibles'}), 404


@bp.route('/api/save-scan-summary', methods=['POST'])
def save_scan_summary():
    """API endpoint para guardar el resumen de un escaneo en la base de datos"""
    data = request.json
    
    folder_path = data.get('folder_path')
    totals = data.get('totals', {})
    by_extension = data.get('by_extension', {})
    total_files = data.get('total_files', 0)
    total_size = data.get('total_size', 0)
    
    if not folder_path:
        return jsonify({'error': 'Se requiere folder_path'}), 400
    
    try:
        # Crear lista de tipos de archivos encontrados
        file_types_found = []
        for ext, count in by_extension.items():
            if count > 0:
                file_types_found.append({
                    'extension': ext,
                    'count': count
                })
        
        # Crear el resumen
        summary = PhotoScanSummary(
            path=folder_path,
            directory=folder_path,
            directories_count=1,  # Por ahora, podemos mejorar esto después
            num_images=totals.get('image', 0),
            num_videos=totals.get('video', 0),
            num_audio=totals.get('audio', 0),
            num_other=totals.get('other', 0),
            total_files=total_files,
            total_size=total_size,
            processed_files=total_files,
            failed_files=0,
            status='completed',
            scan_date=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        
        # Asignar tipos de archivos encontrados
        summary.file_types_list = file_types_found
        
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
