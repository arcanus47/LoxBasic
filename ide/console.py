from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor, QFont
from PySide6.QtWidgets import QPlainTextEdit


class Console(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setReadOnly(True)
        self.setUndoRedoEnabled(False)

        font = QFont("Consolas")
        font.setPointSize(10)

        self.setFont(font)

        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #111111;
                color: #d4d4d4;
                border: none;
                padding: 8px;
                selection-background-color: #264f78;
            }
        """)

    def write(self, text):
        if text is None:
            return

        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        self.setTextCursor(cursor)
        self.insertPlainText(str(text))

        self.ensureCursorVisible()

    def writeln(self, text=""):
        self.write(f"{text}\n")

    def clear_console(self):
        self.clear()

    def show_error(self, text):
        self.writeln(text)

    def keyPressEvent(self, event):
        event.ignore()
