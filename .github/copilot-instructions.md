# AI Agent Instructions for organizando-fotos

This document provides essential context for AI agents working with the organizando-fotos codebase, a Flask web application for organizing multimedia files.

## Project Architecture

### Core Components

1. **Flask Web Application** (`app/`)
   - Built with Flask framework
   - Uses Flask-SQLAlchemy for ORM
   - Modular structure with Blueprints:
     - `main`: Core functionality
     - `maintenance`: System maintenance
     - `tables`: Dynamic table management
     - `api`: RESTful endpoints

2. **Database Layer** (`app/models/`)
   - SQLite3-based storage with SQLAlchemy ORM
   - Key models:
     - `FileType`: Media file type management
     - `DynamicTable`: Custom table definitions
     - `TableField`: Dynamic table field configurations

### Data Flow
- HTTP Requests → Flask Routes → SQLAlchemy Models → SQLite database
- File System Operations → File Scanner Service → JSON Response

## Development Setup

1. **Environment Setup**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.\.venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
```

2. **Application Setup**
```bash
# Set up environment variables
cp .env.example .env

# Run the application
python run.py
```

## Key Patterns and Conventions

### Database Operations
- ORM-based using SQLAlchemy
- Models in `app/models/database.py`:
  - `FileType`: Manages supported file extensions
  - `DynamicTable`: Defines custom table structures
  - `TableField`: Configures fields for dynamic tables
- Key operations:
  - Dynamic table creation and management
  - File type registration and validation
  - Database schema synchronization

### Supported Media Types
- Images: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff`, `.webp`, `.heic`, `.svg`, `.raw`, `.CR2`, `.CR3`
- Videos: `.mp4`, `.avi`, `.mov`, `.wmv`, `.flv`, `.mkv`
- Audio: `.mp3`, `.wav`, `.ogg`, `.aac`, `.flac`

### Project Structure
```
.
├── app/                # Flask application package
│   ├── __init__.py    # Application factory
│   ├── models/        # Database models
│   ├── routes/        # Route blueprints
│   ├── services/      # Business logic
│   ├── static/        # Static assets
│   └── templates/     # Jinja2 templates
├── data/              # Data directory
│   └── multimedia.db  # SQLite database
├── config.py          # Configuration
├── run.py            # Application entry point
└── requirements.txt   # Dependencies
```

## Development Guidelines
1. Follow Flask blueprint organization for modular code
2. Use type hints and docstrings for better documentation
3. Keep business logic in service modules
4. Leverage SQLAlchemy ORM for database operations
5. Use Bootstrap for responsive UI design