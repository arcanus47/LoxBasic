from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat


class LoxBasicHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        self.rules = []

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#c586c0"))
        keyword_format.setFontWeight(QFont.Weight.Bold)

        keywords = [
            "VAR",
            "AND",
            "OR",
            "NOT",
            "IF",
            "ELIF",
            "ELSE",
            "THEN",
            "FOR",
            "TO",
            "STEP",
            "IN",
            "WHILE",
            "FUN",
            "RETURN",
            "CONTINUE",
            "BREAK",
            "END",
            "TRUE",
            "FALSE",
            "NULL"
        ]

        for keyword in keywords:
            self.rules.append(
                (
                    QRegularExpression(
                        rf"\b{keyword}\b",
                        QRegularExpression.PatternOption.CaseInsensitiveOption
                    ),
                    keyword_format
                )
            )

        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))

        self.rules.append(
            (
                QRegularExpression(r"\b\d+(\.\d+)?\b"),
                number_format
            )
        )

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))

        self.rules.append(
            (
                QRegularExpression(r'"([^"\\]|\\.)*"'),
                string_format
            )
        )

        self.rules.append(
            (
                QRegularExpression(r"'([^'\\]|\\.)*'"),
                string_format
            )
        )

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6a9955"))
        comment_format.setFontItalic(True)

        self.rules.append(
            (
                QRegularExpression(r"#.*$"),
                comment_format
            )
        )

        self.rules.append(
            (
                QRegularExpression(r"//.*$"),
                comment_format
            )
        )

        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#dcdcaa"))

        self.rules.append(
            (
                QRegularExpression(r"\b[A-Za-z_][A-Za-z0-9_]*(?=\s*\()"),
                function_format
            )
        )

        operator_format = QTextCharFormat()
        operator_format.setForeground(QColor("#d4d4d4"))

        self.rules.append(
            (
                QRegularExpression(
                    r"(\+\+|--|\+=|-=|\*=|/=|%=|==|!=|<=|>=|&&|\|\||->|\*\*|[+\-*/%^=!<>])"
                ),
                operator_format
            )
        )

    def highlightBlock(self, text):
        for pattern, text_format in self.rules:
            expression = pattern.globalMatch(text)

            while expression.hasNext():
                match = expression.next()
                self.setFormat(
                    match.capturedStart(),
                    match.capturedLength(),
                    text_format
                )
