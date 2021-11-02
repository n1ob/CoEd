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
from math import dist, asin, degrees, atan2
from operator import attrgetter
from typing import List, Set, Tuple, NamedTuple

import FreeCAD as App
import Part
import Sketcher
from PySide2.QtCore import Signal, QObject, Slot

from . import co_cs
from .. import co_impl
from ..co_base.co_cmn import fmt_vec, ConType, GeoType, ObjType
from ..co_base.co_config import CfgTransient
from ..co_base.co_flag import Dirty
from ..co_base.co_logger import flow, xp, _pa, xps, _ev
from ..co_base.co_lookup import Lookup
from ..co_base.co_observer import observer_event_provider_get


class GeoDiff(NamedTuple):
    geo_idx: int
    difference: float
    construct: bool
    extern: bool

    def __str__(self) -> str:
        return f'({self.geo_idx}) {self.difference:.2f} co {self.construct} ex {self.extern}'

    def __repr__(self) -> str:
        return self.__str__()


class PaEdge:
    def __init__(self, geo_idx: int, y_angel: float, start: App.Vector, end: App.Vector, construct: bool, extern: bool):
        self.geo_idx = geo_idx
        self.pt_start: App.Vector = start
        self.pt_end: App.Vector = end
        self.y_angel: float = y_angel
        self.edg_differences: List[GeoDiff] = list()
        self.construct: bool = construct
        self.extern: bool = extern

    def __str__(self):
        return f"GeoIdx {self.geo_idx}, Start ({fmt_vec(self.pt_start)} End ({fmt_vec(self.pt_end)} " \
               f"ya {self.y_angel:.2f}, diff {self.edg_differences} c {self.construct} e {self.extern}"

    def __repr__(self):
        return self.__str__()

    @flow
    def edg_tolerances_get(self, tol: float) -> List[GeoDiff]:
        res = list()
        for x in self.edg_differences:
            if x.difference <= tol:
                res.append(x)
            else:
                break
        return res

    @flow
    def cons_filter(self, cs: Set[Tuple[int, int]]) -> List[GeoDiff]:
        # find transitive relations
        cn: List[Set[int]] = list()
        for x, y in cs:
            done = False
            xp('in', x, y, **_pa)
            for j in cn:
                if (x in j) and (y in j):
                    xp('skip', **_pa)
                    done = True
                    break
                if (x in j) or (y in j):
                    j.add(x)
                    j.add(y)
                    xp('j', j, **_pa)
                    done = True
                    break
            if not done:
                xp('append', x, y, **_pa)
                cn.append({x, y})
        self._merge_joint_sets(cn)
        # do filter
        res = list()
        for x in self.edg_differences:
            done = False
            for y in cn:
                if (self.geo_idx in y) and (x.geo_idx in y):
                    done = True
                    break  # dismiss
            if not done:
                res.append(x)
        return res

    @flow
    def _merge_joint_sets(self, cn):
        for x in range(len(cn)-1):
            xp(f'in -> x: {x}', **_pa)
            for y in range(x+1, len(cn)):
                xp(f'in -> x: {x} y: {y} cn: {cn}', **_pa)
                if y > len(cn)-1:
                    xp(f'break x: {x} y: {y}', **_pa)
                    break
                if not cn[x].isdisjoint(cn[y]):
                    xp(f'pop x: {x} {cn[x]} y: {y} {cn[y]}', **_pa)
                    cn[x].update(cn[y])
                    cn.pop(y)
                    self._merge_joint_sets(cn)
                else:
                    xp(f'disjoint x: {x} {cn[x]} y: {y} {cn[y]}', **_pa)


