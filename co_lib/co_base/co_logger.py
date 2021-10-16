import functools
import pathlib
import queue
import sys
import threading
import traceback
from datetime import datetime
from time import perf_counter
from typing import Set, List, AnyStr


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
        print(line)
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


# ! profiling
class Profile:
    def __init__(self, enable: bool = True, top_n: int = 10):
        self.profiler = None
        self.top_n: int = top_n
        self.enable: bool = enable

    def __enter__(self):
        import cProfile
        if self.enable:
            self.profiler = cProfile.Profile()
            self.profiler.enable()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
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


class XpConf:
    topics: Set[str] = set()

    def __init__(self, topic='', prepend=None, std_err=False, separator=None, append=None, thread_info=False):
        self.std_err = std_err
        self.prepend = prepend
        self.append = append
        self.topic = topic
        self.separator = separator
        self.logfile = False
        self.thread_info = thread_info

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
        if self.thread_info:
            d.update({'thread_info': 1})
        return d


def xp(*args, **kwargs):
    if kwargs.pop('thread_info', 0):
        kwargs['thread_name'] = threading.current_thread().name
        kwargs['thread_ident'] = threading.current_thread().ident
    global __perf_start
    kwargs['prepre'] = f'{perf_counter() - __perf_start:9.3f}'
    ind, idx = ind_get(threading.current_thread().ident)
    kwargs['glb_ind'] = ind
    kwargs['thread_idx'] = idx
    global GLB_HEADER
    if GLB_HEADER:
        GLB_HEADER = False
        _xp_header()
    xp_worker.queue.put((args, kwargs))


class XpWorker:
    def __init__(self):
        self.queue = queue.Queue()
        self.thread_event = threading.Event()
        self.thread = threading.Thread(target=self._xp, args=(self.thread_event,), daemon=True)
        self.log_path = ''
        self.run()

    def log_path_set(self, val: str):
        self.log_path = val
        self.thread_event.set()

    def _xp(self, ev: threading.Event):
        ev.wait()
        with open(self.log_path, 'a', 1) as file:
            while True:
                args, kwargs = self.queue.get()
                global GLB_LOG
                add_ind: int = kwargs.pop('add_indent', 0)
                prepend: str = kwargs.pop('prepend', '   ')
                append: str = kwargs.pop('append', None)
                topic: str = kwargs.pop('topic', '')
                prepre: str = kwargs.pop('prepre', '')
                glb_ind: int = kwargs.pop('glb_ind', '')
                thread_name: str = kwargs.pop('thread_name', '')
                thread_ident: str = kwargs.pop('thread_ident', '')
                thread_idx: str = kwargs.pop('thread_idx', 0)
                th = ''
                if len(thread_name):
                    th = f'({thread_name}:{thread_ident})'
                _pre = prepend.ljust(3)
                _topic: List[str] = topic.split('.')
                flow_dir: int = kwargs.pop('flow', -1)
                indent = glb_ind
                # args = ['xx ' '{}' ' xx'.format(i) for i in args]
                args = list(args)
                ai = ''
                if add_ind > 0:
                    ai = ' ' * add_ind
                if flow_dir == -1:
                    args[0] = f'{thread_idx:2}| {ai}{args[0]}'
                elif flow_dir == 0:
                    args[0] = f'{thread_idx:2}|   {args[0]}'
                elif flow_dir == 1:
                    args[0] = f'{thread_idx:2}|-> {args[0]}'
                if indent > 0:
                    args.insert(0, ' ' * (indent - 1))
                if prepend is not None:
                    args.insert(0, _pre)
                if prepre is not None:
                    args.insert(0, prepre)
                if append is not None:
                    args.append(append)
                if len(th):
                    args.append(th)
                # print(*args, **kwargs, sep='-')
                # if topic in XpConf.topics:
                try:
                    if not XpConf.topics.isdisjoint(_topic):
                        # print(*args, **kwargs)
                        if GLB_LOG:
                            file.write(' '.join(f'{x}' for x in args))
                            file.write('\n')
                except ReferenceError as err:
                    file.write('ReferenceError')
                    file.write(str(err))
                    file.write('\n')
                self.queue.task_done()

    def run(self):
        self.thread.start()


