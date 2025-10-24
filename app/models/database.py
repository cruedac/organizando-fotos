from app import db
from datetime import datetime
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
                            default_value=str(column.get('default', '')) if column.get('default') is not None else None,
                            description=None
                        )
                        db.session.add(field)
                    db.session.commit()


def ensure_table_field_description_column(app):
    """Garantiza que la tabla table_field disponga de la columna description."""
    with app.app_context():
        inspector = inspect(db.engine)
        if 'table_field' not in inspector.get_table_names():
            return

        column_names = {col['name'] for col in inspector.get_columns('table_field')}
        if 'description' in column_names:
            return

        with db.engine.begin() as connection:
            connection.execute(text('ALTER TABLE table_field ADD COLUMN description VARCHAR(255)'))


def ensure_photos_scan_table(app):
    """Crea o actualiza la tabla photos_scan según el modelo actual."""
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        if 'photos_scan' not in tables:
            PhotoScan.__table__.create(bind=db.engine)
            return

        column_names = {col['name'] for col in inspector.get_columns('photos_scan')}

        if 'mont_text' in column_names and 'month_text' not in column_names:
            try:
                with db.engine.begin() as connection:
                    connection.execute(text('ALTER TABLE photos_scan RENAME COLUMN mont_text TO month_text'))
            except Exception:
                with db.engine.begin() as connection:
                    connection.execute(text('ALTER TABLE photos_scan ADD COLUMN month_text VARCHAR(50)'))
                    connection.execute(text('UPDATE photos_scan SET month_text = mont_text WHERE month_text IS NULL'))

        # Refresh inspector state after potential rename/add
        inspector = inspect(db.engine)
        column_names = {col['name'] for col in inspector.get_columns('photos_scan')}

        statements = []
        if 'last_scan' not in column_names:
            statements.append('ALTER TABLE photos_scan ADD COLUMN last_scan DATETIME')
        if 'created_at' not in column_names:
            statements.append('ALTER TABLE photos_scan ADD COLUMN created_at DATETIME')
        if 'year' not in column_names:
            statements.append('ALTER TABLE photos_scan ADD COLUMN year INTEGER')
        if 'month_number' not in column_names:
            statements.append('ALTER TABLE photos_scan ADD COLUMN month_number INTEGER')
        if 'month_text' not in column_names:
            statements.append('ALTER TABLE photos_scan ADD COLUMN month_text VARCHAR(50)')
        if 'total_size' not in column_names:
            statements.append('ALTER TABLE photos_scan ADD COLUMN total_size BIGINT DEFAULT 0')

        if statements:
            with db.engine.begin() as connection:
                for stmt in statements:
                    connection.execute(text(stmt))


def ensure_photos_scan_summary_table(app):
    """Crea o ajusta la tabla photos_scan_summary para reflejar el modelo actual."""
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        if 'photos_scan_summary' not in tables:
            PhotoScanSummary.__table__.create(bind=db.engine)
            return

        column_names = {col['name'] for col in inspector.get_columns('photos_scan_summary')}
        statements = []

        if 'path' not in column_names:
            statements.append('ALTER TABLE photos_scan_summary ADD COLUMN path VARCHAR(255) NOT NULL DEFAULT ""')
        if 'directories_count' not in column_names:
            statements.append('ALTER TABLE photos_scan_summary ADD COLUMN directories_count INTEGER NOT NULL DEFAULT 0')
        if 'num_images' not in column_names:
            statements.append('ALTER TABLE photos_scan_summary ADD COLUMN num_images INTEGER NOT NULL DEFAULT 0')
        if 'num_videos' not in column_names:
            statements.append('ALTER TABLE photos_scan_summary ADD COLUMN num_videos INTEGER NOT NULL DEFAULT 0')
        if 'year' not in column_names:
            statements.append('ALTER TABLE photos_scan_summary ADD COLUMN year INTEGER')
        if 'month_number' not in column_names:
            statements.append('ALTER TABLE photos_scan_summary ADD COLUMN month_number INTEGER')
        if 'month_text' not in column_names:
            statements.append('ALTER TABLE photos_scan_summary ADD COLUMN month_text VARCHAR(50)')
        if 'total_size' not in column_names:
            statements.append('ALTER TABLE photos_scan_summary ADD COLUMN total_size BIGINT NOT NULL DEFAULT 0')
        if 'created_at' not in column_names:
            statements.append('ALTER TABLE photos_scan_summary ADD COLUMN created_at DATETIME')

        if statements:
            with db.engine.begin() as connection:
                for stmt in statements:
                    connection.execute(text(stmt))

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
    description = db.Column(db.String(255))
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


class TipoSoporte(db.Model):
    """Catálogo de tipos de soporte físico o digital para los videos."""
    __tablename__ = 'tipo_soporte'

    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<TipoSoporte {self.tipo}>'


class PhotoScan(db.Model):
    """Registro resumido de resultados de escaneos de carpetas de fotos."""
    __tablename__ = 'photos_scan'

    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(255), nullable=False)
    parent_path = db.Column(db.String(255))
    end_name = db.Column(db.String(255))
    num_images = db.Column(db.Integer, default=0, nullable=False)
    num_videos = db.Column(db.Integer, default=0, nullable=False)
    media_types = db.Column(db.String(500))
    last_scan = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    year = db.Column(db.Integer)
    month_number = db.Column(db.Integer)
    month_text = db.Column(db.String(50))
    total_size = db.Column(db.BigInteger, nullable=False, default=0)

    def __repr__(self):
        return f'<PhotoScan {self.path} ({self.last_scan:%Y-%m-%d %H:%M:%S})>'


class PhotoScanSummary(db.Model):
    """Resumen agregado por escaneo de la sección de fotos."""
    __tablename__ = 'photos_scan_summary'

    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(255), nullable=False)
    directories_count = db.Column(db.Integer, nullable=False, default=0)
    num_images = db.Column(db.Integer, nullable=False, default=0)
    num_videos = db.Column(db.Integer, nullable=False, default=0)
    year = db.Column(db.Integer)
    month_number = db.Column(db.Integer)
    month_text = db.Column(db.String(50))
    total_size = db.Column(db.BigInteger, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<PhotoScanSummary {self.path} ({self.created_at:%Y-%m-%d %H:%M:%S})>'
