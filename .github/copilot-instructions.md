# AI Agent Instructions for organizando-fotos

- **Bootstrapping**
  - Create a venv and `pip install -r requirements.txt`; copy `.env.example` to `.env` before launching.
  - App starts via `python run.py`, which calls `create_app` in `app/__init__.py`. That factory seeds directories (`uploads/`, `logs/`, `data/import_reports/`), wires blueprints, and runs `db.create_all()`.
  - Logging is preconfigured with a rotating handler that writes UTF-8 logs to `logs/app.log`; reuse the logger instead of printing when possible.

- **Architecture Overview**
  - Blueprints live in `app/routes/`: `main` (UI + directory scanning), `maintenance` (DB health, backups, exports), `tables` (dynamic schema builder), `videos` (legacy catalogue CRUD), `api` (JSON endpoints mirroring scanner features).
  - Business logic sits in `app/services/`; models are in `app/models/`. Keep route handlers thin—delegate new logic to a service when it spans multiple responsibilities.

- **Persistence & Models**
  - SQLite DB path is `data/multimedia.db` (see `Config.SQLALCHEMY_DATABASE_URI`). `FileType.init_db` seeds allowed extensions from `Config.ALLOWED_EXTENSIONS`; update that dict if you need new defaults.
  - `init_existing_tables` back-fills `DynamicTable`/`TableField` metadata for any pre-existing SQLite tables. When creating or dropping tables manually, ensure metadata stays aligned.
  - `Movie` model mirrors the legacy schema (uppercase column names); helper properties like `title` and `dateadded_str()` keep view/template code cleaner.

- **Dynamic Tables**
  - `app/routes/tables.py` orchestrates both metadata rows and physical schema changes using raw SQL (`ALTER TABLE`, `DROP TABLE`). Always go through helper functions like `_add_column_to_table` to keep defaults and type casting consistent (booleans stored as `INTEGER` 0/1, date/datetime stored as `TEXT`).
  - Deletion safeguards: tables cannot drop if FK references exist or if they contain rows—respect this flow when building admin actions.

- **Media Scanning Workflow**
  - `scan_for_media_recursive` normalises extensions to lowercase and counts totals/by-extension; it honours the `scan_subdirs` flag by switching between `os.walk` and a shallow listing. Both `main.scan_directory` and `api.scan_folder` fetch extensions from the DB, so extend `FileType` entries before expecting new formats to be recognised.
  - Windows drive and directory browsing for the UI lives in `main.list_drives` / `main.list_directory`; keep Windows path quirks in mind when accepting user input.

- **Video Catalogue**
  - Field definitions for forms/detail views are centralised in `videos.py` (`MOVIE_FIELD_DEFINITIONS`). Any new field must be added there, to the template, and to the `Movie` model.
  - `VideoService.search_videos` composes filters with SQLAlchemy; reuse its helpers (`get_categories`, `get_media_types`, `get_years`) to keep dropdowns synchronized with DB contents.
  - Legacy imports: `app/services/video_import.py.import_sql_file` rewrites INSERTs to `INSERT OR IGNORE` and emits a JSON report to `data/import_reports/`. Enable by setting `IMPORT_LEGACY_SQL=1` before starting the app; interactive trigger is `/videos/import-legacy`.

- **Maintenance Blueprint**
  - `_get_database_info` compiles live stats using `sqlalchemy.inspect` and drives the dashboard plus `/maintenance/stats.json`. Backup/export actions stream files using `send_file`; prefer returning buffers rather than touching disk when adding formats.
  - Target paths supplied by users are normalised with `pathlib.Path`; keep using that approach to avoid Windows/Unix path issues.

- **Utilities & Scripts**
  - Standalone data scripts live under `database/` (e.g., `migrate_dates.py` normalises movie dates and writes reports). They derive the DB location from `config.Config`, so changes to the DB path must stay in sync.
  - Reports, logs, and backups are user-visible artefacts; avoid renaming directories without updating the creation logic in the app factory.

- **Testing & Verification**
  - No automated tests today; verify changes by running the Flask server and exercising affected blueprints. For DB migrations or dynamic table changes, inspect `data/multimedia.db` (e.g., with `sqlite3`) after running through the UI.