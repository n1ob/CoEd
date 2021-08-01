import math
from enum import Enum
from math import *
from typing import List, NamedTuple, Set

from io import StringIO

import Part
import Sketcher
from FreeCAD import Base

from tools import xp, flow, _cir, _xy, _hv, _co_build, _co_co, _geo, _prn_edge, xpe

try:
    SketcherType = Sketcher.SketchObject
except AttributeError:
    SketcherType = Sketcher.Sketch

pt_pos_str = {
    0: 'n',
    1: 's',
    2: 'e',
    3: 'm'
}


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


class FixIt:
    class Circle(NamedTuple):
        geo_id: int
        center_x: float
        center_y: float
        angle_xu: float
        radius: float

        def __str__(self):
            s = "GeoId {}, Center ({}, {}), xu {}, rad {}"
            return s.format(self.geo_id, self.center_x, self.center_y, self.angle_xu, self.radius)

    class Point:
        def __init__(self, geo_item_pt: Base.Vector, geo_list_idx: int, pt_type: int):
            self.geo_item_pt: Base.Vector = geo_item_pt
            self.coin_pts: List[FixIt.Point.CoinPt] = []
            self.extend(geo_list_idx, pt_type)

        def __str__(self):
            s = "GeoId {}.{}, Start {:.2f}, End {:.2f}, CPts {}"
            return s.format(self.coin_pts[0].geo_idx, self.coin_pts[0].pt_type, self.geo_item_pt.x,
                            self.geo_item_pt.y, self.coin_pts)

        def extend(self, geo_list_idx: int, pt_type: int):
            item = FixIt.Point.CoinPt(geo_list_idx, pt_type)
            self.coin_pts.append(item)

        class CoinPt(NamedTuple):
            geo_idx: int
            pt_type: int

            def __str__(self):
                return "GeoId {}.{}".format(self.geo_idx, self.pt_type)

    class HvEdge:
        def __init__(self, geo_idx: int, seg: Part.LineSegment, x_angel: float, y_angel: float, has_hv: bool = False):
            self.geo_idx = geo_idx
            self.seg: Part.LineSegment = seg
            self.pt_start: Base.Vector = Base.Vector(seg.StartPoint)
            self.pt_end: Base.Vector = Base.Vector(seg.EndPoint)
            self.x_angel: float = fabs(x_angel)
            self.y_angel: float = fabs(y_angel)
            self.has_hv_cons = has_hv

        def __str__(self):
            s = "GeoId {}, Start ({:.2f}, {:.2f}), End ({:.2f}, {:.2f}), xa {}, ya {}, cs {}"
            return s.format(self.geo_idx, self.pt_start.x, self.pt_start.y, self.pt_end.x, self.pt_end.y,
                            self.x_angel, self.y_angel, self.has_hv_cons)

    class XyEdge:
        def __init__(self, geo_id: int, start: Base.Vector, end: Base.Vector, has_x: bool = False, has_y: bool = False):
            self.geo_id: int = geo_id
            self.start: Base.Vector = start
            self.end: Base.Vector = end
            self.has_x: bool = has_x
            self.has_y: bool = has_y

        def __str__(self):
            s = "GeoId {}, Start ({:.2f}, {:.2f}), End ({:.2f}, {:.2f}), csX {}, csY {}"
            return s.format(self.geo_id, self.start.x, self.start.y, self.end.x, self.end.y, self.has_x, self.has_y)

    class Constraint:
        def __init__(self, co_idx: int, type_id: str, **kwargs):
            self.co_idx: int = co_idx
            self.type_id: str = type_id
            self.first: int = kwargs.get('FIRST', -1)
            self.first_pos: str = kwargs.get('FIRST_POS', 0)
            self.second: int = kwargs.get('SECOND', -1)
            self.second_pos: str = kwargs.get('SECOND_POS', 0)
            self.third: int = kwargs.get('THIRD', -1)
            self.third_pos: str = kwargs.get('THIRD_POS', 0)
            self.value: float = kwargs.get('VALUE', -0)
            self.fmt = kwargs.get('FMT', "{0} : {1} : {2} : {3} : {4} : {5} : {6} : {7}")

        def __str__(self):
            return self.fmt.format(self.first + 1, self.first_pos,  # (0),(1)
                                   self.second + 1, self.second_pos,  # (2),(3)
                                   self.third + 1, self.third_pos,  # (4),(5)
                                   self.value, self.co_idx)  # (6),(7)

    x_axis: Base.Vector = Base.Vector(1, 0, 0)
    y_axis: Base.Vector = Base.Vector(0, 1, 0)

    @flow
    def __init__(self, sk: SketcherType, snap_dist: float = 0, snap_angel: float = 0):
        self.__init = False
        self.sketch: SketcherType = sk
        self.snap_dist: float = snap_dist
        self.snap_angel: float = snap_angel
        self.radius: float = 5
        self.__hv_edges: List[FixIt.HvEdge] = list()
        self.__xy_edges: List[FixIt.XyEdge] = list()
        self.__coin_points: List[FixIt.Point] = list()
        self.__constraints: List[FixIt.Constraint] = list()
        self.__hv_edges_dirty: bool = True
        self.__xy_edges_dirty: bool = True
        self.__coin_points_dirty: bool = True
        self.__constraints_dirty: bool = True
        self.__dbg_co_pts_list: List[str] = list()
        self.__init = True

    @property
    def radius(self) -> float:
        return self.__radius

    @radius.setter
    def radius(self, value: float):
        self.__radius = value
        pass

    @property
    def snap_dist(self) -> float:
        return self.__snap_dist

    @snap_dist.setter
    def snap_dist(self, value: float):
        self.__snap_dist: float = value
        self.__coin_points_dirty = True

    @property
    def snap_angel(self) -> float:
        return self.__snap_angel

    @snap_angel.setter
    def snap_angel(self, value: float):
        self.__snap_angel: float = value
        self.__hv_edges_dirty = True

    @property
    def sketch(self) -> SketcherType:
        return self.__sketch

    @sketch.setter
    def sketch(self, value: SketcherType):
        self.__sketch: SketcherType = value
        self.__constraints_dirty = True
        self.__hv_edges_dirty = True
        self.__coin_points_dirty = True

    @flow
    def circle_get_list(self) -> List[Circle]:
        geo_list = self.sketch.Geometry
        c_list: List[FixIt.Circle] = [FixIt.Circle(idx, x.Center.x, x.Center.y, x.AngleXU, x.Radius)
                                      for idx, x in enumerate(geo_list)
                                      if x.TypeId == 'Part::GeomCircle']
        xp(c_list, **_cir.k())
        return c_list

    @flow
    def points_get_list(self) -> List[Point]:
        if self.__coin_points_dirty:
            self.coin_detect_missing()
        return self.__coin_points

    @flow
    def constraints_get_list(self) -> List[Constraint]:
        if self.__constraints_dirty:
            self.constraints_detect()
        return self.__constraints

    @flow
    def hv_edges_get_list(self) -> List[HvEdge]:
        if self.__hv_edges_dirty:
            self.hv_detect_missing()
        return self.__hv_edges

    @flow
    def xy_edg_get_list(self):
        if self.__xy_edges_dirty:
            self.xy_detect_missing()
        return self.__xy_edges

    @flow
    def xy_detect_missing(self):
        self.__xy_edges.clear()
        co_list: List[FixIt.Constraint] = self.constraints_get_list()
        exist_x: List[(int, int)] = [(x.first, x.second)
                                     for x in co_list
                                     if x.type_id == 'DistanceX']
        exist_y: List[(int, int)] = [(x.first, x.second)
                                     for x in co_list
                                     if x.type_id == 'DistanceY']
        xp('existing constrains GeoId: X', ' '.join(map(str, exist_x)), ' Y', ' '.join(map(str, exist_y)), **_xy.k())
        xpe(_xy, 0, 'existing constrains GeoId: X', ' '.join(map(str, exist_x)), ' Y', ' '.join(map(str, exist_y)))
        geo_list = self.sketch.Geometry
        for idx, geo_item in enumerate(geo_list):
            if geo_item.TypeId == 'Part::GeomLineSegment':
                seg: Part.LineSegment = geo_item
                ed: FixIt.XyEdge = FixIt.XyEdge(idx, Base.Vector(seg.StartPoint), Base.Vector(seg.EndPoint),
                                                ((idx, idx) in exist_x), ((idx, idx) in exist_y))
                self.__xy_edges.append(ed)
        [xp(xy_edge, **_xy.k()) for xy_edge in self.__xy_edges]
        self.__xy_edges_dirty = False

    ###############
    # Vertical / Horizontal
    @staticmethod
    def __ge(start: Base.Vector, end: Base.Vector) -> float:
        pt: List[float] = [start.x, end.y, 0.0]
        en: List[float] = [end.x, end.y, 0.0]
        return dist(en, pt)

    @staticmethod
    def __hy(start: Base.Vector, end: Base.Vector) -> float:
        st: List[float] = [start.x, start.y, 0.0]
        en: List[float] = [end.x, end.y, 0.0]
        return dist(st, en)

    def __alpha(self, start: Base.Vector, end: Base.Vector) -> float:
        return degrees(asin(self.__ge(start, end) / self.__hy(start, end)))

    @flow
    def hv_detect_missing(self) -> None:
        self.__hv_edges.clear()
        co_list: List[FixIt.Constraint] = self.constraints_get_list()
        existing: List[int] = [x.first for x in co_list if (x.type_id == 'Horizontal') or (x.type_id == 'Vertical')]
        xp('existing constrains GeoId:', ' '.join(map(str, existing)), **_hv.k())
        geo_list = self.sketch.Geometry
        for idx, geo_item in enumerate(geo_list):
            if geo_item.TypeId == 'Part::GeomLineSegment':
                seg: Part.LineSegment = geo_item
                a: float = self.__alpha(Base.Vector(seg.StartPoint), Base.Vector(seg.EndPoint))
                if (a < self.snap_angel) or ((90 - a) < self.snap_angel):
                    self.__hv_edges.append(FixIt.HvEdge(idx, seg, 90 - a, a, (idx in existing)))
        self.__hv_edges_dirty = False
        self.print_edge_angel_list()

    @flow
    def hv_create(self, edge_id_list: List[int]):
        for idx in edge_id_list:
            edge: FixIt.HvEdge = self.__hv_edges[idx]
            if edge.x_angel <= self.snap_angel:
                con = Sketcher.Constraint('Horizontal', edge.geo_idx)
                self.sketch.addConstraint(con)
                continue
            if edge.y_angel <= self.snap_angel:
                con = Sketcher.Constraint('Vertical', edge.geo_idx)
                self.sketch.addConstraint(con)
        self.__hv_edges_dirty = True

    ##############
    # Coincident
    def __coin_add_point(self, geo_item_pt: Base.Vector, geo_list_idx: int, pt_type: int, tolerance: float, cs: Set[ConsCoin]):
        xp("({:.2f}, {:.2f}) : Id {:n} : Type {:n}".format(geo_item_pt.x, geo_item_pt.y, geo_list_idx, pt_type),
           **_co_build.k(2))
        new_pt = FixIt.Point(geo_item_pt, geo_list_idx, pt_type)
        for i, pt in enumerate(self.__coin_points):
            xp("Id: {:n} Dist {:.4f}".format(i, pt.geo_item_pt.distanceToPoint(new_pt.geo_item_pt)), **_co_build.k(4))
            if self.__coin_consider(pt, new_pt, cs):
                if pt.geo_item_pt.isEqual(new_pt.geo_item_pt, tolerance):
                    xp('snap', **_co_build.k(8))
                    pt.extend(geo_list_idx, pt_type)
                    return
        self.__coin_points.append(new_pt)

    def __coin_get_cons_tuples(self) -> Set[ConsCoin]:
        co_list: List[FixIt.Constraint] = self.constraints_get_list()
        col: Set[ConsCoin] = {ConsCoin(GeoPt(x.first, x.first_pos), GeoPt(x.second, x.second_pos))
                              for x in co_list
                              if ConType(x.type_id) == ConType.COINCIDENT}
        return col

    def __coin_consider(self, pt: Point, new_pt: Point, cs: Set[ConsCoin]) -> bool:
        pn: GeoPt = GeoPt(new_pt.coin_pts[0].geo_idx, pt_pos_str[new_pt.coin_pts[0].pt_type])
        pts: Set[GeoPt] = set(map(lambda x: GeoPt(x.geo_idx, pt_pos_str[x.pt_type]), pt.coin_pts))
        xp('CS :', str(cs), 'PN :', str(pn), 'PTS: ' + str(pts), **_co_co.k(4))
        if any(a.geo_id == pn.geo_id for a in pts):
            xp('any(a[0] == pn[0] for a in pts)', **_co_co.k(8))
            return False
        if any(((a, pn) in cs) for a in pts):
            xp('any(((a, pn) in cs) for a in pts)', **_co_co.k(8))
            return False
        if any(((pn, a) in cs) for a in pts):
            xp('any(((pn, a) in cs) for a in pts)', **_co_co.k(8))
            return False
        return True

    @flow
    def coin_detect_missing(self) -> None:
        self.__coin_points.clear()
        cs: Set[ConsCoin] = self.__coin_get_cons_tuples()
        geo_list = self.sketch.Geometry
        for i in range(len(geo_list)):
            xp("Sketch.Geometry: {:n}".format(i), **_co_build.k())
            if geo_list[i].TypeId == 'Part::GeomLineSegment':
                start: Base.Vector = geo_list[i].StartPoint
                end: Base.Vector = geo_list[i].EndPoint
                self.__coin_add_point(start, i, 1, self.snap_dist, cs)
                self.__coin_add_point(end, i, 2, self.snap_dist, cs)

    @flow
    def coin_create(self, pt_idx_list: List[int]):
        for idx in pt_idx_list:
            pt = self.__coin_points[idx]
            if len(pt.coin_pts) == 1:
                continue
            if len(pt.coin_pts) > 1:
                # only create a connect chain
                for i in range(len(pt.coin_pts) - 1):
                    p1 = pt.coin_pts[i - 1]
                    p2 = pt.coin_pts[i]
                    con = Sketcher.Constraint('Coincident', p1.geo_idx, p1.pt_type, p2.geo_idx, p2.pt_type)
                    self.sketch.addConstraint(con)
                    self.__constraints_dirty = True
                    self.__coin_points_dirty = True

    ##############
    # distances
    @flow
    def xy_dist_create(self, geo_id_list: List[int]):
        obj = self.points_get_list()
        for pt in obj:
            self.sketch.addConstraint(Sketcher.Constraint(
                'DistanceX', pt.coin_pts[0].geo_idx, pt.coin_pts[0].pt_type, pt.geo_item_pt.x))
            self.sketch.addConstraint(Sketcher.Constraint(
                'DistanceY', pt.coin_pts[0].geo_idx, pt.coin_pts[0].pt_type, pt.geo_item_pt.y))

    ##############
    # diameters
    @flow
    def diameter_create(self, geo_id_list: List[int], radius: float):
        geo_list: list = self.sketch.Geometry
        for idx in geo_id_list:
            if radius is not None:
                self.sketch.addConstraint(Sketcher.Constraint('Diameter', idx, radius * 2))
            else:
                cir: Part.Circle = geo_list[idx]
                self.sketch.addConstraint(Sketcher.Constraint('Diameter', idx, cir.Radius * 2))

    ##############
    # Constraint
    @flow
    def constraints_detect(self):
        self.__constraints_dirty = False
        self.__constraints.clear()
        # noinspection PyUnresolvedReferences
        co_list: list = self.sketch.Constraints
        for i in range(len(co_list)):
            item = co_list[i]
            ct: ConType = ConType(item.Type)
            if ct == ConType.COINCIDENT:
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2
                kwargs = {
                    'FIRST': item.First,
                    'FIRST_POS': pt_pos_str[item.FirstPos],
                    'SECOND': item.Second,
                    'SECOND_POS': pt_pos_str[item.SecondPos],
                    'FMT': "{0}.{1} : {2}.{3}"
                }
                con = self.Constraint(i, ct.value, **kwargs)
                self.__constraints.append(con)

            elif ct == ConType.HORIZONTAL or ct == ConType.VERTICAL:
                # ConstraintType, GeoIndex
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2
                if item.Second == -2000:
                    kwargs = {
                        'FIRST': item.First,
                        'FIRST_POS': pt_pos_str[item.FirstPos],
                        'FMT': "{0}.{1}"
                    }
                else:
                    kwargs = {
                        'FIRST': item.First,
                        'FIRST_POS': pt_pos_str[item.FirstPos],
                        'SECOND': item.Second,
                        'SECOND_POS': pt_pos_str[item.SecondPos],
                        'FMT': "{0}.{1} : {2}.{3}"
                    }
                con = self.Constraint(i, ct.value, **kwargs)
                self.__constraints.append(con)

            elif ct == ConType.PARALLEL or ct == ConType.EQUAL:
                # ConstraintType, GeoIndex1, GeoIndex2
                kwargs = {
                    'FIRST': item.First,
                    'SECOND': item.Second,
                    'FMT': "{0} : {2}"
                }
                con = self.Constraint(i, ct.value, **kwargs)
                self.__constraints.append(con)

            elif ct == ConType.TANGENT or ct == ConType.PERPENDICULAR:
                # ConstraintType, GeoIndex1, GeoIndex2
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2
                kwargs = {
                    'FIRST': item.First,
                    'FIRST_POS': pt_pos_str[item.FirstPos],
                    'SECOND': item.Second,
                    'SECOND_POS': pt_pos_str[item.SecondPos],
                    'FMT': "{0}.{1} : {2}.{3}"
                }
                con = self.Constraint(i, ct.value, **kwargs)
                self.__constraints.append(con)

            elif ct == ConType.DISTANCE:
                # ConstraintType, GeoIndex, Value
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, Value
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2, Value
                if item.Second == -2000:
                    kwargs = {
                        'FIRST': item.First,
                        'FIRST_POS': pt_pos_str[item.FirstPos],
                        'VALUE': item.Value,
                        'FMT': "{0}.{1}  v: {6:.2f}"
                    }
                else:
                    kwargs = {
                        'FIRST': item.First,
                        'FIRST_POS': pt_pos_str[item.FirstPos],
                        'SECOND': item.Second,
                        'SECOND_POS': pt_pos_str[item.SecondPos],
                        'VALUE': item.Value,
                        'FMT': "{0}.{1} : {2}.{3}  v: {6:.2f}"
                    }
                con = self.Constraint(i, ct.value, **kwargs)
                self.__constraints.append(con)

            elif ct == ConType.DISTANCEX or ct == ConType.DISTANCEY:
                # ConstraintType, GeoIndex, Value
                # ConstraintType, GeoIndex, PosIndex, Value
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2, Value
                kwargs = {
                    'FIRST': item.First,
                    'FIRST_POS': pt_pos_str[item.FirstPos],
                    'SECOND': item.Second,
                    'SECOND_POS': pt_pos_str[item.SecondPos],
                    'VALUE': item.Value,
                    'FMT': "{0}.{1} : {2}.{3}  v: {6:.2f}"
                }
                con = self.Constraint(i, ct.value, **kwargs)
                self.__constraints.append(con)

            elif ct == ConType.ANGLE:
                # ConstraintType, GeoIndex, Value
                # ConstraintType, GeoIndex1, GeoIndex2, Value
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2, Value
                kwargs = {
                    'FIRST': item.First,
                    'FIRST_POS': pt_pos_str[item.FirstPos],
                    'SECOND': item.Second,
                    'SECOND_POS': pt_pos_str[item.SecondPos],
                    'VALUE': math.degrees(item.Value),
                    'FMT': "{0}.{1} : {2}.{3}  v: {6:.2f}"
                }
                con = self.Constraint(i, ct.value, **kwargs)
                self.__constraints.append(con)

            elif ct == ConType.RADIUS or ct == ConType.DIAMETER or ct == ConType.WEIGHT:
                # ConstraintType, GeoIndex, Value
                kwargs = {
                    'FIRST': item.First,
                    'VALUE': item.Value,
                    'FMT': "{0}  v: {6:.2f}"
                }
                con = self.Constraint(i, ct.value, **kwargs)
                self.__constraints.append(con)

            elif ct == ConType.POINTONOBJECT:
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2
                kwargs = {
                    'FIRST': item.First,
                    'FIRST_POS': pt_pos_str[item.FirstPos],
                    'SECOND': item.Second,
                    'FMT': "{0}.{1} : {2}"
                }
                con = self.Constraint(i, ct.value, **kwargs)
                self.__constraints.append(con)

            elif ct == ConType.SYMMETRIC:
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2, GeoIndex3
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2, GeoIndex3, PosIndex3
                kwargs = {
                    'FIRST': item.First,
                    'FIRST_POS': pt_pos_str[item.FirstPos],
                    'SECOND': item.Second,
                    'SECOND_POS': pt_pos_str[item.SecondPos],
                    'THIRD': item.Third,
                    'THIRD_POS': pt_pos_str[item.ThirdPos],
                    'FMT': "{0}.{1} : {2}.{3} : {4}.{5}"
                }
                con = self.Constraint(i, ct.value, **kwargs)
                self.__constraints.append(con)

            elif ct == ConType.INTERNALALIGNMENT:
                # ConstraintType, GeoIndex1, GeoIndex2
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2
                kwargs = {
                    'FIRST': item.First,
                    'FIRST_POS': pt_pos_str[item.FirstPos],
                    'SECOND': item.Second,
                    'SECOND_POS': pt_pos_str[item.SecondPos],
                    'FMT': "{0}.{1} : {2}.{3}"
                }
                con = self.Constraint(i, ct.value, **kwargs)
                self.__constraints.append(con)

            elif ct == ConType.SNELLSLAW:
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2, GeoIndex3, PosIndex3
                kwargs = {
                    'FIRST': item.First,
                    'FIRST_POS': pt_pos_str[item.FirstPos],
                    'SECOND': item.Second,
                    'SECOND_POS': pt_pos_str[item.SecondPos],
                    'THIRD': item.Third,
                    'THIRD_POS': pt_pos_str[item.ThirdPos],
                    'FMT': "{0}.{1} : {2}.{3} : {4}.{5}"
                }
                con = self.Constraint(i, ct.value, **kwargs)
                self.__constraints.append(con)

            elif ct == ConType.BLOCK:
                # ConstraintType, GeoIndex
                kwargs = {
                    'FIRST': item.First,
                    'FMT': "{0}"
                }
                con = self.Constraint(i, ct.value, **kwargs)
                self.__constraints.append(con)

    @flow
    def constraints_delete(self, idx_list: List[int]):
        del_list: [int] = idx_list
        del_list.sort(reverse=True)
        for i in del_list:
            # xp('del: ' + str(i))
            self.sketch.delConstraint(i)
            self.__constraints_dirty = True

    #############
    # dbg info
    @flow
    def print_edge_angel_list(self):
        obj: List[FixIt.HvEdge] = self.hv_edges_get_list()
        for edge in obj:
            s = "Id {} x {:.2f}, y {:.2f} : x {:.2f}, y {:.2f} : xa {:.2f} : ya {:.2f}"
            s = s.format(edge.geo_idx, edge.pt_start.x, edge.pt_start.y, edge.pt_end.x, edge.pt_end.y,
                         edge.x_angel, edge.y_angel)
            xp(s, **_prn_edge.k(4))

    @flow
    def print_coincident_list(self):
        obj = self.points_get_list()
        for i in range(len(obj)):
            xp(str(obj[i].geo_item_pt) + " : " + str(obj[i].coin_pts))

    @flow
    def print_build_co_pts(self):
        for s in self.__dbg_co_pts_list:
            xp(s)

    @flow
    def print_geo(self):
        for idx, item in enumerate(self.sketch.Geometry):
            xp('-- Geo Idx {} ---- {} ---------------------------------------'.format(idx, item.TypeId), **_geo.k())
            if item.TypeId == 'Part::GeomCircle':
                circle: Part.Circle = item
                xp(circle.Content, **_geo.k())
            elif item.TypeId == 'Part::GeomLineSegment':
                line: Part.LineSegment = item
                xp(line.Content, **_geo.k())
            else:
                xp(item, **_geo.k())

    def geo_get(self) -> str:
        # for xml display in ui
        s: List[str] = list()
        for idx, item in enumerate(self.sketch.Geometry):
            s.append('<!-- Geo Idx {} ---- {} ------------------------------------>\n'.format(idx, item.TypeId))
            if item.TypeId == 'Part::GeomCircle':
                circle: Part.Circle = item
                s.append(circle.Content)
            elif item.TypeId == 'Part::GeomLineSegment':
                line: Part.LineSegment = item
                s.append(line.Content)
            else:
                s.append(item)
        return ''.join(s)

    @flow
    def print_constraints(self):
        obj = self.constraints_get_list()
        # noinspection PyUnresolvedReferences
        xp(self.sketch.Constraints)
        xp(', '.join(str(x) for x in obj))
        # noinspection PyUnresolvedReferences
        for item in self.sketch.Constraints:
            xp(item.Content)
