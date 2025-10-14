import tkinter as tk
from tkinter import filedialog, messagebox

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Organizador de Fotos")
        self.root.geometry("600x400")

        # --- Widgets ---
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

    def select_folder(self):
        """Abre un diálogo para seleccionar una carpeta y muestra la ruta."""
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.lbl_folder_path.config(text=folder_path)
            print(f"Carpeta seleccionada: {folder_path}")
        else:
            self.lbl_folder_path.config(text="Ninguna carpeta seleccionada")

if __name__ == "__main__":
    # Inicializar la aplicación
    main_window = tk.Tk()
    app = App(main_window)
    main_window.mainloop()

