import sys
from typing import Set
from functools import wraps

from PySide2.QtCore import Qt
from PySide2.QtGui import QPalette, QColor
from PySide2.QtWidgets import QStyleFactory


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

    def kw(self, indent: int = 0) -> dict:
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
    xp('test', 'hi:'+'ho', **c.kw())
    c.std_err = False
    xp('test', 'hi:'+'ho', **c.kw(4))

    addition_func(6)

