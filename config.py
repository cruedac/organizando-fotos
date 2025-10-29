import os

# Hacer opcional python-dotenv para entornos limitados
try:
    from dotenv import load_dotenv  # type: ignore
except Exception:  # ImportError o cualquier fallo
    def load_dotenv(*args, **kwargs):  # type: ignore
        return False

# Cargar variables de entorno si está disponible
load_dotenv()

class Config:
    # Configuración básica
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    
    # Configuración de la base de datos
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASEDIR, 'data', 'multimedia.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración de archivos
    # Permite analizar vídeos/fotos pesados sin abortar la petición (1 GB)
    MAX_CONTENT_LENGTH = 1024 * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(BASEDIR, 'uploads')
    
    # Extensiones permitidas (movidas desde create_db.py)
    ALLOWED_EXTENSIONS = {
        'image': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.heic', '.svg', '.raw', '.cr2', '.cr3'},
        'video': {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv'},
        'audio': {'.mp3', '.wav', '.ogg', '.aac', '.flac'}
    }