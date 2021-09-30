from math import dist, asin, degrees
from operator import attrgetter
from typing import List, Set

import FreeCAD as App
import Part
import Sketcher
from PySide2.QtCore import Signal, QObject

import co_cs
import co_impl
from co_cmn import fmt_vec
from co_flag import Dirty
from co_logger import flow, xp, _hv, xps, _ev, Profile


class HvEdge:

    def __init__(self, geo_idx: int, y_angel: float, start: App.Vector, end: App.Vector):
        self.geo_idx = geo_idx
        self.pt_start: App.Vector = start
        self.pt_end: App.Vector = end
        self.x_angel: float = 90 - y_angel
        self.y_angel: float = y_angel

    def __str__(self):
        return f"GeoIdx {self.geo_idx}, Start ({fmt_vec(self.pt_start)} End ({fmt_vec(self.pt_end)} " \
               f"xa {self.x_angel:.2f} ya {self.y_angel:.2f}"

    def __repr__(self):
        return self.__str__()

    @flow
    def cons_filter(self, cs: Set[int]) -> bool:
        if self.geo_idx not in cs:
            return True
        return False


class HvEdges(QObject):

    created = Signal(str, int)
    creation_done = Signal()

    def __init__(self, base):
        super(HvEdges, self).__init__()
        self.__init = False
        self.__tol_init = False
        self.__angle_init = False
        self.base: co_impl.CoEd = base
        self.tolerance: float = 0.1
        self.angles: List[HvEdge] = list()
        self.tolerances: List[HvEdge] = list()
        self.__init = True

    @property
    def tolerance(self):
        return self._tolerance

    @tolerance.setter
    def tolerance(self, value):
        self._tolerance = value
        if self.__init:
            self.tolerances_create()

    @property
    def tolerances(self) -> List[HvEdge]:
        if not self.__tol_init:
            self.__tol_init = True
            self.tolerances_create()

        if self.base.flags.has(Dirty.HV_EDGES):
            self.tolerances_create()

        return self._tolerance_lst

    @tolerances.setter
    def tolerances(self, value):
        self._tolerance_lst = value

    @property
    def angles(self) -> List[HvEdge]:
        with Profile(enable=False):
            if not self.__angle_init:
                self.__angle_init = True
                self.angles_create()

            if self.base.flags.has(Dirty.HV_EDGES):
                self.angles_create()

        return self._angles

    @angles.setter
    def angles(self, value):
        self._angles = value

    # def hv_edges_get_list(self) -> List[HvEdge]:
    #     pass

    @staticmethod
    def __ge(start: App.Vector, end: App.Vector) -> float:
        pt: List[float] = [start.x, end.y, 0.0]
        en: List[float] = [end.x, end.y, 0.0]
        return dist(en, pt)

    @staticmethod
    def __hy(start: App.Vector, end: App.Vector) -> float:
        st: List[float] = [start.x, start.y, 0.0]
        en: List[float] = [end.x, end.y, 0.0]
        return dist(st, en)

    def __alpha(self, start: App.Vector, end: App.Vector) -> float:
        return degrees(asin(self.__ge(start, end) / self.__hy(start, end)))

    @flow
    def cons_get(self) -> (Set[int], Set[int]):
        co_list: List[co_cs.Constraint] = self.base.cs.constraints
        exist_h: Set[int] = {x.first
                             for x in co_list
                             if (x.type_id == 'Horizontal') and (x.first_pos == 0)}
        exist_v: Set[int] = {x.first
                             for x in co_list
                             if (x.type_id == 'Vertical') and (x.first_pos == 0)}
        xp('exist v/h cons GeoId:', ' '.join(map(str, exist_v)), ' '.join(map(str, exist_h)), **_hv)
        return exist_v, exist_h

    @flow
    def angles_create(self) -> None:
        self._angles.clear()
        geo_lst = [(idx, geo) for idx, geo
                   in enumerate(self.base.sketch.Geometry)
                   if geo.TypeId == 'Part::GeomLineSegment']
        len_geo = len(geo_lst)
        for x in range(len_geo):
            idx, line = geo_lst[x]
            line: Part.LineSegment
            y_angle: float = self.__alpha(App.Vector(line.StartPoint), App.Vector(line.EndPoint))
            edg = HvEdge(idx, y_angle, App.Vector(line.StartPoint), App.Vector(line.EndPoint))
            self._angles.append(edg)
        self._angles.sort(key=attrgetter('y_angel'))
        self.base.flags.reset(Dirty.HV_EDGES)
        self.log_angle()

    @flow
    def tolerances_create(self):
        self._tolerance_lst.clear()
        # sorted by y
        for edg in self.angles:
            if edg.y_angel < self._tolerance:
                self._tolerance_lst.append(edg)
            else:
                break
        for edg in reversed(self.angles):
            if edg.x_angel < self._tolerance:
                self._tolerance_lst.append(edg)
            else:
                break
        self.log_tol()

    # @flow
    # def filter_lst(self, cs: Set[int]):
    #     res: List[HvEdge] = list()
    #     for edg in self.tolerance_lst:
    #         if edg.geo_idx not in cs:
    #             res.append(edg)
    #     return res

    @flow
    def create(self, edge_lst: List[HvEdge]):
        doc: App.Document = App.ActiveDocument
        for edge in edge_lst:
            if edge.x_angel <= self.tolerance:
                con = Sketcher.Constraint('Horizontal', edge.geo_idx)
                doc.openTransaction('coed: Horizontal constraint')
                self.base.sketch.addConstraint(con)
                doc.commitTransaction()
                xp('created.emit: Horizontal', edge.geo_idx, **_ev)
                self.created.emit('Horizontal', edge.geo_idx)
                continue
            if edge.y_angel <= self.tolerance:
                con = Sketcher.Constraint('Vertical', edge.geo_idx)
                doc.openTransaction('coed: Vertical constraint')
                self.base.sketch.addConstraint(con)
                doc.commitTransaction()
                xp('created.emit: Vertical', edge.geo_idx, **_ev)
                self.created.emit('Vertical', edge.geo_idx)
        sk: Sketcher.SketchObject = self.base.sketch
        sk.addProperty('App::PropertyString', 'coed')
        sk.coed = 'hv_recompute'
        doc.openTransaction('coed: obj recompute')
        sk.recompute()
        doc.commitTransaction()
        self.base.flags.set(Dirty.HV_EDGES)
        self.base.flags.set(Dirty.CONSTRAINTS)
        # xp('hv_edg_chg.emit', **_ev)
        # self.base.ev.hv_edg_chg.emit('hv create finish')
        xp('creation_done.emit', **_ev)
        self.creation_done.emit()

    def log_angle(self):
        xps('difference_lst', **_hv)
        for item in self.angles:
            xp(item, **_hv)

    def log_tol(self):
        xps(f'tolerance {self.tolerance}', **_hv)
        for item in self.tolerances:
            xp(item, **_hv)


xps(__name__)
