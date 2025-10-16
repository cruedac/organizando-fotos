"""
Modelos para la gestión de videos y contenido adicional
"""

from app import db
from datetime import datetime, date

# Nota: algunas filas legacy almacenan cadenas vacías para campos de fecha.
# SQLAlchemy puede intentar aplicar date.fromisoformat('') y provocar
# ValueError. Para evitarlo almacenamos las fechas como texto y exponemos
# propiedades que intentan parsear el valor a date de forma segura.

class Movie(db.Model):
    """Modelo para almacenar información sobre videos/películas"""
    __tablename__ = 'movies'

    num = db.Column('NUM', db.Integer, primary_key=True)
    checked = db.Column('CHECKED', db.String(5))
    colortag = db.Column('COLORTAG', db.Integer)
    media = db.Column('MEDIA', db.String(100))
    mediatype = db.Column('MEDIATYPE', db.String(50))
    source = db.Column('SOURCE', db.String(100))
    dateadded = db.Column('DATEADDED', db.Date)
    borrower = db.Column('BORROWER', db.String(100))
    datewatched = db.Column('DATEWATCHED', db.Date)
    userrating = db.Column('USERRATING', db.Float)
    rating = db.Column('RATING', db.Float)
    originaltitle = db.Column('ORIGINALTITLE', db.String(200))
    translatedtitle = db.Column('TRANSLATEDTITLE', db.String(200))
    formattedtitle = db.Column('FORMATTEDTITLE', db.String(200))
    director = db.Column('DIRECTOR', db.String(200))
    producer = db.Column('PRODUCER', db.String(200))
    writer = db.Column('WRITER', db.String(200))
    composer = db.Column('COMPOSER', db.String(200))
    actors = db.Column('ACTORS', db.Text)
    country = db.Column('COUNTRY', db.String(100))
    year = db.Column('YEAR', db.Integer)
    length = db.Column('LENGTH', db.Integer)
    category = db.Column('CATEGORY', db.String(100))
    certification = db.Column('CERTIFICATION', db.String(50))
    url = db.Column('URL', db.String(500))
    description = db.Column('DESCRIPTION', db.Text)
    comments = db.Column('COMMENTS', db.Text)
    filepath = db.Column('FILEPATH', db.String(500))
    videoformat = db.Column('VIDEOFORMAT', db.String(50))
    videobitrate = db.Column('VIDEOBITRATE', db.Integer)
    audioformat = db.Column('AUDIOFORMAT', db.String(50))
    audiobitrate = db.Column('AUDIOBITRATE', db.Integer)
    resolution = db.Column('RESOLUTION', db.String(50))
    framerate = db.Column('FRAMERATE', db.String(20))
    languages = db.Column('LANGUAGES', db.String(200))
    subtitles = db.Column('SUBTITLES', db.String(200))
    filesize = db.Column('FILESIZE', db.String(50))
    disks = db.Column('DISKS', db.Integer)
    picturestatus = db.Column('PICTURESTATUS', db.String(50))
    nbextras = db.Column('NBEXTRAS', db.Integer)
    picturename = db.Column('PICTURENAME', db.String(200))

    # Helpers seguros para formato de fecha
    def dateadded_str(self):
        if self.dateadded is None:
            return ''
        try:
            return self.dateadded.isoformat()
        except Exception:
            return str(self.dateadded)

    def datewatched_str(self):
        if self.datewatched is None:
            return ''
        try:
            return self.datewatched.isoformat()
        except Exception:
            return str(self.datewatched)

    extras = db.relationship('Extra', backref='movie', lazy=True)

    def __repr__(self):
        return f'<Movie {self.num}: {self.originaltitle or self.translatedtitle or self.formattedtitle}>'
    
    @property
    def title(self):
        """Retorna el primer título no vacío siguiendo la prioridad: original, traducido, formateado"""
        return self.originaltitle or self.translatedtitle or self.formattedtitle or f"Video #{self.num}"


class Extra(db.Model):
    """Modelo para almacenar contenido adicional relacionado con videos"""
    __tablename__ = 'extras'

    num = db.Column('NUM', db.Integer, primary_key=True)
    movienum = db.Column('MOVIENUM', db.Integer, db.ForeignKey('movies.NUM'), primary_key=True)
    checked = db.Column('CHECKED', db.String(5))
    tag = db.Column('TAG', db.String(100))
    title = db.Column('TITLE', db.String(200))
    category = db.Column('CATEGORY', db.String(100))
    url = db.Column('URL', db.String(500))
    description = db.Column('DESCRIPTION', db.Text)
    comments = db.Column('COMMENTS', db.Text)
    createdby = db.Column('CREATEDBY', db.String(100))
    picturestatus = db.Column('PICTURESTATUS', db.String(50))

    def __repr__(self):
        return f'<Extra {self.num} for Movie {self.movienum}: {self.title}>'