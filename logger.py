import functools
import sys
from typing import Set


class XpConf:

    topics: Set[str] = set()

    def __init__(self, topic='', prepend=None, std_err=False, separator=None, append=None):
        self.std_err = std_err
        self.prepend = prepend
        self.append = append
        self.topic = topic
        self.separator = separator

    def k(self, add_ind: int = 0) -> dict:
        d: dict = dict()
        if add_ind > 0:
            d.update({'add_indent': add_ind})
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


def xp(*args, **kwargs):
    global GLB_IND
    add_ind: int = kwargs.pop('add_indent', 0)
    prepend: str = kwargs.pop('prepend', '   ')
    append: str = kwargs.pop('append', None)
    topic: str = kwargs.pop('topic', '')
    indent = GLB_IND
    # args = ['xx ' '{}' ' xx'.format(i) for i in args]
    args = list(args)
    _ind = add_ind
    if indent > 0:
        _ind += indent
    if _ind > 0:
        args.insert(0, ' ' * (_ind - 1))
    if prepend is not None:
        args.insert(0, prepend)
    if append is not None:
        args.append(append)
    # print(*args, **kwargs, sep='-')
    if topic in XpConf.topics:
        print(*args, **kwargs)

def sep():
    print('------------------------------------')


def xpc(*args):
    return XpConf(args[0], args[1])


def xpt(*args):
    XpConf.topics.add(args[0])


GLB_SHORT: bool = True
GLB_IND: int = -2

_cogx = xpc('coin_g', 'ui ')
_cog = _cogx.k()
_cox = xpc('coin', 'co ')
_co = _cox.k()
_hv_g = xpc('hv_g', 'ui ')
_rad = xpc('rad_g', 'ui ')
_lay = xpc('lay_g', 'ui ')
_prn_edge = xpc('edge', 'eg ')
_co_co = xpc('consider_coin', 'cc ')
_co_build = xpc('co_build', 'cb ')
_hv = xpc('hv', 'hv ')
_xy = xpc('xy', 'xy ')
_cir = xpc('circle', 'cr ')
_geo = xpc('geo_list', 'ge ')
_confx = xpc('config', 'cf ')
_cf = _confx.k()
xpt('flow')
xpt('')
xpt('config')
# xpt('xy')
xpt('coin_g')
xpt('coin')
# xpt('hv_g')
# xpt('rad_g')
# xpt('lay_g')
# xpt('circle')
# xpt('geo_list')
# xpt('edge')
# xpt('consider_coin')
# xpt('hv')
# xpt('co_build')


def flow(_func=None, *, off=False, short=False):
    def decorator_flow(func):
        @functools.wraps(func)
        def wrapper_flow(*args, **kwargs):
            global GLB_IND
            kw = {'topic': 'flow'}
            # kw = {'topic': 'flow', 'indent': GLB_IND}
            if off:
                obj = func(*args, **kwargs)
            elif short or GLB_SHORT:
                GLB_IND += 2
                nam = func.__qualname__.split('.')
                f = nam[len(nam) - 1]
                p = '.'.join(x for x in nam if x is not f)
                xp('|-> {}  ({})'.format(f, p), **kw)
                obj = func(*args, **kwargs)
                GLB_IND -= 2
            else:
                GLB_IND += 2
                args_repr = [repr(a) for a in args]
                kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
                signature = ", ".join(args_repr + kwargs_repr)
                xp(f"|-> {func.__name__} ({signature})", **kw)
                obj = func(*args, **kwargs)
                xp(f"|   {func.__name__}  ->  {obj!r}", **kw)
                # xp(f"|   {func.__name__!r}  ->  {obj!r}", **kw)
                GLB_IND -= 2
            return obj
        return wrapper_flow
    if _func is None:
        return decorator_flow
    else:
        return decorator_flow(_func)


if __name__ == '__main__':

    XpConf.topics.add('flow')

    @flow
    def addition_func(x):
        return x + x

    c = XpConf('test', 'ooo', True, '*', 'xxx')
    XpConf.topics.add('test')
    XpConf.topics.add('')

    xp('hi:' + 'ho')
    xp('test', 'hi:' + 'ho', **c.k())
    c.std_err = False
    xp('test', 'hi:' + 'ho', **c.k(4))

    addition_func(6)
