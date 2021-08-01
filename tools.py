import sys
from typing import Set
from functools import wraps

from PySide2.QtCore import Qt, QRegExp
from PySide2.QtGui import QPalette, QColor, QSyntaxHighlighter, QTextCharFormat
from PySide2.QtWidgets import QStyleFactory


class XMLHighlighter(QSyntaxHighlighter):
    """
    Class for highlighting xml text inherited from QSyntaxHighlighter
    """
    # noinspection PyArgumentList
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlight_rules = list()
        xml_elem_format = QTextCharFormat()
        xml_elem_format.setForeground(QColor("#007070"))
        self.highlight_rules.append((QRegExp("\\b[A-Za-z0-9_]+(?=[\s/>])"), xml_elem_format))

        xml_attr_format = QTextCharFormat()
        xml_attr_format.setFontItalic(True)
        xml_attr_format.setForeground(QColor("#177317"))
        self.highlight_rules.append((QRegExp("\\b[A-Za-z0-9_]+(?=\\=)"), xml_attr_format))
        self.highlight_rules.append((QRegExp("="), xml_attr_format))

        self.value_format = QTextCharFormat()
        # self.value_format.setForeground(QColor("#b36020"))
        self.value_format.setForeground(QColor(203, 119, 47))
        self.value_start_expr = QRegExp("\"")
        self.value_end_expr = QRegExp("\"(?=[\s></])")

        single_line_comment_format = QTextCharFormat()
        single_line_comment_format.setForeground(QColor("#a0a0a4"))
        self.highlight_rules.append((QRegExp("<!--[^\n]*-->"), single_line_comment_format))

        text_format = QTextCharFormat()
        text_format.setForeground(QColor("#bababa"))
        self.highlight_rules.append((QRegExp(">(.+)(?=</)"), text_format))

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#007070"))
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


class XpConf:

    topics: Set[str] = set()

    def __init__(self, topic='', prepend=None, std_err=False, separator=None, append=None):
        self.std_err = std_err
        self.prepend = prepend
        self.append = append
        self.topic = topic
        self.separator = separator

    def k(self, indent: int = 0) -> dict:
        d: dict = dict()
        if indent:
            d.update({'indent': indent})
        if self.std_err:
            d.update({'file': sys.stderr})
        if self.prepend is not None:
            d.update({'prepend': self.prepend})
        if self.append is not None:
            d.update({'append': self.append})
        if self.topic is not None:
            d.update({'topic': self.topic})
        if self.separator is not None:
            d.update({'sep': self.separator})
        return d

    @staticmethod
    def get(kwargs, key, default=None):
        obj = kwargs.get(key, default)
        if key in kwargs.keys():
            kwargs.pop(key)
        return obj


def xp(*args, **kwargs):
    prepend: str = XpConf.get(kwargs, 'prepend')
    append: str = XpConf.get(kwargs, 'append')
    topic: str = XpConf.get(kwargs, 'topic', '')
    indent: int = XpConf.get(kwargs, 'indent', 0)
    # args = ['xx ' '{}' ' xx'.format(i) for i in args]
    args = ['{}'.format(i) for i in args]
    if indent:
        args.insert(0, ' ' * (indent - 1))
    if prepend is not None:
        args.insert(0, prepend)
    if append is not None:
        args.append(append)
    # print(*args, **kwargs, sep='-')
    if topic in XpConf.topics:
        print(*args, **kwargs)


def xpe(x: XpConf, ind: int, *args):
    d: dict = x.k(ind)
    prepend: str = d.pop('prepend', None)
    append: str = d.pop('append', None)
    topic: str = d.pop('topic', '')
    indent: int = d.pop('indent', 0)
    args = ['{}'.format(i) for i in args]
    if indent:
        args.insert(0, ' ' * (indent - 1))
    if prepend is not None:
        args.insert(0, prepend)
    if append is not None:
        args.append(append)
    # print(*args, **kwargs, sep='-')
    if topic in XpConf.topics:
        print(*args, **d)


def xpc(*args):
    return XpConf(args[0], args[1])


def xpt(*args):
    XpConf.topics.add(args[0])


# dbg config
_coin = xpc('coin_g', 'ui-coi')
_hv_g = xpc('hv_g', 'ui-hv ')
_rad = xpc('rad_g', 'ui-rad')
_lay = xpc('lay_g', 'ui-lay')
_prn_edge = xpc('edge', 'edg')
_co_co = xpc('consider_coin', 'coc')
_co_build = xpc('co_build', 'cob')
_hv = xpc('hv', 'hv ')
_xy = xpc('xy', 'xy ')
_cir = xpc('circle', 'cir')
_geo = xpc('geo_list', 'geo')

xpt('flow')
# xpt('')
xpt('xy')
# xpt('coin_g')
# xpt('hv_g')
# xpt('rad_g')
# xpt('lay_g')
# xpt('circle')
# xpt('geo_list')
# xpt('edge')
# xpt('consider_coin')
# xpt('hv')
# xpt('co_build')


def flow(func):
    @wraps(func)
    def with_logging(*args, **kwargs):
        kw = {'topic': 'flow'}
        xp('>>>', func.__name__, **kw)
        return func(*args, **kwargs)
    return with_logging


if __name__ == '__main__':

    XpConf.topics.add('flow')

    @flow
    def addition_func(x):
        return x + x

    c = XpConf('test', 'ooo', True, '*', 'xxx')
    XpConf.topics.add('test')
    XpConf.topics.add('')

    xp('hi:'+'ho')
    xp('test', 'hi:' +'ho', **c.k())
    c.std_err = False
    xp('test', 'hi:' +'ho', **c.k(4))

    addition_func(6)
