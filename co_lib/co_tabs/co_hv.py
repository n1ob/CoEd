# ***************************************************************************
# *   Copyright (c) 2021 n1ob <niob@gmx.com>                                *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# ***************************************************************************
from math import dist, asin, degrees
from operator import attrgetter
from typing import List, Set

import FreeCAD as App
import Part
import Sketcher
from PySide2.QtCore import Signal, QObject, Slot

from . import co_cs
from .. import co_impl
from ..co_base.co_cmn import fmt_vec, GeoType, ObjType
from ..co_base.co_config import CfgTransient
from ..co_base.co_flag import Dirty
from ..co_base.co_logger import flow, xp, _hv, xps, _ev, Profile
from ..co_base.co_lookup import Lookup
from ..co_base.co_observer import observer_event_provider_get


class HvEdge:
    def __init__(self, geo_idx: int, y_angel: float, start: App.Vector, end: App.Vector, construct: bool, extern: bool):
        self.geo_idx = geo_idx
        self.pt_start: App.Vector = start
        self.pt_end: App.Vector = end
        self.x_angel: float = 90 - y_angel
        self.y_angel: float = y_angel
        self.construct: bool = construct
        self.extern: bool = extern

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
        self.sketch: Sketcher.SketchObject = self.base.sketch
        self.evo = observer_event_provider_get()
        self.evo.in_edit.connect(self.on_in_edit)
        self.cfg = CfgTransient()
        self.tolerance: float = self.cfg.get(self.cfg.HV_TOLERANCE)
        self.angles: List[HvEdge] = list()
        self.tolerances: List[HvEdge] = list()
        self.__init = True

    @property
    def tolerance(self):
        return self._tolerance

    @tolerance.setter
    def tolerance(self, value):
        self._tolerance = value
        self.cfg.set(self.cfg.HV_TOLERANCE, value)
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

    @flow
    @Slot(object)
    def on_in_edit(self, obj):
        if obj.TypeId == ObjType.VIEW_PROVIDER_SKETCH:
            ed_info = App.Gui.ActiveDocument.InEditInfo
            if (ed_info is not None) and (ed_info[0].TypeId == ObjType.SKETCH_OBJECT):
                self.sketch = ed_info[0]

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
        geo_lst = [(idx, geo, self.sketch.getConstruction(idx), idx <= -3)
                   for idx, geo
                   in enumerate(self.sketch.Geometry)
                   if geo.TypeId == GeoType.LINE_SEGMENT]
        lo = Lookup(self.sketch)
        geo_lst += [(id_.idx, geo, True, True)
                    for id_, geo
                    in lo.extern_points('E')
                    if geo.TypeId == GeoType.LINE_SEGMENT]
        # geo_lst += [(idx, len_, True, True) for idx, len_ in lo.extern_points()]
        xp(geo_lst)
        len_geo = len(geo_lst)
        for x in range(len_geo):
            idx, line, c, e = geo_lst[x]
            line: Part.LineSegment
            y_angle: float = self.__alpha(App.Vector(line.StartPoint), App.Vector(line.EndPoint))
            edg = HvEdge(idx, y_angle, App.Vector(line.StartPoint), App.Vector(line.EndPoint), c, e)
            xp(f'HvEdge: {idx} {y_angle:.2f} {fmt_vec(App.Vector(line.StartPoint))} {fmt_vec(App.Vector(line.EndPoint))} c {c} e {e}')
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

    @flow
    def create(self, edge_lst: List[HvEdge]):
        doc: App.Document = App.ActiveDocument
        con_list = []
        for edge in edge_lst:
            if edge.x_angel <= self.tolerance:
                con = Sketcher.Constraint('Horizontal', edge.geo_idx)
                con_list.append(con)
                xp('created.emit: Horizontal', edge.geo_idx, **_ev)
                self.created.emit('Horizontal', edge.geo_idx)
                continue
            if edge.y_angel <= self.tolerance:
                con = Sketcher.Constraint('Vertical', edge.geo_idx)
                con_list.append(con)
                xp('created.emit: Vertical', edge.geo_idx, **_ev)
                self.created.emit('Vertical', edge.geo_idx)
        doc.openTransaction('coed: Horizontal/Vertical constraint')
        self.sketch.addConstraint(con_list)
        doc.commitTransaction()

        sk: Sketcher.SketchObject = self.sketch
        sk.addProperty('App::PropertyString', 'coed')
        sk.coed = 'hv_recompute'
        doc.openTransaction('coed: obj recompute')
        sk.recompute()
        doc.commitTransaction()
        self.base.flags.set(Dirty.HV_EDGES)
        self.base.flags.set(Dirty.CONSTRAINTS)
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
