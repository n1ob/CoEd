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
    flow_dir: int = kwargs.pop('flow', -1)
    indent = GLB_IND
    # args = ['xx ' '{}' ' xx'.format(i) for i in args]
    args = list(args)
    if flow_dir == -1:
        args[0] = '| {}'.format(args[0])
    elif flow_dir == 0:
        args[0] = '|   {}'.format(args[0])
    elif flow_dir == 1:
        args[0] = '|-> {}'.format(args[0])
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

_co_gx = xpc('coincident_g', 'cog')
_co_g = _co_gx.k()
_co_x = xpc('coincident', 'co ')
_co = _co_x.k()

_cs_x = xpc('constraint', 'cs ')
_cs = _cs_x.k()

_cf_x = xpc('config', 'cf ')
_cf = _cf_x.k()

_hv_gx = xpc('hor_vert_g', 'hvg')
_hv_x = xpc('hor_vert', 'hv ')

_xy_x = xpc('xy_dist', 'xy ')
_rd_gx = xpc('radius_g', 'rdg')
_ly_gx = xpc('layout_g', 'lyg')
_ly_g = _ly_gx.k()

_prn_edge = xpc('edge', 'eg ')
_co_co = xpc('consider_coincident', 'cc ')
_co_build = xpc('co_build', 'cb ')
_cir = xpc('circle', 'cr ')
_geo = xpc('geo_list', 'ge ')

xpt('')
xpt('flow')
xpt('config')
xpt('coincident_g')
xpt('coincident')
xpt('constraint')
xpt('layout_g')


def flow(_func=None, *, off=False, short=False):
    def decorator_flow(func):
        @functools.wraps(func)
        def wrapper_flow(*args, **kwargs):
            global GLB_IND
            kw = {'topic': 'flow'}
            if off:
                obj = func(*args, **kwargs)
            elif short or GLB_SHORT:
                GLB_IND += 2
                nam = func.__qualname__.split('.')
                f = nam[len(nam) - 1]
                p = '.'.join(x for x in nam if x is not f)
                kw = {'topic': 'flow', 'flow': 1}
                xp('{}  ({})'.format(f, p), **kw)
                obj = func(*args, **kwargs)
                GLB_IND -= 2
            else:
                GLB_IND += 2
                args_repr = [repr(a) for a in args]
                kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
                signature = ", ".join(args_repr + kwargs_repr)
                kw = {'topic': 'flow', 'flow': 1}
                xp(f"{func.__name__} ({signature})", **kw)
                obj = func(*args, **kwargs)
                kw = {'topic': 'flow', 'flow': 0}
                xp(f"{func.__name__}  ->  {obj!r}", **kw)
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
