import functools
import pathlib
import sys
import traceback
from datetime import datetime
from typing import Set, List, AnyStr

'''
>>> import dis
>>> add = lambda x, y: x + y
>>> type(add)
<class 'function'>
>>> dis.dis(add)
  1           0 LOAD_FAST                0 (x)
              2 LOAD_FAST                1 (y)
              4 BINARY_ADD
              6 RETURN_VALUE
>>> add
<function <lambda> at 0x7f30c6ce9ea0>

(lambda x:
(x % 2 and 'odd' or 'even'))(3)
'odd'
(lambda x:
(x % 2 and 'odd' or 'even'))(4)
'even'

>>> (lambda x, y, z: x + y + z)(1, 2, 3)
6
>>> (lambda x, y, z=3: x + y + z)(1, 2)
6
>>> (lambda x, y, z=3: x + y + z)(1, y=2)
6
>>> (lambda *args: sum(args))(1,2,3)
6
>>> (lambda **kwargs: sum(kwargs.values()))(one=1, two=2, three=3)
6
>>> (lambda x, *, y=0, z=0: x + y + z)(1, y=2, z=3)
6

def fullname(o):
    # o.__module__ + "." + o.__class__.__qualname__ is an example in
    # this context of H.L. Mencken's "neat, plausible, and wrong."
    # Python makes no guarantees as to whether the __module__ special
    # attribute is defined, so we take a more circumspect approach.
    # Alas, the module name is explicitly excluded from __qualname__
    # in Python 3.

    print(inspect.signature(o))
    for x in inspect.getmembers(o):
        print(x)
    module = o.__class__.__module__
    print('o'.ljust(30), o)
    print('o.__class__'.ljust(30), o.__class__)
    print('o.__name__'.ljust(30), o.__name__)
    if hasattr(o, '__module__'):
        print('o.__module__'.ljust(30), o.__module__)
    print('o.__class__.__module__'.ljust(30), o.__class__.__module__)
    print('o.__class__.__name__'.ljust(30), o.__class__.__name__)


    if module is None or module == str.__class__.__module__:
        return o.__class__.__name__  # Avoid reporting __builtin__
    else:
        return module + '.' + o.__class__.__name__

'''
# todo have a dbg switch ???

class XpConf:
    topics: Set[str] = set()

    def __init__(self, topic='', prepend=None, std_err=False, separator=None, append=None):
        self.std_err = std_err
        self.prepend = prepend
        self.append = append
        self.topic = topic
        self.separator = separator
        self.logfile = False

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


class XpWriter:

    def write(self, s: AnyStr) -> int:
        xp(s)
        return 0


def stack_tracer():
    xps("stack tracer")
    exc_type, exc_value, exc_traceback = sys.exc_info()
    # xps("print_tb:")
    # traceback.print_tb(exc_traceback, limit=10, file=xpw)
    # xps("print_exception:")
    # # exc_type below is ignored on 3.5 and later
    # traceback.print_exception(exc_type, exc_value, exc_traceback, limit=20, file=xpw)
    # xps("print_exc:")
    # traceback.print_exc(limit=20, file=xpw)
    xps("format_exc:")
    formatted_lines = traceback.format_exc().splitlines()
    for line in formatted_lines:
        xp(line)
    # xps("format_exception:")
    # # exc_type below is ignored on 3.5 and later
    # f_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    # for line in f_lines:
    #     xp(line)
    xps("extract_tb:")
    f_lines: traceback.StackSummary[traceback.FrameSummary] = traceback.extract_tb(exc_traceback)
    for li in f_lines:
        xp(li)
        xp(li.line)
    # xps("format_tb:")
    # f_lines = traceback.format_tb(exc_traceback)
    # for line in f_lines:
    #     xp(line)
    # xps("tb_lineno:")
    # xp(exc_traceback.tb_lineno)
    xps("eof")


