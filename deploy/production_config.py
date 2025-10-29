import os

class ProductionConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'tu-clave-secreta-muy-segura-aqui'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_PATH') or 'sqlite:///multimedia.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración de archivos
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024 * 1024  # 1GB
    UPLOAD_FOLDER = '/var/www/organizando-fotos/uploads'
    
    # Extensiones permitidas
    ALLOWED_EXTENSIONS = {
        'image': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'},
        'video': {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'},
        'audio': {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'}
    }
    
    # Desactivar modo debug en producción
    DEBUG = False
    TESTING = False