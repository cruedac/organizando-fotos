# AI Agent Instructions for organizando-fotos

This document provides essential context for AI agents working with the organizando-fotos codebase, a Python desktop application for organizing multimedia files.

## Project Architecture

### Core Components

1. **GUI Application** (`main_app.py`)
   - Built with PySide6 (Qt)
   - Main window class: `DatabaseApp`
   - Handles user interface and database interactions

2. **Database Layer** (`database/`)
   - SQLite3-based storage
   - Key files:
     - `create_db.py`: Database initialization and schema
     - `utils.py`: Database operation utilities

### Data Flow
- User interactions → GUI (`main_app.py`) → Database utilities (`database/utils.py`) → SQLite database (`data/multimedia.db`)

## Development Setup

1. **Environment Setup**
```bash
pip install -r requirements.txt
```

2. **Database Initialization**
```bash
python database/create_db.py
```

## Key Patterns and Conventions

### Database Operations
- All database operations are abstracted in `database/utils.py`
- Standard CRUD functions:
  - `fetch_all(table)`: Retrieve all records
  - `fetch_columns(table)`: Get table structure
  - `insert_record(table, columns, values)`
  - `update_record(table, columns, values, record_id)`
  - `delete_record(table, record_id)`

### Supported Media Types
- Images: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff`, `.webp`, `.heic`, `.svg`, `.raw`, `.CR2`, `.CR3`
- Videos: `.mp4`, `.avi`, `.mov`, `.wmv`, `.flv`, `.mkv`
- Audio: `.mp3`, `.wav`, `.ogg`, `.aac`, `.flac`

### Project Structure
```
.
├── main_app.py      # Main GUI application
├── database/        # Database operations
│   ├── create_db.py # Database initialization
│   └── utils.py     # Database utilities
├── data/           # Data storage directory
│   └── multimedia.db
└── requirements.txt # Dependencies
```

## Development Guidelines
1. Use type hints for function parameters and return values
2. Follow PySide6 patterns for UI components
3. Keep database operations centralized in `database/utils.py`
4. Use the predefined media type constants in `create_db.py` for file type validation