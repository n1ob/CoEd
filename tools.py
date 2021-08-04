from enum import Enum
from typing import NamedTuple
import threading

from FreeCADTypes import Sketcher

try:
    SketcherType = Sketcher.SketchObject
except AttributeError:
    SketcherType = Sketcher.Sketch


pt_typ_str = {0: 'n', 1: 's', 2: 'e', 3: 'm'}
pt_typ_int = {y: x for x, y in pt_typ_str.items()}


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


if __name__ == '__main__':

    s1 = Singleton()
    s2 = Singleton()

    print(s1)
    print(s2)





