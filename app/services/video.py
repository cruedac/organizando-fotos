"""
Servicios para la gestión de videos
"""

from app import db
from app.models.movie import Movie
from datetime import datetime

class VideoService:
    """Clase de servicio para la gestión de videos"""
    
    @staticmethod
    def search_videos(query, filters=None):
        """
        Busca videos según criterios específicos
        """
        # Iniciamos la consulta base
        movies_query = Movie.query

        if filters:
            # Aplicamos los filtros proporcionados
            if filters.get('year'):
                movies_query = movies_query.filter(Movie.year == filters['year'])
            if filters.get('category'):
                movies_query = movies_query.filter(Movie.category == filters['category'])
            if filters.get('media_type'):
                movies_query = movies_query.filter(Movie.mediatype == filters['media_type'])

        if query:
            # Búsqueda en campos relevantes
            search = f"%{query}%"
            movies_query = movies_query.filter(
                db.or_(
                    Movie.originaltitle.ilike(search),
                    Movie.translatedtitle.ilike(search),
                    Movie.formattedtitle.ilike(search),
                    Movie.description.ilike(search),
                    Movie.comments.ilike(search)
                )
            )

        # Ejecutamos la consulta
        return movies_query.all()

    @staticmethod
    def get_categories():
        """
        Obtiene todas las categorías únicas de videos
        """
        return db.session.query(Movie.category)\
            .filter(Movie.category != '')\
            .filter(Movie.category.isnot(None))\
            .distinct()\
            .all()

    @staticmethod
    def get_media_types():
        """
        Obtiene todos los tipos de medios únicos
        """
        return db.session.query(Movie.mediatype)\
            .filter(Movie.mediatype != '')\
            .filter(Movie.mediatype.isnot(None))\
            .distinct()\
            .all()

    @staticmethod
    def get_years():
        """
        Obtiene todos los años únicos
        """
        return db.session.query(Movie.year)\
            .filter(Movie.year != 0)\
            .filter(Movie.year.isnot(None))\
            .distinct()\
            .order_by(Movie.year.desc())\
            .all()