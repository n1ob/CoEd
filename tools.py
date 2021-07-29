import sys
from typing import Set
from functools import wraps


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

