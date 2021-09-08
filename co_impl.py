from enum import Flag, auto
from math import *
from typing import List, NamedTuple, Set
from xml.dom.minidom import Element, Document

import Part
import Sketcher
from FreeCAD import Base
import FreeCAD as App
from PySide2.QtCore import Slot

from co_flag import DataChgEvent, Dirty, Flags, Cs
from co_logger import xp, _co, _prn_edge, _co_co, _co_build, _hv, _xy, _cir, _geo, flow, _cs, xps, _ob_s
from co_lookup import Lookup
from co_cmn import pt_typ_str, pt_typ_int, ConType, GeoPt, ConsCoin, SketchType, GeoPtn, fmt_vec, ConsTrans
from co_observer import EventProvider


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

        def __repr__(self):
            return self.__str__()

    class Point:
        def __init__(self, geo_item_pt: Base.Vector, geo_list_idx: int, pt_type: str):
            self.geo_item_pt: Base.Vector = geo_item_pt
            self.coin_pts: List[GeoPt] = list()
            self.extend(geo_list_idx, pt_type)

        def __str__(self):
            s = "GeoId {}.{}, Start {:.2f}, End {:.2f}, CPts {}"
            return s.format(self.coin_pts[0].geo_id, self.coin_pts[0].type_id, self.geo_item_pt.x,
                            self.geo_item_pt.y, self.coin_pts)

        def __repr__(self):
            return self.__str__()

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

        def __repr__(self):
            return self.__str__()

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

        def __repr__(self):
            return self.__str__()

    class Constraint:
        def __init__(self, co_idx: int, type_id: str, **kwargs):
            self.co_idx: int = co_idx
            self.type_id: str = type_id
            self.sub_type: Cs = Cs(0)
            self.first: int = kwargs.get('FIRST', -2000)
            self.first_pos: str = kwargs.get('FIRST_POS', 0)
            self.second: int = kwargs.get('SECOND', -2000)
            self.second_pos: str = kwargs.get('SECOND_POS', 0)
            self.third: int = kwargs.get('THIRD', -2000)
            self.third_pos: str = kwargs.get('THIRD_POS', 0)
            self.value: float = kwargs.get('VALUE', -0)
            self.fmt = kwargs.get('FMT', "{0} : {1} : {2} : {3} : {4} : {5} : {6} : {7}")

        def __str__(self):
            return self.fmt.format(self.first, self.first_pos,  # (0),(1)
                                   self.second, self.second_pos,  # (2),(3)
                                   self.third, self.third_pos,  # (4),(5)
                                   self.value, self.co_idx)  # (6),(7)

        def __repr__(self):
            return self.__str__()

    # x_axis: Base.Vector = Base.Vector(1, 0, 0)
    # y_axis: Base.Vector = Base.Vector(0, 1, 0)

    @flow
    def __init__(self, sk: SketchType, snap_dist: float = 0, snap_angel: float = 0, parent=None):
        super().__init__()
        self.__init = False
        self.__flags: Flags = Flags(Dirty)
        self.__flags.all()
        self.sketch: SketchType = sk
        self.snap_dist: float = snap_dist
        self.snap_angel: float = snap_angel
        self.radius: float = 5
        self.__hv_edges: List[CoEd.HvEdge] = list()
        self.__xy_edges: List[CoEd.XyEdge] = list()
        self.__coin_points: List[CoEd.Point] = list()
        self.__constraints: List[CoEd.Constraint] = list()
        self.__dbg_co_pts_list: List[str] = list()
        self.ev = DataChgEvent()
        self.evo = EventProvider.ev
        self.evo.obj_recomputed.connect(self.on_obj_recomputed)
        self.evo.open_transact.connect(self.on_open_transact)
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
    def sketch(self) -> SketchType:
        return self.__sketch

    @sketch.setter
    def sketch(self, value: SketchType):
        self.__sketch: SketchType = value
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

    @flow
    @Slot(object)
    def on_obj_recomputed(self, obj):
        xp(f'on_obj_recomputed obj:', str(obj), **_ob_s)
        self.__flags.all()

    @flow
    @Slot(object, str)
    def on_open_transact(self, doc, name):
        xp(f'on_open_transact doc: {doc} name: {name}', **_ob_s)
        if 'coed' in name:
            xp('ignore own')
        else:
            self.__flags.all()

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
    def rad_dia_create(self, cir_list: List[Circle], radius: float):
        doc: App.Document = App.ActiveDocument
        if len(cir_list):
            geo_list: list = self.sketch.Geometry
            for cir in cir_list:
                cir: CoEd.Circle
                if radius is not None:
                    doc.openTransaction('coed: Diameter constraint')
                    self.sketch.addConstraint(Sketcher.Constraint('Diameter', cir.geo_id, radius * 2))
                    doc.commitTransaction()
                else:
                    p_cir: Part.Circle = geo_list[cir.geo_id]
                    doc.openTransaction('coed: Diameter constraint')
                    self.sketch.addConstraint(Sketcher.Constraint('Diameter', cir.geo_id, p_cir.Radius * 2))
                    doc.commitTransaction()
            self.__flags.set(Dirty.CONSTRAINTS)
            sk: Sketcher.SketchObject = self.sketch
            sk.addProperty('App::PropertyString', 'coed')
            sk.coed = 'rad_recompute'
            doc.openTransaction('coed: obj recompute')
            sk.recompute()
            # self.sketch.Document.recompute()
            doc.commitTransaction()
            self.ev.rad_chg.emit('rad create finish')

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

    '''
xy        | GeoId 2, Start (-8.00, -6.00), End (7.00, -9.00), csX False, csY False
    >>> # Gui.Selection.addSelection('Test','Sketch','Vertex5',-8,-6,0.012,False)
    >>> # Gui.Selection.addSelection('Test','Sketch','Vertex6',7,-9,0.012,False)
    >>> ### Begin command Sketcher_ConstrainLock
    >>> App.getDocument('Test').getObject('Sketch').addConstraint(Sketcher.Constraint('DistanceX',2,1,2,2,15.000000)) 
    >>> App.getDocument('Test').getObject('Sketch').addConstraint(Sketcher.Constraint('DistanceY',2,1,2,2,-3.000000)) 
    >>> ### End command Sketcher_ConstrainLock
    
    7 - (-8) 15
    -9 - (-6) -3
    '''

    @flow
    def xy_dist_create(self, geo_id_list: List[int], x: bool, y: bool):
        doc: App.Document = App.ActiveDocument
        xp('geo_list', geo_id_list, **_xy)
        for idx in geo_id_list:
            geo = self.sketch.Geometry[idx]
            if geo.TypeId == 'Part::GeomLineSegment':
                seg: Part.LineSegment = geo
                if x:
                    x1 = App.Vector(seg.StartPoint).x
                    x2 = App.Vector(seg.EndPoint).x
                    doc.openTransaction('coed: DistanceX constraint')
                    self.sketch.addConstraint(Sketcher.Constraint('DistanceX', idx, 1, idx, 2, (x2-x1)))
                    doc.commitTransaction()
                    xp(f'DistanceX, geo_start ({idx}.1) geo_end ({idx}.2), {(x2-x1)}', **_xy)
                if y:
                    y1 = App.Vector(seg.StartPoint).y
                    y2 = App.Vector(seg.EndPoint).y
                    doc.openTransaction('coed: DistanceY constraint')
                    self.sketch.addConstraint(Sketcher.Constraint('DistanceY', idx, 1, idx, 2, (y2-y1)))
                    doc.commitTransaction()
                    xp(f'DistanceY, geo_start ({idx}.1) geo_end ({idx}.2), {(y2-y1)}', **_xy)

        if len(geo_id_list) > 0:
            self.__flags.set(Dirty.CONSTRAINTS)
            self.__flags.set(Dirty.XY_EDGES)
            sk: Sketcher.SketchObject = self.sketch
            sk.addProperty('App::PropertyString', 'coed')
            sk.coed = 'xy_recompute'
            doc.openTransaction('coed: obj recompute')
            sk.recompute()
            # self.sketch.Document.recompute()
            doc.commitTransaction()
            self.ev.xy_edg_chg.emit('xy create finish')

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
        # self.print_edge_angel_list()

    @flow
    def hv_create(self, edge_id_list: List[HvEdge]):
        doc: App.Document = App.ActiveDocument
        # edges: List[CoEd.HvEdge] = self.hv_edges_get_list()
        for edge in edge_id_list:
            # edge: CoEd.HvEdge = edges[idx]
            if edge.x_angel <= self.snap_angel:
                con = Sketcher.Constraint('Horizontal', edge.geo_idx)
                doc.openTransaction('coed: Horizontal constraint')
                self.sketch.addConstraint(con)
                doc.commitTransaction()
                continue
            if edge.y_angel <= self.snap_angel:
                con = Sketcher.Constraint('Vertical', edge.geo_idx)
                doc.openTransaction('coed: Vertical constraint')
                self.sketch.addConstraint(con)
                doc.commitTransaction()
        self.__flags.set(Dirty.HV_EDGES)
        self.__flags.set(Dirty.CONSTRAINTS)
        sk: Sketcher.SketchObject = self.sketch
        sk.addProperty('App::PropertyString', 'coed')
        sk.coed = 'hv_recompute'
        doc.openTransaction('coed: obj recompute')
        sk.recompute()
        # self.sketch.Document.recompute()
        doc.commitTransaction()
        self.ev.hv_edg_chg.emit('hv create finish')

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
    def coin_create(self, pt_idx_list: List[Point]):
        doc: App.Document = App.ActiveDocument
        xp('pt_idx_list', pt_idx_list, **_co)
        if len(pt_idx_list) == 0:
            return
        for pt in pt_idx_list:
            # pt: CoEd.Point = self.__coin_points[idx]
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
                    doc.openTransaction('coed: Coincident constraint')
                    self.sketch.addConstraint(con)
                    doc.commitTransaction()
                self.__flags.all()
                sk: Sketcher.SketchObject = self.sketch
                sk.addProperty('App::PropertyString', 'coed')
                sk.coed = 'coin_recompute'
                doc.openTransaction('coed: obj recompute')
                sk.recompute()
                # self.sketch.Document.recompute()
                doc.commitTransaction()
                self.ev.coin_pts_chg.emit('coin_create finish')

    # ---------------
    # Constraint
    # @flow(off=True)
    def constraints_detect(self):
        self.__constraints.clear()
        # noinspection PyUnresolvedReferences
        co_list: List[Sketcher.Constraint] = self.sketch.Constraints
        xp('co_lst', co_list, **_cs)
        for idx, item in enumerate(co_list):
            ct: ConType = ConType(item.Type)
            if ct == ConType.COINCIDENT:
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2
                if item.Third == -2000:
                    cs: Cs = Cs.F | Cs.FP | Cs.S | Cs.SP
                    kwargs = self.__get_kwargs(cs, item, "({0}.{1}) ({2}.{3})")
                else:
                    xp('unexpected case:', ct, **_cs)
                    raise ValueError(item)

                con = self.Constraint(idx, ct.value, **kwargs)
                con.sub_type = cs
                self.__constraints.append(con)

            elif ct == ConType.HORIZONTAL or ct == ConType.VERTICAL:
                # ConstraintType, GeoIndex
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2
                if item.Second == -2000:
                    cs: Cs = Cs.F
                    kwargs = self.__get_kwargs(cs, item, "({0})")
                elif item.Third == -2000:
                    cs: Cs = Cs.F | Cs.FP | Cs.S | Cs.SP
                    kwargs = self.__get_kwargs(cs, item, "({0}.{1}) ({2}.{3})")
                else:
                    xp('unexpected case:', ct, **_cs)
                    raise ValueError(item)

                con = self.Constraint(idx, ct.value, **kwargs)
                con.sub_type = cs
                self.__constraints.append(con)

            elif ct == ConType.PARALLEL or ct == ConType.EQUAL:
                # ConstraintType, GeoIndex1, GeoIndex2
                if item.Third == -2000:
                    cs: Cs = Cs.F | Cs.S
                    kwargs = self.__get_kwargs(cs, item, "({0}) ({2})")
                else:
                    xp('unexpected case:', ct, **_cs)
                    raise ValueError(item)

                con = self.Constraint(idx, ct.value, **kwargs)
                con.sub_type = cs
                self.__constraints.append(con)

            elif ct == ConType.TANGENT or ct == ConType.PERPENDICULAR:
                # ConstraintType, GeoIndex1, GeoIndex2
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2
                if item.FirstPos == 0:  # e.g. edge on edge
                    cs: Cs = Cs.F | Cs.S
                    kwargs = self.__get_kwargs(cs, item, "({0}) ({2})")
                elif item.SecondPos == 0:  # e.g. vertex on edge
                    cs: Cs = Cs.F | Cs.FP | Cs.S
                    kwargs = self.__get_kwargs(cs, item, "({0}.{1}) ({2})")
                elif item.Third == -2000:  # e.g. vertex on vertex
                    cs: Cs = Cs.F | Cs.FP | Cs.S | Cs.SP
                    kwargs = self.__get_kwargs(cs, item, "({0}.{1}) ({2}.{3})")
                else:
                    xp('unexpected case:', ct, **_cs)
                    raise ValueError(item)

                con = self.Constraint(idx, ct.value, **kwargs)
                con.sub_type = cs
                self.__constraints.append(con)

            elif ct == ConType.DISTANCE:
                # ConstraintType, GeoIndex, Value
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, Value
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2, Value
                if item.FirstPos == 0:
                    cs: Cs = Cs.F | Cs.V
                    kwargs = self.__get_kwargs(cs, item, "({0}) v: {6:.2f}")
                elif item.SecondPos == 0:
                    cs: Cs = Cs.F | Cs.FP | Cs.S | Cs.V
                    kwargs = self.__get_kwargs(cs, item, "({0}.{1}) ({2}) v: {6:.2f}")
                elif item.Third == -2000:
                    cs: Cs = Cs.F | Cs.FP | Cs.S | Cs.SP | Cs.V
                    kwargs = self.__get_kwargs(cs, item, "({0}.{1}) ({2}.{3}) v: {6:.2f}")
                else:
                    xp('unexpected case:', ct, **_cs)
                    raise ValueError(item)

                con = self.Constraint(idx, ct.value, **kwargs)
                con.sub_type = cs
                self.__constraints.append(con)

            elif ct == ConType.DISTANCEX or ct == ConType.DISTANCEY:
                if item.FirstPos == 0:
                    cs: Cs = Cs.F | Cs.V
                    kwargs = self.__get_kwargs(cs, item, "({0}) v: {6:.2f}")
                elif item.Second == -2000:
                    cs: Cs = Cs.F | Cs.FP | Cs.V
                    kwargs = self.__get_kwargs(cs, item, "({0}.{1}) v: {6:.2f}")
                elif item.Third == -2000:
                    cs: Cs = Cs.F | Cs.FP | Cs.S | Cs.SP | Cs.V
                    kwargs = self.__get_kwargs(cs, item, "({0}.{1}) ({2}.{3}) v: {6:.2f}")
                else:
                    xp('unexpected case:', ct, **_cs)
                    raise ValueError(item)

                con = self.Constraint(idx, ct.value, **kwargs)
                con.sub_type = cs
                self.__constraints.append(con)

            elif ct == ConType.ANGLE:
                # ConstraintType, GeoIndex, Value
                # ConstraintType, GeoIndex1, GeoIndex2, Value
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2, Value
                if item.FirstPos == 0:
                    cs: Cs = Cs.F | Cs.V
                    kwargs = self.__get_kwargs(cs, item, "({0}) v: {6:.2f}")
                elif item.SecondPos == 0:
                    cs: Cs = Cs.F | Cs.S | Cs.V
                    kwargs = self.__get_kwargs(cs, item, "({0}) ({2}) v: {6:.2f}")
                elif item.Third == -2000:
                    cs: Cs = Cs.F | Cs.FP | Cs.S | Cs.SP | Cs.V
                    kwargs = self.__get_kwargs(cs, item, "({0}.{1}) ({2}.{3}) v: {6:.2f}")
                else:
                    xp('unexpected case:', ct, **_cs)
                    raise ValueError(item)

                con = self.Constraint(idx, ct.value, **kwargs)
                con.sub_type = cs
                self.__constraints.append(con)

            elif ct == ConType.RADIUS or ct == ConType.DIAMETER or ct == ConType.WEIGHT:
                # ConstraintType, GeoIndex, Value
                if item.FirstPos == 0:
                    cs: Cs = Cs.F | Cs.V
                    kwargs = self.__get_kwargs(cs, item, "({0}) v: {6:.2f}")
                else:
                    xp('unexpected case:', ct, **_cs)
                    raise ValueError(item)

                con = self.Constraint(idx, ct.value, **kwargs)
                con.sub_type = cs
                self.__constraints.append(con)

            elif ct == ConType.POINTONOBJECT:
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2
                if item.SecondPos == 0:
                    cs: Cs = Cs.F | Cs.FP | Cs.S
                    kwargs = self.__get_kwargs(cs, item, "({0}.{1}) ({2})")
                else:
                    xp('unexpected case:', ct, **_cs)
                    raise ValueError(item)

                con = self.Constraint(idx, ct.value, **kwargs)
                con.sub_type = cs
                self.__constraints.append(con)

            elif ct == ConType.SYMMETRIC:
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2, GeoIndex3
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2, GeoIndex3, PosIndex3
                if item.ThirdPos == 0:
                    cs: Cs = Cs.F | Cs.FP | Cs.S | Cs.SP | Cs.T
                    kwargs = self.__get_kwargs(cs, item, "({0}.{1}) ({2}.{3}) ({4})")
                else:
                    cs: Cs = Cs.F | Cs.FP | Cs.S | Cs.SP | Cs.T | Cs.ST
                    kwargs = self.__get_kwargs(cs, item, "({0}.{1}) ({2}.{3}) ({4}.{5})")
                con = self.Constraint(idx, ct.value, **kwargs)
                con.sub_type = cs
                self.__constraints.append(con)

            elif ct == ConType.INTERNALALIGNMENT:
                # ConstraintType, GeoIndex1, GeoIndex2
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2
                if item.FirstPos == 0:
                    cs: Cs = Cs.F | Cs.S
                    kwargs = self.__get_kwargs(cs, item, "({0}) ({2})")
                elif item.SecondPos == 0:
                    cs: Cs = Cs.F | Cs.FP | Cs.S
                    kwargs = self.__get_kwargs(cs, item, "({0}.{1}) ({2})")
                elif item.Third == -2000:
                    cs: Cs = Cs.F | Cs.FP | Cs.S | Cs.SP
                    kwargs = self.__get_kwargs(cs, item, "({0}.{1}) ({2}.{3})")
                else:
                    xp('unexpected case:', ct, **_cs)
                    raise ValueError(item)

                con = self.Constraint(idx, ct.value, **kwargs)
                con.sub_type = cs
                self.__constraints.append(con)

            elif ct == ConType.SNELLSLAW:
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2, GeoIndex3 ????
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2, GeoIndex3, PosIndex3
                if item.ThirdPos == 0:
                    cs: Cs = Cs.F | Cs.FP | Cs.S | Cs.SP | Cs.T
                    kwargs = self.__get_kwargs(cs, item, "({0}.{1}) ({2}.{3}) ({4})")
                else:
                    cs: Cs = Cs.F | Cs.FP | Cs.S | Cs.SP | Cs.T | Cs.TP
                    kwargs = self.__get_kwargs(cs, item, "({0}.{1}) ({2}.{3}) ({4}.{5})")

                con = self.Constraint(idx, ct.value, **kwargs)
                con.sub_type = cs
                self.__constraints.append(con)

            elif ct == ConType.BLOCK:
                # ConstraintType, GeoIndex
                cs: Cs = Cs.F
                kwargs = self.__get_kwargs(cs, item, "({0})")
                con = self.Constraint(idx, ct.value, **kwargs)
                con.sub_type = cs
                self.__constraints.append(con)
        self.__flags.reset(Dirty.CONSTRAINTS)
        self.ev.cons_chg.emit('cons detect finish')

    @staticmethod
    def __get_kwargs(cont: Cs, item: Sketcher.Constraint, fmt: str) -> dict:
        d: dict = dict()
        if Cs.F in cont:
            d['FIRST'] = item.First
        if Cs.FP in cont:
            d['FIRST_POS'] = pt_typ_str[item.FirstPos]
        if Cs.S in cont:
            d['SECOND'] = item.Second
        if Cs.SP in cont:
            d['SECOND_POS'] = pt_typ_str[item.SecondPos]
        if Cs.T in cont:
            d['THIRD'] = item.Third
        if Cs.TP in cont:
            d['THIRD_POS'] = pt_typ_str[item.ThirdPos]
        if Cs.V in cont:
            d['VALUE'] = item.Value
        d['FMT'] = fmt
        return d

    @flow
    def constraints_delete(self, idx_list: List[int]):
        doc: App.Document = App.ActiveDocument
        if len(idx_list):
            del_list: [int] = idx_list
            del_list.sort(reverse=True)
            for i in del_list:
                xp('del: ' + str(i), **_cs)
                doc.openTransaction('coed: delete constraint')
                self.sketch.delConstraint(i)
                doc.commitTransaction()
            self.__flags.set(Dirty.CONSTRAINTS)
            doc.openTransaction('coed: obj recompute')
            sk: Sketcher.SketchObject = self.sketch
            sk.addProperty('App::PropertyString', 'coed')
            sk.coed = 'cons_recompute'
            sk.recompute()
            # self.sketch.Document.recompute()
            doc.commitTransaction()
            self.ev.cons_chg.emit('cons delete finish')

    '''
    | idx: 0 type_id: Part::GeomLineSegment start: (4.00, 8.00, 0.00) end: (20.00, 10.00, 0.00)
    | idx: 1 type_id: Part::GeomPoint item: <Point (17.6509,4.76469,0) >
    | idx: 2 type_id: Part::GeomArcOfCircle item: ArcOfCircle (Radius : 3, Position : (9, 14, 0), Direction : (0, 0, 1), Parameter : (1.5708, 3.14159))
    | idx: 3 type_id: Part::GeomCircle center: (16.21, 20.24, 0.00) radius: 1.793571
    '''

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
            elif item.TypeId == 'Part::GeomArcOfCircle':
                arc: Part.ArcOfCircle = item
                s.append(f'{arc.Content}\n')
            else:
                xp('geo_xml_get unexpected', item.TypeId)
                s.append(str(item))
        return ''.join(s)

    def sketch_info_xml_get(self) -> str:
        from xml.dom import minidom
        doc: Document = minidom.Document()

        for obj in App.ActiveDocument.Objects:
            root: Element = doc.createElement(obj.TypeId)
            if obj.TypeId == 'Sketcher::SketchObject':
                sk: Sketcher.Sketch = obj
                root.setAttribute('FullName', sk.FullName)
                doc.appendChild(root)

                leaf_gwdp: Element = doc.createElement('GeometryWithDependentParameters')
                text = doc.createTextNode(f'{obj.getGeometryWithDependentParameters()}')
                leaf_gwdp.appendChild(text)
                root.appendChild(leaf_gwdp)

                leaf_op_vert: Element = doc.createElement('OpenVertices')
                for idx, item in enumerate(sk.OpenVertices):
                    leaf_item: Element = doc.createElement('item')
                    leaf_item.setAttribute('idx', str(idx))
                    text: Element = doc.createTextNode(f'Point {fmt_vec(App.Vector(item))}')
                    leaf_item.appendChild(text)
                    leaf_op_vert.appendChild(leaf_item)
                root.appendChild(leaf_op_vert)

                leaf_geo: Element = doc.createElement('Geometry')
                leaf_line: Element = doc.createElement('Line')
                leaf_circle: Element = doc.createElement('Circle')
                leaf_arc: Element = doc.createElement('ArcOfCircle')
                leaf_pt: Element = doc.createElement('Point')
                leaf_other: Element = doc.createElement('Other')
                for idx, item in enumerate(sk.Geometry):

                    if item.TypeId == 'Part::GeomLineSegment':
                        line: Part.LineSegment = item
                        leaf_item: Element = doc.createElement('item')
                        leaf_item.setAttribute('idx', str(idx))
                        leaf_item.setAttribute('TypeId', item.TypeId)
                        s: str = f'start {fmt_vec(App.Vector(line.StartPoint))} end {fmt_vec(App.Vector(line.EndPoint))}'
                        text: Element = doc.createTextNode(s)
                        leaf_item.appendChild(text)
                        leaf_line.appendChild(leaf_item)
                    elif item.TypeId == 'Part::GeomCircle':
                        cir: Part.Circle = item
                        leaf_item: Element = doc.createElement('item')
                        leaf_item.setAttribute('idx', str(idx))
                        leaf_item.setAttribute('TypeId', item.TypeId)
                        s: str = f'Center: {fmt_vec(App.Vector(cir.Center))} Radius: {cir.Radius}'
                        text: Element = doc.createTextNode(s)
                        leaf_item.appendChild(text)
                        leaf_circle.appendChild(leaf_item)
                    elif item.TypeId == 'Part::GeomArcOfCircle':
                        arc: Part.ArcOfCircle = item
                        leaf_item: Element = doc.createElement('item')
                        leaf_item.setAttribute('idx', str(idx))
                        leaf_item.setAttribute('TypeId', item.TypeId)
                        s: str = f'Arc: {arc}'
                        text: Element = doc.createTextNode(s)
                        leaf_item.appendChild(text)
                        leaf_arc.appendChild(leaf_item)
                    elif item.TypeId == 'Part::GeomPoint':
                        pt: Part.Point = item
                        leaf_item: Element = doc.createElement('item')
                        leaf_item.setAttribute('idx', str(idx))
                        leaf_item.setAttribute('TypeId', item.TypeId)
                        s: str = f'Point: {fmt_vec(App.Vector(pt.X, pt.Y, pt.Z))}'
                        text: Element = doc.createTextNode(s)
                        leaf_item.appendChild(text)
                        leaf_pt.appendChild(leaf_item)
                    else:
                        leaf_item: Element = doc.createElement('item')
                        leaf_item.setAttribute('idx', str(idx))
                        leaf_item.setAttribute('TypeId', item.TypeId)
                        text: Element = doc.createTextNode(f'item {item}')
                        leaf_item.appendChild(text)
                        leaf_other.appendChild(leaf_item)

                leaf_geo.appendChild(leaf_line)
                leaf_geo.appendChild(leaf_circle)
                leaf_geo.appendChild(leaf_arc)
                leaf_geo.appendChild(leaf_pt)
                leaf_geo.appendChild(leaf_other)
                root.appendChild(leaf_geo)

                leaf_geo_idx: Element = doc.createElement('getGeoVertexIndex')
                idx = 0
                while True:
                    geo, pos = self.sketch.getGeoVertexIndex(idx)
                    if (geo == -2000) and (pos == 0):
                        break
                    leaf_item: Element = doc.createElement('item')
                    leaf_item.setAttribute('idx', str(idx))
                    leaf_item.setAttribute('geo', f'({geo}.{pos})')
                    leaf_geo_idx.appendChild(leaf_item)
                    idx += 1
                root.appendChild(leaf_geo_idx)

                leaf_cons: Element = doc.createElement('constraints_get_list')
                co_list = self.constraints_get_list()
                lo = Lookup(sk)
                for idx, item in enumerate(co_list):
                    s1, s2 = lo.lookup(ConsTrans(item.co_idx, item.type_id, item.sub_type, item.fmt))
                    leaf_item: Element = doc.createElement('item')
                    leaf_item.setAttribute('idx', str(idx))
                    leaf_item.setAttribute('type_id', item.type_id)
                    leaf_item.setAttribute('sub_type', f'{item.sub_type}')
                    leaf_item.setAttribute('item', f'{item}')
                    text: Element = doc.createTextNode(f'{s2} {s1}')
                    leaf_item.appendChild(text)
                    leaf_cons.appendChild(leaf_item)
                root.appendChild(leaf_cons)

                leaf_shape_edge: Element = doc.createElement('Shape.Edges')
                for idx, edg in enumerate(obj.Shape.Edges):
                    leaf_item1: Element = doc.createElement('item')
                    leaf_item1.setAttribute('idx', str(idx))
                    leaf_item1.setAttribute('ShapeType', edg.ShapeType)
                    if edg.ShapeType == 'Edge':
                        if hasattr(edg, 'Curve'):
                            if isinstance(edg.Curve, Part.Circle):
                                leaf_item2: Element = doc.createElement('Part.Circle')
                                leaf_item2.setAttribute('TypeId', edg.Curve.TypeId)
                                s = f"Curve: Part.Circle Center: {fmt_vec(App.Vector(edg.Curve.Center))} Radius: {edg.Curve.Radius} Tag: {edg.Curve.Tag}"
                            elif isinstance(edg.Curve, Part.Line):
                                leaf_item2: Element = doc.createElement('Part.Line')
                                leaf_item2.setAttribute('TypeId', edg.Curve.TypeId)
                                s = f"Curve: Part.Line Location: {fmt_vec(App.Vector(edg.Curve.Location))} Tag: {edg.Curve.Tag}"
                            else:
                                leaf_item2: Element = doc.createElement('unexpected')
                                leaf_item2.setAttribute('TypeId', edg.Curve.TypeId)
                                s = f"Curve: unexpected type: {type(edg)}"
                            text: Element = doc.createTextNode(f'{s}')
                            leaf_item2.appendChild(text)
                            leaf_item1.appendChild(leaf_item2)

                        for idy, vert in enumerate(edg.SubShapes):
                            leaf_item2: Element = doc.createElement('shape')
                            leaf_item2.setAttribute('idx', str(idy))
                            leaf_item2.setAttribute('ShapeType', vert.ShapeType)
                            s = f"Point: {fmt_vec(vert.Point)}"
                            text: Element = doc.createTextNode(f'{s}')
                            leaf_item2.appendChild(text)
                            leaf_item1.appendChild(leaf_item2)
                    leaf_shape_edge.appendChild(leaf_item1)
                root.appendChild(leaf_shape_edge)

                leaf_shape_vertex: Element = doc.createElement('Shape.Vertex')
                for idx, vert in enumerate(obj.Shape.Vertexes):
                    leaf_item: Element = doc.createElement('item')
                    leaf_item.setAttribute('idx', str(idx))
                    leaf_item.setAttribute('ShapeType', vert.ShapeType)
                    text: Element = doc.createTextNode(f'Point {fmt_vec(vert.Point)}')
                    leaf_item.appendChild(text)
                    leaf_shape_vertex.appendChild(leaf_item)
                root.appendChild(leaf_shape_vertex)

                leaf_shape_sub: Element = doc.createElement('sub_shapes')
                self.xml_sub_shapes(obj.Shape, leaf_shape_sub, doc)
                root.appendChild(leaf_shape_sub)

        xml_str = doc.toprettyxml(indent="  ")
        return xml_str

    def xml_sub_shapes(self, obj, leaf: Element, doc: Document):
        if isinstance(obj, Part.Compound):
            leaf_item: Element = doc.createElement('item')
            leaf_item.setAttribute('ShapeType', obj.ShapeType)
            leaf_item.setAttribute('TypeId', obj.TypeId)
            leaf_item.setAttribute('Tag', obj.Tag)
            leaf.appendChild(leaf_item)
            self.xml_sub_shapes(obj.SubShapes, leaf_item, doc)
        if isinstance(obj, list):
            for idx, sub in enumerate(obj):
                leaf_item: Element = doc.createElement('item')
                if isinstance(sub, Part.Wire):
                    leaf_item.setAttribute('Idx', str(idx))
                    leaf_item.setAttribute('Type', 'Part.Wire')
                elif isinstance(sub, Part.Edge):
                    leaf_item.setAttribute('Idx', str(idx))
                    leaf_item.setAttribute('Type', 'Part.Edge')
                elif isinstance(sub, Part.Vertex):
                    leaf_item.setAttribute('Idx', str(idx))
                    leaf_item.setAttribute('Type', 'Part.Vertex')
                    leaf_item.setAttribute('Point', f'{fmt_vec(sub.Point)}')
                else:
                    leaf_item.setAttribute('Idx', str(idx))
                    leaf_item.setAttribute('Type', f'unexpected type: {type(sub)}')
                leaf.appendChild(leaf_item)

                if hasattr(sub, 'Curve'):
                    leaf_item: Element = doc.createElement('item')
                    if isinstance(sub.Curve, Part.Circle):
                        leaf_item.setAttribute('Idx', str(idx))
                        leaf_item.setAttribute('Type', 'Part.Circle')
                        leaf_item.setAttribute('TypeId', f'{sub.Curve.TypeId}')
                        leaf_item.setAttribute('Tag', f'{sub.Curve.Tag}')
                        s = f"Center: {fmt_vec(App.Vector(sub.Curve.Center))} Radius: {sub.Curve.Radius}"
                        text: Element = doc.createTextNode(f'{s}')
                        leaf_item.appendChild(text)
                    elif isinstance(sub.Curve, Part.Line):
                        leaf_item.setAttribute('Idx', str(idx))
                        leaf_item.setAttribute('Type', 'Part.Line')
                        leaf_item.setAttribute('TypeId', f'{sub.Curve.TypeId}')
                        leaf_item.setAttribute('Tag', f'{sub.Curve.Tag}')
                        s = f"Location: {fmt_vec(App.Vector(sub.Curve.Location))}"
                        text: Element = doc.createTextNode(f'{s}')
                        leaf_item.appendChild(text)
                    else:
                        leaf_item.setAttribute('Idx', str(idx))
                        leaf_item.setAttribute('Type', 'unexpected')
                        s = f"type: {type(sub)}"
                        text: Element = doc.createTextNode(f'{s}')
                        leaf_item.appendChild(text)
                    leaf.appendChild(leaf_item)

                self.xml_sub_shapes(sub.SubShapes, leaf_item, doc)

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
                xp('full_name:', sk.FullName)
                xp('GeometryWithDependentParameters:', obj.getGeometryWithDependentParameters())
                xps('OpenVertices')
                for idx, item in enumerate(sk.OpenVertices):
                    xp('idx:', idx, 'item:', fmt_vec(App.Vector(item)))

                '''
                | idx: 0 type_id: Part::GeomLineSegment start: (4.00, 8.00, 0.00) end: (20.00, 10.00, 0.00)
                | idx: 1 type_id: Part::GeomPoint item: <Point (17.6509,4.76469,0) >
                | idx: 2 type_id: Part::GeomArcOfCircle item: ArcOfCircle (Radius : 3, Position : (9, 14, 0), Direction : (0, 0, 1), Parameter : (1.5708, 3.14159))
                | idx: 3 type_id: Part::GeomCircle center: (16.21, 20.24, 0.00) radius: 1.793571
                '''

                xps('Geometry')
                for idx, item in enumerate(sk.Geometry):
                    if item.TypeId == 'Part::GeomLineSegment':
                        line: Part.LineSegment = item
                        xp('idx:', idx, 'TypeId:', item.TypeId, 'Start:',
                           fmt_vec(App.Vector(line.StartPoint)), 'End:', fmt_vec(App.Vector(line.EndPoint)))
                    elif item.TypeId == 'Part::GeomCircle':
                        cir: Part.Circle = item
                        xp(f'idx: {idx} TypeId: {cir.TypeId} Center: {fmt_vec(App.Vector(cir.Center))} '
                           f'Radius: {cir.Radius}')
                    elif item.TypeId == 'Part::GeomArcOfCircle':
                        cir: Part.ArcOfCircle = item
                        xp('idx:', idx, 'TypeId:', item.TypeId, 'item:', item)
                        xp(f'idx: {idx} TypeId: {cir.TypeId} Center: {fmt_vec(App.Vector(cir.Center))} '
                           f'Radius: {cir.Radius} Circle: {cir.Circle} StartPt: {cir.StartPoint} EndPt: {cir.EndPoint} '
                           f'FirstPara: {cir.FirstParameter} LastPara: {cir.LastParameter}')
                    elif item.TypeId == 'Part::GeomPoint':
                        pt: Part.Point = item
                        xp(f'idx: {idx} TypeId: {pt.TypeId} Point: {fmt_vec(App.Vector(pt.X, pt.Y, pt.Z))}')
                        # xp(f'idx: {idx} TypeId: {pn.TypeId} Point: {fmt_vec(App.Vector(pn.X, pn.Y, pn.Z))}')
                    else:
                        xp('idx:', idx, 'TypeId:', item.TypeId, 'item:', item)
                # xps('sketch.Constraints')
                # for idx, item in enumerate(sk.Constraints):
                #     xp('idx:', idx, 'type_id:', item.TypeId, 'item:', item)

                xps('getGeoVertexIndex')
                idx = 0
                while True:
                    geo, pos = self.sketch.getGeoVertexIndex(idx)
                    if (geo == -2000) and (pos == 0):
                        break
                    xp(f'idx: {idx} ({geo}.{pos})')
                    idx += 1

                xps('constraints_get_list')
                co_list = self.constraints_get_list()
                lo = Lookup(sk)
                for idx, item in enumerate(co_list):
                    xp(f"idx: '{idx}' type_id: '{item.type_id}' sub_type: '{item.sub_type}' item: {item}")
                    # ct = ConType(item.type_id)
                    s1, s2 = lo.lookup(ConsTrans(item.co_idx, item.type_id, item.sub_type, item.fmt))
                    xp(' ', s2)
                    xp(' ', list(s1))

                    # if ct == ConType.COINCIDENT:
                    # if ct == ConType.HORIZONTAL or ct == ConType.VERTICAL:
                    # if ct == ConType.PARALLEL or ct == ConType.EQUAL:
                    # if ct == ConType.TANGENT or ct == ConType.PERPENDICULAR:
                    # if ct == ConType.DISTANCE:
                    # if ct == ConType.DISTANCEX or ct == ConType.DISTANCEY:
                    # if ct == ConType.ANGLE:
                    # if ct == ConType.RADIUS or ct == ConType.DIAMETER or ct == ConType.WEIGHT:
                    # if ct == ConType.POINTONOBJECT:
                    # if ct == ConType.SYMMETRIC:
                    # if ct == ConType.INTERNALALIGNMENT:
                    # if ct == ConType.SNELLSLAW:
                    # if ct == ConType.BLOCK:

                xps('Shape.Edges')
                for idx, edg in enumerate(obj.Shape.Edges):
                    xp('idx', idx, 'shape_type:', edg.ShapeType)
                    if edg.ShapeType == 'Edge':
                        if hasattr(edg, 'Curve'):
                            # xp(f"{' ' *i}  idx: {idx} hasattr(sub, 'Curve')")
                            if isinstance(edg.Curve, Part.Circle):
                                xp(f"  idx: {idx} Curve: Part.Circle Center: {fmt_vec(App.Vector(edg.Curve.Center))} Radius: {edg.Curve.Radius} TypeId: {edg.Curve.TypeId} Tag: {edg.Curve.Tag}")
                            elif isinstance(edg.Curve, Part.Line):
                                xp(f"  idx: {idx} Curve: Part.Line Location: {fmt_vec(App.Vector(edg.Curve.Location))} TypeId: {edg.Curve.TypeId} Tag: {edg.Curve.Tag}")
                            else:
                                xp(f"  idx: {idx} Curve: unexpected type: {type(edg)}")
                        for idy, vert in enumerate(edg.SubShapes):
                            xp(f'    idx: {idy} shape: {vert.ShapeType} pt: {fmt_vec(vert.Point)}')
                    else:
                        xp('not an edge')
                xps('Shape.Vertexes')
                for idx, vert in enumerate(obj.Shape.Vertexes):
                    xp(f'idx: {idx} shape: {vert.ShapeType} pt: {fmt_vec(vert.Point)}')

                xps('sub_shapes')
                self.sub_shapes(obj.Shape)

        xps()

    def sub_shapes(self, obj, i=0):
        if isinstance(obj, Part.Compound):
            xp(' '*i, 'ShapeType', obj.ShapeType, 'TypeId', obj.TypeId, 'Tag', obj.Tag)
            self.sub_shapes(obj.SubShapes, i+2)
        if isinstance(obj, list):
            for idx, sub in enumerate(obj):
                # xp(f"{' ' *i}  idx: {idx} ShapeType: {sub.ShapeType} TypeId: {sub.TypeId} Tag: {sub.Tag} ")
                if isinstance(sub, Part.Wire):
                    xp(f"{' '*i}  idx: {idx} Part.Wire")
                elif isinstance(sub, Part.Edge):
                    xp(f"{' '*i}  idx: {idx} Part.Edge")
                elif isinstance(sub, Part.Vertex):
                    xp(f"{' ' *i}  idx: {idx} Part.Vertex pt: {fmt_vec(sub.Point)}")
                else:
                    xp(f"{' ' *i}  idx: {idx} unexpected type: {type(sub)}")

                if hasattr(sub, 'Curve'):
                    # xp(f"{' ' *i}  idx: {idx} hasattr(sub, 'Curve')")
                    if isinstance(sub.Curve, Part.Circle):
                        xp(f"{' ' *i}  idx: {idx} Curve: Part.Circle Center: {fmt_vec(App.Vector(sub.Curve.Center))} Radius: {sub.Curve.Radius} TypeId: {sub.Curve.TypeId} Tag: {sub.Curve.Tag}")
                    elif isinstance(sub.Curve, Part.Line):
                        xp(f"{' ' *i}  idx: {idx} Curve: Part.Line Location: {fmt_vec(App.Vector(sub.Curve.Location))} TypeId: {sub.Curve.TypeId} Tag: {sub.Curve.Tag}")
                    else:
                        xp(f"{' ' *i}  idx: {idx} Curve: unexpected type: {type(sub)}")

                self.sub_shapes(sub.SubShapes, i+2)

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
