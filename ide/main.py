import contextlib
import importlib.util
import io
import os
import sys
import traceback

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFileSystemModel,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QTreeView,
    QVBoxLayout,
    QWidget,
    QToolBar,
    QStatusBar
)

from .editor import CodeEditor
from .console import Console


class LoxBasicWorker(QThread):
    output = Signal(str)
    error = Signal(str)
    finished_signal = Signal()

    def __init__(self, root_path, filename, source):
        super().__init__()

        self.root_path = root_path
        self.filename = filename
        self.source = source

    def run(self):
        stdout = io.StringIO()
        stderr = io.StringIO()

        try:
            loxbasic_path = os.path.join(
                self.root_path,
                "LoxBasic.py"
            )

            if not os.path.exists(loxbasic_path):
                raise FileNotFoundError(
                    "No se encontró LoxBasic.py en:\n"
                    + self.root_path
                )

            spec = importlib.util.spec_from_file_location(
                "LoxBasic",
                loxbasic_path
            )

            if spec is None or spec.loader is None:
                raise ImportError(
                    "No se pudo cargar LoxBasic.py."
                )

            module = importlib.util.module_from_spec(spec)

            sys.path.insert(
                0,
                self.root_path
            )

            try:
                spec.loader.exec_module(module)
            finally:
                if self.root_path in sys.path:
                    sys.path.remove(self.root_path)

            if not hasattr(module, "run"):
                raise AttributeError(
                    "LoxBasic.py no contiene la función run()."
                )

            with contextlib.redirect_stdout(stdout):
                with contextlib.redirect_stderr(stderr):
                    result = module.run(
                        self.filename,
                        self.source
                    )

            stdout_value = stdout.getvalue()
            stderr_value = stderr.getvalue()

            if stdout_value:
                self.output.emit(stdout_value)

            if stderr_value:
                self.error.emit(stderr_value)

            if result is not None:
                if hasattr(result, "as_string"):
                    try:
                        result_text = result.as_string()

                        if result_text:
                            self.error.emit(
                                result_text
                            )

                    except Exception:
                        pass
                else:
                    result_text = str(result)

                    if result_text:
                        self.output.emit(
                            result_text
                        )

        except Exception:
            error_text = traceback.format_exc()
            self.error.emit(error_text)

        finally:
            self.finished_signal.emit()


