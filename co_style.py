from PySide2.QtCore import QRegExp, Qt
from PySide2.QtGui import QSyntaxHighlighter, QColor, QTextCharFormat, QPalette
from PySide2.QtWidgets import QStyleFactory

from co_config import CfgColors
from co_logger import xps


class XMLHighlighter(QSyntaxHighlighter):
    """
    Class for highlighting xml text inherited from QSyntaxHighlighter
    """

    # noinspection PyArgumentList
    def __init__(self, parent=None):
        super().__init__(parent)
        cfg = CfgColors()

        self.highlight_rules = list()
        xml_elem_format = QTextCharFormat()
        xml_elem_format.setForeground(cfg.color_get(CfgColors.COLOR_XML_ELEM))
        self.highlight_rules.append((QRegExp("\\b[A-Za-z0-9_]+(?=[\s/>])"), xml_elem_format))

        xml_attr_format = QTextCharFormat()
        xml_attr_format.setFontItalic(True)
        xml_attr_format.setForeground(cfg.color_get(CfgColors.COLOR_XML_ATTR))
        self.highlight_rules.append((QRegExp("\\b[A-Za-z0-9_]+(?=\\=)"), xml_attr_format))
        self.highlight_rules.append((QRegExp("="), xml_attr_format))

        self.value_format = QTextCharFormat()
        self.value_format.setForeground(cfg.color_get(CfgColors.COLOR_XML_VAL))
        self.value_start_expr = QRegExp("\"")
        self.value_end_expr = QRegExp("\"(?=[\s></])")

        single_line_comment_format = QTextCharFormat()
        single_line_comment_format.setForeground(cfg.color_get(CfgColors.COLOR_XML_LN_CMT))
        self.highlight_rules.append((QRegExp("<!--[^\n]*-->"), single_line_comment_format))

        text_format = QTextCharFormat()
        text_format.setForeground(cfg.color_get(CfgColors.COLOR_XML_TXT))
        self.highlight_rules.append((QRegExp(">(.+)(?=</)"), text_format))

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(cfg.color_get(CfgColors.COLOR_XML_KEYWORD))
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


def set_style(wid):
    wid.setStyle(QStyleFactory.create("Fusion"))


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


