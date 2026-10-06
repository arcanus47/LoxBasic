from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QFont, QTextCursor
from PySide6.QtWidgets import QPlainTextEdit, QWidget

from .syntax import LoxBasicHighlighter


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.paint_line_numbers(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.line_number_area = LineNumberArea(self)

        self.blockCountChanged.connect(
            self.update_line_number_area_width
        )

        self.updateRequest.connect(
            self.update_line_number_area
        )

        self.cursorPositionChanged.connect(
            self.highlight_current_line
        )

        self.update_line_number_area_width(0)

        font = QFont("Consolas")
        font.setPointSize(11)

        self.setFont(font)

        self.setTabStopDistance(
            4 * self.fontMetrics().horizontalAdvance(" ")
        )

        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
                selection-background-color: #264f78;
                padding: 4px;
            }
        """)

        self.highlighter = LoxBasicHighlighter(
            self.document()
        )

    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))

        return (
            12
            + self.fontMetrics().horizontalAdvance("9") * digits
        )

    def update_line_number_area_width(self, _):
        self.setViewportMargins(
            self.line_number_area_width(),
            0,
            0,
            0
        )

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(
                0,
                rect.y(),
                self.line_number_area.width(),
                rect.height()
            )

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        rect = self.contentsRect()

        self.line_number_area.setGeometry(
            QRect(
                rect.left(),
                rect.top(),
                self.line_number_area_width(),
                rect.height()
            )
        )

    def paint_line_numbers(self, event):
        painter = QPainter(self.line_number_area)

        painter.fillRect(
            event.rect(),
            QColor("#181818")
        )

        block = self.firstVisibleBlock()

        block_number = block.blockNumber()

        top = int(
            self.blockBoundingGeometry(block)
            .translated(self.contentOffset())
            .top()
        )

        bottom = top + int(
            self.blockBoundingRect(block).height()
        )

        while block.isValid() and top <= event.rect().bottom():
            if (
                block.isVisible()
                and bottom >= event.rect().top()
            ):
                number = str(block_number + 1)

                if block == self.textCursor().block():
                    painter.setPen(QColor("#ffffff"))
                else:
                    painter.setPen(QColor("#858585"))

                painter.drawText(
                    0,
                    top,
                    self.line_number_area.width() - 6,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    number
                )

            block = block.next()

            top = bottom

            bottom = top + int(
                self.blockBoundingRect(block).height()
            )

            block_number += 1

    def highlight_current_line(self):
        extra_selections = []

        selection = QPlainTextEdit.ExtraSelection()

        selection.format.setBackground(
            QColor("#252526")
        )

        selection.format.setProperty(
            1,
            True
        )

        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()

        extra_selections.append(selection)

        self.setExtraSelections(
            extra_selections
        )

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Tab:
            self.insertPlainText("    ")
            return

        if event.key() == Qt.Key.Key_Backtab:
            cursor = self.textCursor()

            if cursor.hasSelection():
                super().keyPressEvent(event)
                return

            position = cursor.positionInBlock()

            if position >= 4:
                cursor.movePosition(
                    QTextCursor.MoveOperation.Left,
                    QTextCursor.MoveMode.KeepAnchor,
                    4
                )

                if cursor.selectedText() == "    ":
                    cursor.removeSelectedText()

            return

        if event.key() == Qt.Key.Key_Return:
            cursor = self.textCursor()

            current_line = cursor.block().text()

            indentation = ""

            for char in current_line:
                if char in (" ", "\t"):
                    indentation += char
                else:
                    break

            stripped = current_line.strip().upper()

            super().keyPressEvent(event)

            if (
                stripped.endswith("THEN")
                or stripped.startswith("FUN ")
                or stripped == "FUN"
            ):
                indentation += "    "

            self.insertPlainText(indentation)

            return

        super().keyPressEvent(event)