def flow(_func=None, *, off=False, short=False):
    def decorator_flow(func):
        @functools.wraps(func)
        def wrapper_flow(*args, **kwargs):
            global GLB_LOG
            _flow['flow'] = -1
            if off or not GLB_LOG:
                obj = func(*args, **kwargs)
            elif short or GLB_SHORT:
                ind_inc(threading.current_thread().ident, 2)
                if hasattr(func, '__qualname__'):
                    nam = func.__qualname__.split('.')
                else:
                    nam = func.__name__
                f = nam[len(nam) - 1]
                p = '.'.join(x for x in nam if x is not f)
                _flow['flow'] = 1
                xp('{}  ({})'.format(f, p), **_flow)
                obj = func(*args, **kwargs)
                _flow['flow'] = 0
                xp('exit {}  ({})'.format(f, p), **_flow)
                ind_dec(threading.current_thread().ident, 2)
            else:
                ind_inc(threading.current_thread().ident, 2)
                args_repr = [repr(a) for a in args]
                kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
                signature = ", ".join(args_repr + kwargs_repr)
                _flow['flow'] = 1
                xp(f"{func.__name__} ({signature})", **_flow)
                obj = func(*args, **kwargs)
                _flow['flow'] = 0
                xp(f"{func.__name__}  ->  {obj!r}", **_flow)
                # xp(f"|   {func.__name__!r}  ->  {obj!r}", **kw)
                ind_dec(threading.current_thread().ident, 2)
            return obj
        return wrapper_flow
    if _func is None:
        return decorator_flow
    else:
        return decorator_flow(_func)


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


class XpWriter:
    def write(self, s: AnyStr) -> int:
        xp(s)
        return 0


def sep(*args):
    print(f'----{args}---')


def _xp_topic(*args):
    [XpConf.topics.add(x) for x in args]


_IND = dict()


def seq_gen(start=1, step=1, reset=0):
    num = start
    while True:
        yield num
        if reset and (num >= reset):
            num = start
        num += step


_T_IDX = seq_gen()


# ! thread sensitive indent handling
def ind_get(ident):
    global _T_IDX
    try:
        return _IND[ident]
    except KeyError:
        _IND[ident] = (0, next(_T_IDX))
        return _IND[ident]


def ind_inc(ident, inc):
    global _T_IDX
    try:
        j, x = _IND[ident]
        j += inc
        _IND[ident] = (j, x)
    except KeyError:
        _IND[ident] = (0, next(_T_IDX))


def ind_dec(ident, dec):
    global _T_IDX
    try:
        j, x = _IND[ident]
        j -= dec
        _IND[ident] = (j, x)
    except KeyError:
        _IND[ident] = (0, next(_T_IDX))


__perf_start: float = perf_counter()
xp_worker: XpWorker = XpWorker()
# ! shorter form for flow
GLB_SHORT: bool = True
# !shut up switch
GLB_LOG: bool = True
# ! print the header once
GLB_HEADER: bool = True


# '': use without kwargs
_xp_topic('')
# _xp_topic('', 'all')


topics = {
    'co': XpConf('all.tab.coincident', prepend='co').k(),
    'cs': XpConf('all.tab.constraint', prepend='cs').k(),
    'hv': XpConf('all.tab.hor_vert', prepend='hv').k(),
    'xy': XpConf('all.tab.xy_dist', prepend='xy').k(),
    'rd': XpConf('all.tab.radius', prepend='rd').k(),
    'pa': XpConf('all.tab.parallel', prepend='pa').k(),
    'eq': XpConf('all.tab.equal', prepend='eq').k(),
    'cf': XpConf('all.tab.config', prepend='cf').k(),
    'go': XpConf('all.tab.geo', prepend='go').k(),

    'tr': XpConf('all.thread', prepend='tr', thread_info=True).k(),
    'ti': XpConf('all.q_thread', prepend='ti').k(),
    'ly': XpConf('all.layout', prepend='ly').k(),
    'ev': XpConf('all.notify.event', prepend='ev').k(),
    'fl': XpConf('all.notify.flags', prepend='fl').k(),
    'flo': XpConf('all.flow').k(),
    'ob_s': XpConf('all.notify.observer.obs_sel', prepend='ob').k(),
    'ob_g': XpConf('all.notify.observer.obs_gui', prepend='ob').k(),
    'ob_a': XpConf('all.notify.observer.obs_app', prepend='ob').k()
}

_co = topics['co']
_cs = topics['cs']
_hv = topics['hv']
_xy = topics['xy']
_rd = topics['rd']
_eq = topics['eq']
_pa = topics['pa']
_cf = topics['cf']
_go = topics['go']

_tr = topics['tr']
_ti = topics['ti']
_ly = topics['ly']
_fl = topics['fl']
_ev = topics['ev']
_flow = topics['flo']
_ob_s = topics['ob_s']
_ob_g = topics['ob_g']
_ob_a = topics['ob_a']

xps(__name__)
if __name__ == '__main__':
    pass

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
