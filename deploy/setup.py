from setuptools import setup
from Cython.Build import cythonize
import os

# Buscar todos los archivos .py para compilar
py_files = []
for root, dirs, files in os.walk("app"):
    for file in files:
        if file.endswith('.py') and file != '__init__.py':
            py_files.append(os.path.join(root, file))

# Compilar a .so (Linux) o .pyd (Windows)
setup(
    name='organizando-fotos-compiled',
    ext_modules=cythonize(
        py_files,
        compiler_directives={
            'language_level': 3,
            'boundscheck': False,
            'wraparound': False
        }
    ),
    zip_safe=False,
)