class LoxBasicIDE(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("LoxBasic IDE")
        self.resize(1400, 850)

        self.current_file = None
        self.project_root = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                ".."
            )
        )

        self.worker = None

        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_shortcuts()

        self.statusBar().showMessage(
            "LoxBasic IDE listo"
        )

        self.new_file()

    def setup_ui(self):
        central = QWidget()

        main_layout = QVBoxLayout(
            central
        )

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        main_layout.setSpacing(0)

        splitter = QSplitter(
            Qt.Orientation.Horizontal
        )

        self.file_model = QFileSystemModel()

        self.file_model.setRootPath(
            self.project_root
        )

        self.file_model.setNameFilters(
            [
                "*.lox",
                "*.py",
                "*.txt"
            ]
        )

        self.file_model.setNameFilterDisables(
            False
        )

        self.file_tree = QTreeView()

        self.file_tree.setModel(
            self.file_model
        )

        root_index = self.file_model.index(
            self.project_root
        )

        self.file_tree.setRootIndex(
            root_index
        )

        self.file_tree.setHeaderHidden(
            False
        )

        self.file_tree.setMinimumWidth(
            220
        )

        self.file_tree.doubleClicked.connect(
            self.open_tree_file
        )

        splitter.addWidget(
            self.file_tree
        )

        editor_console_splitter = QSplitter(
            Qt.Orientation.Vertical
        )

        self.editor = CodeEditor()

        self.console = Console()

        editor_console_splitter.addWidget(
            self.editor
        )

        editor_console_splitter.addWidget(
            self.console
        )

        editor_console_splitter.setSizes(
            [
                600,
                200
            ]
        )

        splitter.addWidget(
            editor_console_splitter
        )

        splitter.setSizes(
            [
                260,
                1140
            ]
        )

        main_layout.addWidget(
            splitter
        )

        self.setCentralWidget(
            central
        )

        self.setStatusBar(
            QStatusBar()
        )

    def setup_menu(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu(
            "Archivo"
        )

        new_action = QAction(
            "Nuevo",
            self
        )

        new_action.setShortcut(
            "Ctrl+N"
        )

        new_action.triggered.connect(
            self.new_file
        )

        file_menu.addAction(
            new_action
        )

        open_action = QAction(
            "Abrir",
            self
        )

        open_action.setShortcut(
            "Ctrl+O"
        )

        open_action.triggered.connect(
            self.open_file
        )

        file_menu.addAction(
            open_action
        )

        save_action = QAction(
            "Guardar",
            self
        )

        save_action.setShortcut(
            "Ctrl+S"
        )

        save_action.triggered.connect(
            self.save_file
        )

        file_menu.addAction(
            save_action
        )

        save_as_action = QAction(
            "Guardar como",
            self
        )

        save_as_action.setShortcut(
            "Ctrl+Shift+S"
        )

        save_as_action.triggered.connect(
            self.save_file_as
        )

        file_menu.addAction(
            save_as_action
        )

        file_menu.addSeparator()

        exit_action = QAction(
            "Salir",
            self
        )

        exit_action.triggered.connect(
            self.close
        )

        file_menu.addAction(
            exit_action
        )

        run_menu = menu_bar.addMenu(
            "Ejecutar"
        )

        run_action = QAction(
            "Ejecutar",
            self
        )

        run_action.setShortcut(
            "F5"
        )

        run_action.triggered.connect(
            self.run_code
        )

        run_menu.addAction(
            run_action
        )

        clear_console_action = QAction(
            "Limpiar consola",
            self
        )

        clear_console_action.setShortcut(
            "Ctrl+L"
        )

        clear_console_action.triggered.connect(
            self.console.clear_console
        )

        run_menu.addAction(
            clear_console_action
        )

        help_menu = menu_bar.addMenu(
            "Ayuda"
        )

        about_action = QAction(
            "Acerca de LoxBasic",
            self
        )

        about_action.triggered.connect(
            self.show_about
        )

        help_menu.addAction(
            about_action
        )

    def setup_toolbar(self):
        toolbar = QToolBar(
            "Principal"
        )

        toolbar.setMovable(
            False
        )

        self.addToolBar(
            toolbar
        )

        new_action = QAction(
            "Nuevo",
            self
        )

        new_action.triggered.connect(
            self.new_file
        )

        toolbar.addAction(
            new_action
        )

        open_action = QAction(
            "Abrir",
            self
        )

        open_action.triggered.connect(
            self.open_file
        )

        toolbar.addAction(
            open_action
        )

        save_action = QAction(
            "Guardar",
            self
        )

        save_action.triggered.connect(
            self.save_file
        )

        toolbar.addAction(
            save_action
        )

        toolbar.addSeparator()

        run_action = QAction(
            "▶ Ejecutar",
            self
        )

        run_action.triggered.connect(
            self.run_code
        )

        toolbar.addAction(
            run_action
        )

        clear_action = QAction(
            "Limpiar consola",
            self
        )

        clear_action.triggered.connect(
            self.console.clear_console
        )

        toolbar.addAction(
            clear_action
        )

    def setup_shortcuts(self):
        pass

    def new_file(self):
        self.current_file = None

        self.editor.clear()

        self.editor.setPlainText(
            'PRINT("Hola desde LoxBasic")\n'
        )

        self.editor.document().setModified(
            False
        )

        self.update_title()

        self.statusBar().showMessage(
            "Nuevo archivo"
        )

    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir archivo LoxBasic",
            self.project_root,
            "LoxBasic (*.lox);;Todos los archivos (*)"
        )

        if not filename:
            return

        self.load_file(
            filename
        )

    def open_tree_file(self, index):
        if not self.file_model.isDir(index):
            filename = self.file_model.filePath(
                index
            )

            if filename.endswith(
                ".lox"
            ):
                self.load_file(
                    filename
                )

    def load_file(self, filename):
        try:
            with open(
                filename,
                "r",
                encoding="utf-8"
            ) as file:
                content = file.read()

            self.editor.setPlainText(
                content
            )

            self.current_file = os.path.abspath(
                filename
            )

            self.editor.document().setModified(
                False
            )

            self.update_title()

            self.statusBar().showMessage(
                f"Abierto: {filename}"
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo abrir el archivo:\n\n{error}"
            )

    def save_file(self):
        if self.current_file is None:
            return self.save_file_as()

        return self.write_file(
            self.current_file
        )

    def save_file_as(self):
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar archivo LoxBasic",
            self.project_root,
            "LoxBasic (*.lox);;Todos los archivos (*)"
        )

        if not filename:
            return False

        if not filename.lower().endswith(
            ".lox"
        ):
            filename += ".lox"

        self.current_file = os.path.abspath(
            filename
        )

        return self.write_file(
            self.current_file
        )

    def write_file(self, filename):
        try:
            with open(
                filename,
                "w",
                encoding="utf-8"
            ) as file:
                file.write(
                    self.editor.toPlainText()
                )

            self.editor.document().setModified(
                False
            )

            self.update_title()

            self.statusBar().showMessage(
                f"Guardado: {filename}"
            )

            self.refresh_file_tree()

            return True

        except Exception as error:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo guardar el archivo:\n\n{error}"
            )

            return False

    def refresh_file_tree(self):
        root_index = self.file_model.index(
            self.project_root
        )

        self.file_tree.setRootIndex(
            root_index
        )

    def run_code(self):
        if self.worker is not None:
            if self.worker.isRunning():
                QMessageBox.information(
                    self,
                    "LoxBasic",
                    "Ya hay un programa ejecutándose."
                )

                return

        source = self.editor.toPlainText()

        if not source.strip():
            self.console.writeln(
                "No hay código para ejecutar."
            )

            return

        if self.current_file is None:
            filename = "<editor>"

        else:
            filename = self.current_file

        self.console.writeln(
            "────────────────────────────────────────"
        )

        self.console.writeln(
            "LoxBasic"
        )

        self.console.writeln(
            "Ejecutando..."
        )

        self.console.writeln()

        self.worker = LoxBasicWorker(
            self.project_root,
            filename,
            source
        )

        self.worker.output.connect(
            self.handle_output
        )

        self.worker.error.connect(
            self.handle_error
        )

        self.worker.finished_signal.connect(
            self.execution_finished
        )

        self.worker.start()

        self.statusBar().showMessage(
            "Ejecutando LoxBasic..."
        )

    def handle_output(self, text):
        self.console.write(
            text
        )

    def handle_error(self, text):
        self.console.writeln(
            text
        )

    def execution_finished(self):
        self.console.writeln()

        self.console.writeln(
            "Programa terminado."
        )

        self.console.writeln(
            "────────────────────────────────────────"
        )

        self.statusBar().showMessage(
            "Ejecución terminada"
        )

        self.worker = None

    def update_title(self):
        if self.current_file:
            filename = os.path.basename(
                self.current_file
            )

            title = (
                f"{filename} - LoxBasic IDE"
            )

        else:
            title = (
                "Sin título - LoxBasic IDE"
            )

        if self.editor.document().isModified():
            title = "* " + title

        self.setWindowTitle(
            title
        )

    def show_about(self):
        QMessageBox.about(
            self,
            "LoxBasic IDE",
            """
            <h2>LoxBasic IDE</h2>
            <p>Entorno de desarrollo para el lenguaje LoxBasic.</p>
            <p>Versión 0.1.0</p>
            <p>Editor, explorador, consola y ejecución integrada.</p>
            """
        )

    def closeEvent(self, event):
        if self.editor.document().isModified():
            answer = QMessageBox.question(
                self,
                "Cambios sin guardar",
                "Hay cambios sin guardar. ¿Quieres guardarlos antes de salir?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel
            )

            if answer == QMessageBox.StandardButton.Save:
                if not self.save_file():
                    event.ignore()
                    return

            elif answer == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return

        if self.worker is not None:
            if self.worker.isRunning():
                self.worker.terminate()
                self.worker.wait(1000)

        event.accept()


