from typing import Set, NamedTuple, List, Tuple

import FreeCAD as App
import Part
import Sketcher

import co_cs
import co_impl
from co_cmn import fmt_vec, pt_typ_str
from co_flag import Dirty
from co_logger import flow, xp, _xy, _ev, xps


class GeoId(NamedTuple):
    idx: int
    typ: int

    def __str__(self) -> str:
        return f'({self.idx}.{pt_typ_str(self.typ)})'

    def __repr__(self) -> str:
        return f'({self.idx}.{self.typ})'


class XyEdge:

    def __init__(self, geo_idx: int, start: App.Vector, end: App.Vector, x: bool, y: bool):
        self.geo_idx = geo_idx
        self.start: App.Vector = start
        self.end: App.Vector = end
        self.has_x: bool = x
        self.has_y: bool = y

    def __str__(self):
        return f"GeoIdx {self.geo_idx}, Start ({fmt_vec(self.start)} End ({fmt_vec(self.end)} x {self.has_x} " \
               f"y {self.has_y}"

    def __repr__(self):
        return self.__str__()

    @flow
    def filter(self, cs: Set[int]) -> bool:
        if self.geo_idx not in cs:
            return True
        return False


class XyEdges:

    def __init__(self, base):
        self.__init = False
        self.base: co_impl.CoEd = base
        self.edges: List[XyEdge] = list()
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
    def cons_get(self) -> (Set[Tuple[GeoId, GeoId]], Set[Tuple[GeoId, GeoId]]):
        co_list: List[co_cs.Constraint] = self.base.constraints_get_list()
        exist_x: Set[Tuple[GeoId, GeoId]] = {(GeoId(x.first, x.first_pos), GeoId(x.second, x.second_pos))
                                             for x in co_list
                                             if (x.type_id == 'DistanceX') and (x.second_pos != 0)}
        exist_y: Set[Tuple[GeoId, GeoId]] = {(GeoId(x.first, x.first_pos), GeoId(x.second, x.second_pos))
                                             for x in co_list
                                             if (x.type_id == 'DistanceY') and (x.second_pos != 0)}
        xp('exist xy cons GeoId: X', ' '.join(map(str, exist_x)), ' Y', ' '.join(map(str, exist_y)), **_xy)
        return exist_x, exist_y

    @flow
    def edges_create(self):
        self._edges.clear()
        geo_lst = [(idx, geo) for idx, geo
                   in enumerate(self.base.sketch.Geometry)
                   if geo.TypeId == 'Part::GeomLineSegment']
        exist_x, exist_y = self.cons_get()
        exist_x: Set[Tuple[GeoId, GeoId]]
        exist_y: Set[Tuple[GeoId, GeoId]]
        ex_x = {(x[0].idx, x[1].idx) for x in exist_x}
        ex_y = {(x[0].idx, x[1].idx) for x in exist_y}
        for idx, line in geo_lst:
            line: Part.LineSegment
            ed: XyEdge = XyEdge(idx, App.Vector(line.StartPoint), App.Vector(line.EndPoint),
                                ((idx, idx) in ex_x), ((idx, idx) in ex_y))
            self._edges.append(ed)
        [xp(xy_edge, **_xy) for xy_edge in self._edges]
        self.base.flags.reset(Dirty.XY_EDGES)

    @flow
    def dist_create(self, edg_list: List[XyEdge], x: bool, y: bool):
        doc: App.Document = App.ActiveDocument
        xp('geo_list', edg_list, **_xy)
        for edg in edg_list:
            idx = edg.geo_idx
            if (not edg.has_x) and x:
                x1 = edg.start.x
                x2 = edg.end.x
                doc.openTransaction('coed: DistanceX constraint')
                self.base.sketch.addConstraint(Sketcher.Constraint('DistanceX', idx, 1, idx, 2, (x2 - x1)))
                doc.commitTransaction()
                xp(f'DistanceX, geo_start ({idx}.1) geo_end ({idx}.2), {(x2 - x1)}', **_xy)
            if (not edg.has_y) and y:
                y1 = edg.start.y
                y2 = edg.end.y
                doc.openTransaction('coed: DistanceX constraint')
                self.base.sketch.addConstraint(Sketcher.Constraint('DistanceX', idx, 1, idx, 2, (y2 - y1)))
                doc.commitTransaction()
                xp(f'DistanceX, geo_start ({idx}.1) geo_end ({idx}.2), {(y2 - y1)}', **_xy)

        if len(edg_list) > 0:
            sk: Sketcher.SketchObject = self.base.sketch
            sk.addProperty('App::PropertyString', 'coed')
            sk.coed = 'xy_recompute'
            doc.openTransaction('coed: obj recompute')
            sk.recompute()
            doc.commitTransaction()
            self.base.flags.set(Dirty.CONSTRAINTS)
            self.base.flags.set(Dirty.XY_EDGES)
            xp('xy_edg_chg.emit', **_ev)
            self.base.ev.xy_edg_chg.emit('xy create finish')


xps(__name__)
