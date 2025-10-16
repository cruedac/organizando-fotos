import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMenuBar, QMenu, QFileDialog,
    QTableWidget, QTableWidgetItem, QPushButton, QVBoxLayout,
    QWidget, QHBoxLayout, QMessageBox, QDialog, QLabel,
    QLineEdit, QFormLayout, QGroupBox, QComboBox, QCheckBox
)
from PySide6.QtCore import Qt

from database.utils import (
    get_connection, get_tables, fetch_all, fetch_columns,
    insert_record, update_record, delete_record
)

class TableFieldDialog(QDialog):
    """Diálogo para crear o editar un campo de una tabla."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Campo de Tabla")
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()

        # Nombre del campo
        self.field_name = QLineEdit()
        layout.addRow("Nombre del campo:", self.field_name)

        # Tipo de dato
        self.data_type = QComboBox()
        self.data_type.addItems(["TEXT", "INTEGER", "REAL", "BLOB", "DATE", "DATETIME"])
        layout.addRow("Tipo de dato:", self.data_type)

        # Opciones adicionales
        self.primary_key = QCheckBox("Clave primaria")
        self.not_null = QCheckBox("No nulo")
        self.auto_increment = QCheckBox("Auto incremento")
        
        options_layout = QVBoxLayout()
        options_layout.addWidget(self.primary_key)
        options_layout.addWidget(self.not_null)
        options_layout.addWidget(self.auto_increment)
        layout.addRow("Opciones:", options_layout)

        # Botones
        btn_box = QHBoxLayout()
        save_btn = QPushButton("Aceptar")
        cancel_btn = QPushButton("Cancelar")
        
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        btn_box.addWidget(save_btn)
        btn_box.addWidget(cancel_btn)
        layout.addRow("", btn_box)
        
        self.setLayout(layout)

    def get_field_definition(self):
        definition = {
            'name': self.field_name.text(),
            'type': self.data_type.currentText(),
            'primary_key': self.primary_key.isChecked(),
            'not_null': self.not_null.isChecked(),
            'auto_increment': self.auto_increment.isChecked()
        }
        return definition

class TableMaintenanceDialog(QDialog):
    """Diálogo para el mantenimiento de tablas."""
    def __init__(self, connection, parent=None):
        super().__init__(parent)
        self.connection = connection
        self.fields = []
        
        self.setWindowTitle("Mantenimiento de Tablas")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Selector de tablas existentes
        table_group = QGroupBox("Tablas Existentes")
        table_layout = QVBoxLayout()
        
        self.table_list = QComboBox()
        self.refresh_tables()
        
        self.show_structure_btn = QPushButton("Ver Estructura")
        self.show_structure_btn.clicked.connect(self.show_table_structure)
        
        table_layout.addWidget(self.table_list)
        table_layout.addWidget(self.show_structure_btn)
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)

        # Creación de nueva tabla
        new_table_group = QGroupBox("Crear Nueva Tabla")
        new_table_layout = QVBoxLayout()
        
        # Nombre de la tabla
        name_layout = QHBoxLayout()
        self.table_name = QLineEdit()
        name_layout.addWidget(QLabel("Nombre de la tabla:"))
        name_layout.addWidget(self.table_name)
        new_table_layout.addLayout(name_layout)

        # Lista de campos
        self.fields_list = QTableWidget()
        self.fields_list.setColumnCount(5)
        self.fields_list.setHorizontalHeaderLabels(["Nombre", "Tipo", "PK", "Not Null", "Auto Inc"])
        self.fields_list.horizontalHeader().setStretchLastSection(True)
        new_table_layout.addWidget(self.fields_list)

        # Botones para campos
        field_buttons = QHBoxLayout()
        add_field_btn = QPushButton("Añadir Campo")
        add_field_btn.clicked.connect(self.add_field)
        remove_field_btn = QPushButton("Eliminar Campo")
        remove_field_btn.clicked.connect(self.remove_field)
        
        field_buttons.addWidget(add_field_btn)
        field_buttons.addWidget(remove_field_btn)
        new_table_layout.addLayout(field_buttons)

        # Botón crear tabla
        create_table_btn = QPushButton("Crear Tabla")
        create_table_btn.clicked.connect(self.create_table)
        new_table_layout.addWidget(create_table_btn)
        
        new_table_group.setLayout(new_table_layout)
        layout.addWidget(new_table_group)

        self.setLayout(layout)

    def refresh_tables(self):
        """Actualiza la lista de tablas disponibles."""
        self.table_list.clear()
        if self.connection:
            tables = get_tables(self.connection)
            self.table_list.addItems(tables)

    def show_table_structure(self):
        """Muestra la estructura de la tabla seleccionada."""
        table_name = self.table_list.currentText()
        if not table_name:
            return

        cursor = self.connection.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        structure = "Estructura de la tabla:\n\n"
        for col in columns:
            pk = "PK" if col[5] else ""  # col[5] es el indicador de clave primaria
            nn = "NOT NULL" if col[3] else ""  # col[3] es el indicador de NOT NULL
            structure += f"{col[1]} {col[2]} {pk} {nn}\n"

        QMessageBox.information(self, f"Estructura de {table_name}", structure)

    def add_field(self):
        """Añade un nuevo campo a la tabla en creación."""
        dialog = TableFieldDialog(self)
        if dialog.exec():
            field = dialog.get_field_definition()
            self.fields.append(field)
            
            row = self.fields_list.rowCount()
            self.fields_list.insertRow(row)
            self.fields_list.setItem(row, 0, QTableWidgetItem(field['name']))
            self.fields_list.setItem(row, 1, QTableWidgetItem(field['type']))
            self.fields_list.setItem(row, 2, QTableWidgetItem('Sí' if field['primary_key'] else 'No'))
            self.fields_list.setItem(row, 3, QTableWidgetItem('Sí' if field['not_null'] else 'No'))
            self.fields_list.setItem(row, 4, QTableWidgetItem('Sí' if field['auto_increment'] else 'No'))

    def remove_field(self):
        """Elimina el campo seleccionado."""
        current_row = self.fields_list.currentRow()
        if current_row >= 0:
            self.fields_list.removeRow(current_row)
            self.fields.pop(current_row)

    def create_table(self):
        """Crea una nueva tabla con los campos definidos."""
        if not self.table_name.text():
            QMessageBox.warning(self, "Error", "Debe especificar un nombre para la tabla")
            return
        
        if not self.fields:
            QMessageBox.warning(self, "Error", "Debe añadir al menos un campo")
            return

        try:
            # Construir la sentencia SQL
            sql = f"CREATE TABLE {self.table_name.text()} (\n"
            field_defs = []

            for field in self.fields:
                definition = f"{field['name']} {field['type']}"
                
                if field['primary_key']:
                    definition += " PRIMARY KEY"
                    if field['auto_increment']:
                        definition += " AUTOINCREMENT"
                
                if field['not_null']:
                    definition += " NOT NULL"
                
                field_defs.append(definition)

            sql += ",\n".join(field_defs)
            sql += "\n);"

            # Ejecutar la creación de la tabla
            cursor = self.connection.cursor()
            cursor.execute(sql)
            self.connection.commit()

            QMessageBox.information(self, "Éxito", f"Tabla {self.table_name.text()} creada correctamente")
            self.refresh_tables()
            self.table_name.clear()
            self.fields_list.setRowCount(0)
            self.fields.clear()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al crear la tabla: {str(e)}")

class RecordDialog(QDialog):
    def __init__(self, columns, values=None, parent=None):
        super().__init__(parent)
        self.columns = columns
        self.values = values
        self.inputs = {}
        
        self.setWindowTitle("Registro" if not values else "Modificar Registro")
        self.init_ui()
        
    def init_ui(self):
        layout = QFormLayout()
        
        # Crear campos de entrada para cada columna
        for i, col in enumerate(self.columns):
            if col.lower() != 'id':  # Ignorar la columna ID
                line_edit = QLineEdit(str(self.values[i]) if self.values else "")
                self.inputs[col] = line_edit
                layout.addRow(f"{col}:", line_edit)
        
        # Botones
        btn_box = QHBoxLayout()
        save_btn = QPushButton("Guardar")
        cancel_btn = QPushButton("Cancelar")
        
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        btn_box.addWidget(save_btn)
        btn_box.addWidget(cancel_btn)
        layout.addRow("", btn_box)
        
        self.setLayout(layout)
    
    def get_values(self):
        return [self.inputs[col].text() for col in self.columns if col.lower() != 'id']

class DatabaseApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestor de Base de Datos Multimedia")
        self.resize(1024, 768)

        self.connection = None
        self.current_table = None

        # UI
        self.init_ui()

    def init_ui(self):
        # Barra de menú principal
        self.create_menu_bar()

        # Área central
        self.create_central_widget()

    def create_menu_bar(self):
        menu_bar = self.menuBar()
        
        # Menú Archivo
        file_menu = menu_bar.addMenu("Archivo")
        open_action = file_menu.addAction("Abrir Base de Datos")
        open_action.triggered.connect(self.open_database)
        exit_action = file_menu.addAction("Salir")
        exit_action.triggered.connect(self.close)

        # Menú Tablas
        self.table_menu = menu_bar.addMenu("Tablas")

        # Menú Herramientas
        tools_menu = menu_bar.addMenu("Herramientas")
        
        # Opción de importar archivos
        import_action = tools_menu.addAction("Importar Archivos")
        import_action.triggered.connect(self.import_files)
        
        # Opción de mantenimiento de tablas
        maintenance_action = tools_menu.addAction("Mantenimiento de Tablas")
        maintenance_action.triggered.connect(self.show_table_maintenance)

    def create_central_widget(self):
        # Tabla para mostrar datos
        self.table_widget = QTableWidget()
        self.table_widget.setSortingEnabled(True)

        # Botones de acción
        btn_layout = QHBoxLayout()
        buttons = [
            ("Insertar", self.insert_record),
            ("Modificar", self.update_record),
            ("Borrar", self.delete_record),
            ("Actualizar", self.load_table_data)
        ]
        
        for label, handler in buttons:
            btn = QPushButton(label)
            btn.clicked.connect(handler)
            btn_layout.addWidget(btn)

        # Layout principal
        layout = QVBoxLayout()
        layout.addWidget(self.table_widget)
        layout.addLayout(btn_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def open_database(self):
        """Abre una base de datos existente."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar base de datos", "", "SQLite Files (*.db *.sqlite)"
        )
        if file_path:
            try:
                self.connection = get_connection(file_path)
                self.load_tables()
                QMessageBox.information(self, "Éxito", f"Base de datos cargada: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo abrir la base de datos: {str(e)}")

    def load_tables(self):
        """Carga las tablas disponibles en el menú."""
        if not self.connection:
            return
        
        self.table_menu.clear()
        tables = get_tables(self.connection)
        
        for table_name in tables:
            action = self.table_menu.addAction(table_name)
            action.triggered.connect(lambda checked, t=table_name: self.select_table(t))

    def select_table(self, table_name: str):
        """Selecciona una tabla para mostrar sus datos."""
        self.current_table = table_name
        self.load_table_data()

    def load_table_data(self):
        """Carga los datos de la tabla seleccionada."""
        if not self.current_table or not self.connection:
            return

        try:
            rows = fetch_all(self.current_table, self.connection)
            columns = fetch_columns(self.current_table, self.connection)

            self.table_widget.setRowCount(len(rows))
            self.table_widget.setColumnCount(len(columns))
            self.table_widget.setHorizontalHeaderLabels(columns)

            for i, row in enumerate(rows):
                for j, value in enumerate(row):
                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                    self.table_widget.setItem(i, j, item)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar los datos: {str(e)}")

    def insert_record(self):
        """Abre un diálogo para insertar un nuevo registro."""
        if not self.current_table:
            QMessageBox.warning(self, "Aviso", "Seleccione una tabla primero")
            return
        
        try:
            # Obtener columnas de la tabla
            columns = fetch_columns(self.current_table, self.connection)
            
            # Crear y mostrar el diálogo
            dialog = RecordDialog(columns, parent=self)
            if dialog.exec():
                # Filtrar las columnas excluyendo 'id'
                columns_without_id = [col for col in columns if col.lower() != 'id']
                values = dialog.get_values()
                
                # Insertar el nuevo registro
                insert_record(self.current_table, columns_without_id, tuple(values), self.connection)
                
                # Recargar los datos
                self.load_table_data()
                QMessageBox.information(self, "Éxito", "Registro insertado correctamente")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al insertar el registro: {str(e)}")

    def update_record(self):
        """Abre un diálogo para modificar el registro seleccionado."""
        if not self.current_table:
            QMessageBox.warning(self, "Aviso", "Seleccione una tabla primero")
            return
            
        selected = self.table_widget.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Error", "Seleccione un registro para modificar")
            return
        
        try:
            # Obtener columnas y datos del registro seleccionado
            columns = fetch_columns(self.current_table, self.connection)
            current_values = []
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(selected, col)
                current_values.append(item.text() if item else "")
            
            # Crear y mostrar el diálogo
            dialog = RecordDialog(columns, current_values, parent=self)
            if dialog.exec():
                # Obtener el ID del registro
                id_col_index = columns.index('id')
                record_id = int(current_values[id_col_index])
                
                # Filtrar las columnas excluyendo 'id'
                columns_without_id = [col for col in columns if col.lower() != 'id']
                values = dialog.get_values()
                
                # Actualizar el registro
                update_record(self.current_table, columns_without_id, tuple(values), record_id, self.connection)
                
                # Recargar los datos
                self.load_table_data()
                QMessageBox.information(self, "Éxito", "Registro actualizado correctamente")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al actualizar el registro: {str(e)}")

    def delete_record(self):
        """Elimina el registro seleccionado."""
        if not self.current_table:
            QMessageBox.warning(self, "Aviso", "Seleccione una tabla primero")
            return
            
        selected = self.table_widget.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Error", "Seleccione un registro para borrar")
            return
            
        try:
            # Obtener el ID del registro seleccionado
            id_item = self.table_widget.item(selected, 0)
            if not id_item:
                raise ValueError("No se pudo obtener el ID del registro")
            
            record_id = int(id_item.text())
            
            reply = QMessageBox.question(
                self, 
                "Confirmar", 
                "¿Está seguro de que desea eliminar el registro seleccionado?",
                QMessageBox.Yes | QMessageBox.No
            )
                                   
            if reply == QMessageBox.Yes:
                # Eliminar el registro
                delete_record(self.current_table, record_id, self.connection)
                
                # Recargar los datos
                self.load_table_data()
                QMessageBox.information(self, "Éxito", "Registro eliminado correctamente")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al eliminar el registro: {str(e)}")

    def import_files(self):
        """Importa archivos multimedia a la base de datos."""
        QMessageBox.information(self, "Próximamente", "Función de importación en desarrollo")

    def show_table_maintenance(self):
        """Muestra el diálogo de mantenimiento de tablas."""
        if not self.connection:
            QMessageBox.warning(self, "Aviso", "Debe abrir una base de datos primero")
            return
        
        dialog = TableMaintenanceDialog(self.connection, self)
        dialog.exec()
        
        # Actualizar el menú de tablas después de posibles cambios
        self.load_tables()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DatabaseApp()
    window.show()
    sys.exit(app.exec())
