#!/usr/bin/env python
"""Script de prueba para verificar la funcionalidad del scanner"""
import os
import tempfile
from pathlib import Path

# Crear un directorio temporal con archivos de prueba
test_dir = Path(tempfile.mkdtemp(prefix='test_scan_'))
print(f"Directorio de prueba creado: {test_dir}")

# Crear algunos archivos de prueba
test_files = [
    'image1.jpg',
    'image2.png',
    'video1.mp4',
    'video2.avi',
    'audio1.mp3',
    'document.txt'
]

for filename in test_files:
    file_path = test_dir / filename
    file_path.write_text(f"Test file: {filename}")
    print(f"  Creado: {filename}")

# Crear un subdirectorio con más archivos
subdir = test_dir / 'subdir'
subdir.mkdir()
for i in range(3):
    file_path = subdir / f'photo{i}.jpg'
    file_path.write_text(f"Test photo {i}")
    print(f"  Creado: subdir/photo{i}.jpg")

print(f"\n✅ Directorio de prueba listo: {test_dir}")
print(f"\nPuedes usar esta ruta en el scanner:")
print(f"  {test_dir}")
print(f"\nPara limpiar después:")
print(f"  rm -rf {test_dir}")
