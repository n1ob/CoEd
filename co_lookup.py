import threading
from typing import Dict, NamedTuple, NewType, overload, Tuple

import FreeCAD as App
import FreeCADGui as Gui
import Part
from Sketcher import Sketch

from co_logger import xp, flow
from co_cmn import GeoPt, GeoPtn, fmt_vec


# class Constraint:
#
#     def __init__(self, type_id: str):
#         self.__type_id = type_id
#
#     @property
#     def type(self):
#         return self.__type_id
#
#
# class Coincident(Constraint):
#     class GeoId(NamedTuple):
#         geo: int = -1
#         pos: int = -1
#
#     def __init__(self, first: GeoId, second: GeoId) -> None:
#         super(Coincident, self).__init__('Coincident')
#         self.first: Coincident.GeoId = first
#         self.second: Coincident.GeoId = second
#
#     @property
#     def first(self):
#         return self._first
#
#     @first.setter
#     def first(self, value):
#         self._first = value
#
#     @property
#     def second(self):
#         return self._second
#
#     @second.setter
#     def second(self, value):
#         self._second = value


# class Geometry:
#
#     def __init__(self, type_id: str):
#         self.__type_id = type_id
#
#     @property
#     def type(self):
#         return self.__type_id
#
#
# class LineSegment(Geometry):
#
#     def __init__(self, start: Vector, end: Vector) -> None:
#         super(LineSegment, self).__init__('Part::GeomLineSegment')
#         self.start: Vector = start
#         self.end: Vector = end
#
#     @property
#     def start(self) -> Vector:
#         return self.__start
#
#     @start.setter
#     def start(self, value: Vector):
#         self.__start = value
#
#     @property
#     def end(self) -> Vector:
#         return self.__end
#
#     @end.setter
#     def end(self, value: Vector):
#         self.__end = value


# class VectorMap(NamedTuple):
#     geo_idx: int = -1
#     op_vertex_idx: int = -1
#     edge_idx: int = -1
#     vertex_idx: int = -1



# d: Dict[Vector, VectorMap] = dict()
#
# v: VectorMap = VectorMap()
#
# v1: Vector = Vector(1, 2, 3)
# v2: Vector = Vector(4, 5, 6)
#
# d[v1] = VectorMap(geo_idx=11)
# d[v1] = VectorMap(geo_idx=d[v1].geo_idx, op_vertex_idx=22,
#                   edge_idx=d[v1].edge_idx, vertex_idx=d[v1].vertex_idx)
# d[v1] = VectorMap(geo_idx=d[v1].geo_idx, op_vertex_idx=d[v1].op_vertex_idx,
#                   edge_idx=33, vertex_idx=d[v1].vertex_idx)
# d[v1] = VectorMap(geo_idx=d[v1].geo_idx, op_vertex_idx=d[v1].op_vertex_idx,
#                   edge_idx=d[v1].edge_idx, vertex_idx=44)
#
# d[v2] = VectorMap(geo_idx=111)
# d[v2] = VectorMap(geo_idx=d[v2].geo_idx, op_vertex_idx=222,
#                   edge_idx=d[v2].edge_idx, vertex_idx=d[v2].vertex_idx)
# d[v2] = VectorMap(geo_idx=d[v2].geo_idx, op_vertex_idx=d[v2].op_vertex_idx,
#                   edge_idx=333, vertex_idx=d[v2].vertex_idx)
# d[v2] = VectorMap(geo_idx=d[v2].geo_idx, op_vertex_idx=d[v2].op_vertex_idx,
#                   edge_idx=d[v2].edge_idx, vertex_idx=444)



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
        sk: Sketch = obj
        self.sketch = sk
        self.geo = sk.Geometry
        self.cons = sk.Constraints
        self.op_vert = sk.OpenVertices
        self.Edges = sk.Shape.Edges
        self.Vertices = sk.Shape.Vertexes

    def __new__(cls, *args, **kwargs):
        # ! singleton
        if not cls.__instance:
            with cls.__lock:
                cls.__instance = super().__new__(cls)
        else:
            # ! init once per inst
            def init_pass(self, *dt, **mp):
                pass
            cls.__init__ = init_pass
        return cls.__instance

    __instance: object = None
    __lock = threading.Lock()

    @overload
    def lookup(self, vert: GeoPtn) -> str: ...

    @overload
    def lookup(self, vert_first: GeoPtn, vert_second: GeoPtn) -> str: ...

    @overload
    def lookup(self, geo_id: int) -> str: ...

    @overload
    def lookup(self, geo_id1: int, geo_id2: int) -> str: ...

    def lookup(self, *args):

        if len(args) == 1:
            if isinstance(args[0], int):
                geo_id: int = args[0]
                geo_item: Part.LineSegment = self.geo[geo_id]
                vec1: App.Vector = App.Vector(geo_item.StartPoint)
                vec2: App.Vector = App.Vector(geo_item.EndPoint)
                # ? too much assumption ?
                for idx, edge in enumerate(self.Edges):
                    if edge.SubShapes[0].Point == vec1 and edge.SubShapes[1].Point == vec2:
                        return f'Edge{idx + 1} start: {fmt_vec(edge.SubShapes[0].Point)} end: ' \
                               f'{fmt_vec(edge.SubShapes[1].Point)}'
                return 'not found'
            else:
                pt: GeoPtn = args[0]
                geo_item: Part.LineSegment = self.geo[pt.geo_id]
                if pt.type_id == 1:
                    vec: App.Vector = App.Vector(geo_item.StartPoint)
                else:
                    vec: App.Vector = App.Vector(geo_item.EndPoint)
                for idx, vert in enumerate(self.Vertices):
                    if vert.Point == vec:
                        return f'Vertex{idx + 1} point: {fmt_vec(vert.Point)}'
                return 'not found'

        elif len(args) == 2:
            if isinstance(args[0], int):
                geo_id1: int = args[0]
                geo_id2: int = args[1]
                s1: str = self.lookup(geo_id1)
                s2: str = self.lookup(geo_id2)
                return s1 + ' ' + s2
            else:
                vert_first: GeoPtn = args[0]
                vert_second: GeoPtn = args[1]
                s1: str = self.lookup(vert_first)
                s2: str = self.lookup(vert_second)
                return s1 + ' ' + s2


    """
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
