from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from config import Config

# Inicializar extensiones
db = SQLAlchemy()
cache = Cache()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Configurar cache simple en memoria
    app.config['CACHE_TYPE'] = 'simple'
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # 5 minutos
    
    # Inicializar extensiones
    db.init_app(app)
    cache.init_app(app)
    
    # Asegurarse de que existan los directorios necesarios
    import os
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    # Directorio para logs y reportes de importación
    logs_dir = os.path.join(os.path.dirname(app.instance_path), 'logs')
    reports_dir = os.path.join(os.path.dirname(app.instance_path), 'data', 'import_reports')
    os.makedirs(logs_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    # Configurar logging a fichero (rotating)
    try:
        import logging
        from logging.handlers import RotatingFileHandler
        log_file = os.path.join(logs_dir, 'app.log')
        handler = RotatingFileHandler(log_file, maxBytes=2 * 1024 * 1024, backupCount=5, encoding='utf-8')
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
        handler.setFormatter(formatter)
        if not app.logger.handlers:
            app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Aplicación iniciada, logger a fichero configurado.')
    except Exception as e:
        app.logger.warning('No se pudo configurar logging a fichero: %s', e)
    
    # Registrar blueprints
    from .routes import main, api, maintenance, tables, videos, photos
    app.register_blueprint(main.bp)
    app.register_blueprint(api.bp, url_prefix='/api')
    app.register_blueprint(photos.bp)
    app.register_blueprint(maintenance.bp)
    app.register_blueprint(tables.bp)
    app.register_blueprint(videos.bp)
    
    # Crear las tablas de la base de datos y asegurar que el directorio data existe
    import os
    os.makedirs(os.path.dirname(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')), exist_ok=True)
    
    with app.app_context():
        db.create_all()
    from .models.database import (
        ensure_table_field_description_column,
        ensure_photos_scan_table,
        ensure_photos_scan_summary_table,
    )
    ensure_table_field_description_column(app)
    ensure_photos_scan_table(app)
    ensure_photos_scan_summary_table(app)
        
    # Inicializar extensiones de archivo
    from .models.database import FileType, init_existing_tables
    FileType.init_db(app)
    init_existing_tables(app)

    # Ejecutar archivo SQL legacy para poblar la base de datos con películas
    from .services.video_import import import_sql_file
    import os
    if os.getenv('IMPORT_LEGACY_SQL', '').lower() in ['1', 'true', 'yes']:
        import_sql_file(app=app)
    else:
        app.logger.info('IMPORT_LEGACY_SQL no activado. Para ejecutar Cintas.sql establece IMPORT_LEGACY_SQL=1 en el entorno.')
    
    return app