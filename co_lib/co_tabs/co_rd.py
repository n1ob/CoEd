from typing import List, Set

import FreeCAD as App
import Part
import Sketcher
from PySide2.QtCore import Signal, QObject

from . import co_cs
from .. import co_impl
from ..co_base.co_cmn import fmt_vec
from ..co_base.co_flag import Dirty
from ..co_base.co_logger import flow, xp, _rd, _ev, xps


class RdCircle:
    def __init__(self, idx: int, center: App.Vector, xu: float, rd: float, typ: str, construct: bool):
        self.geo_idx: int = idx
        self.center: App.Vector = center
        self.angle_xu: float = xu
        self.radius: float = rd
        self.type_id: str = typ
        self.construct: bool = construct

    def __str__(self):
        s = f"GeoIdx {self.geo_idx}, Center {fmt_vec(self.center)}, xu {self.angle_xu}, rad {self.radius}"
        return s

    def __repr__(self):
        return self.__str__()


class RdCircles(QObject):
    created = Signal(int, float)
    creation_done = Signal()

    def __init__(self, base):
        super(RdCircles, self).__init__()
        self.__init = False
        self.base: co_impl.CoEd = base
        self.circles: List[RdCircle] = list()
        self.radius: float = 1
        self.__init = True

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, value):
        self._radius = value

    @property
    def circles(self) -> List[RdCircle]:
        if not self.__init:
            self.__init = True
            self.circles_update()
        if self.base.flags.has(Dirty.RD_CIRCLES):
            self.circles_update()
        return self._circles

    @circles.setter
    def circles(self, value):
        self._circles = value

    @flow
    def circles_update(self):
        self._circles.clear()
        geo_list = self.base.sketch.Geometry
        x: Part.Circle
        c_list: List[RdCircle] = [RdCircle(idx, App.Vector(x.Center), x.AngleXU, x.Radius, x.TypeId, self.base.sketch.getConstruction(idx))
                                  for idx, x in enumerate(geo_list)
                                  if (x.TypeId == 'Part::GeomCircle') or (x.TypeId == 'Part::GeomArcOfCircle')]
        xp(c_list, **_rd)
        self._circles = c_list

    @flow
    def dia_create(self, cir_list: List[RdCircle], radius: float):
        doc: App.Document = App.ActiveDocument
        con_list = []
        if len(cir_list):
            for cir in cir_list:
                if radius is not None:
                    con_list.append(Sketcher.Constraint('Diameter', cir.geo_idx, radius * 2))
                    xp('created.emit', cir.type_id, cir.geo_idx, radius, **_ev)
                    self.created.emit(cir.geo_idx, radius)
                else:
                    con_list.append(Sketcher.Constraint('Diameter', cir.geo_idx, cir.radius * 2))
                    xp('created.emit', cir.type_id, cir.geo_idx, cir.radius, **_ev)
                    self.created.emit(cir.geo_idx, cir.radius)
            doc.openTransaction('coed: Diameter constraint')
            self.base.sketch.addConstraint(con_list)
            doc.commitTransaction()
            sk: Sketcher.SketchObject = self.base.sketch
            sk.addProperty('App::PropertyString', 'coed')
            sk.coed = 'rad_recompute'
            doc.openTransaction('coed: obj recompute')
            sk.recompute()
            doc.commitTransaction()
            self.base.flags.set(Dirty.CONSTRAINTS)
            self.base.flags.set(Dirty.RD_CIRCLES)
            xp('creation_done.emit', **_ev)
            self.creation_done.emit()

    @flow
    def cons_get(self):
        co_list: List[co_cs.Constraint] = self.base.cs.constraints
        rad: Set[int] = {x.first
                         for x in co_list
                         if x.type_id == 'Radius'}
        dia: Set[int] = {x.first
                         for x in co_list
                         if x.type_id == 'Diameter' }
        xp('rad/dia GeoId:', ' '.join(map(str, rad)), ' '.join(map(str, dia)), **_rd)
        return rad, dia


xps(__name__)
