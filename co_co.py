from operator import attrgetter

import FreeCAD as App
from typing import List, NamedTuple, Tuple, Set

import Sketcher
import Part

# geo_lst = [()]
from PySide2.QtCore import Signal, QObject

import co_cs
import co_impl
from co_cmn import ConType, pt_typ_int
from co_flag import Dirty, Flags
from co_logger import flow, xp, xps, _co, _ev


class GeoId(NamedTuple):
    idx: int
    typ: int

    def __str__(self) -> str:
        return f'({self.idx}.{self.typ})'

    def __repr__(self) -> str:
        return self.__str__()


class GeoIdDist(NamedTuple):
    geo_id: GeoId
    distance: float

    def __str__(self) -> str:
        return f'{self.geo_id} {self.distance:6.2f}'

    def __repr__(self) -> str:
        return self.__str__()


class CoPoint:
    def __init__(self, geo: GeoId, pt: App.Vector) -> None:
        self.geo_id: GeoId = geo
        self.point: App.Vector = pt
        self.pt_distance_lst: List[GeoIdDist] = list()

    def __str__(self) -> str:
        return f'{self.geo_id} ({self.point.x:5.2f}, {self.point.y:5.2f}, {self.point.z:5.2f})  {self.pt_distance_lst}'

    def __repr__(self) -> str:
        return self.__str__()

    @flow
    def distances_get(self, tol: float) -> List[GeoIdDist]:
        res = list()
        for x in self.pt_distance_lst:
            if x.distance <= tol:
                res.append(x)
            else:
                break
        return res

    @flow
    def cons_filter(self, cs: Set[Tuple[GeoId, GeoId]]) -> List[GeoIdDist]:
        # find transitive relations
        cn: List[Set[GeoId]] = list()
        for x, y in cs:
            done = False
            xp('in', x, y, **_co)
            for j in cn:
                if (x in j) and (y in j):
                    xp('skip', **_co)
                    done = True
                    break
                if (x in j) or (y in j):
                    j.add(x)
                    j.add(y)
                    xp('j', j, **_co)
                    done = True
                    break
            if not done:
                xp('append', x, y, **_co)
                cn.append({x, y})
        self._merge_joint_sets(cn)
        # do filter
        res = list()
        for x in self.pt_distance_lst:
            done = False
            for y in cn:
                xp(f'{self.geo_id} {x} cn {y}', **_co)
                if (self.geo_id in y) and (x.geo_id in y):
                    xp('dismiss', **_co)
                    done = True
                    break  # dismiss
            if not done:
                xp('append', x, **_co)
                res.append(x)
        return res

    @flow
    def _merge_joint_sets(self, cn):
        for x in range(len(cn) - 1):
            xp(f'in -> x: {x}', **_co)
            for y in range(x + 1, len(cn)):
                xp(f'in -> x: {x} y: {y} cn: {cn}', **_co)
                if y > len(cn) - 1:
                    xp(f'break x: {x} y: {y}', **_co)
                    break
                if not cn[x].isdisjoint(cn[y]):
                    xp(f'pop x: {x} {cn[x]} y: {y} {cn[y]}', **_co)
                    cn[x].update(cn[y])
                    cn.pop(y)
                    self._merge_joint_sets(cn)
                else:
                    xp(f'disjoint x: {x} {cn[x]} y: {y} {cn[y]}', **_co)


