from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

# Inicializar extensiones
db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Inicializar extensiones
    db.init_app(app)
    
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
        print(f'No se pudo configurar logging a fichero: {e}')
    
    # Registrar blueprints
    from .routes import main, api, maintenance, tables, videos
    app.register_blueprint(main.bp)
    app.register_blueprint(api.bp, url_prefix='/api')
    app.register_blueprint(maintenance.bp)
    app.register_blueprint(tables.bp)
    app.register_blueprint(videos.bp)
    
    # Crear las tablas de la base de datos y asegurar que el directorio data existe
    import os
    os.makedirs(os.path.dirname(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')), exist_ok=True)
    
    with app.app_context():
        db.create_all()
        
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
        print('IMPORT_LEGACY_SQL no activado. Para ejecutar Cintas.sql establece IMPORT_LEGACY_SQL=1 en el entorno.')
    
    return app