"""
Servicio de cacheo para tipos de soporte.
Proporciona acceso cacheado a los tipos de soporte desde la base de datos.
"""
from app import cache
from app.models.database import TipoSoporte


@cache.memoize(timeout=300)
def get_support_types_cached():
    """
    Obtiene todos los tipos de soporte desde la base de datos con cacheo.
    
    Returns:
        list: Lista de objetos TipoSoporte ordenados alfabéticamente.
    """
    return TipoSoporte.query.order_by(TipoSoporte.tipo).all()


def clear_support_types_cache():
    """
    Limpia el cache de tipos de soporte.
    Debe llamarse cuando se modifican tipos de soporte en la base de datos.
    """
    cache.delete_memoized(get_support_types_cached)
