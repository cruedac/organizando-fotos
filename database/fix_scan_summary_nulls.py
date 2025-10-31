"""
Script para arreglar valores NULL en PhotoScanSummary
"""
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app, db
from app.models.database import PhotoScanSummary
from datetime import datetime

def fix_null_values():
    """Actualiza registros con valores NULL a valores por defecto"""
    app = create_app()
    with app.app_context():
        # Buscar registros con scan_date NULL
        null_dates = PhotoScanSummary.query.filter(PhotoScanSummary.scan_date.is_(None)).all()
        print(f"Registros con scan_date NULL: {len(null_dates)}")
        
        if null_dates:
            # Actualizar con fecha por defecto
            for summary in null_dates:
                print(f"  - ID {summary.id}: {summary.path}")
                summary.scan_date = summary.created_at or datetime.utcnow()
                summary.directory = summary.directory or summary.path
                summary.total_files = summary.total_files or 0
                summary.processed_files = summary.processed_files or 0
                summary.failed_files = summary.failed_files or 0
                summary.status = summary.status or 'completed'
            
            db.session.commit()
            print(f"\n[OK] Actualizados {len(null_dates)} registros")
        else:
            print("[OK] No hay registros con scan_date NULL")

if __name__ == '__main__':
    fix_null_values()
