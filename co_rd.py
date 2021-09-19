from typing import List, Set
import FreeCAD as App
import Part
import Sketcher

import co_cs
import co_impl
from co_cmn import fmt_vec
from co_flag import Dirty
from co_logger import flow, xp, _cir, _rd, _ev, xps


class RdCircle:

    def __init__(self, idx: int, center: App.Vector, xu: float, rd: float):
        self.geo_idx: int = idx
        self.center: App.Vector = center
        self.angle_xu: float = xu
        self.radius: float = rd

    def __str__(self):
        s = f"GeoIdx {self.geo_idx}, Center {fmt_vec(self.center)}, xu {self.angle_xu}, rad {self.radius}"
        return s

    def __repr__(self):
        return self.__str__()


class RdCircles:

    def __init__(self, base):
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
            self.circles_create()
        if self.base.flags.has(Dirty.RD_CIRCLES):
            self.circles_create()
        return self._circles

    @circles.setter
    def circles(self, value):
        self._circles = value

    # @flow
    # def circle_get_list(self) -> List[RdCircle]:
    #     return self.rad_circle_detect()

    @flow
    def circles_create(self):
        self._circles.clear()
        geo_list = self.base.sketch.Geometry
        x: Part.Circle
        c_list: List[RdCircle] = [RdCircle(idx, App.Vector(x.Center), x.AngleXU, x.Radius)
                                  for idx, x in enumerate(geo_list)
                                  if x.TypeId == 'Part::GeomCircle']
        xp(c_list, **_rd)
        self._circles = c_list

    @flow
    def dia_create(self, cir_list: List[RdCircle], radius: float):
        doc: App.Document = App.ActiveDocument
        if len(cir_list):
            for cir in cir_list:
                if radius is not None:
                    doc.openTransaction('coed: Diameter constraint')
                    self.base.sketch.addConstraint(Sketcher.Constraint('Diameter', cir.geo_idx, radius * 2))
                    doc.commitTransaction()
                else:
                    doc.openTransaction('coed: Diameter constraint')
                    self.base.sketch.addConstraint(Sketcher.Constraint('Diameter', cir.geo_idx, cir.radius * 2))
                    doc.commitTransaction()
            sk: Sketcher.SketchObject = self.base.sketch
            sk.addProperty('App::PropertyString', 'coed')
            sk.coed = 'rad_recompute'
            doc.openTransaction('coed: obj recompute')
            sk.recompute()
            doc.commitTransaction()
            self.base.flags.set(Dirty.CONSTRAINTS)
            self.base.flags.set(Dirty.RD_CIRCLES)
            xp('rad_chg.emit', **_ev)
            self.base.ev.rad_chg.emit('rad create finish')

    @flow
    def cons_get(self):
        co_list: List[co_cs.Constraint] = self.base.constraints_get_list()
        rad: Set[int] = {x.first
                         for x in co_list
                         if x.type_id == 'Radius'}
        dia: Set[int] = {x.first
                         for x in co_list
                         if x.type_id == 'Diameter' }
        xp('rad/dia GeoId:', ' '.join(map(str, rad)), ' '.join(map(str, dia)), **_rd)
        return rad, dia


xps(__name__)
