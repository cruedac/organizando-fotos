import mimetypes
import os
import string
import tempfile
from datetime import datetime
from pathlib import Path

from flask import Blueprint, render_template, request, jsonify, current_app
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from werkzeug.utils import secure_filename

from app.models.database import FileType, db
from app.services.file_scanner import scan_for_media_recursive

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/fotos')
def photos():
    return render_template('photos/analysis.html')


@bp.route('/utilidades')
def utilities():
    return render_template('utilities/index.html')


def _format_size(num_bytes: int) -> str:
    units = ['bytes', 'KB', 'MB', 'GB', 'TB']
    size = float(num_bytes)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.2f} {unit}" if unit != 'bytes' else f"{int(size)} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


def _ratio_to_float(value):
    try:
        return float(value[0]) / float(value[1]) if value[1] else None
    except Exception:
        return None


def _convert_to_degrees(value):
    if not value or len(value) < 3:
        return None
    degrees = _ratio_to_float(value[0])
    minutes = _ratio_to_float(value[1])
    seconds = _ratio_to_float(value[2])
    if None in (degrees, minutes, seconds):
        return None
    return degrees + (minutes / 60.0) + (seconds / 3600.0)


def _sanitize_exif_value(value):
    if isinstance(value, bytes):
        try:
            return value.decode('utf-8', errors='replace')
        except Exception:
            return value.hex()
    if isinstance(value, (list, tuple)):
        return ', '.join(str(item) for item in value)
    return value


def _extract_image_metadata(image_path: Path):
    exif_clean = {}
    gps_payload = None

    with Image.open(image_path) as img:
        raw = getattr(img, '_getexif', lambda: None)()

    if not raw:
        return {}, None

    gps_raw = {}
    for tag, value in raw.items():
        tag_name = TAGS.get(tag, tag)
        if tag_name == 'GPSInfo':
            for key, gps_value in value.items():
                gps_tag = GPSTAGS.get(key, key)
                gps_raw[gps_tag] = gps_value
        else:
            exif_clean[tag_name] = _sanitize_exif_value(value)

    if gps_raw:
        lat = gps_raw.get('GPSLatitude')
        lat_ref = gps_raw.get('GPSLatitudeRef')
        lon = gps_raw.get('GPSLongitude')
        lon_ref = gps_raw.get('GPSLongitudeRef')
        alt = gps_raw.get('GPSAltitude')
        alt_ref = gps_raw.get('GPSAltitudeRef')

        lat_deg = _convert_to_degrees(lat) if lat else None
        lon_deg = _convert_to_degrees(lon) if lon else None

        if lat_deg is not None and lat_ref in ('S', 'N'):
            lat_deg = lat_deg if lat_ref == 'N' else -lat_deg
        if lon_deg is not None and lon_ref in ('W', 'E'):
            lon_deg = lon_deg if lon_ref == 'E' else -lon_deg

        gps_payload = {
            'latitude': lat_deg,
            'latitude_ref': lat_ref,
            'longitude': lon_deg,
            'longitude_ref': lon_ref,
            'altitude': _ratio_to_float(alt) if alt else None,
            'altitude_ref': alt_ref,
            'raw': {key: _sanitize_exif_value(val) for key, val in gps_raw.items()}
        }

        if lat_deg is not None and lon_deg is not None:
            gps_payload['map_url'] = f"https://www.google.com/maps?q={lat_deg},{lon_deg}"

    ordered_exif = dict(sorted(exif_clean.items()))
    return ordered_exif, gps_payload


