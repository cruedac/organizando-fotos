"""
Servicios para la gestión de videos
"""

import os
import sqlite3
from app import db
from app.models.movie import Movie, Extra
from datetime import datetime
import re

class VideoService:
    """Clase de servicio para la gestión de videos"""

    @staticmethod
    def import_from_sql(sql_file):
        """
        Importa datos desde un archivo SQL que contiene la estructura e información de videos
        """
        try:
            # Leemos el archivo SQL
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()

            # Separamos los comandos SQL individuales
            # Usamos regex para manejar valores que puedan contener punto y coma
            commands = re.split(r';(?=(?:[^\']*\'[^\']*\')*[^\']*$)', sql_content)
            commands = [cmd.strip() for cmd in commands if cmd.strip()]

            # Creamos una conexión temporal a SQLite en memoria
            conn = sqlite3.connect(':memory:')
            cursor = conn.cursor()

            # Ejecutamos cada comando SQL
            for command in commands:
                if command:
                    cursor.execute(command)
                    conn.commit()

            # Importamos los datos a nuestros modelos
            # Primero las películas
            cursor.execute('SELECT * FROM movies')
            columns = [desc[0] for desc in cursor.description]
            movies_data = cursor.fetchall()

            for movie in movies_data:
                movie_dict = dict(zip(columns, movie))
                # Convertimos fechas
                for date_field in ['DATEADDED', 'DATEWATCHED']:
                    if movie_dict.get(date_field):
                        try:
                            movie_dict[date_field] = datetime.strptime(movie_dict[date_field], '%Y-%m-%d').date()
                        except ValueError:
                            movie_dict[date_field] = None
                
                # Creamos el registro
                movie_obj = Movie(**movie_dict)
                db.session.add(movie_obj)

            # Importamos los extras
            cursor.execute('SELECT * FROM extras')
            columns = [desc[0] for desc in cursor.description]
            extras_data = cursor.fetchall()

            for extra in extras_data:
                extra_dict = dict(zip(columns, extra))
                extra_obj = Extra(**extra_dict)
                db.session.add(extra_obj)

            # Guardamos todos los cambios
            db.session.commit()
            conn.close()

            return True, "Importación completada con éxito"

        except Exception as e:
            db.session.rollback()
            return False, f"Error durante la importación: {str(e)}"
    
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