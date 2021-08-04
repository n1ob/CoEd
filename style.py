from PySide2.QtCore import QRegExp, Qt
from PySide2.QtGui import QSyntaxHighlighter, QColor, QTextCharFormat, QPalette
from PySide2.QtWidgets import QStyleFactory


class XMLHighlighter(QSyntaxHighlighter):
    """
    Class for highlighting xml text inherited from QSyntaxHighlighter
    """
    # noinspection PyArgumentList
    def __init__(self, parent=None):
        super().__init__(parent)
        # material color tool
        red = QColor('#b71c1c')  # red
        pink = QColor('#880e4f')  # pink
        purple = QColor('#aa00ff')  # purple
        deep_purple = QColor('#311b92')  # deep purple
        indigo = QColor('#3d5afe')  # indigo
        blue = QColor('#0d47a1')  # blue
        light_blue = QColor('#01579b')  # light blue
        cyan = QColor('#00b8d4')  # cyan
        teal = QColor('#004d40')  # teal
        green = QColor('#1b5e20')  # green
        light_green = QColor('#64dd17')  # light green
        lime = QColor('#827717')  # lime
        yellow = QColor('#f57f17')  # yellow
        amber = QColor('#ff6f00')  # amber
        orange = QColor('#e65100')  # orange
        deep_orange = QColor('#bf360c')  # deep orange

        self.highlight_rules = list()
        xml_elem_format = QTextCharFormat()
        xml_elem_format.setForeground(green)
        self.highlight_rules.append((QRegExp("\\b[A-Za-z0-9_]+(?=[\s/>])"), xml_elem_format))

        xml_attr_format = QTextCharFormat()
        xml_attr_format.setFontItalic(True)
        xml_attr_format.setForeground(indigo)
        self.highlight_rules.append((QRegExp("\\b[A-Za-z0-9_]+(?=\\=)"), xml_attr_format))
        self.highlight_rules.append((QRegExp("="), xml_attr_format))

        self.value_format = QTextCharFormat()
        self.value_format.setForeground(light_green)
        self.value_start_expr = QRegExp("\"")
        self.value_end_expr = QRegExp("\"(?=[\s></])")

        single_line_comment_format = QTextCharFormat()
        single_line_comment_format.setForeground(cyan)
        self.highlight_rules.append((QRegExp("<!--[^\n]*-->"), single_line_comment_format))

        text_format = QTextCharFormat()
        text_format.setForeground(teal)
        self.highlight_rules.append((QRegExp(">(.+)(?=</)"), text_format))

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(light_blue)
        keyword_patterns = ["\\b?xml\\b", "/>", ">", "<", "</"]
        self.highlight_rules += [(QRegExp(pattern), keyword_format) for pattern in keyword_patterns]

    # noinspection PyArgumentList
    def highlightBlock(self, text):
        for pattern, fmt in self.highlight_rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, fmt)
                index = expression.indexIn(text, index + length)
        self.setCurrentBlockState(0)
        start_index = 0
        if self.previousBlockState() != 1:
            start_index = self.value_start_expr.indexIn(text)
        while start_index >= 0:
            end_index = self.value_end_expr.indexIn(text, start_index)
            if end_index == -1:
                self.setCurrentBlockState(1)
                comment_length = len(text) - start_index
            else:
                comment_length = end_index - start_index + self.value_end_expr.matchedLength()
            self.setFormat(start_index, comment_length, self.value_format)
            start_index = self.value_start_expr.indexIn(text, start_index + comment_length)


# noinspection PyArgumentList
def my_style(app):
    app.setStyle(QStyleFactory.create("Fusion"))
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
    palette.setColor(QPalette.Base, QColor(42, 42, 42))
    palette.setColor(QPalette.AlternateBase, QColor(66, 66, 66))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, QColor(53, 53, 53))
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
    palette.setColor(QPalette.Dark, QColor(35, 35, 35))
    palette.setColor(QPalette.Shadow, QColor(20, 20, 20))
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(203, 119, 47))
    palette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(80, 80, 80))
    palette.setColor(QPalette.HighlightedText, Qt.white)
    palette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(127, 127, 127))
    app.setPalette(palette)