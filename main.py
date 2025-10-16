import os
import tkinter as tk
from tkinter import filedialog, messagebox

# Listas de extensiones conocidas para cada tipo de archivo
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".wmv", ".flv", ".mkv"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".aac", ".flac"}

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Organizador de Fotos")
        self.root.geometry("600x400")

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
        
        self.lbl_media_info = tk.Label(self.main_frame, text="No se ha detectado contenido multimedia.")
        self.lbl_media_info.pack(pady=10)

    def select_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.lbl_folder_path.config(text=folder_path)
            img_count, vid_count, aud_count = self.scan_for_media(folder_path)
            info = (
                f"Imágenes: {img_count}\n"
                f"Videos: {vid_count}\n"
                f"Audios: {aud_count}"
            )
            self.lbl_media_info.config(text=info)
        else:
            self.lbl_folder_path.config(text="Ninguna carpeta seleccionada")
            self.lbl_media_info.config(text="No se ha detectado contenido multimedia.")

    def scan_for_media(self, folder_path):
        img_count = vid_count = aud_count = 0
        for filename in os.listdir(folder_path):
            _, ext = os.path.splitext(filename.lower())
            if ext in IMAGE_EXTENSIONS:
                img_count += 1
            elif ext in VIDEO_EXTENSIONS:
                vid_count += 1
            elif ext in AUDIO_EXTENSIONS:
                aud_count += 1
        return img_count, vid_count, aud_count

if __name__ == "__main__":
    main_window = tk.Tk()
    app = App(main_window)
    main_window.mainloop()
