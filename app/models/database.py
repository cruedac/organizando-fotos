from app import db
from datetime import datetime
import sqlite3
from sqlalchemy import inspect, text

class FileType(db.Model):
    """Modelo para tipos de archivo y sus extensiones"""
    id = db.Column(db.Integer, primary_key=True)
    extension = db.Column(db.String(10), unique=True, nullable=False)
    type = db.Column(db.String(10), nullable=False)
    
    def __repr__(self):
        return f'<FileType {self.extension}>'
    
    @staticmethod
    def init_db(app):
        """Inicializa la tabla con las extensiones predefinidas"""
        with app.app_context():
            for media_type, extensions in app.config['ALLOWED_EXTENSIONS'].items():
                for ext in extensions:
                    if not FileType.query.filter_by(extension=ext).first():
                        file_type = FileType(extension=ext, type=media_type)
                        db.session.add(file_type)
            db.session.commit()

def init_existing_tables(app):
    """Sincroniza los modelos con las tablas existentes en la base de datos"""
    with app.app_context():
        # Obtener el inspector de SQLAlchemy
        inspector = inspect(db.engine)
        
        # Obtener todas las tablas existentes
        existing_tables = inspector.get_table_names()
        
        # Buscar tablas dinámicas (excluyendo las tablas del sistema)
        for table_name in existing_tables:
            if table_name not in ['file_types', 'dynamic_table', 'table_field']:
                # Verificar si ya existe en dynamic_table
                if not DynamicTable.query.filter_by(name=table_name).first():
                    # Crear entrada en dynamic_table
                    table = DynamicTable(name=table_name, description=f"Tabla existente: {table_name}")
                    db.session.add(table)
                    db.session.commit()
                    
                    # Obtener información de las columnas
                    columns = inspector.get_columns(table_name)
                    for column in columns:
                        # Crear entrada en table_field
                        field = TableField(
                            table_id=table.id,
                            name=column['name'],
                            field_type=str(column['type']).upper(),
                            is_required=not column['nullable'],
                            is_primary_key=column.get('primary_key', False),
                            is_auto_increment=column.get('autoincrement', False),
                            default_value=str(column.get('default', '')) if column.get('default') is not None else None
                        )
                        db.session.add(field)
                    db.session.commit()

class DynamicTable(db.Model):
    """Modelo para almacenar información sobre tablas dinámicas"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    fields = db.relationship('TableField', backref='table', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<DynamicTable {self.name}>'

class TableField(db.Model):
    """Modelo para almacenar los campos de las tablas dinámicas"""
    id = db.Column(db.Integer, primary_key=True)
    table_id = db.Column(db.Integer, db.ForeignKey('dynamic_table.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    field_type = db.Column(db.String(20), nullable=False)  # TEXT, INTEGER, REAL, DATE, etc.
    is_required = db.Column(db.Boolean, default=False)
    is_primary_key = db.Column(db.Boolean, default=False)
    is_auto_increment = db.Column(db.Boolean, default=False)
    default_value = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<TableField {self.name} ({self.field_type})>'

    class FieldTypes:
        TEXT = 'TEXT'
        INTEGER = 'INTEGER'
        REAL = 'REAL'
        DATE = 'DATE'
        DATETIME = 'DATETIME'
        BOOLEAN = 'BOOLEAN'
        
        @classmethod
        def choices(cls):
            return [
                (cls.TEXT, 'Texto'),
                (cls.INTEGER, 'Número Entero'),
                (cls.REAL, 'Número Decimal'),
                (cls.DATE, 'Fecha'),
                (cls.DATETIME, 'Fecha y Hora'),
                (cls.BOOLEAN, 'Sí/No')
            ]