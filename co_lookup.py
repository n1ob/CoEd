import threading
from typing import NewType, overload, List, Tuple, Set

import FreeCAD as App
import Part
from Sketcher import Sketch, Constraint

from co_flag import Cs
from co_cmn import GeoPtn, fmt_vec, pt_typ_int, ConType, ConsTrans, SketchType

from co_logger import flow, xps, xp


class Lookup:
    """
    CONS =      dict{ConsIdx, (Type, Coin(GeoId, GeoId))} -> GEO
    VEC =       dict{Vector, (GeoIdx, OpVertIdx, EdgeIdx, VertIdx)}
    GEO =       dict{GeoIdx, Coin(Vector, Vector)}
    OP_VERT =   dict{OpVertIdx, Vector}
    EDGE =      dict{idx, (Vector, Vector) }
    VERT =      dict{idx, Vector}
    """
    Idx = NewType('Idx', int)

    def __init__(self, obj) -> None:
        sk: SketchType = obj
        self.sketch: SketchType = sk
        self.geo = sk.Geometry
        self.cons: List[Constraint] = sk.Constraints
        self.op_vert = sk.OpenVertices
        self.Edges: List[Part.Edge] = sk.Shape.Edges
        self.Vertices: List[Part.Vertex] = sk.Shape.Vertexes

    # def __new__(cls, *args, **kwargs):
    #     # ! singleton
    #     if not cls.__instance:
    #         with cls.__lock:
    #             cls.__instance = super().__new__(cls)
    #     else:
    #         # ! init once per inst
    #         def init_pass(self, *dt, **mp):
    #             pass
    #         cls.__init__ = init_pass
    #     return cls.__instance
    #
    # __instance: object = None
    # __lock = threading.Lock()

    @overload
    def lookup(self, vert: GeoPtn) -> Tuple[str, str]: ...

    @overload
    def lookup(self, geo_id: int) -> Tuple[Set[str], str]: ...

    @overload
    def lookup(self, item: ConsTrans) -> Tuple[Set[str], str]: ...

    @flow(off=True)
    def lookup(self, *args):
        if len(args) == 1:
            if isinstance(args[0], int):
                geo_id: int = args[0]
                if self.geo[geo_id].TypeId == 'Part::GeomLineSegment':
                    res_set: Set[str] = set()
                    idx = 0
                    while True:
                        geo, pos = self.sketch.getGeoVertexIndex(idx)
                        if geo == geo_id:
                            res_set.add(f'Vertex{idx + 1}')
                        if (geo == -2000) and (pos == 0):
                            break
                        idx += 1
                    line: Part.LineSegment = self.geo[geo_id]
                    vec1: App.Vector = App.Vector(line.StartPoint)
                    vec2: App.Vector = App.Vector(line.EndPoint)
                    res_set.add(f'Edge{geo_id + 1}')
                    return res_set, f'Edge{geo_id + 1} geo_id: {geo_id} start: {fmt_vec(vec1)} end: {fmt_vec(vec2)}'
                if self.geo[geo_id].TypeId == 'Part::GeomCircle':
                    res_set: Set[str] = set()
                    idx = 0
                    while True:
                        geo, pos = self.sketch.getGeoVertexIndex(idx)
                        if geo == geo_id:
                            res_set.add(f'Vertex{idx + 1}')
                        if (geo == -2000) and (pos == 0):
                            break
                        idx += 1
                    cir: Part.Circle = self.geo[geo_id]
                    res_set.add(f'Edge{geo_id + 1}')
                    return res_set, f'geo_id: {geo_id} TypeId: {cir.TypeId} Center: {fmt_vec(App.Vector(cir.Center))} Radius: {cir.Radius}'
                if self.geo[geo_id].TypeId == 'Part::GeomArcOfCircle':
                    res_set: Set[str] = set()
                    idx = 0
                    while True:
                        geo, pos = self.sketch.getGeoVertexIndex(idx)
                        if geo == geo_id:
                            res_set.add(f'Vertex{idx + 1}')
                        if (geo == -2000) and (pos == 0):
                            break
                        idx += 1
                    arc: Part.ArcOfCircle = self.geo[geo_id]
                    res_set.add(f'Edge{geo_id + 1}')
                    return res_set, f'geo_id: {geo_id} TypeId: {arc.TypeId} Center: {fmt_vec(App.Vector(arc.Center))} Radius: {arc.Radius}'
                if self.geo[geo_id].TypeId == 'Part::GeomPoint':
                    res_set: Set[str] = set()
                    idx = 0
                    while True:
                        geo, pos = self.sketch.getGeoVertexIndex(idx)
                        if geo == geo_id:
                            res_set.add(f'Vertex{idx + 1}')
                        if (geo == -2000) and (pos == 0):
                            break
                        idx += 1
                    pt: Part.Point = self.geo[geo_id]
                    return res_set, f'geo_id: {geo_id} TypeId: {pt.TypeId} Item: {pt}'

                return f'none', f'{geo_id} {self.geo[geo_id].TypeId}'

            elif isinstance(args[0], GeoPtn):
                pt: GeoPtn = args[0]
                # geo_item: Part.LineSegment = self.geo[pt.geo_id]
                idx = 0
                while True:
                    geo, pos = self.sketch.getGeoVertexIndex(idx)
                    if (geo == pt.geo_id) and (pos == pt.type_id):
                        return f'Vertex{idx + 1}', f'Vertex{idx + 1} idx: {idx} geo: ({geo}.{pos})'
                    if (geo == -2000) and (pos == 0):
                        break
                    idx += 1
                return f'not found', f'not found'

            elif isinstance(args[0], ConsTrans):
                item: ConsTrans = args[0]
                s: str = ''
                set_: Set[str] = set()
                cs: Constraint = self.cons[item.co_idx]
                if (Cs.F | Cs.FP) in item.sub_type:
                    s1, s2 = self.lookup(GeoPtn(cs.First, cs.FirstPos))
                    set_.add(s1)
                    s += f'{s2} '
                elif Cs.F in item.sub_type:
                    s1, s2 = self.lookup(cs.First)
                    set_ = set_.union(s1)
                    s += f'{s2} '
                else:
                    raise ValueError('no first available')

                if (Cs.S | Cs.SP) in item.sub_type:
                    s1, s2 = self.lookup(GeoPtn(cs.Second, cs.SecondPos))
                    set_.add(s1)
                    s += f'{s2} '
                elif Cs.S in item.sub_type:
                    s1, s2 = self.lookup(cs.Second)
                    set_ = set_.union(s1)
                    s += f'{s2} '

                if (Cs.T | Cs.TP) in item.sub_type:
                    s1, s2 = self.lookup(GeoPtn(cs.Third, cs.ThirdPos))
                    set_.add(s1)
                    s += f'{s2} '
                elif Cs.T in item.sub_type:
                    s1, s2 = self.lookup(cs.Third)
                    set_ = set_.union(s1)
                    s += f'{s2} '
                return set_, s
            else:
                raise TypeError(args[0])
        else:
            raise TypeError(len(args))



    """
    
      | ---Geometry----------------------------------------
      | idx: 0 type_id: Part::GeomLineSegment start: (4.00, 8.00, 0.00) end: (20.00, 10.00, 0.00)
      | idx: 1 type_id: Part::GeomPoint item: <Point (17.6509,4.76469,0) >
      | idx: 2 type_id: Part::GeomArcOfCircle item: ArcOfCircle (Radius : 3, Position : (9, 14, 0), Direction : (0, 0, 1), Parameter : (1.5708, 3.14159))
      | idx: 3 type_id: Part::GeomCircle center: (16.21, 20.24, 0.00) radius: 1.793571
      | idx: 4 type_id: Part::GeomLineSegment start: (-7.00, 17.00, 0.00) end: (-9.00, 13.29, 0.00)
      | idx: 5 type_id: Part::GeomLineSegment start: (-9.00, 13.29, 0.00) end: (-4.38, 13.50, 0.00)
      | idx: 6 type_id: Part::GeomLineSegment start: (-4.38, 13.50, 0.00) end: (-7.00, 17.00, 0.00)
      | idx: 7 type_id: Part::GeomArcOfCircle item: ArcOfCircle (Radius : 0.965578, Position : (3, 26.5016, 0), Direction : (0, 0, 1), Parameter : (1.5708, 4.71239))
      | idx: 8 type_id: Part::GeomArcOfCircle item: ArcOfCircle (Radius : 0.965578, Position : (7.35276, 26.5016, 0), Direction : (0, 0, 1), Parameter : (4.71239, 7.85398))
      | idx: 9 type_id: Part::GeomLineSegment start: (3.00, 25.54, 0.00) end: (7.35, 25.54, 0.00)
      | idx: 10 type_id: Part::GeomLineSegment start: (3.00, 27.47, 0.00) end: (7.35, 27.47, 0.00)
      | ---getGeoVertexIndex----------------------------------------
      | idx: 0 (0.1)
      | idx: 1 (0.2)
      | idx: 2 (1.1)
      | idx: 3 (2.1)
      | idx: 4 (2.2)
      | idx: 5 (2.3)
      | idx: 6 (3.3)
      | idx: 7 (4.1)
      | idx: 8 (4.2)
      | idx: 9 (5.1)
      | idx: 10 (5.2)
      | idx: 11 (6.1)
      | idx: 12 (6.2)
      | idx: 13 (7.1)
      | idx: 14 (7.2)
      | idx: 15 (7.3)
      | idx: 16 (8.1)
      | idx: 17 (8.2)
      | idx: 18 (8.3)
      | idx: 19 (9.1)
      | idx: 20 (9.2)
      | idx: 21 (10.1)
      | idx: 22 (10.2)
    
    | ---obj.TypeId: Sketcher::SketchObject----------------------------------------
    | GeometryWithDependentParameters: [(0, 1), (0, 1), (1, 1), (1, 1), (2, 1), (2, 1), (3, 1), (3, 1), (4, 1)]
    | full_name: Test#Sketch
    | ---Geometry----------------------------------------
    | idx: 0 type_id: Part::GeomLineSegment start_end: Vector (-8.0, -5.0, 0.0) Vector (4.0, 8.0, 0.0)
    | idx: 1 type_id: Part::GeomLineSegment start_end: Vector (4.0, 8.0, 0.0) Vector (7.0, -8.0, 0.0)
    | idx: 2 type_id: Part::GeomLineSegment start_end: Vector (-8.0, -6.0, 0.0) Vector (7.0, -9.0, 0.0)
    | idx: 3 type_id: Part::GeomLineSegment start_end: Vector (4.0, 8.0, 0.0) Vector (20.0, 10.0, 0.0)
    | idx: 4 type_id: Part::GeomPoint item: <Point (16,-5,0) >
    | ---Constraints----------------------------------------
    | idx: 0 type_id: Sketcher::Constraint item: <Constraint 'Coincident'>
    | (3.1) (0.2)
    | idx: 1 type_id: Sketcher::Constraint item: <Constraint 'Coincident'>
    | (0.2) (1.1)
    | ---OpenVertices----------------------------------------
    | idx: 0 item: (-8.0, -5.0, 0.0)
    | idx: 1 item: (4.0, 8.0, 0.0)
    | idx: 2 item: (20.0, 10.0, 0.0)
    | idx: 3 item: (7.0, -8.0, 0.0)
    | idx: 4 item: (-8.0, -6.0, 0.0)
    | idx: 5 item: (7.0, -9.0, 0.0)
    | ---Shape.Edges----------------------------------------
    | idx 0 type_id Edge
    |    idx: 0 geo ( 0 , 1 ) ShapeType: Vertex Point: Vector (-8.0, -5.0, 0.0)
    |    idx: 1 geo ( 0 , 2 ) ShapeType: Vertex Point: Vector (4.0, 8.0, 0.0)
    | idx 1 type_id Edge
    |    idx: 0 geo ( 0 , 1 ) ShapeType: Vertex Point: Vector (4.0, 8.0, 0.0)
    |    idx: 1 geo ( 0 , 2 ) ShapeType: Vertex Point: Vector (20.0, 10.0, 0.0)
    | idx 2 type_id Edge
    |    idx: 0 geo ( 0 , 1 ) ShapeType: Vertex Point: Vector (4.0, 8.0, 0.0)
    |    idx: 1 geo ( 0 , 2 ) ShapeType: Vertex Point: Vector (7.0, -8.0, 0.0)
    | idx 3 type_id Edge
    |    idx: 0 geo ( 0 , 1 ) ShapeType: Vertex Point: Vector (-8.0, -6.0, 0.0)
    |    idx: 1 geo ( 0 , 2 ) ShapeType: Vertex Point: Vector (7.0, -9.0, 0.0)
    | ---Shape.Vertexes----------------------------------------
    | idx: 0 geo ( 0 , 1 ) ShapeType: Vertex Point: Vector (-8.0, -5.0, 0.0)
    | idx: 1 geo ( 0 , 2 ) ShapeType: Vertex Point: Vector (4.0, 8.0, 0.0)
    | idx: 2 geo ( 1 , 1 ) ShapeType: Vertex Point: Vector (20.0, 10.0, 0.0)
    | idx: 3 geo ( 1 , 2 ) ShapeType: Vertex Point: Vector (7.0, -8.0, 0.0)
    | idx: 4 geo ( 2 , 1 ) ShapeType: Vertex Point: Vector (-8.0, -6.0, 0.0)
    | idx: 5 geo ( 2 , 2 ) ShapeType: Vertex Point: Vector (7.0, -9.0, 0.0)
    | -------------------------------------------
    """
