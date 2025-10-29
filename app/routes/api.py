from flask import Blueprint, jsonify, request
from app.services.file_scanner import scan_for_media_recursive
from app.services.file_type_cache import get_allowed_extensions_cached

bp = Blueprint('api', __name__)

@bp.route('/scan', methods=['POST'])
def scan_folder():
    """Endpoint para escanear una carpeta y obtener estadísticas de archivos"""
    data = request.get_json()
    
    if not data or 'folder_path' not in data:
        return jsonify({'error': 'No se proporcionó una ruta de carpeta'}), 400
        
    folder_path = data['folder_path']
    
    # Obtener extensiones cacheadas (evita query a la DB en cada request)
    extensions = get_allowed_extensions_cached()
    
    try:
        result = scan_for_media_recursive(
            folder_path,
            image_extensions=set(extensions['image']),
            video_extensions=set(extensions['video']),
            audio_extensions=set(extensions['audio'])
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500