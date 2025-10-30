from app import db
from datetime import datetime

class PhotoScanSummary(db.Model):
    """Modelo para el resumen de escaneo de fotos"""
    __tablename__ = 'photos_scan_summary'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    # Columnas originales de la tabla
    path = db.Column(db.String(500))
    directories_count = db.Column(db.Integer, default=0)
    num_images = db.Column(db.Integer, default=0)
    num_videos = db.Column(db.Integer, default=0)
    year = db.Column(db.Integer)
    month_number = db.Column(db.Integer)
    month_text = db.Column(db.String(20))
    total_size = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Nuevas columnas
    directory = db.Column(db.String(500))
    scan_date = db.Column(db.DateTime, default=datetime.now)
    total_files = db.Column(db.Integer, default=0)
    processed_files = db.Column(db.Integer, default=0)
    failed_files = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='pending')
    details = db.Column(db.Text)

    def __repr__(self):
        return f'<PhotoScanSummary {self.path or self.directory}>'

    def to_dict(self):
        return {
            'id': self.id,
            'path': self.path,
            'directories_count': self.directories_count,
            'num_images': self.num_images,
            'num_videos': self.num_videos,
            'year': self.year,
            'month_number': self.month_number,
            'month_text': self.month_text,
            'total_size': self.total_size,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'directory': self.directory,
            'scan_date': self.scan_date.isoformat() if self.scan_date else None,
            'total_files': self.total_files,
            'processed_files': self.processed_files,
            'failed_files': self.failed_files,
            'status': self.status,
            'details': self.details
        }

    @staticmethod
    def get_status_choices():
        return ['pending', 'in_progress', 'completed', 'failed']