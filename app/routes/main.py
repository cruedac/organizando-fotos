import mimetypes
import os
import re
import string
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from flask import Blueprint, render_template, request, jsonify, current_app
from werkzeug.utils import secure_filename

from app.models.database import (
    FileType,
    PhotoScan,
    PhotoScanSummary,
    db,
    ensure_photos_scan_summary_table,
)
from app.services.file_scanner import NO_EXTENSION, scan_for_media_recursive
from app.services.media_metadata import format_size, read_image_metadata, read_media_tags

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


_YEAR_PATTERN = re.compile(r'(19|20)\d{2}')
_MONTH_VARIANTS = {
    1: ['enero', 'ene', 'january', 'jan'],
    2: ['febrero', 'feb', 'february'],
    3: ['marzo', 'mar', 'march'],
    4: ['abril', 'abr', 'april', 'apr'],
    5: ['mayo', 'may'],
    6: ['junio', 'jun', 'june'],
    7: ['julio', 'jul', 'july'],
    8: ['agosto', 'ago', 'august', 'aug'],
    9: ['septiembre', 'setiembre', 'sep', 'sept', 'september'],
    10: ['octubre', 'oct', 'october'],
    11: ['noviembre', 'nov', 'november'],
    12: ['diciembre', 'dic', 'december', 'dec'],
}
_MONTH_CANONICAL = {num: variants[0].capitalize() for num, variants in _MONTH_VARIANTS.items()}
_MONTH_LOOKUP = {alias: num for num, variants in _MONTH_VARIANTS.items() for alias in variants}
for number in range(1, 13):
    _MONTH_LOOKUP[str(number)] = number
    _MONTH_LOOKUP[f'{number:02d}'] = number


def _parse_year_from_name(name: str) -> Optional[int]:
    if not name:
        return None
    match = _YEAR_PATTERN.search(name)
    if match:
        value = int(match.group())
        if 1900 <= value <= 2100:
            return value
    return None


def _parse_month_from_name(name: str) -> Tuple[Optional[int], Optional[str]]:
    if not name:
        return None, None

    month_number: Optional[int] = None
    month_text: Optional[str] = None
    cleaned = name.strip()
    if not cleaned:
        return None, None

    prefix_match = re.match(r'(?P<num>\d{1,2})\D*(?P<rest>.*)$', cleaned)
    if prefix_match:
        try:
            candidate = int(prefix_match.group('num'))
            if 1 <= candidate <= 12:
                month_number = candidate
        except ValueError:
            month_number = None
        remainder = prefix_match.group('rest').strip(" -_.")
        if remainder and any(char.isalpha() for char in remainder):
            month_text = remainder

    tokens = re.split(r'[\s\-_/.,]+', cleaned.lower())
    for token in tokens:
        if token in _MONTH_LOOKUP:
            resolved = _MONTH_LOOKUP[token]
            if month_number is None:
                month_number = resolved
            if not month_text:
                month_text = _MONTH_CANONICAL.get(resolved)
            break

    if month_number and not month_text:
        month_text = _MONTH_CANONICAL.get(month_number)

    if month_text:
        month_text = ' '.join(part.capitalize() for part in month_text.strip().split())

    return month_number, month_text


def _extract_year_and_month(path_obj: Path) -> Tuple[Optional[int], Optional[int], Optional[str]]:
    candidates = []
    current = path_obj
    visited = 0
    while current and current.parent != current and visited < 5:
        candidates.append(current.name)
        current = current.parent
        visited += 1
    if current and current.parent == current:
        candidates.append(current.name)

    year = None
    for candidate in candidates:
        year_candidate = _parse_year_from_name(candidate)
        if year_candidate is not None:
            year = year_candidate
            break

    month_number = None
    month_text = None
    for candidate in candidates:
        candidate_month, candidate_text = _parse_month_from_name(candidate)
        if candidate_month is None and candidate_text is None:
            continue

        if candidate_month is not None:
            month_number = candidate_month
        if candidate_text:
            month_text = candidate_text

        if month_number is not None and not month_text:
            month_text = _MONTH_CANONICAL.get(month_number)

        if month_number is not None and month_text:
            break

    return year, month_number, month_text


