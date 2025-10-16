import os
import sqlite3
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Dict, Set

def get_extensions_from_db() -> Dict[str, Set[str]]:
    """Obtiene las extensiones por tipo desde la tabla file_types.
    
    Returns:
        Dict con claves 'image', 'video', 'audio' y valores como sets de extensiones
    """
    try:
        conn = sqlite3.connect('data/multimedia.db')
        cursor = conn.cursor()
        cursor.execute("SELECT extension, type FROM file_types")
        results = cursor.fetchall()
        
        extensions = {
            'image': set(),
            'video': set(),
            'audio': set()
        }
        
        for ext, type_ in results:
            if type_ in extensions:
                extensions[type_].add(ext.lower())
        
        return extensions
    except Exception as e:
        print(f"Error al leer extensiones de BD: {e}")
        # Valores por defecto si hay error
        return {
            'image': {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"},
            'video': {".mp4", ".avi", ".mov", ".wmv", ".flv", ".mkv"},
            'audio': {".mp3", ".wav", ".ogg", ".aac", ".flac"}
        }
    finally:
        if 'conn' in locals():
            conn.close()

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Organizador de Fotos")
        self.root.geometry("700x500")
        
        # Cargar extensiones desde la base de datos
        self.extensions = get_extensions_from_db()
        
        self.main_frame = tk.Frame(self.root, padx=10, pady=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.btn_select_folder = tk.Button(
            self.main_frame,
            text="Seleccionar Carpeta",
            command=self.select_folder
        )
        self.btn_select_folder.pack(pady=10)

        self.lbl_folder_path = tk.Label(self.main_frame, text="Ninguna carpeta seleccionada")
        self.lbl_folder_path.pack(pady=5)
        
        self.lbl_media_info = tk.Label(
            self.main_frame,
            text="No se ha detectado contenido multimedia.",
            justify=tk.LEFT,
            anchor="w"
        )
        self.lbl_media_info.pack(fill=tk.BOTH, expand=False, pady=10)

    def select_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.lbl_folder_path.config(text=folder_path)
            result = self.scan_for_media_recursive(folder_path)
            # Construir texto legible con totales y desglose por extensión
            totals = result['totals']
            by_ext = result['by_extension']
            info_lines = [
                f"Imágenes: {totals.get('image',0)}",
                f"Videos: {totals.get('video',0)}",
                f"Audios: {totals.get('audio',0)}",
                f"Otros: {totals.get('other',0)}",
                "",
                "Desglose por extensión:"
            ]
            # Ordenar extensiones por conteo descendente
            for ext, cnt in sorted(by_ext.items(), key=lambda x: x[1], reverse=True):
                info_lines.append(f"{ext}: {cnt}")
            self.lbl_media_info.config(text="\n".join(info_lines))
        else:
            self.lbl_folder_path.config(text="Ninguna carpeta seleccionada")
            self.lbl_media_info.config(text="No se ha detectado contenido multimedia.")

    def scan_for_media_recursive(self, folder_path):
        """Recorre folder_path recursivamente y cuenta archivos por tipo y por extensión.

        Retorna un diccionario con dos claves:
        - 'totals': dict con llaves 'image','video','audio','other' y sus conteos
        - 'by_extension': dict mapeando extensión (incluyendo '.') a conteo
        """
        totals = {'image': 0, 'video': 0, 'audio': 0, 'other': 0}
        by_extension = {}

        for root, dirs, files in os.walk(folder_path):
            for fname in files:
                _, ext = os.path.splitext(fname)
                ext_norm = ext.strip().lower()
                if not ext_norm:
                    # Archivos sin extension cuentan como 'other' y usan clave '<no_ext>'
                    totals['other'] += 1
                    by_extension['<no_ext>'] = by_extension.get('<no_ext>', 0) + 1
                    continue

                if ext_norm in self.extensions['image']:
                    totals['image'] += 1
                elif ext_norm in self.extensions['video']:
                    totals['video'] += 1
                elif ext_norm in self.extensions['audio']:
                    totals['audio'] += 1
                else:
                    totals['other'] += 1

                by_extension[ext_norm] = by_extension.get(ext_norm, 0) + 1

        return {'totals': totals, 'by_extension': by_extension}

if __name__ == "__main__":
    main_window = tk.Tk()
    app = App(main_window)
    main_window.mainloop()