file = open('C:/Users/red/AppData/Roaming/JetBrains/PyCharmCE2021.2/scratches/logger.log', 'a', 1)


def xp(*args, **kwargs) -> None:
    global GLB_HEADER
    global GLB_IND
    global GLB_LOG
    if GLB_HEADER:
        GLB_HEADER = False
        _xp_header()
    add_ind: int = kwargs.pop('add_indent', 0)
    prepend: str = kwargs.pop('prepend', '   ')
    append: str = kwargs.pop('append', None)
    topic: str = kwargs.pop('topic', '')
    _pre = prepend.ljust(3)
    _topic: List[str] = topic.split('.')
    flow_dir: int = kwargs.pop('flow', -1)
    indent = GLB_IND
    # args = ['xx ' '{}' ' xx'.format(i) for i in args]
    args = list(args)
    ai = ''
    if add_ind > 0:
        ai = ' ' * add_ind
    if flow_dir == -1:
        args[0] = '| {}{}'.format(ai, args[0])
    elif flow_dir == 0:
        args[0] = '|   {}'.format(args[0])
    elif flow_dir == 1:
        args[0] = '|-> {}'.format(args[0])
    if indent > 0:
        args.insert(0, ' ' * (indent - 1))
    if prepend is not None:
        args.insert(0, _pre)
    if append is not None:
        args.append(append)
    # print(*args, **kwargs, sep='-')
    # if topic in XpConf.topics:
    if not XpConf.topics.isdisjoint(_topic):
        print(*args, **kwargs)
        if GLB_LOG:
            # '../../AppData/Roaming/JetBrains/PyCharmCE2021.2/scratches/'
            # C:/Users/red/AppData/Roaming/JetBrains/PyCharmCE2021.2/scratches/logger.log
            # with open('C:/Users/red/AppData/Roaming/JetBrains/PyCharmCE2021.2/scratches/logger.log', 'a', 1) as file:
            file.write(' '.join(f'{x}' for x in args))
            file.write('\n')


def xps(*args: object, **kwargs: object) -> None:
    xp(f"---{' '.join(f'{x}' for x in args)}----------------------------------------", **kwargs)


def _xp_header(val=None):
    if val is None:
        val = pathlib.Path().resolve()
    xp('')
    xp('')
    xps(f'{datetime.now().hour}:{datetime.now().minute:02}:{datetime.now().second} --- {val}')
    # xp(f'{__file__}')
    xp('')
    xp('')


def sep(*args):
    print(f'----{args}---')


def _xpt(*args):
    [XpConf.topics.add(x) for x in args]


# ! profiling
class Profile:
    def __init__(self, enable: bool = True, top_n: int = 10):
        # print('__init__ called')
        self.profiler = None
        self.top_n: int = top_n
        self.enable: bool = enable

    def __enter__(self):
        # print('__enter__ called')
        import cProfile
        if self.enable:
            self.profiler = cProfile.Profile()
            self.profiler.enable()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        # print('__exit__ called')
        if exc_type:
            xp(f'exc_type: {exc_type}')
            xp(f'exc_value: {exc_value}')
            xp(f'exc_traceback: {exc_traceback}')
        import pstats
        import io
        if self.enable:
            self.profiler.disable()
            output = io.StringIO()
            stats = pstats.Stats(self.profiler, stream=output).sort_stats('cumtime')
            stats.print_stats(self.top_n)
            # print(output.tell())
            output.seek(0)
            # print(output.tell())
            for line in output:
                xp(line.rstrip("\n"))
            # contents = output.getvalue()
            # print(contents)
            output.close()


