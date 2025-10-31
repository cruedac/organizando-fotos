"""
Database schema definitions package.

Importa todos los módulos de esquema para facilitar el acceso.
"""

from database.schema import file_types
from database.schema import movies
from database.schema import support_types
from database.schema import photo_scans
from database.schema import dynamic_tables

__all__ = [
    'file_types',
    'movies',
    'support_types',
    'photo_scans',
    'dynamic_tables',
]
