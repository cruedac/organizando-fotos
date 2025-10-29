#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test de verificación de optimizaciones
Verifica que todos los componentes estén en su lugar
"""
import os
import sys
import sqlite3
from pathlib import Path

def test_files_exist():
    """Verifica que los archivos nuevos existan"""
    print("📁 Verificando archivos creados...")
    files = {
        'app/services/file_type_cache.py': 'Servicio de cacheo de extensiones',
        'app/services/support_type_cache.py': 'Servicio de cacheo de tipos de soporte',
        'app/services/date_utils.py': 'Utilidades de fechas consolidadas',
        'RESUMEN_OPTIMIZACIONES.md': 'Documentación de optimizaciones',
        'deploy_optimizations.py': 'Script de despliegue'
    }
    
    all_ok = True
    for file, description in files.items():
        exists = Path(file).exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {file} - {description}")
        if not exists:
            all_ok = False
    
    return all_ok

def test_cache_imports():
    """Verifica que los imports de cache estén correctos"""
    print("\n📦 Verificando imports de cache...")
    
    files_to_check = {
        'app/__init__.py': ['from flask_caching import Cache', 'cache = Cache()'],
        'app/routes/api.py': ['from app.services.file_type_cache import get_allowed_extensions_cached'],
        'app/routes/maintenance.py': ['from app.services.file_type_cache import clear_extensions_cache',
                                       'from app.services.support_type_cache import clear_support_types_cache']
    }
    
    all_ok = True
    for file, patterns in files_to_check.items():
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                for pattern in patterns:
                    if pattern in content:
                        print(f"  ✓ {file}: '{pattern[:40]}...' encontrado")
                    else:
                        print(f"  ✗ {file}: '{pattern[:40]}...' NO encontrado")
                        all_ok = False
        except Exception as e:
            print(f"  ✗ Error leyendo {file}: {e}")
            all_ok = False
    
    return all_ok

def test_indices():
    """Verifica que los índices existan en la BD"""
    print("\n🗃️  Verificando índices en la base de datos...")
    
    db_path = 'data/multimedia.db'
    if not Path(db_path).exists():
        print(f"  ⚠ Base de datos no encontrada: {db_path}")
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='movies'")
        if not cursor.fetchone():
            print("  ⚠ Tabla 'movies' no encontrada")
            conn.close()
            return None
        
        expected_indices = ['idx_movie_year', 'idx_movie_category', 'idx_movie_mediatype']
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        existing_indices = [row[0] for row in cursor.fetchall()]
        
        all_ok = True
        for idx in expected_indices:
            if idx in existing_indices:
                print(f"  ✓ Índice '{idx}' existe")
            else:
                print(f"  ✗ Índice '{idx}' NO existe")
                all_ok = False
        
        conn.close()
        return all_ok
        
    except Exception as e:
        print(f"  ✗ Error verificando índices: {e}")
        return False

def test_model_indices():
    """Verifica que el modelo Movie tenga índices definidos"""
    print("\n🏗️  Verificando definición de índices en modelo...")
    
    try:
        with open('app/models/movie.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        checks = [
            ('__table_args__', 'Definición de índices'),
            ('idx_movie_year', 'Índice de año'),
            ('idx_movie_category', 'Índice de categoría'),
            ('idx_movie_mediatype', 'Índice de tipo de medio')
        ]
        
        all_ok = True
        for pattern, description in checks:
            if pattern in content:
                print(f"  ✓ {description} definido")
            else:
                print(f"  ✗ {description} NO definido")
                all_ok = False
        
        return all_ok
        
    except Exception as e:
        print(f"  ✗ Error leyendo modelo: {e}")
        return False

def test_consolidated_scripts():
    """Verifica que los scripts usen date_utils"""
    print("\n🔧 Verificando consolidación de scripts...")
    
    scripts = {
        'database/migrate_dates.py': 'from app.services.date_utils import normalize_date_value',
        'database/check_values_len.py': 'from app.services.date_utils import normalize_date_value'
    }
    
    all_ok = True
    for script, import_line in scripts.items():
        try:
            with open(script, 'r', encoding='utf-8') as f:
                content = f.read()
                if import_line in content:
                    print(f"  ✓ {script} usa date_utils")
                else:
                    print(f"  ✗ {script} NO usa date_utils")
                    all_ok = False
        except Exception as e:
            print(f"  ✗ Error leyendo {script}: {e}")
            all_ok = False
    
    return all_ok

def test_requirements():
    """Verifica que Flask-Caching esté en requirements.txt"""
    print("\n📋 Verificando requirements.txt...")
    
    try:
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'Flask-Caching' in content:
                print("  ✓ Flask-Caching está en requirements.txt")
                return True
            else:
                print("  ✗ Flask-Caching NO está en requirements.txt")
                return False
    except Exception as e:
        print(f"  ✗ Error leyendo requirements.txt: {e}")
        return False

def main():
    """Ejecuta todos los tests"""
    print("="*60)
    print("TEST DE VERIFICACIÓN DE OPTIMIZACIONES")
    print("="*60)
    
    results = []
    
    results.append(("Archivos nuevos", test_files_exist()))
    results.append(("Imports de cache", test_cache_imports()))
    results.append(("Índices en modelo", test_model_indices()))
    results.append(("Índices en BD", test_indices()))
    results.append(("Scripts consolidados", test_consolidated_scripts()))
    results.append(("Requirements.txt", test_requirements()))
    
    print("\n" + "="*60)
    print("RESUMEN DE VERIFICACIÓN")
    print("="*60)
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test_name, result in results:
        if result is True:
            print(f"✓ {test_name}: PASADO")
            passed += 1
        elif result is False:
            print(f"✗ {test_name}: FALLIDO")
            failed += 1
        else:
            print(f"⚠ {test_name}: OMITIDO")
            skipped += 1
    
    print(f"\nTotal: {passed} pasados, {failed} fallidos, {skipped} omitidos")
    
    if failed == 0:
        print("\n✓ ¡Todas las optimizaciones están correctamente implementadas!")
        return True
    else:
        print(f"\n⚠ Algunas verificaciones fallaron. Revisa los detalles arriba.")
        return False

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Error inesperado: {e}")
        sys.exit(1)