def _build_scan_summary(
    folder_path: str,
    totals: dict,
    by_extension: dict,
    timestamp: Optional[datetime] = None,
    total_size: Optional[int] = None
) -> dict:
    """Prepara un resumen de escaneo para una carpeta concreta."""
    path_obj = Path(folder_path)
    try:
        path_obj = path_obj.resolve()
    except Exception:
        # Si no se puede normalizar completamente la ruta trabajamos con la original
        path_obj = Path(folder_path)

    full_path = str(path_obj)
    parent_obj = path_obj.parent if path_obj.parent != path_obj else None
    parent_path = str(parent_obj) if parent_obj else None
    end_name = path_obj.name or full_path

    cleaned_extensions = [ext for ext, count in (by_extension or {}).items() if ext and ext != NO_EXTENSION and count > 0]
    cleaned_extensions.sort()
    media_types = ','.join(cleaned_extensions)

    completed_at = timestamp or datetime.utcnow()

    year, month_number, month_text = _extract_year_and_month(path_obj)

    size_value = 0
    if total_size is not None:
        try:
            size_value = max(int(total_size), 0)
        except (TypeError, ValueError):
            size_value = 0
    size_human = format_size(size_value) if size_value else '0 bytes'

    return {
        'path': full_path,
        'parent_path': parent_path,
        'end_name': end_name,
        'num_images': int(totals.get('image', 0)) if totals else 0,
        'num_videos': int(totals.get('video', 0)) if totals else 0,
        'media_types': media_types,
        'last_scan': completed_at.isoformat(timespec='seconds'),
        'year': year,
        'month_number': month_number,
        'month_text': month_text,
        'total_size': size_value,
        'total_size_human': size_human
    }


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
                chunk_size = 1 * 1024 * 1024
                bytes_written = 0
                too_large = False

                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    temp_path = Path(tmp.name)
                    while True:
                        chunk = upload_stream.read(chunk_size)
                        if not chunk:
                            break
                        bytes_written += len(chunk)
                        if max_size and bytes_written > max_size:
                            errors.append('El archivo excede el tamaño máximo permitido por la configuración del servidor.')
                            too_large = True
                            break
                        tmp.write(chunk)

                if too_large:
                    raise RuntimeError('FILE_TOO_LARGE')

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
                        image_info, exif_data, gps_data = read_image_metadata(temp_path)
                    except Exception as exc:
                        errors.append(f'No se pudieron leer los metadatos de imagen: {exc}')

                media_tags = None
                media_details = None
                should_extract_media = False
                if mime_type and (mime_type.startswith('audio') or mime_type.startswith('video')):
                    should_extract_media = True
                if category in {'audio', 'video'}:
                    should_extract_media = True

                if should_extract_media:
                    tags, details, note = read_media_tags(temp_path)
                    media_tags = tags
                    media_details = details
                    if note:
                        info_messages.append(note)

                analysis = {
                    'filename': filename,
                    'extension': extension or '(sin extension)',
                    'size_bytes': stat.st_size,
                    'size_human': format_size(stat.st_size),
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
                if str(exc) != 'FILE_TOO_LARGE':
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
        scan_timestamp = datetime.utcnow()
        summary = _build_scan_summary(
            folder_path,
            result.get('totals'),
            result.get('by_extension'),
            timestamp=scan_timestamp,
            total_size=result.get('total_size')
        )
        directory_summaries = []
        for entry in result.get('directories', []) or []:
            directory_summaries.append(
                _build_scan_summary(
                    entry.get('path', ''),
                    entry.get('totals') or {},
                    entry.get('by_extension') or {},
                    timestamp=scan_timestamp,
                    total_size=entry.get('total_size')
                )
            )
        result['summary'] = summary
        result['directory_summaries'] = directory_summaries
        result['directories_count'] = len(directory_summaries)
        result['total_size'] = summary.get('total_size')
        result['total_size_human'] = summary.get('total_size_human')
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'error': f'Error al escanear el directorio: {str(e)}'
        }), 500