class CoPoints(QObject):

    created = Signal(tuple, tuple)
    creation_done = Signal()

    def __init__(self, base) -> None:
        self.__init = False
        super(CoPoints, self).__init__()
        self.__tol_init = False
        self.__dist_init = False
        self.base: co_impl.CoEd = base
        self.tolerance: float = 1.1
        self.distances: List[CoPoint] = list()
        self.tolerances: List[CoPoint] = list()
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
    def tolerances(self) -> List[CoPoint]:
        if not self.__tol_init:
            self.__tol_init = True
            self.tolerances_create()

        if self.base.flags.has(Dirty.EQ_EDGES):
            self.tolerances_create()

        return self._tolerance_lst

    @tolerances.setter
    def tolerances(self, value):
        self._tolerance_lst = value

    @property
    def distances(self) -> List[CoPoint]:
        if not self.__dist_init:
            self.__dist_init = True
            self.distances_create()

        if self.base.flags.has(Dirty.EQ_EDGES):
            self.distances_create()

        return self._distance_lst

    @distances.setter
    def distances(self, value):
        self._distance_lst = value

    @flow
    def distances_create(self):
        self._distance_lst.clear()
        # filter for line segments

        geo_lst: List[Tuple[int, Part.LineSegment]] = [(idx, geo) for idx, geo
                                                       in enumerate(self.base.sketch.Geometry)
                                                       if geo.TypeId == 'Part::GeomLineSegment']

        pt_lst = [CoPoint(GeoId(idx, 1), App.Vector(line.StartPoint)) for idx, line in geo_lst]
        pt_lst += [CoPoint(GeoId(idx, 2), App.Vector(line.EndPoint)) for idx, line in geo_lst]

        pt_len = len(pt_lst)
        for y in range(pt_len):
            pt_y: CoPoint = pt_lst[y]
            for x in range(pt_len):
                if x == y:
                    continue
                pt_x: CoPoint = pt_lst[x]
                if x < y:
                    dist = self._distance_lst[x].pt_distance_lst[y - 1].distance
                    i = GeoId(pt_x.geo_id.idx, pt_x.geo_id.typ)
                    n = GeoIdDist(i, dist)
                    pt_y.pt_distance_lst.append(n)
                else:
                    pt_x: CoPoint = pt_lst[x]
                    dist = pt_y.point.distanceToPoint(pt_x.point)
                    g_dist = GeoIdDist(pt_x.geo_id, dist)
                    pt_y.pt_distance_lst.append(g_dist)
            self._distance_lst.append(pt_y)
        for pt in self._distance_lst:
            pt.pt_distance_lst.sort(key=attrgetter('distance'))
        self.log_diff()

    @flow
    def tolerances_create(self) -> None:
        self._tolerance_lst.clear()
        for item in self.distances:
            a = CoPoint(GeoId(item.geo_id.idx, item.geo_id.typ), item.point)
            a.pt_distance_lst = item.distances_get(self.tolerance)
            self._tolerance_lst.append(a)
        self.log_tol()

    @flow
    def cons_get(self) -> Set[Tuple[GeoId, GeoId]]:
        co_list: List[co_cs.Constraint] = self.base.cs.constraints
        # co_list: List[co_cs.Constraint] = self.base.constraints_get_list()
        col: Set[Tuple[GeoId, GeoId]] = {
            (GeoId(x.first, x.first_pos), GeoId(x.second, x.second_pos))
            for x in co_list
            if ConType(x.type_id) == ConType.COINCIDENT}
        return col

    @flow
    def create(self, co_pt_list: List[CoPoint]):
        doc: App.Document = App.ActiveDocument
        xp('pt_idx_list', co_pt_list, **_co)
        if len(co_pt_list) == 0:
            return
        s: Set[Tuple[GeoId, GeoId]] = set()
        for pt in co_pt_list:
            xp('pt', pt.pt_distance_lst, **_co)
            for dist in pt.pt_distance_lst:
                xp('Coincident', pt.geo_id, dist.geo_id, **_co)
                if (dist.geo_id, pt.geo_id) in s:
                    xp('skip redundant', dist.geo_id, pt.geo_id, **_co)
                    continue
                s.add((pt.geo_id, dist.geo_id))
                con = Sketcher.Constraint('Coincident', pt.geo_id.idx, pt.geo_id.typ, dist.geo_id.idx,
                                          dist.geo_id.typ)
                doc.openTransaction('coed: Coincident constraint')
                self.base.sketch.addConstraint(con)
                doc.commitTransaction()
                xp('created.emit', pt.geo_id, dist.geo_id, **_ev)
                self.created.emit((pt.geo_id.idx, pt.geo_id.typ), (dist.geo_id.idx, dist.geo_id.typ))
        self.base.flags.all()
        sk: Sketcher.SketchObject = self.base.sketch
        sk.addProperty('App::PropertyString', 'coed')
        sk.coed = 'coin_recompute'
        doc.openTransaction('coed: obj recompute')
        sk.recompute()
        doc.commitTransaction()
        # xp('coin_pts_chg.emit', **_ev)
        # self.base.ev.coin_pts_chg.emit('coin_create finish')
        xp('creation_done.emit', **_ev)
        self.creation_done.emit()

    def log_diff(self):
        xps('difference_lst', **_co)
        for item in self._distance_lst:
            xp(item, **_co)

    def log_tol(self):
        xps(f'tolerance {self._tolerance}', **_co)
        for item in self._tolerance_lst:
            xp(item, **_co)


xps(__name__)
if __name__ == '__main__':
    DOC = "Test"
    SKETCH = "Sketch"


    class A:
        def __init__(self):
            self.flags = Flags(Dirty)
            self.flags.all()

        def constraints_get_list(self):
            return []


    a = A()


    def add_geo(o: object, b: bool = False):
        App.getDocument(DOC).getObject(SKETCH).addGeometry(o, b)


    App.newDocument(DOC)
    App.setActiveDocument(DOC)
    App.ActiveDocument = App.getDocument(DOC)
    App.activeDocument().addObject('Sketcher::SketchObject', 'Sketch')
    App.activeDocument().Sketch.Placement = App.Placement(App.Vector(0.000000, 0.000000, 0.000000),
                                                          App.Rotation(0.000000, 0.000000, 0.000000, 1.000000))
    App.activeDocument().Sketch.MapMode = "Deactivated"
    ActiveSketch = App.getDocument(DOC).getObject('Sketch')
    App.ActiveDocument.recompute()

    add_geo(Part.LineSegment(App.Vector(-8.0, -5.0, 0.0), App.Vector(4.0, 7.0, 0.0)))
    add_geo(Part.LineSegment(App.Vector(5.0, 7.0, 0.0), App.Vector(7.0, -8.0, 0.0)))
    add_geo(Part.LineSegment(App.Vector(-8.0, -6.0, 0.0), App.Vector(7.0, -9.0, 0.0)))
    add_geo(Part.LineSegment(App.Vector(4.0, 8.0, 0.0), App.Vector(20.0, 10.0, 0.0)))

    co = CoPoints(a)
    # co.dist_lst_create()
    co.tolerances_create()

    App.closeDocument(DOC)
