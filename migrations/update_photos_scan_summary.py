from app import db, create_app
from app.models.database import PhotoScanSummary
from sqlalchemy import text

def migrate_photos_scan_summary():
    app = create_app()
    with app.app_context():
        # Obtener información actual de la tabla
        result = db.session.execute(text("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='photos_scan_summary'
        """))
        current_table = result.scalar()
        
        if current_table:
            # Guardar datos actuales
            result = db.session.execute(text("SELECT * FROM photos_scan_summary"))
            old_data = [dict(row) for row in result]
            
            # Renombrar tabla actual
            db.session.execute(text("ALTER TABLE photos_scan_summary RENAME TO photos_scan_summary_old"))
            
            # Crear nueva tabla con la estructura correcta
            db.session.execute(text("""
                CREATE TABLE photos_scan_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    directory VARCHAR(500) NOT NULL,
                    scan_date DATETIME NOT NULL,
                    total_files INTEGER NOT NULL DEFAULT 0,
                    processed_files INTEGER NOT NULL DEFAULT 0,
                    failed_files INTEGER NOT NULL DEFAULT 0,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    details TEXT
                )
            """))
            
            # Migrar datos si es posible
            if old_data:
                for row in old_data:
                    # Mapear campos antiguos a nuevos
                    new_data = {
                        'id': row.get('id'),
                        'directory': row.get('path', ''),  # asumiendo que 'path' era el campo anterior
                        'scan_date': row.get('created_at', 'CURRENT_TIMESTAMP'),
                        'total_files': row.get('num_images', 0) + row.get('num_videos', 0),
                        'processed_files': row.get('num_images', 0) + row.get('num_videos', 0),
                        'failed_files': 0,
                        'status': 'completed',
                        'details': f"Migrated from old structure. Original data: Directories: {row.get('directories_count', 0)}, Images: {row.get('num_images', 0)}, Videos: {row.get('num_videos', 0)}"
                    }
                    
                    # Insertar datos en la nueva tabla
                    insert_sql = """
                        INSERT INTO photos_scan_summary 
                        (id, directory, scan_date, total_files, processed_files, failed_files, status, details)
                        VALUES (:id, :directory, :scan_date, :total_files, :processed_files, :failed_files, :status, :details)
                    """
                    db.session.execute(text(insert_sql), new_data)
            
            # Confirmar cambios
            db.session.commit()
            
            # Eliminar tabla antigua
            db.session.execute(text("DROP TABLE photos_scan_summary_old"))
            db.session.commit()
            
            print("Migración completada con éxito")
        else:
            # Si la tabla no existe, créala
            PhotoScanSummary.__table__.create(db.engine)
            print("Tabla creada desde cero")

if __name__ == '__main__':
    migrate_photos_scan_summary()