class PaEdges(QObject):
    created = Signal(int, int)
    creation_done = Signal()

    def __init__(self, base):
        super(PaEdges, self).__init__()
        self.__init = False
        self.base: co_impl.CoEd = base
        self.sketch: Sketcher.SketchObject = self.base.sketch
        self.cfg = CfgTransient()
        self.tolerance: float = self.cfg.get(self.cfg.PA_TOLERANCE)
        self.differences: List[PaEdge] = list()
        self.tolerances: List[PaEdge] = list()
        self.evo = observer_event_provider_get()
        self.evo.in_edit.connect(self.on_in_edit)
        self.__init = True

    @property
    def tolerance(self):
        return self._tolerance

    @tolerance.setter
    def tolerance(self, value):
        self._tolerance = value
        self.cfg.set(self.cfg.PA_TOLERANCE, value)
        if self.__init:
            self.tolerances_create()

    @property
    def differences(self) -> List[PaEdge]:
        if self.base.flags.has(Dirty.PA_EDGES):
            self.differences_create()
        return self._differences

    @differences.setter
    def differences(self, value):
        self._differences = value

    @property
    def tolerances(self) -> List[PaEdge]:
        if self.base.flags.has(Dirty.PA_EDGES):
            self.tolerances_create()
        return self._tolerances

    @tolerances.setter
    def tolerances(self, value):
        self._tolerances = value

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
        exist_p: Set[Tuple[int, int]] = {(x.first, x.second)
                                         for x in co_list
                                         if ConType(x.type_id) == ConType.PARALLEL}
        xp('exist v/h cons GeoId:', ' '.join(map(str, exist_p)), **_pa)
        return exist_p

    @flow
    def __angles_create(self) -> None:
        geo_lst = [(idx, geo, self.sketch.getConstruction(idx), idx <= -3)
                   for idx, geo
                   in enumerate(self.sketch.Geometry)
                   if geo.TypeId == GeoType.LINE_SEGMENT]
        xp(geo_lst, **_pa)
        lo = Lookup(self.sketch)
        geo_lst += [(geo_id.idx, geo, True, True)
                    for geo_id, geo
                    in lo.extern_points('E')
                    if geo.TypeId == GeoType.LINE_SEGMENT]
        xp(lo.extern_points('E'), **_pa)
        for geo in geo_lst:
            idx, line, c, e = geo
            line: Part.LineSegment
            vs = App.Vector(line.StartPoint)
            ve = App.Vector(line.EndPoint)
            delta_x = ve.x - vs.x
            delta_y = ve.y - vs.y
            angle = degrees(atan2(float(delta_y), float(delta_x)))
            if angle < 0:
                a = 180 + angle
            else:
                a = angle
            # y_angle: float = self.__alpha(App.Vector(line.StartPoint), App.Vector(line.EndPoint))
            edg = PaEdge(idx, a, App.Vector(line.StartPoint), App.Vector(line.EndPoint), c, e)
            self._differences.append(edg)
        self._differences.sort(key=attrgetter('y_angel'))

    @flow
    def differences_create(self):
        self._differences.clear()
        self.__angles_create()
        len_a = len(self._differences)
        for y in range(len_a):
            edg_y: PaEdge = self._differences[y]
            for x in range(len_a):
                if x == y:
                    continue
                edg_x = self._differences[x]
                if x < y:
                    diff = self._differences[x].edg_differences[y - 1].difference
                    n = GeoDiff(edg_x.geo_idx, diff, edg_x.construct, edg_x.extern)
                    edg_y.edg_differences.append(n)
                else:
                    edg_y.edg_differences.append(GeoDiff(edg_x.geo_idx, abs(edg_y.y_angel - edg_x.y_angel), edg_x.construct, edg_x.extern))
        for edg in self._differences:
            edg.edg_differences.sort(key=attrgetter('difference'))
        self.base.flags.reset(Dirty.PA_EDGES)
        self.log_diff()

    @flow
    def tolerances_create(self) -> None:
        self._tolerances.clear()
        for item in self.differences:
            a = PaEdge(item.geo_idx, item.y_angel, item.pt_start, item.pt_end, item.construct, item.extern)
            a.edg_differences = item.edg_tolerances_get(self.tolerance)
            self._tolerances.append(a)
        self.log_tol()

    @flow
    def create(self, edge_lst: List[PaEdge]) -> None:
        doc: App.Document = App.ActiveDocument
        if not len(edge_lst):
            return
        s: Set[Tuple[int, int]] = set()
        con_list = []
        for edge in edge_lst:
            for diff in edge.edg_differences:
                if (diff.geo_idx, edge.geo_idx) in s:
                    xp('skip redundant', diff.geo_idx, edge.geo_idx, **_pa)
                    continue
                s.add((edge.geo_idx, diff.geo_idx))
                con_list.append(Sketcher.Constraint('Parallel', edge.geo_idx, diff.geo_idx))
                xp('created.emit', **_ev)
                self.created.emit(edge.geo_idx, diff.geo_idx)
        doc.openTransaction('coed: Parallel constraint')
        self.sketch.addConstraint(con_list)
        doc.commitTransaction()

        sk: Sketcher.SketchObject = self.sketch
        sk.addProperty('App::PropertyString', 'coed')
        sk.coed = 'eq_recompute'
        doc.openTransaction('coed: obj recompute')
        sk.recompute()
        doc.commitTransaction()
        self.base.flags.all()
        xp('creation_done.emit', **_ev)
        self.creation_done.emit()

    def log_diff(self):
        xps('differences', **_pa)
        for item in self.differences:
            xp(item, **_pa)

    def log_tol(self):
        xps(f'tolerances {self.tolerance}', **_pa)
        for item in self.tolerances:
            xp(item, **_pa)


xps(__name__)
