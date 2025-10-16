from flask import Blueprint, render_template, request, jsonify, current_app
from app.services.file_scanner import scan_for_media_recursive
from app.models.database import FileType, db
import os

bp = Blueprint('main', __name__)

import string
from pathlib import Path

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/list-drives', methods=['GET'])
def list_drives():
    """Lista todas las unidades disponibles en Windows"""
    drives = []
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            try:
                # Intentar obtener el nombre del volumen si está disponible
                volume_name = ""
                drives.append({
                    'path': drive,
                    'name': volume_name if volume_name else drive,
                    'type': 'drive'
                })
            except:
                drives.append({
                    'path': drive,
                    'name': drive,
                    'type': 'drive'
                })
    return jsonify(drives)

@bp.route('/list-directory', methods=['GET'])
def list_directory():
    """Lista el contenido de un directorio"""
    path = request.args.get('path', '')
    if not path:
        return jsonify({'error': 'No se proporcionó una ruta'}), 400
    
    try:
        path = os.path.normpath(path)
        if not os.path.exists(path):
            return jsonify({'error': 'La ruta no existe'}), 404
        
        items = []
        for item in Path(path).iterdir():
            try:
                if item.is_dir():
                    items.append({
                        'path': str(item),
                        'name': item.name,
                        'type': 'directory'
                    })
            except PermissionError:
                continue
        
        # Ordenar por nombre
        items.sort(key=lambda x: x['name'].lower())
        return jsonify(items)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/scan', methods=['POST'])
def scan_directory():
    """Escanea un directorio en busca de archivos multimedia"""
    data = request.get_json()
    folder_path = data.get('folder_path')
    scan_subdirs = data.get('scan_subdirs', True)
    
    # Normalizar la ruta para manejar correctamente las barras en Windows
    folder_path = os.path.normpath(folder_path)
    
    # Validar que la ruta existe y es accesible
    try:
        if not folder_path or not os.path.exists(folder_path):
            return jsonify({
                'error': 'El directorio no existe'
            }), 400
        if not os.path.isdir(folder_path):
            return jsonify({
                'error': 'La ruta especificada no es un directorio'
            }), 400
        if not os.access(folder_path, os.R_OK):
            return jsonify({
                'error': 'No hay permisos de lectura para el directorio'
            }), 403
    except Exception as e:
        return jsonify({
            'error': f'Error al validar el directorio: {str(e)}'
        }), 400
        
    # Obtener las extensiones desde la base de datos
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
            audio_extensions=extensions['audio'],
            scan_subdirs=scan_subdirs
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'error': f'Error al escanear el directorio: {str(e)}'
        }), 500