def flow(_func=None, *, off=False, short=False):
    def decorator_flow(func):
        @functools.wraps(func)
        def wrapper_flow(*args, **kwargs):
            global GLB_IND
            global GLB_LOG
            _flow['flow'] = -1
            if off or not GLB_LOG:
                obj = func(*args, **kwargs)
            elif short or GLB_SHORT:
                GLB_IND += 2
                if hasattr(func, '__qualname__'):
                    nam = func.__qualname__.split('.')
                else:
                    nam = func.__name__
                f = nam[len(nam) - 1]
                p = '.'.join(x for x in nam if x is not f)
                _flow['flow'] = 1
                # kw = {'topic': 'flow', 'flow': 1}
                xp('{}  ({})'.format(f, p), **_flow)
                obj = func(*args, **kwargs)
                GLB_IND -= 2
            else:
                GLB_IND += 2
                args_repr = [repr(a) for a in args]
                kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
                signature = ", ".join(args_repr + kwargs_repr)
                _flow['flow'] = 1
                # kw = {'topic': 'flow', 'flow': 1}
                xp(f"{func.__name__} ({signature})", **_flow)
                obj = func(*args, **kwargs)
                _flow['flow'] = 0
                # kw = {'topic': 'flow', 'flow': 0}
                xp(f"{func.__name__}  ->  {obj!r}", **_flow)
                # xp(f"|   {func.__name__!r}  ->  {obj!r}", **kw)
                GLB_IND -= 2
            return obj

        return wrapper_flow

    if _func is None:
        return decorator_flow
    else:
        return decorator_flow(_func)


# ! shorter form for flow
GLB_SHORT: bool = False
# ! don't change
GLB_IND: int = -2
# !shut up switch
GLB_LOG: bool = True
# ! print the header once
GLB_HEADER: bool = True

# '': use without kwargs
_xpt('', 'all')

topics = {
    'co': XpConf('all.coincident.impl', 'co').k(),
    'cs': XpConf('all.constraint.impl', 'cs').k(),
    'cf': XpConf('all.config.impl', 'cf').k(),
    'hv': XpConf('all.hor_vert.impl', 'hv').k(),
    'xy': XpConf('all.xy_dist.impl', 'xy').k(),
    'rd': XpConf('all.radius.impl', 'rd').k(),
    'ly': XpConf('all.layout.gui', 'ly').k(),
    'fl': XpConf('all.flags', 'fl').k(),
    'eq': XpConf('all.equal', 'eq').k(),
    'ev': XpConf('all.event', 'ev').k(),
    'pr_edg': XpConf('all.edge', 'eg').k(),
    'co_co': XpConf('all.consider_coin', 'cc').k(),
    'co_bld': XpConf('all.co_build', 'cb').k(),
    'cir': XpConf('all.circle', 'cr').k(),
    'geo': XpConf('all.geo_list', 'ge').k(),
    'flo': XpConf('all.flow').k(),
    'ob_s': XpConf('all.observer.observer_sel', 'ob').k(),
    'ob_g': XpConf('all.observer.observer_gui', 'ob').k(),
    'ob_a': XpConf('all.observer.observer_app', 'ob').k()
}

_co = topics['co']
_cs = topics['cs']
_cf = topics['cf']
_hv = topics['hv']
_xy = topics['xy']
_rd = topics['rd']
_ly = topics['ly']
_fl = topics['fl']
_eq = topics['eq']
_ev = topics['ev']

_prn_edge = topics['pr_edg']
_co_co = topics['co_co']
_co_build = topics['co_bld']
_cir = topics['cir']
_geo = topics['geo']
_flow = topics['flo']
_ob_s = topics['ob_s']
_ob_g = topics['ob_g']
_ob_a = topics['ob_a']

xps(__name__)
if __name__ == '__main__':
    XpConf.topics.add('flow')


    @flow
    def addition_func(x):
        return x + x


    c = XpConf('all.test', 'ooo', True, '*', 'xxx')
    XpConf.topics.add('test')
    XpConf.topics.add('')

    xp('hi:' + 'ho')
    xp('test', 'hi:' + 'ho', **c.k())
    c.std_err = False
    xp('test', 'hi:' + 'ho', **c.k(4))

    addition_func(6)
