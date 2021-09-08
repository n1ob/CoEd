from enum import Enum
from typing import NamedTuple, Dict, Tuple
import threading

from FreeCADTypes import Sketcher
import FreeCAD as App

from co_flag import Cs
from co_logger import xps

try:
    SketchType = Sketcher.SketchObject
except AttributeError:
    SketchType = Sketcher.Sketch


class ConsTrans(NamedTuple):
    co_idx: int
    type_id: str
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
    return f'({vec.x:.2f}, {vec.y:.2f}, {vec.z:.2f})'


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
    type_id: str

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


def seq_gen(start=1, step=1):
    num = start
    while True:
        yield num
        num += step

xps(__name__)
if __name__ == '__main__':

    s1 = Singleton()
    s2 = Singleton()

    print(s1)
    print(s2)

    s = seq_gen()
    print(next(s))
    print(next(s))
    print(next(s))
    print(next(s))


    # import re
    # lis = re.findall(r'\d+', s)
    # for x in lis:
    #     xp(int(x))
    # # self.cons_tbl_wid.selectRow(1)

    # idx = self.tabs.currentIndex()
    # if idx < 5:
    #     cur_tbl = switcher.get(idx)
    #     for row in range(cur_tbl.rowCount()):
    #         co: CoEd.Constraint = cur_tbl.item(row, 2)