def _format_duration(seconds):
    if seconds is None:
        return None
    try:
        total_seconds = int(round(float(seconds)))
    except Exception:
        return str(seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def _extract_mutagen_metadata(media_path: Path):
    try:
        import mutagen
    except ImportError:
        return None, None, 'Instala la librería "mutagen" para obtener metadatos embebidos de audio y video.'

    try:
        media = mutagen.File(str(media_path), easy=True)
    except Exception as exc:
        return None, None, f'No se pudieron leer metadatos embebidos: {exc}'

    if media is None:
        return None, None, 'El archivo no contiene etiquetas legibles por mutagen.'

    tags = {}
    for key, value in media.items():
        if isinstance(value, (list, tuple)):
            tags[key] = ', '.join(str(item) for item in value if item is not None)
        else:
            tags[key] = str(value)

    details = {}
    info = getattr(media, 'info', None)
    if info is not None:
        duration = getattr(info, 'length', None)
        bitrate = getattr(info, 'bitrate', None)
        sample_rate = getattr(info, 'sample_rate', None)
        channels = getattr(info, 'channels', None)

        if duration is not None:
            formatted = _format_duration(duration)
            if formatted:
                details['Duración'] = formatted
        if bitrate:
            human_bitrate = f"{int(bitrate / 1000)} kbps" if bitrate > 1000 else f"{bitrate} bps"
            details['Bitrate'] = human_bitrate
        if sample_rate:
            details['Frecuencia de muestreo'] = f"{int(sample_rate)} Hz"
        if channels:
            details['Canales'] = str(channels)

    return tags or None, details or None, None


def _analysis_suggestions(category: str, registered: bool) -> list:
    options = {
        'image': [
            'Incluye el archivo en una carpeta y ejecuta un escaneo desde Fotos para obtener estadisticas en lote.',
            'Captura metadatos adicionales (autor, ubicacion) en una tabla personalizada si necesitas seguimiento detallado.'
        ],
        'video': [
            'Registra la pelicula desde Videos > Gestionar para mantenerla en el catalogo.',
            'Verifica la informacion de soporte (mediatype) antes de crear o actualizar el registro de video.'
        ],
        'audio': [
            'Anota datos como genero o album en una tabla personalizada creada desde la seccion de tablas dinamicas.',
            'Incluye su carpeta en un escaneo para contabilizar archivos de audio soportados.'
        ],
        'other': [
            'Revisa si la extension necesita agregarse a la configuracion de tipos permitidos para ser clasificada automaticamente.',
            'Valida manualmente el contenido antes de integrarlo al catalogo.'
        ]
    }
    result = options.get(category, options['other']).copy()
    if not registered:
        result.append('La extension no esta registrada; agregala a la configuracion de tipos permitidos para que participe en los escaneos automatizados.')
    return result


@bp.route('/utilidades/analizador', methods=['GET', 'POST'])
def analyze_media_file():
    analysis = None
    errors = []
    info_messages = []

    if request.method == 'POST':
        uploaded = request.files.get('media_file')
        if not uploaded or uploaded.filename.strip() == '':
            errors.append('Selecciona un archivo multimedia para analizar.')
        else:
            filename = secure_filename(uploaded.filename)
            temp_path = None
            try:
                max_size = current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
                upload_stream = uploaded.stream
                chunk_size = 1 * 1024 * 1024  # 1 MB
                bytes_written = 0

                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    temp_path = Path(tmp.name)
                    while True:
                        chunk = upload_stream.read(chunk_size)
                        if not chunk:
                            break
                        bytes_written += len(chunk)
                        if max_size and bytes_written > max_size:
                            errors.append('El archivo excede el tamaño máximo permitido por la configuración del servidor.')
                            raise ValueError('File too large')
                        tmp.write(chunk)

                stat = temp_path.stat()
                extension = Path(filename).suffix.lower()
                entry = FileType.query.filter_by(extension=extension).first()
                category = entry.type if entry else 'other'

                mime_type = None
                try:
                    import magic
                    mime_type = magic.from_file(str(temp_path), mime=True)
                except ImportError:
                    mime_type = mimetypes.guess_type(filename)[0]
                except Exception as exc:
                    mime_type = mimetypes.guess_type(filename)[0]

                image_info = None
                exif_data = None
                gps_data = None
                if category == 'image':
                    try:
                        with Image.open(temp_path) as img:
                            image_info = {
                                'format': img.format,
                                'mode': img.mode,
                                'width': img.width,
                                'height': img.height
                            }
                    except Exception as exc:
                        errors.append(f'No se pudieron leer los metadatos de imagen: {exc}')
                    try:
                        exif_data, gps_data = _extract_image_metadata(temp_path)
                    except Exception as exc:
                        errors.append(f'No se pudieron leer los datos EXIF: {exc}')

                media_tags = None
                media_details = None
                should_extract_media = False
                if mime_type and (mime_type.startswith('audio') or mime_type.startswith('video')):
                    should_extract_media = True
                if category in {'audio', 'video'}:
                    should_extract_media = True

                if should_extract_media:
                    tags, details, note = _extract_mutagen_metadata(temp_path)
                    media_tags = tags
                    media_details = details
                    if note:
                        info_messages.append(note)

                analysis = {
                    'filename': filename,
                    'extension': extension or '(sin extension)',
                    'size_bytes': stat.st_size,
                    'size_human': _format_size(stat.st_size),
                    'category': category,
                    'category_label': {'image': 'Imagen', 'video': 'Video', 'audio': 'Audio'}.get(category, 'Otro'),
                    'registered': bool(entry),
                    'mime': mime_type or 'Desconocido',
                    'image_info': image_info,
                    'exif': exif_data,
                    'gps': gps_data,
                    'media_tags': media_tags,
                    'media_info': media_details,
                    'created_at': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                    'modified_at': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'accessed_at': datetime.fromtimestamp(stat.st_atime).strftime('%Y-%m-%d %H:%M:%S'),
                    'suggestions': _analysis_suggestions(category, bool(entry))
                }

            except Exception as exc:
                errors.append(f'No se pudo analizar el archivo seleccionado: {exc}')
            finally:
                if temp_path and temp_path.exists():
                    try:
                        temp_path.unlink()
                    except Exception:
                        pass

    return render_template('utilities/file_analysis.html', analysis=analysis, errors=errors, info_messages=info_messages)

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
    include_files = request.args.get('include_files', '')
    include_files = str(include_files).lower() in ('1', 'true', 'yes')

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
                elif include_files and item.is_file():
                    items.append({
                        'path': str(item),
                        'name': item.name,
                        'type': 'file'
                    })
            except PermissionError:
                continue
        
        # Ordenar: directorios primero, luego archivos, ambos por nombre
        items.sort(key=lambda x: (0 if x['type'] != 'file' else 1, x['name'].lower()))
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