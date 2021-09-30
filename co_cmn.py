from enum import Enum
from typing import NamedTuple, Dict, Tuple, List, Iterable
import threading

from FreeCADTypes import Sketcher
import FreeCAD as App

from co_flag import Cs
from co_logger import xps, xp

try:
    SketchType = Sketcher.SketchObject
except AttributeError:
    SketchType = Sketcher.Sketch


class ConsTrans(NamedTuple):
    co_idx: int
    type_id: int
    sub_type: Cs
    fmt: str

# ! PointPos lets us refer to different aspects of a piece of geometry.  sketcher::none refers
#  * to an edge itself (eg., for a Perpendicular constraint on two lines). sketcher::start and
#  * sketcher::end denote the endpoints of lines or bounded curves.  sketcher::mid denotes
#  * geometries with geometrical centers (eg., circle, ellipse). Bare points use 'start'.  More
#  * complex geometries like parabola focus or b-spline knots use InternalAlignment constraints
#  * in addition to PointPos.
#
# enum PointPos { none    = 0,
#                 start   = 1,
#                 end     = 2,
#                 mid     = 3 };


pt_typ_str = {0: 'n', 1: 's', 2: 'e', 3: 'm'}
pt_typ_int = {y: x for x, y in pt_typ_str.items()}


def fmt_vec(vec: App.Vector) -> str:
    return f'({vec.x:.1f}, {vec.y:.1f}, {vec.z:.1f})'


# noinspection SpellCheckingInspection,PyPep8
class ConType(Enum):
    NONE              = "None"
    COINCIDENT        = "Coincident"
    HORIZONTAL        = "Horizontal"
    VERTICAL          = "Vertical"
    PARALLEL          = "Parallel"
    TANGENT           = "Tangent"
    DISTANCE          = "Distance"
    DISTANCEX         = "DistanceX"
    DISTANCEY         = "DistanceY"
    ANGLE             = "Angle"
    PERPENDICULAR     = "Perpendicular"
    RADIUS            = "Radius"
    EQUAL             = "Equal"
    POINTONOBJECT     = "PointOnObject"
    SYMMETRIC         = "Symmetric"
    INTERNALALIGNMENT = "InternalAlignment"
    SNELLSLAW         = "SnellsLaw"
    BLOCK             = "Block"
    DIAMETER          = "Diameter"
    WEIGHT            = "Weight"
    ALL               = "All"


class GeoPt(NamedTuple):
    geo_id: int
    type_id: int

    def __str__(self):
        return "GeoId {}.{}".format(self.geo_id, self.type_id)


class GeoPtn(NamedTuple):
    geo_id: int
    type_id: int

    def __str__(self):
        return "GeoId {}.{}".format(self.geo_id, self.type_id)


class ConsCoin(NamedTuple):
    first: GeoPt
    second: GeoPt

    def __str__(self):
        return "GeoIds {}, {}".format(self.first, self.second)


class Singleton:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                # another thread could have created the instance
                # before we acquired the lock. So check that the
                # instance is still nonexistent.
                if not cls._instance:
                    cls._instance = super(Singleton, cls).__new__(cls)
        return cls._instance


def get_class_that_defined_method(method):
    method_name = method.__name__
    if method.__self__:
        classes = [method.__self__.__class__]
    else:
        classes = [method.im_class]
    while classes:
        c = classes.pop()
        if method_name in c.__dict__:
            return c
        else:
            classes = list(c.__bases__) + classes
    return None


def seq_gen(start=1, step=1, reset=0):
    num = start
    while True:
        yield num
        if reset and (num >= reset):
            num = start
        num += step


def complement_color(rgb: str) -> str:
    s1 = rgb.replace('#', '0x')
    # f'{0xffffff - 0x110011:06x}'
    return f'#{0xffffff - int(s1, 16):06x}'


def split_rgb(color: str) -> (int, int, int):
    strip = color.lstrip('#')
    r = int(strip[:2], 16)
    g = int(strip[2:4], 16)
    b = int(strip[4:6], 16)
    return r, g, b


# https://stackoverflow.com/questions/3942878/how-to-decide-font-color-in-white-or-black-depending-on-background-color
def lumi(rgb: Iterable) -> float:  # iterable contains [r, g, b]
    res: List[float] = list()
    for c in rgb:
        c = c / 255.0
        if c <= 0.03928:
            c = c / 12.92
        else:
            c = ((c+0.055) / 1.055) ** 2.4
        res.append(c)
    lu = 0.2126 * res[0] + 0.7152 * res[1] + 0.0722 * res[2]
    return lu


def contrast_color(lu: float) -> str:
    if lu > 0.179:  # use #000000 else use #ffffff
        return '#000000'
    else:
        return '#ffffff'


xps(__name__)
if __name__ == '__main__':

    sc = '#aaaaaa'
    xp(contrast_color(lumi(split_rgb(sc))))

    # s1 = Singleton()
    # s2 = Singleton()
    #
    # print(s1)
    # print(s2)
    #
    # s = seq_gen()
    # print(next(s))
    # print(next(s))
    # print(next(s))
    # print(next(s))


    # import re
    # lis = re.findall(r'\d+', s)
    # for x in lis:
    #     xp(int(x))
    # # self.cons_tbl_wid.selectRow(1)

    # idx = self.tabs.currentIndex()
    # if idx < 5:
    #     cur_tbl = switcher.get(idx)
    #     for row in range(cur_tbl.rowCount()):
    #         co: co_cs.Constraint = cur_tbl.item(row, 2)
