"""
Rutas para la gestión de videos
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, Markup
from app.models.movie import Movie
from app.models.database import TipoSoporte
from app.services.video import VideoService
from app.services.video_import import import_sql_file
from app import db
import os
import json

bp = Blueprint('videos', __name__, url_prefix='/videos')

@bp.app_template_filter()
def nl2br(value):
    """Convierte saltos de línea en etiquetas <br/>"""
    if value:
        return Markup(value.replace('\n', '<br/>'))

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
        print(f"[Videos] Registros en DB: {total}")
        for m in sample:
            print(f"[Videos] #{m.num} - {m.title}")
    except Exception as e:
        print(f"[Videos] Error al leer registros para imprimir: {e}")

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
    return render_template('videos/detail.html', video=video)

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
    support_types = TipoSoporte.query.order_by(TipoSoporte.tipo).all()
    if request.method == 'POST':
        form_data = request.form.to_dict()
        form_data['num'] = (form_data.get('num') or '').strip()

        # Validación de NUM
        try:
            num = int(form_data['num'])
        except Exception:
            flash('NUM debe ser un número entero válido.', 'error')
            return render_template('videos/movie_form.html', movie=None, support_types=support_types, form_data=form_data)

        if Movie.query.get(num):
            flash(f'Ya existe una película con NUM={num}.', 'error')
            return render_template('videos/movie_form.html', movie=None, support_types=support_types, form_data=form_data)

        support_names = {s.tipo for s in support_types}
        mediatype_value = (form_data.get('mediatype') or '').strip()
        form_data['mediatype'] = mediatype_value
        mediatype = mediatype_value or None
        if mediatype and mediatype not in support_names:
            flash('El tipo de soporte seleccionado no es válido.', 'error')
            return render_template('videos/movie_form.html', movie=None, support_types=support_types, form_data=form_data)

        # Validar año si viene informado
        year_value = (form_data.get('year') or '').strip()
        form_data['year'] = year_value
        if year_value:
            try:
                year = int(year_value)
            except ValueError:
                flash('El año debe ser un número entero.', 'error')
                return render_template('videos/movie_form.html', movie=None, support_types=support_types, form_data=form_data)
        else:
            year = None

        movie = Movie(
            num=num,
            originaltitle=form_data.get('originaltitle') or None,
            translatedtitle=form_data.get('translatedtitle') or None,
            formattedtitle=form_data.get('formattedtitle') or None,
            year=year,
            category=form_data.get('category') or None,
            mediatype=mediatype,
            description=form_data.get('description') or None,
            filepath=form_data.get('filepath') or None,
        )
        db.session.add(movie)
        db.session.commit()
        flash('Película añadida correctamente.', 'success')
        return redirect(url_for('videos.manage'))

    return render_template('videos/movie_form.html', movie=None, support_types=support_types, form_data=None)


@bp.route('/edit/<int:movie_id>', methods=['GET', 'POST'])
def edit_movie(movie_id):
    """Editar un registro existente"""
    movie = Movie.query.get_or_404(movie_id)
    support_types = TipoSoporte.query.order_by(TipoSoporte.tipo).all()

    if request.method == 'POST':
        form_data = request.form.to_dict()
        support_names = {s.tipo for s in support_types}
        mediatype_value = (form_data.get('mediatype') or '').strip()
        form_data['mediatype'] = mediatype_value
        mediatype = mediatype_value or None
        if mediatype and mediatype not in support_names:
            flash('El tipo de soporte seleccionado no es válido.', 'error')
            return render_template('videos/movie_form.html', movie=movie, support_types=support_types, form_data=form_data)

        year_value = (form_data.get('year') or '').strip()
        form_data['year'] = year_value
        if year_value:
            try:
                movie.year = int(year_value)
            except ValueError:
                flash('El año debe ser un número entero.', 'error')
                return render_template('videos/movie_form.html', movie=movie, support_types=support_types, form_data=form_data)
        else:
            movie.year = None

        movie.originaltitle = form_data.get('originaltitle') or None
        movie.translatedtitle = form_data.get('translatedtitle') or None
        movie.formattedtitle = form_data.get('formattedtitle') or None
        movie.category = form_data.get('category') or None
        movie.mediatype = mediatype
        movie.description = form_data.get('description') or None
        movie.filepath = form_data.get('filepath') or None
        db.session.commit()
        flash('Película actualizada correctamente.', 'success')
        return redirect(url_for('videos.manage'))

    return render_template('videos/movie_form.html', movie=movie, support_types=support_types, form_data=None)


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