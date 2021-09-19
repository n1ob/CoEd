from typing import List, NamedTuple, Tuple, Set

import Sketcher
import FreeCAD as App

import co_cs
from co_cmn import ConType
from co_flag import Dirty
import co_impl

# geo_lst: List[Tuple[int, float]] = [(0, 1.0), (2, 1.1), (4, 0.9), (6, 1.2), (7, 0.8),
#                                     (8, 1.3), (9, 1.1)]
from co_logger import xp, xps, flow, _eq, _ev


class GeoDiff(NamedTuple):
    geo_idx: int
    difference: float

    def __str__(self) -> str:
        return f'{self.geo_idx} {self.difference:.2f}'

    def __repr__(self) -> str:
        return self.__str__()


class EqEdge:
    def __init__(self, geo_idx, length) -> None:
        self.geo_idx: int = geo_idx
        self.length: float = length
        self.edg_differences: List[GeoDiff] = list()

    def __str__(self) -> str:
        return f'geo: {self.geo_idx} length: {self.length:.2f} diff: {self.edg_differences}'

    def __repr__(self) -> str:
        return self.__str__()

    @flow
    def edg_tolerances_get(self, tol: float) -> List[GeoDiff]:
        res = list()
        for x in self.edg_differences:
            if x.difference <= tol:
                res.append(x)
        return res

    @flow
    def cons_filter(self, cs: Set[Tuple[int, int]]) -> List[GeoDiff]:
        # find transitive relations
        cn: List[Set[int]] = list()
        for x, y in cs:
            done = False
            xp('in', x, y, **_eq)
            for j in cn:
                if (x in j) and (y in j):
                    xp('skip', **_eq)
                    done = True
                    break
                if (x in j) or (y in j):
                    j.add(x)
                    j.add(y)
                    xp('j', j, **_eq)
                    done = True
                    break
            if not done:
                xp('append', x, y, **_eq)
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
            xp(f'in -> x: {x}', **_eq)
            for y in range(x+1, len(cn)):
                xp(f'in -> x: {x} y: {y} cn: {cn}', **_eq)
                if y > len(cn)-1:
                    xp(f'break x: {x} y: {y}', **_eq)
                    break
                if not cn[x].isdisjoint(cn[y]):
                    xp(f'pop x: {x} {cn[x]} y: {y} {cn[y]}', **_eq)
                    cn[x].update(cn[y])
                    cn.pop(y)
                    self._merge_joint_sets(cn)
                else:
                    xp(f'disjoint x: {x} {cn[x]} y: {y} {cn[y]}', **_eq)


class EqEdges:
    def __init__(self, base) -> None:
        self.__init = False
        self.base: co_impl.CoEd = base
        self.__diff_init = False
        self.__tol_init = False
        self.tolerance: float = 0.1
        self.differences: List[EqEdge] = list()
        self.tolerances: List[EqEdge] = list()
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
    def tolerances(self) -> List[EqEdge]:
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
    def differences(self) -> List[EqEdge]:
        if not self.__diff_init:
            self.__diff_init = True
            self.differences_create()

        if self.base.flags.has(Dirty.EQ_EDGES):
            self.differences_create()

        return self._differences

    @differences.setter
    def differences(self, value):
        self._differences = value

    @flow
    def differences_create(self) -> None:
        # filter for linesegments
        self._differences.clear()
        geo_lst = [(idx, geo.length()) for idx, geo
                   in enumerate(self.base.sketch.Geometry)
                   if geo.TypeId == 'Part::GeomLineSegment']
        len_geo = len(geo_lst)
        for y in range(len_geo):
            id_y, le_y = geo_lst[y]
            a = EqEdge(id_y, le_y)
            for x in range(len_geo):
                if x == y:
                    # no point for diff on itself
                    continue
                id_x, le_x = geo_lst[x]
                if x < y:
                    # diffs are symetric, no need to recompute
                    diff = self._differences[x].edg_differences[y - 1].difference
                    n = GeoDiff(id_x, diff)
                    a.edg_differences.append(n)
                else:
                    a.edg_differences.append(GeoDiff(id_x, abs(le_y - le_x)))
            self._differences.append(a)
        self.base.flags.reset(Dirty.EQ_EDGES)
        self.log_diff()

    @flow
    def tolerances_create(self) -> None:
        self._tolerance_lst.clear()
        for item in self.differences:
            a = EqEdge(item.geo_idx, item.length)
            a.edg_differences = item.edg_tolerances_get(self.tolerance)
            self._tolerance_lst.append(a)
        self.log_tol()

    @flow
    def create(self, edge_lst: List[EqEdge]) -> None:
        doc: App.Document = App.ActiveDocument
        if not len(edge_lst):
            return
        for edge in edge_lst:
            for diff in edge.edg_differences:
                doc.openTransaction('coed: Equal constraint')
                self.base.sketch.addConstraint(Sketcher.Constraint('Equal', edge.geo_idx, diff.geo_idx))
                doc.commitTransaction()

        self.base.flags.set(Dirty.CONSTRAINTS)
        self.base.flags.set(Dirty.EQ_EDGES)
        self.base.flags.set(Dirty.XY_EDGES)
        self.base.flags.set(Dirty.COIN_POINTS)

        sk: Sketcher.SketchObject = self.base.sketch
        sk.addProperty('App::PropertyString', 'coed')
        sk.coed = 'eq_recompute'
        doc.openTransaction('coed: obj recompute')
        sk.recompute()
        doc.commitTransaction()
        xp('ev.eq_chg.emit', **_ev)
        self.base.ev.eq_chg.emit('eq create finish')

    # Sketcher.Constraint('Equal', 4, 6)
    @flow
    def cons_get(self) -> Set[Tuple[int, int]]:
        co_list: List[co_cs.Constraint] = self.base.constraints_get_list()
        col: Set[Tuple[int, int]] = {(x.first, x.second)
                                     for x in co_list
                                     if ConType(x.type_id) == ConType.EQUAL}
        return col

    def log_diff(self):
        xps('difference_lst', **_eq)
        for item in self.differences:
            xp(item, **_eq)

    def log_tol(self):
        xps(f'tolerance {self.tolerance}', **_eq)
        for item in self.tolerances:
            xp(item, **_eq)


xps(__name__)
if __name__ == '__main__':

    b = EqEdges()

    for item in b.differences:
        print(item)

    print('-------------------------------------------------')
    print('tolerance', b.tolerance)
    for item in b.tolerances:
        print(item)

    b.tolerance = 0.2

    print('-------------------------------------------------')
    print('tolerance', b.tolerance)
    for item in b.tolerances:
        print(item)