def set_palette(wid):
    '''
    QPalette::Window			10			A general background color.
    QPalette::Background		Window		This value is obsolete. Use Window instead.
    QPalette::WindowText		0			A general foreground color.
    QPalette::Foreground		WindowText	This value is obsolete. Use WindowText instead.
    QPalette::Base				9			Used mostly as the background color for text entry widgets, but can also be
                                            used for other painting - such as the background of combobox drop down lists
                                            and toolbar handles. It is usually white or another light color.
    QPalette::AlternateBase		16			Used as the alternate background color in views with alternating row colors
                                            (see QAbstractItemView::setAlternatingRowColors()).
    QPalette::ToolTipBase		18			Used as the background color for QToolTip and QWhatsThis. Tool tips use the
                                            Inactive color group of QPalette, because tool tips are not active windows.
    QPalette::ToolTipText		19			Used as the foreground color for QToolTip and QWhatsThis. Tool tips use the
                                            Inactive color group of QPalette, because tool tips are not active windows.
    QPalette::PlaceholderText	20			Used as the placeholder color for various text input widgets. This enum
                                            value has been introduced in Qt 5.12
    QPalette::Text				6			The foreground color used with Base. This is usually the same as the
                                            WindowText, in which case it must provide good contrast with Window and Base.
    QPalette::Button			1			The general button background color. This background can be different from
                                            Window as some styles require a different background color for buttons.
    QPalette::ButtonText		8			A foreground color used with the Button color.
    QPalette::BrightText		7			A text color that is very different from WindowText, and contrasts well with
                                            e.g. Dark. Typically used for text that needs to be drawn where Text or
                                            WindowText would give poor contrast, such as on pressed push buttons. Note
                                            that text colors can be used for things other than just words; text colors
                                            are usually used for text, but it's quite common to use the text color roles
                                            for lines, icons, etc.

    The Active group is used for the window that has keyboard focus.
    The Inactive group is used for other windows.
    The Disabled group is used for widgets (not windows) that are disabled for some reason.

    QPalette::Disabled			1
    QPalette::Active			0
    QPalette::Inactive			2
    QPalette::Normal			Active		synonym for Active

    QPalette::Light				2			Lighter than Button color.
    QPalette::Midlight			3			Between Button and Light.
    QPalette::Dark				4			Darker than Button.
    QPalette::Mid				5			Between Button and Dark.
    QPalette::Shadow			11			A very dark color. By default, the shadow color is Qt::black.

    QPalette::Highlight			12			A color to indicate a selected item or the current item. By default, the
                                            highlight color is Qt::darkBlue.
    QPalette::HighlightedText	13			A text color that contrasts with Highlight. By default, the highlighted text
                                            color is Qt::white.

    QPalette::Link				14			A text color used for unvisited hyperlinks. By default, the link color is
                                            Qt::blue.
    QPalette::LinkVisited		15			A text color used for already visited hyperlinks. By default, the
                                            linkvisited color is Qt::magenta.

    QPalette::NoRole			17			No role; this special role is often used to indicate that a role has not
                                            been assigned.
    '''

    palette = QPalette()
    palette.setColor(QPalette.Light, QColor('#666666'))
    palette.setColor(QPalette.Midlight, QColor('#454545'))
    palette.setColor(QPalette.Dark, QColor('#232323'))
    palette.setColor(QPalette.Mid, QColor('#303030'))
    palette.setColor(QPalette.Shadow, QColor('#141414'))

    palette.setColor(QPalette.Window, QColor('#353535'))
    palette.setColor(QPalette.WindowText, QColor('#ffffff'))
    palette.setColor(QPalette.Base, QColor('#2a2a2a'))
    palette.setColor(QPalette.AlternateBase, QColor('#424242'))
    palette.setColor(QPalette.ToolTipBase, QColor('#ffffff'))
    palette.setColor(QPalette.ToolTipText, QColor('#353535'))
    palette.setColor(QPalette.PlaceholderText, QColor('#7f7f7f'))
    palette.setColor(QPalette.Text, QColor('#ffffff'))
    palette.setColor(QPalette.Button, QColor('#353535'))
    palette.setColor(QPalette.ButtonText, QColor('#ffffff'))
    palette.setColor(QPalette.BrightText, QColor('#cb772f'))

    palette.setColor(QPalette.Highlight, QColor('#cb772f'))
    palette.setColor(QPalette.HighlightedText, QColor('#ffffff'))
    palette.setColor(QPalette.Link, QColor('#2a82da'))
    # palette.setColor(QPalette.LinkVisited, QColor())

    palette.setColor(QPalette.Disabled, QPalette.Window, QColor('#353535'))
    palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor('#7f7f7f'))
    palette.setColor(QPalette.Disabled, QPalette.Base, QColor('#2a2a2a'))
    palette.setColor(QPalette.Disabled, QPalette.AlternateBase, QColor('#424242'))
    palette.setColor(QPalette.Disabled, QPalette.ToolTipBase, QColor('#ffffff'))
    palette.setColor(QPalette.Disabled, QPalette.ToolTipText, QColor('#353535'))
    palette.setColor(QPalette.Disabled, QPalette.PlaceholderText, QColor('#7f7f7f'))
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor('#7f7f7f'))
    palette.setColor(QPalette.Disabled, QPalette.Button, QColor('#353535'))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor('#7f7f7f'))
    palette.setColor(QPalette.Disabled, QPalette.BrightText, QColor('#915521'))

    palette.setColor(QPalette.Disabled, QPalette.Highlight, QColor('#915521'))
    palette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor('#7f7f7f'))

    # palette.setColor(QPalette.Inactive, QPalette.Window, QColor())
    # palette.setColor(QPalette.Inactive, QPalette.WindowText, QColor())
    # palette.setColor(QPalette.Inactive, QPalette.Base, QColor())
    # palette.setColor(QPalette.Inactive, QPalette.AlternateBase, QColor())
    # palette.setColor(QPalette.Inactive, QPalette.ToolTipBase, QColor())
    # palette.setColor(QPalette.Inactive, QPalette.ToolTipText, QColor())
    # palette.setColor(QPalette.Inactive, QPalette.PlaceholderText, QColor())
    # palette.setColor(QPalette.Inactive, QPalette.Text, QColor())
    # palette.setColor(QPalette.Inactive, QPalette.Button, QColor())
    # palette.setColor(QPalette.Inactive, QPalette.ButtonText, QColor())
    # palette.setColor(QPalette.Inactive, QPalette.BrightText, QColor())
    wid.setPalette(palette)


xps(__name__)
