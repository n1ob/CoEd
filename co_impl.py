import math
import time
from enum import Flag, auto
from math import *
from typing import List, NamedTuple, Set

import Part
import Sketcher
from FreeCAD import Base
import FreeCADGui as Gui
import FreeCAD as App

from co_flag import Event, Dirty, Flags
from co_logger import xp, _co, _prn_edge, _co_co, _co_build, _hv, _xy, _cir, _geo, flow, _cs, xps
from co_lookup import Lookup
from co_cmn import pt_typ_str, pt_typ_int, ConType, GeoPt, ConsCoin, SketcherType, GeoPtn, fmt_vec


class CoEd:
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
        def __init__(self, geo_item_pt: Base.Vector, geo_list_idx: int, pt_type: str):
            self.geo_item_pt: Base.Vector = geo_item_pt
            self.coin_pts: List[GeoPt] = list()
            self.extend(geo_list_idx, pt_type)

        def __str__(self):
            s = "GeoId {}.{}, Start {:.2f}, End {:.2f}, CPts {}"
            return s.format(self.coin_pts[0].geo_id, self.coin_pts[0].type_id, self.geo_item_pt.x,
                            self.geo_item_pt.y, self.coin_pts)

        def extend(self, geo_list_idx: int, pt_type: str):
            item = GeoPt(geo_list_idx, pt_type)
            self.coin_pts.append(item)

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
            self.first: int = kwargs.get('FIRST', -2000)
            self.first_pos: str = kwargs.get('FIRST_POS', 0)
            self.second: int = kwargs.get('SECOND', -2000)
            self.second_pos: str = kwargs.get('SECOND_POS', 0)
            self.third: int = kwargs.get('THIRD', -2000)
            self.third_pos: str = kwargs.get('THIRD_POS', 0)
            self.value: float = kwargs.get('VALUE', -0)
            self.fmt = kwargs.get('FMT', "{0} : {1} : {2} : {3} : {4} : {5} : {6} : {7}")

        def __str__(self):
            return self.fmt.format(self.first + 1, self.first_pos,  # (0),(1)
                                   self.second + 1, self.second_pos,  # (2),(3)
                                   self.third + 1, self.third_pos,  # (4),(5)
                                   self.value, self.co_idx)  # (6),(7)

    # x_axis: Base.Vector = Base.Vector(1, 0, 0)
    # y_axis: Base.Vector = Base.Vector(0, 1, 0)

    class Dirty(Flag):
        hv_edges: auto()
        xy_edges: auto()
        coin_points: auto()
        constraints: auto()
        rad_circle: auto()

    @flow
    def __init__(self, sk: SketcherType, snap_dist: float = 0, snap_angel: float = 0, parent=None):
        super().__init__()
        self.__init = False
        self.__flags: Flags = Flags(Dirty)
        self.__flags.all()
        self.sketch: SketcherType = sk
        self.snap_dist: float = snap_dist
        self.snap_angel: float = snap_angel
        self.radius: float = 5
        self.__hv_edges: List[CoEd.HvEdge] = list()
        self.__xy_edges: List[CoEd.XyEdge] = list()
        self.__coin_points: List[CoEd.Point] = list()
        self.__constraints: List[CoEd.Constraint] = list()
        self.__dbg_co_pts_list: List[str] = list()
        self.ev = Event()
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
        self.__flags.set(Dirty.COIN_POINTS)

    @property
    def snap_angel(self) -> float:
        return self.__snap_angel

    @snap_angel.setter
    def snap_angel(self, value: float):
        self.__snap_angel: float = value
        self.__flags.set(Dirty.HV_EDGES)

    @property
    def sketch(self) -> SketcherType:
        return self.__sketch

    @sketch.setter
    def sketch(self, value: SketcherType):
        self.__sketch: SketcherType = value
        self.__flags.all()

    @flow
    def circle_get_list(self) -> List[Circle]:
        return self.rad_circle_detect()

    @flow
    def points_get_list(self) -> List[Point]:
        if self.__flags.has(Dirty.COIN_POINTS):
            self.coin_detect_missing()
        return self.__coin_points

    @flow
    def constraints_get_list(self) -> List[Constraint]:
        if self.__flags.has(Dirty.CONSTRAINTS):
            self.constraints_detect()
        return self.__constraints

    @flow
    def hv_edges_get_list(self) -> List[HvEdge]:
        if self.__flags.has(Dirty.HV_EDGES):
            self.hv_detect_missing()
        return self.__hv_edges

    # -------------
    # diameters

    @flow
    def rad_circle_detect(self) -> List[Circle]:
        geo_list = self.sketch.Geometry
        c_list: List[CoEd.Circle] = [CoEd.Circle(idx, x.Center.x, x.Center.y, x.AngleXU, x.Radius)
                                     for idx, x in enumerate(geo_list)
                                     if x.TypeId == 'Part::GeomCircle']
        xp(c_list, **_cir)
        return c_list

    @flow
    def rad_dia_create(self, geo_id_list: List[int], radius: float):
        if len(geo_id_list):
            geo_list: list = self.sketch.Geometry
            for idx in geo_id_list:
                if radius is not None:
                    self.sketch.addConstraint(Sketcher.Constraint('Diameter', idx, radius * 2))
                else:
                    cir: Part.Circle = geo_list[idx]
                    self.sketch.addConstraint(Sketcher.Constraint('Diameter', idx, cir.Radius * 2))
            self.__flags.set(Dirty.CONSTRAINTS)
            self.sketch.Document.recompute()

    # -------------
    # X / Y
    @flow
    def xy_edg_get_list(self):
        if self.__flags.has(Dirty.XY_EDGES):
            self.xy_detect_missing()
        return self.__xy_edges

    @flow
    def xy_cons_get(self) -> (List[int], List[int]):
        co_list: List[CoEd.Constraint] = self.constraints_get_list()
        exist_x: List[(int, int)] = [(x.first, x.second)
                                     for x in co_list
                                     if x.type_id == 'DistanceX']
        exist_y: List[(int, int)] = [(x.first, x.second)
                                     for x in co_list
                                     if x.type_id == 'DistanceY']
        xp('exist xy cons GeoId: X', ' '.join(map(str, exist_x)), ' Y', ' '.join(map(str, exist_y)), **_xy)
        return exist_x, exist_y

    @flow
    def xy_detect_missing(self):
        self.__xy_edges.clear()
        co_list: List[CoEd.Constraint] = self.constraints_get_list()
        exist_x, exist_y = self.xy_cons_get()
        geo_list = self.sketch.Geometry
        for idx, geo_item in enumerate(geo_list):
            if geo_item.TypeId == 'Part::GeomLineSegment':
                seg: Part.LineSegment = geo_item
                ed: CoEd.XyEdge = CoEd.XyEdge(idx, Base.Vector(seg.StartPoint), Base.Vector(seg.EndPoint),
                                              ((idx, idx) in exist_x), ((idx, idx) in exist_y))
                self.__xy_edges.append(ed)
        [xp(xy_edge, **_xy) for xy_edge in self.__xy_edges]
        self.__flags.reset(Dirty.XY_EDGES)

    @flow
    def xy_dist_create(self, geo_id_list: List[int]):
        # todo missing impl, on edges not on points
        if len(geo_id_list):
            obj = self.points_get_list()
            for pt in obj:
                self.sketch.addConstraint(Sketcher.Constraint(
                    'DistanceX', pt.coin_pts[0].geo_id, pt_typ_int[pt.coin_pts[0].type_id], pt.geo_item_pt.x))
                self.sketch.addConstraint(Sketcher.Constraint(
                    'DistanceY', pt.coin_pts[0].geo_id, pt_typ_int[pt.coin_pts[0].type_id], pt.geo_item_pt.y))
            self.__flags.set(Dirty.CONSTRAINTS)
            self.sketch.Document.recompute()

    # ---------------------
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
    def hv_cons_get(self) -> (List[int], List[int]):
        co_list: List[CoEd.Constraint] = self.constraints_get_list()
        exist_h: List[(int, int)] = [(x.first, x.second)
                                     for x in co_list
                                     if x.type_id == 'Horizontal']
        exist_v: List[(int, int)] = [(x.first, x.second)
                                     for x in co_list
                                     if x.type_id == 'Vertical']
        # existing: List[int] = [x.first for x in co_list if (x.type_id == 'Horizontal') or (x.type_id == 'Vertical')]
        xp('exist v/h cons GeoId:', ' '.join(map(str, exist_v)), ' '.join(map(str, exist_h)), **_hv)
        return exist_v, exist_h

    @flow
    def hv_detect_missing(self) -> None:
        # * only on edges, not between edges
        # todo ident existing constraints
        self.__hv_edges.clear()
        exist_v, exist_h = self.hv_cons_get()
        existing = exist_v + exist_h
        geo_list = self.sketch.Geometry
        for idx, geo_item in enumerate(geo_list):
            if geo_item.TypeId == 'Part::GeomLineSegment':
                seg: Part.LineSegment = geo_item
                a: float = self.__alpha(Base.Vector(seg.StartPoint), Base.Vector(seg.EndPoint))
                if (a < self.snap_angel) or ((90 - a) < self.snap_angel):
                    self.__hv_edges.append(CoEd.HvEdge(idx, seg, 90 - a, a, (idx in existing)))
        self.__flags.reset(Dirty.HV_EDGES)
        self.print_edge_angel_list()

    @flow
    def hv_create(self, edge_id_list: List[int]):
        for idx in edge_id_list:
            edge: CoEd.HvEdge = self.__hv_edges[idx]
            if edge.x_angel <= self.snap_angel:
                con = Sketcher.Constraint('Horizontal', edge.geo_idx)
                self.sketch.addConstraint(con)
                continue
            if edge.y_angel <= self.snap_angel:
                con = Sketcher.Constraint('Vertical', edge.geo_idx)
                self.sketch.addConstraint(con)
        self.__flags.set(Dirty.HV_EDGES)
        self.__flags.set(Dirty.CONSTRAINTS)
        self.sketch.Document.recompute()

    # -----------------
    # Coincident
    def __coin_add_point(self, geo_item_pt: Base.Vector, geo_list_idx: int, pt_type: str, tolerance: float,
                         cs: Set[ConsCoin]):
        xp("({:.2f}, {:.2f}) : Id {:n} : Type {}".format(geo_item_pt.x, geo_item_pt.y, geo_list_idx, pt_type),
           **_co_build)
        new_pt = CoEd.Point(geo_item_pt, geo_list_idx, pt_type)
        for i, pt in enumerate(self.__coin_points):
            xp("Id: {:n} Dist {:.4f}".format(i, pt.geo_item_pt.distanceToPoint(new_pt.geo_item_pt)), **_co_build)
            if self.__coin_consider(pt, new_pt, cs):
                if pt.geo_item_pt.isEqual(new_pt.geo_item_pt, tolerance):
                    xp('snap', **_co_build)
                    pt.extend(geo_list_idx, pt_type)
                    return
        self.__coin_points.append(new_pt)

    def __coin_consider(self, pt: Point, new_pt: Point, cs: Set[ConsCoin]) -> bool:
        pn: GeoPt = GeoPt(new_pt.coin_pts[0].geo_id, new_pt.coin_pts[0].type_id)
        pts: Set[GeoPt] = set(map(lambda x: GeoPt(x.geo_id, x.type_id), pt.coin_pts))
        xp('CS :', str(cs), 'PN :', str(pn), 'PTS: ' + str(pts), **_co_co)
        if any(a.geo_id == pn.geo_id for a in pts):
            xp('any(a[0] == pn[0] for a in pts)', **_co_co)
            return False
        if any(((a, pn) in cs) for a in pts):
            xp('any(((a, pn) in cs) for a in pts)', **_co_co)
            return False
        if any(((pn, a) in cs) for a in pts):
            xp('any(((pn, a) in cs) for a in pts)', **_co_co)
            return False
        return True

    @flow
    def coin_detect_missing(self) -> None:
        self.__coin_points.clear()
        cs: Set[ConsCoin] = self.coin_cons_get()
        geo_list = self.sketch.Geometry
        for i in range(len(geo_list)):
            xp("Sketch.Geometry: {:n}".format(i), **_co_build)
            if geo_list[i].TypeId == 'Part::GeomLineSegment':
                start: Base.Vector = geo_list[i].StartPoint
                end: Base.Vector = geo_list[i].EndPoint
                self.__coin_add_point(start, i, pt_typ_str[1], self.snap_dist, cs)
                self.__coin_add_point(end, i, pt_typ_str[2], self.snap_dist, cs)
        self.__flags.reset(Dirty.COIN_POINTS)

    @flow
    def coin_cons_get(self) -> Set[ConsCoin]:
        co_list: List[CoEd.Constraint] = self.constraints_get_list()
        col: Set[ConsCoin] = {ConsCoin(GeoPt(x.first, x.first_pos), GeoPt(x.second, x.second_pos))
                              for x in co_list
                              if ConType(x.type_id) == ConType.COINCIDENT}
        return col

    @flow
    def coin_create(self, pt_idx_list: List[int]):
        xp('pt_idx_list', pt_idx_list, **_co)
        if pt_idx_list is None:
            return
        for idx in pt_idx_list:
            pt: CoEd.Point = self.__coin_points[idx]
            xp('pt', pt.coin_pts, **_co)
            if len(pt.coin_pts) == 1:
                continue
            if len(pt.coin_pts) > 1:
                # only create a connect chain
                for i in range(len(pt.coin_pts) - 1):
                    p1 = pt.coin_pts[i - 1]
                    p2 = pt.coin_pts[i]
                    fmt = 'Coincident', p1.geo_id, p1.type_id, p2.geo_id, p2.type_id
                    xp(fmt, **_co)
                    con = Sketcher.Constraint('Coincident', p1.geo_id, pt_typ_int[p1.type_id], p2.geo_id,
                                              pt_typ_int[p2.type_id])
                    self.sketch.addConstraint(con)
                self.__flags.all()
                self.ev.coin_pts_chg.emit('coin_create finish')
                self.sketch.Document.recompute()

    # ---------------
    # Constraint
    # @flow(off=True)
    def constraints_detect(self):
        self.__constraints.clear()
        # noinspection PyUnresolvedReferences
        co_list: list = self.sketch.Constraints
        xp('co_lst', _cs, **_cs)
        xp('co_lst', co_list, **_cs)
        for i in range(len(co_list)):
            item: Sketcher.Constraint = co_list[i]
            ct: ConType = ConType(item.Type)
            if ct == ConType.COINCIDENT:
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2
                if item.Third == -2000:
                    kwargs = self.__get_kwargs(['f', 'fp', 's', 'sp'], item, "({0}.{1}) ({2}.{3})")
                    # kwargs = {
                    #     'FIRST': item.First,
                    #     'FIRST_POS': pt_typ_str[item.FirstPos],
                    #     'SECOND': item.Second,
                    #     'SECOND_POS': pt_typ_str[item.SecondPos],
                    #     'FMT': "({0}.{1}) ({2}.{3})"
                    # }
                else:
                    xp('unexpected case')
                    raise ValueError(item)

                con = self.Constraint(i, ct.value, **kwargs)
                self.__constraints.append(con)

            elif ct == ConType.HORIZONTAL or ct == ConType.VERTICAL:
                # ConstraintType, GeoIndex
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2
                if item.Second == -2000:
                    kwargs = self.__get_kwargs(['f'], item, "({0})")
                    # kwargs = {
                    #     'FIRST': item.First,
                    #     'FMT': "({0})"
                    # }
                elif item.Third == -2000:
                    kwargs = self.__get_kwargs(['f', 'fp', 's', 'sp'], item, "({0}.{1}) ({2}.{3})")
                    # kwargs = {
                    #     'FIRST': item.First,
                    #     'FIRST_POS': pt_typ_str[item.FirstPos],
                    #     'SECOND': item.Second,
                    #     'SECOND_POS': pt_typ_str[item.SecondPos],
                    #     'FMT': "({0}.{1}) ({2}.{3})"
                    # }
                else:
                    xp('unexpected case')
                    raise ValueError(item)

                con = self.Constraint(i, ct.value, **kwargs)
                self.__constraints.append(con)

            elif ct == ConType.PARALLEL or ct == ConType.EQUAL:
                # ConstraintType, GeoIndex1, GeoIndex2
                if item.Third == -2000:
                    kwargs = self.__get_kwargs(['f', 's'], item, "({0}) ({2})")
                    # kwargs = {
                    #     'FIRST': item.First,
                    #     'SECOND': item.Second,
                    #     'FMT': "({0}) ({2})"
                    # }
                else:
                    xp('unexpected case')
                    raise ValueError(item)

                con = self.Constraint(i, ct.value, **kwargs)
                self.__constraints.append(con)

            elif ct == ConType.TANGENT or ct == ConType.PERPENDICULAR:
                # ConstraintType, GeoIndex1, GeoIndex2
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2
                if item.FirstPos == 0:  # e.g. edge on edge
                    kwargs = self.__get_kwargs(['f', 's'], item, "({0}) ({2})")
                    # kwargs = {
                    #     'FIRST': item.First,
                    #     'SECOND': item.Second,
                    #     'FMT': "({0}) ({2})"
                    # }
                elif item.SecondPos == 0:  # e.g. vertex on edge
                    kwargs = self.__get_kwargs(['f', 'fp', 's'], item, "({0}.{1}) ({2})")
                    # kwargs = {
                    #     'FIRST': item.First,
                    #     'FIRST_POS': pt_typ_str[item.FirstPos],
                    #     'SECOND': item.Second,
                    #     'FMT': "({0}.{1}) ({2})"
                    # }
                elif item.Third == -2000:  # e.g. vertex on vertex
                    kwargs = self.__get_kwargs(['f', 'fp', 's', 'sp'], item, "({0}.{1}) ({2}.{3})")
                    # kwargs = {
                    #     'FIRST': item.First,
                    #     'FIRST_POS': pt_typ_str[item.FirstPos],
                    #     'SECOND': item.Second,
                    #     'SECOND_POS': pt_typ_str[item.SecondPos],
                    #     'FMT': "({0}.{1}) ({2}.{3})"
                    # }
                else:
                    xp('unexpected case')
                    raise ValueError(item)

                con = self.Constraint(i, ct.value, **kwargs)
                self.__constraints.append(con)

            elif ct == ConType.DISTANCE:
                # ConstraintType, GeoIndex, Value
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, Value
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2, Value
                if item.FirstPos == 0:
                    kwargs = self.__get_kwargs(['f', 'v'], item, "({0}) v: {6:.2f}")
                    # kwargs = {
                    #     'FIRST': item.First,
                    #     'VALUE': item.Value,
                    #     'FMT': "({0}) v: {6:.2f}"
                    # }
                elif item.SecondPos == 0:
                    kwargs = self.__get_kwargs(['f', 'fp', 's', 'v'], item, "({0}.{1}) ({2}) v: {6:.2f}")
                    # kwargs = {
                    #     'FIRST': item.First,
                    #     'FIRST_POS': pt_typ_str[item.FirstPos],
                    #     'SECOND': item.Second,
                    #     'VALUE': item.Value,
                    #     'FMT': "({0}.{1}) ({2})  v: {6:.2f}"
                    # }
                elif item.Third == -2000:
                    kwargs = self.__get_kwargs(['f', 'fp', 's', 'sp', 'v'], item, "({0}.{1}) ({2}.{3}) v: {6:.2f}")
                    # kwargs = {
                    #     'FIRST': item.First,
                    #     'FIRST_POS': pt_typ_str[item.FirstPos],
                    #     'SECOND': item.Second,
                    #     'SECOND_POS': pt_typ_str[item.SecondPos],
                    #     'VALUE': item.Value,
                    #     'FMT': "({0}.{1}) ({2}.{3}) v: {6:.2f}"
                    # }
                else:
                    xp('unexpected case')
                    raise ValueError(item)

                con = self.Constraint(i, ct.value, **kwargs)
                self.__constraints.append(con)

            elif ct == ConType.DISTANCEX or ct == ConType.DISTANCEY:
                # ConstraintType, GeoIndex, Value
                # ConstraintType, GeoIndex, PosIndex, Value
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2, Value
                if item.FirstPos == 0:
                    kwargs = self.__get_kwargs(['f', 'v'], item, "({0}) v: {6:.2f}")
                    # kwargs = {
                    #     'FIRST': item.First,
                    #     'VALUE': item.Value,
                    #     'FMT': "({0}) v: {6:.2f}"
                    # }
                elif item.Second == -2000:
                    kwargs = self.__get_kwargs(['f', 'fp', 'v'], item, "({0}.{1}) v: {6:.2f}")
                    # kwargs = {
                    #     'FIRST': item.First,
                    #     'FIRST_POS': pt_typ_str[item.FirstPos],
                    #     'VALUE': item.Value,
                    #     'FMT': "({0}.{1}) v: {6:.2f}"
                    # }
                elif item.Third == -2000:
                    kwargs = self.__get_kwargs(['f', 'fp', 's', 'sp', 'v'], item, "({0}.{1}) ({2}.{3}) v: {6:.2f}")
                    # kwargs = {
                    #     'FIRST': item.First,
                    #     'FIRST_POS': pt_typ_str[item.FirstPos],
                    #     'SECOND': item.Second,
                    #     'SECOND_POS': pt_typ_str[item.SecondPos],
                    #     'VALUE': item.Value,
                    #     'FMT': "({0}.{1}) ({2}.{3})  v: {6:.2f}"
                    # }
                else:
                    xp('unexpected case')
                    raise ValueError(item)

                con = self.Constraint(i, ct.value, **kwargs)
                self.__constraints.append(con)

            elif ct == ConType.ANGLE:
                # ConstraintType, GeoIndex, Value
                # ConstraintType, GeoIndex1, GeoIndex2, Value
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2, Value
                if item.FirstPos == 0:
                    kwargs = self.__get_kwargs(['f', 'v'], item, "({0}) v: {6:.2f}")
                    # kwargs = {
                    #     'FIRST': item.First,
                    #     'VALUE': item.Value,
                    #     'FMT': "({0}) v: {6:.2f}"
                    # }
                elif item.SecondPos == 0:
                    kwargs = self.__get_kwargs(['f', 's', 'v'], item, "({0}) ({2}) v: {6:.2f}")
                    # kwargs = {
                    #     'FIRST': item.First,
                    #     'SECOND': item.Second,
                    #     'VALUE': item.Value,
                    #     'FMT': "({0}) ({2}) v: {6:.2f}"
                    # }
                elif item.Third == -2000:
                    kwargs = self.__get_kwargs(['f', 'fp', 's', 'sp', 'v'], item, "({0}.{1}) ({2}.{3}) v: {6:.2f}")
                    # kwargs = {
                    #     'FIRST': item.First,
                    #     'FIRST_POS': pt_typ_str[item.FirstPos],
                    #     'SECOND': item.Second,
                    #     'SECOND_POS': pt_typ_str[item.SecondPos],
                    #     'VALUE': item.Value,
                    #     'FMT': "({0}.{1}) ({2}.{3})  v: {6:.2f}"
                    # }
                else:
                    xp('unexpected case')
                    raise ValueError(item)

                con = self.Constraint(i, ct.value, **kwargs)
                self.__constraints.append(con)

            elif ct == ConType.RADIUS or ct == ConType.DIAMETER or ct == ConType.WEIGHT:
                # ConstraintType, GeoIndex, Value
                if item.FirstPos == 0:
                    kwargs = self.__get_kwargs(['f', 'v'], item, "({0}) v: {6:.2f}")
                    # kwargs = {
                    #     'FIRST': item.First,
                    #     'VALUE': item.Value,
                    #     'FMT': "({0})  v: {6:.2f}"
                    # }
                else:
                    xp('unexpected case')
                    raise ValueError(item)

                con = self.Constraint(i, ct.value, **kwargs)
                self.__constraints.append(con)

            elif ct == ConType.POINTONOBJECT:
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2
                if item.SecondPos == 0:
                    kwargs = self.__get_kwargs(['f', 'fp', 's'], item, "({0}.{1}) ({2})")
                    # kwargs = {
                    #     'FIRST': item.First,
                    #     'FIRST_POS': pt_typ_str[item.FirstPos],
                    #     'SECOND': item.Second,
                    #     'FMT': "({0}.{1}) ({2})"
                    # }
                else:
                    xp('unexpected case')
                    raise ValueError(item)

                con = self.Constraint(i, ct.value, **kwargs)
                self.__constraints.append(con)

            elif ct == ConType.SYMMETRIC:
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2, GeoIndex3
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2, GeoIndex3, PosIndex3
                if item.ThirdPos == 0:
                    kwargs = self.__get_kwargs(['f', 'fp', 's', 'sp', 't'], item, "({0}.{1}) ({2}.{3}) ({4})")
                    # kwargs = {
                    #     'FIRST': item.First,
                    #     'FIRST_POS': pt_typ_str[item.FirstPos],
                    #     'SECOND': item.Second,
                    #     'SECOND_POS': pt_typ_str[item.SecondPos],
                    #     'THIRD': item.Third,
                    #     'FMT': "({0}.{1}) ({2}.{3}) ({4})"
                    # }
                else:
                    kwargs = self.__get_kwargs(['f', 'fp', 's', 'sp', 't', 'tp'], item, "({0}.{1}) ({2}.{3}) ({4}.{5})")
                    # kwargs = {
                    #     'FIRST': item.First,
                    #     'FIRST_POS': pt_typ_str[item.FirstPos],
                    #     'SECOND': item.Second,
                    #     'SECOND_POS': pt_typ_str[item.SecondPos],
                    #     'THIRD': item.Third,
                    #     'THIRD_POS': pt_typ_str[item.ThirdPos],
                    #     'FMT': "({0}.{1}) ({2}.{3}) ({4}.{5})"
                    # }
                con = self.Constraint(i, ct.value, **kwargs)
                self.__constraints.append(con)

            elif ct == ConType.INTERNALALIGNMENT:
                # ConstraintType, GeoIndex1, GeoIndex2
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2
                if item.FirstPos == 0:
                    kwargs = self.__get_kwargs(['f', 's'], item, "({0}) ({2})")
                    # kwargs = {
                    #     'FIRST': item.First,
                    #     'SECOND': item.Second,
                    #     'FMT': "({0}) ({2})"
                    # }
                elif item.SecondPos == 0:
                    kwargs = self.__get_kwargs(['f', 'fp', 's'], item, "({0}.{1}) ({2})")
                    # kwargs = {
                    #     'FIRST': item.First,
                    #     'FIRST_POS': pt_typ_str[item.FirstPos],
                    #     'SECOND': item.Second,
                    #     'FMT': "({0}.{1}) ({2})"
                    # }
                elif item.Third == -2000:
                    kwargs = self.__get_kwargs(['f', 'fp', 's', 'sp'], item, "({0}.{1}) ({2}.{3})")
                    # kwargs = {
                    #     'FIRST': item.First,
                    #     'FIRST_POS': pt_typ_str[item.FirstPos],
                    #     'SECOND': item.Second,
                    #     'SECOND_POS': pt_typ_str[item.SecondPos],
                    #     'FMT': "({0}.{1}) ({2}.{3})"
                    # }
                else:
                    xp('unexpected case')
                    raise ValueError(item)

                con = self.Constraint(i, ct.value, **kwargs)
                self.__constraints.append(con)

            elif ct == ConType.SNELLSLAW:
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2, GeoIndex3, PosIndex3
                kwargs = self.__get_kwargs(['f', 'fp', 's', 'sp', 't', 'tp'], item, "({0}.{1}) ({2}.{3}) ({4}.{5})")
                # kwargs = {
                #     'FIRST': item.First,
                #     'FIRST_POS': pt_typ_str[item.FirstPos],
                #     'SECOND': item.Second,
                #     'SECOND_POS': pt_typ_str[item.SecondPos],
                #     'THIRD': item.Third,
                #     'THIRD_POS': pt_typ_str[item.ThirdPos],
                #     'FMT': "({0}.{1}) ({2}.{3}) ({4}.{5})"
                # }
                con = self.Constraint(i, ct.value, **kwargs)
                self.__constraints.append(con)

            elif ct == ConType.BLOCK:
                # ConstraintType, GeoIndex
                kwargs = self.__get_kwargs(['f'], item, "({0})")
                # kwargs = {
                #     'FIRST': item.First,
                #     'FMT': "({0})"
                # }
                con = self.Constraint(i, ct.value, **kwargs)
                self.__constraints.append(con)
        self.__flags.reset(Dirty.CONSTRAINTS)
        self.ev.cons_chg.emit('cons detect finish')


    @staticmethod
    def __get_kwargs(cont: List, item: Sketcher.Constraint, fmt: str) -> dict:
        d: dict = dict()
        for x in cont:
            if x == 'f':
                d['FIRST'] = item.First
            if x == 'fp':
                d['FIRST_POS'] = pt_typ_str[item.FirstPos]
            if x == 's':
                d['SECOND'] = item.Second
            if x == 'sp':
                d['SECOND_POS'] = pt_typ_str[item.SecondPos]
            if x == 't':
                d['THIRD'] = item.Third
            if x == 'tp':
                d['THIRD_POS'] = pt_typ_str[item.ThirdPos]
            if x == 'v':
                d['VALUE'] = item.Value
        d['FMT'] = fmt
        return d

    @flow
    def constraints_delete(self, idx_list: List[int]):
        if len(idx_list):
            del_list: [int] = idx_list
            del_list.sort(reverse=True)
            for i in del_list:
                xp('del: ' + str(i), **_cs)
                self.sketch.delConstraint(i)
            self.__flags.set(Dirty.CONSTRAINTS)
            self.sketch.Document.recompute()

    # -------------
    # info & dbg
    @flow
    def geo_xml_get(self) -> str:
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
            elif item.TypeId == 'Part::GeomPoint':
                pt: Part.Point = item
                s.append(pt.Content)
            else:
                xp('geo_xml_get unexpected', item.TypeId)
                s.append(str(item))
        return ''.join(s)

    @flow
    def analyse_sketch(self):
        # xps()
        # for obj in Gui.ActiveDocument.Document.Objects:
        #     if obj.TypeId == 'Sketcher::SketchObject':  # remove this line to see expressions for all objects
        #         xp(str(obj.Label) + " : " + str(obj.ExpressionEngine))

        # xps()
        # for obj in App.ActiveDocument.Objects:  # liste all object in document
        #     xp('addSelection', obj.Name)  # object before selection
        #     Gui.Selection.addSelection(obj)  # select the object
        #     Gui.updateGui()
        #     time.sleep(1)  # pause
        #     Gui.Selection.removeSelection(obj)  # remove the selection object

        for obj in App.ActiveDocument.Objects:
            xps('obj.TypeId:', obj.TypeId)
            if obj.TypeId == 'Sketcher::SketchObject':
                sk: Sketcher.Sketch = obj
                sko: Sketcher.SketchObject = obj
                xp('GeometryWithDependentParameters:', obj.getGeometryWithDependentParameters())
                xp('full_name:', sko.FullName)
                xps('Geometry')
                for idx, item in enumerate(sk.Geometry):
                    if item.TypeId == 'Part::GeomLineSegment':
                        line: Part.LineSegment = item
                        xp('idx:', idx, 'type_id:', item.TypeId, 'start_end:',
                           fmt_vec(App.Vector(line.StartPoint)), fmt_vec(App.Vector(line.EndPoint)))
                    else:
                        xp('idx:', idx, 'type_id:', item.TypeId, 'item:', item)
                xps('Constraints')
                lo = Lookup(sk)
                for idx, item in enumerate(sk.Constraints):
                    xp('idx:', idx, 'type_id:', item.TypeId, 'item:', item)
                    ct: ConType = ConType(item.Type)
                    if ct == ConType.COINCIDENT:
                        p1 = GeoPtn(item.First, item.FirstPos)
                        p2 = GeoPtn(item.Second, item.SecondPos)
                        xp(f"   ({p1}) ({p2})")
                        xp('  ', lo.lookup(p1, p2))
                    if ct == ConType.HORIZONTAL or ct == ConType.VERTICAL:
                        if item.Second == -2000:
                            geo_id = item.First
                            xp(f"   {ct.value} ({geo_id})")
                            xp('  ', lo.lookup(geo_id))
                        else:
                            p1 = GeoPtn(item.First, item.FirstPos)
                            p2 = GeoPtn(item.Second, item.SecondPos)
                            xp(f"   {ct.value} ({p1}), ({p2})")
                            xp('  ', lo.lookup(p1, p2))
                    if ct == ConType.PARALLEL or ct == ConType.EQUAL:
                        geo_id1 = item.First
                        geo_id2 = item.Second
                        xp(f"   {ct.value} ({geo_id1}) ({geo_id2})")
                        xp('  ', lo.lookup(geo_id1, geo_id2))
                    if ct == ConType.TANGENT or ct == ConType.PERPENDICULAR:
                        # ConstraintType, GeoIndex1, GeoIndex2
                        # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2
                        # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2
                        pass

                xps('OpenVertices')
                for idx, item in enumerate(sko.OpenVertices):
                    xp('idx:', idx, 'item:', fmt_vec(App.Vector(item)))
                xps('Shape.Edges')
                for idx, edg in enumerate(obj.Shape.Edges):
                    xp('idx', idx, 'shape_type:', edg.ShapeType)
                    if edg.ShapeType == 'Edge':
                        for idy, vert in enumerate(edg.SubShapes):
                            geo, pos = self.sketch.getGeoVertexIndex(idy)
                            xp(f'   idx: {idy} geo: ({geo},{pos}) shape: {vert.ShapeType} pt: {fmt_vec(vert.Point)}')
                    else:
                        xp('not an edge')
                xps('Shape.Vertexes')
                for idx, vert in enumerate(obj.Shape.Vertexes):
                    geo, pos = self.sketch.getGeoVertexIndex(idx)
                    xp(f'   idx: {idx} geo: ({geo},{pos}) shape: {vert.ShapeType} pt: {fmt_vec(vert.Point)}')

        xps()
    # Vertex.ShapeType, .Point, .TypeId, .x, .y, .z
    # Edge.TypeId, .Vertexes, .SubShapes, .ShapeType
    # Sketch.Geometry, .Constraints, .FullName, .Name, .OpenVertices, .Shape, .TypeId
    # Shape.dumpToString() -> bulky output
    # connectEdgesToWires(TopoShape)
    # def Closed(self) -> bool:
    #     """Returns true if the edge is closed"""
    # def Continuity(self) -> str:
    #     """Returns the continuity"""
    # def Degenerated(self) -> bool:
    #     """Returns true if the edge is degenerated"""



    @flow
    def print_edge_angel_list(self):
        obj: List[CoEd.HvEdge] = self.hv_edges_get_list()
        for edge in obj:
            s = "Id {} x {:.2f}, y {:.2f} : x {:.2f}, y {:.2f} : xa {:.2f} : ya {:.2f}"
            s = s.format(edge.geo_idx, edge.pt_start.x, edge.pt_start.y, edge.pt_end.x, edge.pt_end.y,
                         edge.x_angel, edge.y_angel)
            xp(s, **_prn_edge)

    @flow
    def print_coincident_list(self):
        obj = self.points_get_list()
        for i in range(len(obj)):
            xp(str(obj[i].geo_item_pt) + " : " + str(obj[i].coin_pts))
            geo_id, pos_id = self.sketch.getGeoVertexIndex(i)
            xp('i', i, 'geo id', geo_id, 'pos id', pos_id)
            # void getGeoVertexIndex(int VertexId, int & GeoId, PointPos & PosId)
            # retrieves for a Vertex number the corresponding GeoId and PosId

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
                xp(circle.Content, **_geo)
            elif item.TypeId == 'Part::GeomLineSegment':
                line: Part.LineSegment = item
                xp(line.Content, **_geo)
            else:
                xp(item, **_geo)

    @flow
    def print_constraints(self):
        obj = self.constraints_get_list()
        # noinspection PyUnresolvedReferences
        xp(self.sketch.Constraints)
        xp(', '.join(str(x) for x in obj))
        # noinspection PyUnresolvedReferences
        for item in self.sketch.Constraints:
            xp(item.Content)


xps(__name__)