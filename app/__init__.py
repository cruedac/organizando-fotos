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
    
    # Registrar blueprints
    from .routes import main, api, maintenance, tables
    app.register_blueprint(main.bp)
    app.register_blueprint(api.bp, url_prefix='/api')
    app.register_blueprint(maintenance.bp)
    app.register_blueprint(tables.bp)
    
    # Crear las tablas de la base de datos
    with app.app_context():
        db.create_all()
    
    return app