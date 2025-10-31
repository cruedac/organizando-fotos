"""
Rutas para la gestión de videos
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from markupsafe import Markup
from app.models.movie import Movie
from app.models.database import TipoSoporte
from app.services.video import VideoService
from app.services.video_import import import_sql_file
from app.services.support_type_cache import get_support_types_cached
from app import db
import os
import json
from datetime import datetime, date
from sqlalchemy import func

bp = Blueprint('videos', __name__, url_prefix='/videos')

@bp.app_template_filter()
def nl2br(value):
    """Convierte saltos de línea en etiquetas <br/>"""
    if value:
        return Markup(value.replace('\n', '<br/>'))

MOVIE_FIELD_DEFINITIONS = [
    {'name': 'num', 'label': 'NUM', 'input': 'int', 'section': 'Identificación y títulos', 'width': 6},
    {'name': 'originaltitle', 'label': 'Título original', 'input': 'text', 'section': 'Identificación y títulos', 'width': 6},
    {'name': 'translatedtitle', 'label': 'Título traducido', 'input': 'text', 'section': 'Identificación y títulos', 'width': 6},
    {'name': 'formattedtitle', 'label': 'Título formateado', 'input': 'text', 'section': 'Identificación y títulos', 'width': 6},
    {'name': 'checked', 'label': 'Checked', 'input': 'text', 'section': 'Estado y soporte', 'width': 6},
    {'name': 'colortag', 'label': 'Etiqueta de color', 'input': 'int', 'section': 'Estado y soporte', 'width': 6},
    {'name': 'media', 'label': 'Medio', 'input': 'text', 'section': 'Estado y soporte', 'width': 6},
    {'name': 'mediatype', 'label': 'Tipo de soporte', 'input': 'support', 'section': 'Estado y soporte', 'width': 6},
    {'name': 'source', 'label': 'Fuente', 'input': 'text', 'section': 'Estado y soporte', 'width': 6},
    {'name': 'borrower', 'label': 'Prestado a', 'input': 'text', 'section': 'Estado y soporte', 'width': 6},
    {'name': 'picturestatus', 'label': 'Estado de imagen', 'input': 'text', 'section': 'Estado y soporte', 'width': 6},
    {'name': 'picturename', 'label': 'Nombre de imagen', 'input': 'text', 'section': 'Estado y soporte', 'width': 6},
    {'name': 'dateadded', 'label': 'Fecha de alta', 'input': 'date', 'section': 'Fechas y seguimiento', 'width': 6},
    {'name': 'datewatched', 'label': 'Fecha de visionado', 'input': 'date', 'section': 'Fechas y seguimiento', 'width': 6},
    {'name': 'userrating', 'label': 'Valoración usuario', 'input': 'float', 'section': 'Calificaciones y clasificación', 'width': 6},
    {'name': 'rating', 'label': 'Valoración global', 'input': 'float', 'section': 'Calificaciones y clasificación', 'width': 6},
    {'name': 'category', 'label': 'Categoría', 'input': 'text', 'section': 'Calificaciones y clasificación', 'width': 6},
    {'name': 'certification', 'label': 'Certificación', 'input': 'text', 'section': 'Calificaciones y clasificación', 'width': 6},
    {'name': 'country', 'label': 'País', 'input': 'text', 'section': 'Contenido y producción', 'width': 6},
    {'name': 'year', 'label': 'Año', 'input': 'int', 'section': 'Contenido y producción', 'width': 6},
    {'name': 'length', 'label': 'Duración (min)', 'input': 'int', 'section': 'Contenido y producción', 'width': 6},
    {'name': 'director', 'label': 'Director', 'input': 'text', 'section': 'Contenido y producción', 'width': 6},
    {'name': 'producer', 'label': 'Productor', 'input': 'text', 'section': 'Contenido y producción', 'width': 6},
    {'name': 'writer', 'label': 'Guionista', 'input': 'text', 'section': 'Contenido y producción', 'width': 6},
    {'name': 'composer', 'label': 'Compositor', 'input': 'text', 'section': 'Contenido y producción', 'width': 6},
    {'name': 'actors', 'label': 'Reparto', 'input': 'textarea', 'section': 'Contenido y producción', 'width': 12, 'rows': 3},
    {'name': 'languages', 'label': 'Idiomas', 'input': 'text', 'section': 'Contenido y producción', 'width': 6},
    {'name': 'subtitles', 'label': 'Subtítulos', 'input': 'text', 'section': 'Contenido y producción', 'width': 6},
    {'name': 'url', 'label': 'URL', 'input': 'text', 'section': 'Metadatos adicionales', 'width': 12},
    {'name': 'filepath', 'label': 'Ruta del archivo', 'input': 'filepath', 'section': 'Metadatos adicionales', 'width': 12},
    {'name': 'videoformat', 'label': 'Formato de video', 'input': 'text', 'section': 'Detalles técnicos', 'width': 6},
    {'name': 'videobitrate', 'label': 'Bitrate de video', 'input': 'int', 'section': 'Detalles técnicos', 'width': 6},
    {'name': 'audioformat', 'label': 'Formato de audio', 'input': 'text', 'section': 'Detalles técnicos', 'width': 6},
    {'name': 'audiobitrate', 'label': 'Bitrate de audio', 'input': 'int', 'section': 'Detalles técnicos', 'width': 6},
    {'name': 'resolution', 'label': 'Resolución', 'input': 'text', 'section': 'Detalles técnicos', 'width': 6},
    {'name': 'framerate', 'label': 'Framerate', 'input': 'text', 'section': 'Detalles técnicos', 'width': 6},
    {'name': 'filesize', 'label': 'Tamaño de archivo', 'input': 'text', 'section': 'Detalles técnicos', 'width': 6},
    {'name': 'disks', 'label': 'Discos', 'input': 'int', 'section': 'Detalles técnicos', 'width': 6},
    {'name': 'nbextras', 'label': 'Extras', 'input': 'int', 'section': 'Detalles técnicos', 'width': 6},
    {'name': 'description', 'label': 'Descripción', 'input': 'textarea', 'section': 'Notas', 'width': 12, 'rows': 4},
    {'name': 'comments', 'label': 'Comentarios', 'input': 'textarea', 'section': 'Notas', 'width': 12, 'rows': 3},
]


def _get_movie_form_sections():
    sections = []
    for field in MOVIE_FIELD_DEFINITIONS:
        if field['name'] == 'num':
            continue
        if not sections or sections[-1]['title'] != field['section']:
            sections.append({'title': field['section'], 'fields': []})
        sections[-1]['fields'].append(field)
    return sections


def _format_form_value(field, value):
    if value is None:
        return ''
    if field['input'] == 'date':
        if isinstance(value, (date, datetime)):
            return value.strftime('%Y-%m-%d')
        return str(value)
    if field['input'] == 'float':
        try:
            return format(value, 'g')
        except Exception:
            return str(value)
    return str(value)


def _build_initial_form_values(movie=None):
    values = {}
    for field in MOVIE_FIELD_DEFINITIONS:
        attr_value = getattr(movie, field['name'], None) if movie else None
        values[field['name']] = _format_form_value(field, attr_value)
    if movie:
        values['num'] = str(movie.num)
    else:
        values['num'] = ''
    return values


def _parse_movie_field(field, raw, support_names):
    input_type = field['input']
    if input_type == 'textarea':
        value = (raw or '').strip()
        return (value or None, None)
    if input_type == 'text':
        value = (raw or '').strip()
        return (value or None, None)
    if input_type == 'filepath':
        value = (raw or '').strip()
        return (value or None, None)
    if input_type == 'support':
        value = (raw or '').strip()
        if not value:
            return (None, None)
        if value not in support_names:
            return (value, f'El tipo de soporte "{value}" no es válido.')
        return (value, None)
    if input_type == 'int':
        raw_value = (raw or '').strip()
        if raw_value == '':
            return (None, None)
        try:
            return (int(raw_value), None)
        except ValueError:
            return (None, f'El campo "{field["label"]}" debe ser un número entero.')
    if input_type == 'float':
        raw_value = (raw or '').strip()
        if raw_value == '':
            return (None, None)
        normalized = raw_value.replace(',', '.')
        try:
            return (float(normalized), None)
        except ValueError:
            return (None, f'El campo "{field["label"]}" debe ser un número decimal.')
    if input_type == 'date':
        raw_value = (raw or '').strip()
        if raw_value == '':
            return (None, None)
        try:
            return (datetime.strptime(raw_value, '%Y-%m-%d').date(), None)
        except ValueError:
            return (None, f'El campo "{field["label"]}" debe tener el formato YYYY-MM-DD.')
    value = (raw or '').strip()
    return (value or None, None)


def _coerce_movie_payload(form_values, support_types):
    payload = {}
    errors = []
    support_names = {s.tipo for s in support_types}
    for field in MOVIE_FIELD_DEFINITIONS:
        if field['name'] == 'num':
            continue
        raw = form_values.get(field['name'], '')
        value, error = _parse_movie_field(field, raw, support_names)
        if error:
            errors.append(error)
        payload[field['name']] = value
    return payload, errors


def _format_detail_value(field, value):
    if value is None:
        return ''
    if field['input'] == 'date':
        if isinstance(value, (date, datetime)):
            return value.strftime('%Y-%m-%d')
        return str(value)
    if field['input'] == 'float':
        try:
            formatted = f"{float(value):.2f}"
            return formatted.rstrip('0').rstrip('.') if '.' in formatted else formatted
        except Exception:
            return str(value)
    return str(value)


def _build_movie_detail_sections(movie):
    sections = []
    for field in MOVIE_FIELD_DEFINITIONS:
        if not sections or sections[-1]['title'] != field['section']:
            sections.append({'title': field['section'], 'rows': []})
        value = getattr(movie, field['name'], None)
        display_value = _format_detail_value(field, value)
        is_empty = display_value in ('', None)
        sections[-1]['rows'].append({
            'field': field,
            'value': 'Sin datos' if is_empty else display_value,
            'empty': is_empty
        })
    return sections

@bp.route('/')
def index():
    """Página principal de gestión de videos"""
    # Obtenemos los filtros disponibles
    categories = VideoService.get_categories()
    media_types = VideoService.get_media_types()
    years = VideoService.get_years()

    # Obtenemos los parámetros de búsqueda y filtrado
    search_query = request.args.get('q', '')
    filters = {
        'category': request.args.get('category'),
        'media_type': request.args.get('media_type'),
        'year': request.args.get('year', type=int)
    }

    # Realizamos la búsqueda
    videos = VideoService.search_videos(search_query, filters)

    # Imprimir en consola información rápida de los registros existentes
    try:
        total = Movie.query.count()
        sample = Movie.query.order_by(Movie.num).limit(10).all()
        current_app.logger.debug("[Videos] Registros en DB: %s", total)
        for movie in sample:
            current_app.logger.debug("[Videos] #%s - %s", movie.num, movie.title)
    except Exception as exc:
        current_app.logger.exception("[Videos] Error al leer registros para imprimir: %s", exc)

    return render_template('videos/index.html',
                         videos=videos,
                         categories=categories,
                         media_types=media_types,
                         years=years,
                         current_filters=filters,
                         search_query=search_query)


@bp.route('/import-legacy', methods=['POST'])
def import_legacy():
    """Ejecuta el SQL legacy (Cintas.sql) manualmente y muestra resultado."""
    import os
    # Ejecutar la importación y devolver el resultado
    count = import_sql_file(app=__import__('flask').current_app)
    if count:
        flash(f'Importación legacy completada. INSERTs aproximados: {count}', 'success')
    else:
        flash('No se importaron registros (revisa la consola para errores o activa IMPORT_LEGACY_SQL).', 'warning')
    return redirect(url_for('videos.index'))

@bp.route('/import', methods=['POST'])
def import_data():
    """Importa datos desde el archivo SQL"""
    sql_file = 'imports/Cintas.sql'  # Ruta al archivo SQL
    
    success, message = VideoService.import_from_sql(sql_file)
    
    if success:
        flash('Datos importados correctamente', 'success')
    else:
        flash(f'Error al importar los datos: {message}', 'error')
    
    return redirect(url_for('videos.index'))

@bp.route('/detail/<int:video_id>')
def detail(video_id):
    """Muestra los detalles de un video específico"""
    video = Movie.query.get_or_404(video_id)
    detail_sections = _build_movie_detail_sections(video)
    return render_template('videos/detail.html', video=video, detail_sections=detail_sections)

@bp.route('/api/search')
def api_search():
    """Endpoint API para búsqueda de videos"""
    query = request.args.get('q', '')
    filters = {
        'category': request.args.get('category'),
        'media_type': request.args.get('media_type'),
        'year': request.args.get('year', type=int)
    }

    videos = VideoService.search_videos(query, filters)
    
    return jsonify([{
        'id': v.num,
        'title': v.title,
        'year': v.year,
        'category': v.category,
        'media_type': v.mediatype,
        'description': v.description
    } for v in videos])


# ---------------------
# Mantenimiento CRUD
# ---------------------
@bp.route('/manage')
def manage():
    """Lista todos los registros de movies con paginación simple"""
    page = request.args.get('page', 1, type=int)
    per_page = 25
    pagination = Movie.query.order_by(Movie.num).paginate(page=page, per_page=per_page, error_out=False)
    movies = pagination.items
    return render_template('videos/manage.html', movies=movies, pagination=pagination)


@bp.route('/add', methods=['GET', 'POST'])
def add_movie():
    """Agregar nuevo registro a movies"""
    support_types = get_support_types_cached()  # Usar cache en lugar de query directa
    sections = _get_movie_form_sections()

    if request.method == 'POST':
        next_num = (db.session.query(func.max(Movie.num)).scalar() or 0) + 1
        form_values = {field['name']: request.form.get(field['name'], '') for field in MOVIE_FIELD_DEFINITIONS}
        form_values['num'] = str(next_num)

        payload, errors = _coerce_movie_payload(form_values, support_types)
        if errors:
            for message in errors:
                flash(message, 'error')
            return render_template('videos/movie_form.html', movie=None, support_types=support_types, form_data=form_values, field_sections=sections)

        payload['num'] = next_num
        movie = Movie(**payload)
        db.session.add(movie)
        db.session.commit()
        flash('Película añadida correctamente.', 'success')
        return redirect(url_for('videos.manage'))

    next_num = (db.session.query(func.max(Movie.num)).scalar() or 0) + 1
    form_data = _build_initial_form_values()
    form_data['num'] = str(next_num)
    return render_template('videos/movie_form.html', movie=None, support_types=support_types, form_data=form_data, field_sections=sections)


@bp.route('/edit/<int:movie_id>', methods=['GET', 'POST'])
def edit_movie(movie_id):
    """Editar un registro existente"""
    movie = Movie.query.get_or_404(movie_id)
    support_types = get_support_types_cached()  # Usar cache en lugar de query directa
    sections = _get_movie_form_sections()

    if request.method == 'POST':
        form_values = {field['name']: request.form.get(field['name'], '') for field in MOVIE_FIELD_DEFINITIONS}
        form_values['num'] = str(movie.num)

        payload, errors = _coerce_movie_payload(form_values, support_types)
        if errors:
            for message in errors:
                flash(message, 'error')
            return render_template('videos/movie_form.html', movie=movie, support_types=support_types, form_data=form_values, field_sections=sections)

        for key, value in payload.items():
            setattr(movie, key, value)
        db.session.commit()
        flash('Película actualizada correctamente.', 'success')
        return redirect(url_for('videos.manage'))

    form_data = _build_initial_form_values(movie)
    return render_template('videos/movie_form.html', movie=movie, support_types=support_types, form_data=form_data, field_sections=sections)


@bp.route('/delete/<int:movie_id>', methods=['POST'])
def delete_movie(movie_id):
    """Eliminar un registro de movies"""
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    flash('Película eliminada correctamente.', 'success')
    return redirect(url_for('videos.manage'))


@bp.route('/import-report')
def import_report():
    """Devuelve el informe JSON más reciente de importación legacy si existe."""
    # Buscar en data/import_reports
    base = os.getcwd()
    reports_dir = os.path.join(base, 'data', 'import_reports')
    if not os.path.exists(reports_dir):
        flash('No existe directorio de informes de importación.', 'warning')
        return redirect(url_for('videos.index'))

    files = [f for f in os.listdir(reports_dir) if f.lower().endswith('.json')]
    if not files:
        flash('No se han encontrado informes de importación.', 'info')
        return redirect(url_for('videos.index'))

    files.sort(reverse=True)
    latest = files[0]
    path = os.path.join(reports_dir, latest)
    try:
        with open(path, 'r', encoding='utf-8') as rf:
            data = json.load(rf)
        # Mostrar el informe en una plantilla sencilla
        return render_template('videos/import_report.html', report=data, report_name=latest)
    except Exception as e:
        flash(f'Error leyendo informe: {e}', 'error')
        return redirect(url_for('videos.index'))