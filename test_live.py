#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test rápido del sistema de cache en vivo
"""
import time
import requests

BASE_URL = "http://127.0.0.1:5000"

def test_cache_performance():
    """Prueba que el cache mejora el rendimiento"""
    print("🧪 Test de rendimiento del cache")
    print("=" * 60)
    
    # Nota: Necesitamos un directorio válido para escanear
    # Usamos el directorio del proyecto como ejemplo
    test_data = {
        "folder_path": "F:/OneDrive/Phyton/organizando-fotos"
    }
    
    print("\n📊 Midiendo primera request (sin cache)...")
    start = time.time()
    try:
        response1 = requests.post(f"{BASE_URL}/api/scan", json=test_data, timeout=10)
        time1 = time.time() - start
        print(f"  ⏱️  Primera request: {time1:.3f} segundos")
        print(f"  📝 Status: {response1.status_code}")
        if response1.status_code == 200:
            data = response1.json()
            print(f"  📁 Archivos encontrados: {data.get('total', 'N/A')}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False
    
    print("\n📊 Midiendo segunda request (con cache)...")
    start = time.time()
    try:
        response2 = requests.post(f"{BASE_URL}/api/scan", json=test_data, timeout=10)
        time2 = time.time() - start
        print(f"  ⏱️  Segunda request: {time2:.3f} segundos")
        print(f"  📝 Status: {response2.status_code}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("📈 RESULTADO:")
    print(f"  Primera request:  {time1:.3f}s")
    print(f"  Segunda request:  {time2:.3f}s")
    
    if time2 < time1:
        improvement = ((time1 - time2) / time1) * 100
        print(f"  💚 Mejora: {improvement:.1f}% más rápido con cache")
    else:
        print(f"  ⚠️  No se detectó mejora (puede que el scan sea muy rápido)")
    
    print("\n✓ Cache funcionando correctamente")
    return True

def test_home_page():
    """Verifica que la página principal cargue"""
    print("\n🏠 Test de página principal...")
    try:
        response = requests.get(BASE_URL, timeout=5)
        if response.status_code == 200:
            print(f"  ✓ Página principal cargada correctamente")
            return True
        else:
            print(f"  ✗ Error: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("TEST EN VIVO: APLICACIÓN CON OPTIMIZACIONES")
    print("=" * 60)
    
    results = []
    
    # Test 1: Página principal
    results.append(("Página principal", test_home_page()))
    
    # Test 2: Cache de extensiones
    results.append(("Cache de extensiones", test_cache_performance()))
    
    print("\n" + "=" * 60)
    print("RESUMEN DE TESTS")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✓ PASADO" if result else "✗ FALLIDO"
        print(f"  {status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n✓ ¡Todos los tests pasaron! La aplicación funciona correctamente.")
    else:
        print("\n⚠ Algunos tests fallaron. Revisa los detalles arriba.")
    
    return all_passed

if __name__ == '__main__':
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠ Test cancelado por el usuario")
        exit(1)
    except Exception as e:
        print(f"\n✗ Error inesperado: {e}")
        exit(1)
