"""
Servicio de cacheo para tipos de archivo.
Proporciona acceso cacheado a las extensiones permitidas desde la base de datos.
"""
from app import cache
from app.models.database import FileType


@cache.memoize(timeout=300)
def get_allowed_extensions_cached():
    """
    Obtiene todas las extensiones permitidas desde la base de datos con cacheo.
    
    Returns:
        dict: Diccionario {tipo: [extensiones]} donde tipo es 'image', 'video', 'audio'
              y extensiones es una lista de strings en minúsculas sin punto.
              
    Ejemplo:
        {
            'image': ['jpg', 'png', 'gif'],
            'video': ['mp4', 'avi', 'mkv'],
            'audio': ['mp3', 'wav', 'flac']
        }
    """
    file_types = FileType.query.all()
    
    extensions = {
        'image': [],
        'video': [],
        'audio': []
    }
    
    for ft in file_types:
        if ft.type in extensions:
            # Normalizar: minúsculas, sin punto inicial
            ext = ft.extension.lower().lstrip('.')
            extensions[ft.type].append(ext)
    
    return extensions


def clear_extensions_cache():
    """
    Limpia el cache de extensiones.
    Debe llamarse cuando se modifican tipos de archivo en la base de datos.
    """
    cache.delete_memoized(get_allowed_extensions_cached)