@bp.route('/scan/save', methods=['POST'])
def save_scan_summary():
    """Guarda en la base de datos el resumen de un escaneo realizado."""
    payload = request.get_json() or {}

    folder_path = payload.get('folder_path')
    totals = payload.get('totals') or {}
    by_extension = payload.get('by_extension') or {}
    directories = payload.get('directories') or []
    directories_count_value = payload.get('directories_count')
    summary_payload = payload.get('summary') if isinstance(payload.get('summary'), dict) else None

    if not folder_path:
        return jsonify({'error': 'Se requiere la ruta analizada para guardar el resumen.'}), 400

    try:
        ensure_photos_scan_summary_table(current_app)
        records_to_persist = []
        saved_at = datetime.utcnow()

        def _safe_int(value, default=0):
            try:
                parsed = int(value)
                return parsed if parsed >= 0 else default
            except (TypeError, ValueError):
                return default

        def _safe_optional_int(value):
            try:
                parsed = int(value)
                return parsed if parsed >= 0 else None
            except (TypeError, ValueError):
                return None

        summary_total_size = 0
        payload_total_size = payload.get('total_size')
        if payload_total_size is not None:
            summary_total_size = _safe_int(payload_total_size, 0)
        if summary_total_size <= 0 and summary_payload and summary_payload.get('total_size') is not None:
            summary_total_size = _safe_int(summary_payload.get('total_size'), 0)
        if summary_total_size <= 0:
            summary_total_size = sum(_safe_int(entry.get('total_size'), 0) for entry in directories)
        if summary_total_size <= 0:
            summary_total_size = _safe_int(totals.get('total_size'), 0)

        summaries = directories
        if not summaries:
            total_values = list((totals or {}).values())
            extension_values = list((by_extension or {}).values())
            if any(value > 0 for value in total_values + extension_values):
                summaries = [_build_scan_summary(
                    folder_path,
                    totals,
                    by_extension,
                    timestamp=saved_at,
                    total_size=summary_total_size
                )]
            else:
                return jsonify({'error': 'No se encontraron carpetas con archivos para guardar.'}), 400

        canonical_summary = _build_scan_summary(
            folder_path,
            totals,
            by_extension,
            timestamp=saved_at,
            total_size=summary_total_size
        )
        summary_details = canonical_summary.copy()
        if summary_payload:
            summary_details.update({k: v for k, v in summary_payload.items() if v is not None})
        if not summary_details.get('path'):
            summary_details['path'] = canonical_summary['path']

        directories_count = _safe_int(directories_count_value, len(directories))
        if directories_count <= 0 and summaries:
            directories_count = len(summaries)

        summary_num_images = _safe_int(summary_details.get('num_images'), totals.get('image', 0))
        summary_num_videos = _safe_int(summary_details.get('num_videos'), totals.get('video', 0))
        summary_year = _safe_optional_int(summary_details.get('year'))
        summary_month_number = _safe_optional_int(summary_details.get('month_number'))
        summary_total_size = _safe_int(summary_details.get('total_size'), summary_total_size)

        summary_month_text = summary_details.get('month_text')
        if isinstance(summary_month_text, str):
            summary_month_text = summary_month_text.strip() or None
        else:
            summary_month_text = None

        if summary_month_text:
            parsed_month, parsed_text = _parse_month_from_name(summary_month_text)
            if summary_month_number is None and parsed_month is not None:
                summary_month_number = parsed_month
            if parsed_text:
                summary_month_text = parsed_text
            elif summary_month_number is not None:
                summary_month_text = _MONTH_CANONICAL.get(summary_month_number, summary_month_text.title())
            else:
                summary_month_text = summary_month_text.title()
        elif summary_month_number is not None:
            summary_month_text = _MONTH_CANONICAL.get(summary_month_number)

        summary_record = PhotoScanSummary(
            path=summary_details.get('path'),
            directories_count=directories_count,
            num_images=summary_num_images,
            num_videos=summary_num_videos,
            year=summary_year,
            month_number=summary_month_number,
            month_text=summary_month_text,
            total_size=summary_total_size,
            created_at=saved_at
        )

        for summary in summaries:
            path_value = summary.get('path')
            if not path_value:
                continue

            num_images = summary.get('num_images', 0)
            try:
                num_images = int(num_images)
            except (TypeError, ValueError):
                num_images = 0

            num_videos = summary.get('num_videos', 0)
            try:
                num_videos = int(num_videos)
            except (TypeError, ValueError):
                num_videos = 0

            year_value = summary.get('year')
            try:
                year_value = int(year_value) if year_value is not None else None
            except (TypeError, ValueError):
                year_value = None

            month_value = summary.get('month_number')
            try:
                month_value = int(month_value) if month_value is not None else None
            except (TypeError, ValueError):
                month_value = None

            month_label = summary.get('month_text')
            if isinstance(month_label, str):
                month_label = month_label.strip() or None
            else:
                month_label = None

            if month_label:
                parsed_month_value, parsed_month_text = _parse_month_from_name(month_label)
                if month_value is None and parsed_month_value is not None:
                    month_value = parsed_month_value
                if parsed_month_text:
                    month_label = parsed_month_text
                elif month_value is not None:
                    month_label = _MONTH_CANONICAL.get(month_value, month_label.title())
                else:
                    month_label = month_label.title()
            elif month_value is not None:
                month_label = _MONTH_CANONICAL.get(month_value)

            folder_size = _safe_int(summary.get('total_size'), 0)

            record = PhotoScan(
                path=summary.get('path'),
                parent_path=summary.get('parent_path'),
                end_name=summary.get('end_name'),
                num_images=num_images,
                num_videos=num_videos,
                media_types=(summary.get('media_types') or None),
                last_scan=saved_at,
                created_at=saved_at,
                year=year_value,
                month_number=month_value,
                month_text=month_label,
                total_size=folder_size
            )
            records_to_persist.append(record)

        if not records_to_persist:
            return jsonify({'error': 'No se encontraron carpetas con archivos para guardar.'}), 400

        db.session.add(summary_record)
        db.session.add_all(records_to_persist)
        db.session.commit()

        current_app.logger.info(
            'Se guardaron %s carpetas y 1 resumen agregado para %s',
            len(records_to_persist),
            folder_path
        )
        return jsonify({'status': 'ok', 'stored': len(records_to_persist), 'summary_id': summary_record.id})
    except Exception as exc:
        current_app.logger.exception('No se pudo guardar el resumen del escaneo para %s', folder_path)
        db.session.rollback()
        return jsonify({'error': f'No se pudo guardar el resumen: {exc}'}), 500