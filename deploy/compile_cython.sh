#!/bin/bash

# Script para compilar con Cython

# 1. Instalar dependencias
pip install cython setuptools

# 2. Compilar
python setup.py build_ext --inplace

# 3. Crear paquete de distribución
python setup.py bdist_wheel

echo "Código compilado. Los archivos .so/.pyd reemplazan los .py originales"