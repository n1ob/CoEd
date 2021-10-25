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
from typing import Set, NamedTuple, List, Tuple

import FreeCAD as App
import Part
import Sketcher
from PySide2.QtCore import Signal, QObject, Slot

from . import co_cs
from .. import co_impl
from ..co_base.co_cmn import fmt_vec, pt_typ_str, GeoType, ConType, ObjType
from ..co_base.co_flag import Dirty
from ..co_base.co_logger import flow, xp, _xy, _ev, xps
from ..co_base.co_lookup import Lookup
from ..co_base.co_observer import observer_event_provider_get


class GeoId(NamedTuple):
    idx: int
    typ: int

    def __str__(self) -> str:
        return f'({self.idx}.{pt_typ_str[self.typ]})'

    def __repr__(self) -> str:
        return f'({self.idx}.{self.typ})'


class XyEdge:
    def __init__(self, geo_idx: int, start: App.Vector, end: App.Vector, x: bool, y: bool, construct: bool, extern: bool):
        self.geo_idx = geo_idx
        self.start: App.Vector = start
        self.end: App.Vector = end
        self.has_x: bool = x
        self.has_y: bool = y
        self.construct: bool = construct
        self.extern: bool = extern

    def __str__(self):
        return f"GeoIdx {self.geo_idx}, Start ({fmt_vec(self.start)} End ({fmt_vec(self.end)} x {self.has_x} " \
               f"y {self.has_y} co {self.construct} ex {self.extern}"

    def __repr__(self):
        return self.__str__()

    @flow
    def filter(self, cs: Set[int]) -> bool:
        if self.geo_idx not in cs:
            return True
        return False


class XyEdges(QObject):
    created = Signal(str, int, float)
    creation_done = Signal()

    def __init__(self, base):
        super(XyEdges, self).__init__()
        self.__init = False
        self.base: co_impl.CoEd = base
        self.sketch: Sketcher.SketchObject = self.base.sketch
        self.edges: List[XyEdge] = list()
        self.evo = observer_event_provider_get()
        self.evo.in_edit.connect(self.on_in_edit)
        self.__init = True

    @property
    def edges(self) -> List[XyEdge]:
        if not self.__init:
            self.__init = True
            self.edges_create()
        if self.base.flags.has(Dirty.XY_EDGES):
            self.edges_create()
        return self._edges

    @edges.setter
    def edges(self, value):
        self._edges = value

    @flow
    @Slot(object)
    def on_in_edit(self, obj):
        if obj.TypeId == ObjType.VIEW_PROVIDER_SKETCH:
            ed_info = App.Gui.ActiveDocument.InEditInfo
            if (ed_info is not None) and (ed_info[0].TypeId == ObjType.SKETCH_OBJECT):
                self.sketch = ed_info[0]

    @flow
    def cons_get(self) -> (Set[Tuple[GeoId, GeoId]], Set[Tuple[GeoId, GeoId]]):
        co_list: List[co_cs.Constraint] = self.base.cs.constraints
        exist_x: Set[Tuple[GeoId, GeoId]] = {(GeoId(x.first, x.first_pos), GeoId(x.second, x.second_pos))
                                             for x in co_list
                                             if (x.type_id == ConType.DISTANCEX.value) and (x.second_pos != 0)}
        exist_y: Set[Tuple[GeoId, GeoId]] = {(GeoId(x.first, x.first_pos), GeoId(x.second, x.second_pos))
                                             for x in co_list
                                             if (x.type_id == ConType.DISTANCEY.value) and (x.second_pos != 0)}
        xp('exist xy cons GeoId: X', ' '.join(map(str, exist_x)), ' Y', ' '.join(map(str, exist_y)), **_xy)
        return exist_x, exist_y

    @flow
    def edges_create(self):
        self._edges.clear()
        geo_lst = [(idx, geo)
                   for idx, geo
                   in enumerate(self.sketch.Geometry)
                   if geo.TypeId == GeoType.LINE_SEGMENT]
        lo = Lookup(self.sketch)
        geo_lst += [(id_.idx, geo)
                    for id_, geo
                    in lo.extern_points('E')
                    if geo.TypeId == GeoType.LINE_SEGMENT]
        exist_x, exist_y = self.cons_get()
        exist_x: Set[Tuple[GeoId, GeoId]]
        exist_y: Set[Tuple[GeoId, GeoId]]
        ex_x = {(x[0].idx, x[1].idx) for x in exist_x}
        ex_y = {(x[0].idx, x[1].idx) for x in exist_y}
        for idx, line in geo_lst:
            line: Part.LineSegment
            ed: XyEdge = XyEdge(idx, App.Vector(line.StartPoint), App.Vector(line.EndPoint),
                                ((idx, idx) in ex_x), ((idx, idx) in ex_y), self.sketch.getConstruction(idx), idx <= -3)
            self._edges.append(ed)
        [xp(xy_edge, **_xy) for xy_edge in self._edges]
        self.base.flags.reset(Dirty.XY_EDGES)

    @flow
    def dist_create(self, edg_list: List[XyEdge], x: bool, y: bool):
        doc: App.Document = App.ActiveDocument
        xp('geo_list', edg_list, **_xy)
        con_list = []
        for edg in edg_list:
            idx = edg.geo_idx
            if (not edg.has_x) and x:
                x1 = edg.start.x
                x2 = edg.end.x
                con_list.append(Sketcher.Constraint(ConType.DISTANCEX.value, idx, 1, idx, 2, (x2 - x1)))
                xp(f'DistanceX created, geo_start ({idx}.1) geo_end ({idx}.2), {(x2 - x1)}', **_xy)
                xp('created.emit: DistanceX', idx, (x2 - x1), **_ev)
                self.created.emit('DistanceX', idx, (x2 - x1))
            if (not edg.has_y) and y:
                y1 = edg.start.y
                y2 = edg.end.y
                con_list.append(Sketcher.Constraint(ConType.DISTANCEY.value, idx, 1, idx, 2, (y2 - y1)))
                xp(f'DistanceY created, geo_start ({idx}.1) geo_end ({idx}.2), {(y2 - y1)}', **_xy)
                xp('created.emit: DistanceY', idx, (y2 - y1), **_ev)
                self.created.emit('DistanceY', idx, (y2 - y1))
        doc.openTransaction('coed: DistanceX/DistanceX constraint')
        self.sketch.addConstraint(con_list)
        doc.commitTransaction()

        if len(edg_list) > 0:
            sk: Sketcher.SketchObject = self.sketch
            sk.addProperty('App::PropertyString', 'coed')
            sk.coed = 'xy_recompute'
            doc.openTransaction('coed: obj recompute')
            sk.recompute()
            doc.commitTransaction()
            self.base.flags.set(Dirty.CONSTRAINTS)
            self.base.flags.set(Dirty.XY_EDGES)
            xp('creation_done.emit', **_ev)
            self.creation_done.emit()


xps(__name__)
