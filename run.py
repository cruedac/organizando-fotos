from app import create_app
from app.models.database import FileType

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Inicializar la base de datos con las extensiones predefinidas
        FileType.init_db(app)
    app.run(debug=True)