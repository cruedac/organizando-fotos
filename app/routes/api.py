from flask import Blueprint, jsonify, request
from app.services.file_scanner import scan_for_media_recursive
from app.models.database import FileType

bp = Blueprint('api', __name__)

@bp.route('/scan', methods=['POST'])
def scan_folder():
    """Endpoint para escanear una carpeta y obtener estadísticas de archivos"""
    data = request.get_json()
    
    if not data or 'folder_path' not in data:
        return jsonify({'error': 'No se proporcionó una ruta de carpeta'}), 400
        
    folder_path = data['folder_path']
    
    # Obtener extensiones de la base de datos
    extensions = {
        'image': {ft.extension for ft in FileType.query.filter_by(type='image').all()},
        'video': {ft.extension for ft in FileType.query.filter_by(type='video').all()},
        'audio': {ft.extension for ft in FileType.query.filter_by(type='audio').all()}
    }
    
    try:
        result = scan_for_media_recursive(
            folder_path,
            image_extensions=extensions['image'],
            video_extensions=extensions['video'],
            audio_extensions=extensions['audio']
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500