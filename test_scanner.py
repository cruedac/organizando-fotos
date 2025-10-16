import os
import shutil
from pathlib import Path
from utils.file_scanner import scan_for_media_recursive

def create_test_files(base_dir):
    """Crea una estructura de carpetas y archivos para pruebas."""
    # Crear estructura de carpetas
    paths = {
        'images': base_dir / 'photos',
        'videos': base_dir / 'videos',
        'audio': base_dir / 'music',
        'others': base_dir / 'docs'
    }
    
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)

    # Crear archivos de prueba (0-byte files)
    test_files = [
        # Imágenes
        paths['images'] / 'photo1.jpg',
        paths['images'] / 'photo2.png',
        paths['images'] / 'photo3.gif',
        paths['images'] / '.hidden.jpg',  # archivo oculto
        # Videos
        paths['videos'] / 'video1.mp4',
        paths['videos'] / 'video2.avi',
        # Audio
        paths['audio'] / 'song1.mp3',
        paths['audio'] / 'song2.wav',
        # Otros
        paths['others'] / 'doc1.pdf',
        paths['others'] / 'doc2.txt',
        paths['others'] / 'noextension'
    ]
    
    for file in test_files:
        file.touch()
    
    return base_dir

def cleanup_test_files(base_dir):
    """Elimina los archivos y carpetas de prueba."""
    shutil.rmtree(base_dir)

def run_test():
    """Ejecuta prueba completa de escaneo."""
    # Crear directorio temporal para pruebas
    test_dir = Path('test_media_files')
    
    try:
        # Crear archivos de prueba
        print("Creando archivos de prueba...")
        create_test_files(test_dir)
        
        # Escanear directorio
        print("\nEscaneando directorio...")
        result = scan_for_media_recursive(str(test_dir))
        
        # Mostrar resultados
        print("\nResultados del escaneo:")
        print("------------------------")
        print(f"Imágenes: {result['totals']['image']}")
        print(f"Videos: {result['totals']['video']}")
        print(f"Audios: {result['totals']['audio']}")
        print(f"Otros: {result['totals']['other']}")
        print("\nArchivos por extensión:")
        for ext, count in sorted(result['by_extension'].items()):
            print(f"{ext}: {count}")
            
        # Validar resultados esperados
        expected = {
            'image': 4,  # 3 imágenes normales + 1 oculta
            'video': 2,
            'audio': 2,
            'other': 3  # 2 docs + 1 sin extensión
        }
        
        print("\nValidación:")
        print("-----------")
        all_correct = True
        for category, expected_count in expected.items():
            actual = result['totals'][category]
            is_correct = actual == expected_count
            print(f"{category}: esperado={expected_count}, obtenido={actual} {'✓' if is_correct else '✗'}")
            if not is_correct:
                all_correct = False
        
        if all_correct:
            print("\n✅ Todas las validaciones pasaron correctamente")
        else:
            print("\n❌ Algunas validaciones fallaron")
            
    finally:
        # Limpiar archivos temporales
        print("\nLimpiando archivos de prueba...")
        cleanup_test_files(test_dir)
        print("Prueba completada.")

if __name__ == '__main__':
    run_test()