def apply_theme(app):
    app.setStyleSheet("""
        QMainWindow {
            background-color: #1e1e1e;
            color: #d4d4d4;
        }

        QMenuBar {
            background-color: #181818;
            color: #d4d4d4;
            border-bottom: 1px solid #303030;
        }

        QMenuBar::item {
            background-color: transparent;
            padding: 6px 10px;
        }

        QMenuBar::item:selected {
            background-color: #2d2d30;
        }

        QMenu {
            background-color: #252526;
            color: #d4d4d4;
            border: 1px solid #3f3f46;
        }

        QMenu::item {
            padding: 7px 30px 7px 12px;
        }

        QMenu::item:selected {
            background-color: #094771;
        }

        QToolBar {
            background-color: #181818;
            border: none;
            spacing: 5px;
            padding: 5px;
        }

        QToolButton {
            background-color: #252526;
            color: #d4d4d4;
            border: 1px solid #3f3f46;
            border-radius: 4px;
            padding: 6px 10px;
        }

        QToolButton:hover {
            background-color: #333333;
        }

        QTreeView {
            background-color: #181818;
            color: #d4d4d4;
            border: none;
            outline: none;
        }

        QTreeView::item {
            padding: 4px;
        }

        QTreeView::item:hover {
            background-color: #2a2d2e;
        }

        QTreeView::item:selected {
            background-color: #094771;
            color: #ffffff;
        }

        QStatusBar {
            background-color: #007acc;
            color: white;
        }

        QSplitter::handle {
            background-color: #303030;
        }
    """)


def main():
    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        "LoxBasic IDE"
    )

    app.setApplicationVersion(
        "0.1.0"
    )

    apply_theme(
        app
    )

    window = LoxBasicIDE()

    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()
    
