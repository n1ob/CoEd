from typing import NewType, overload, List, Tuple, Set, Dict

import FreeCAD as App
import Part
import Sketcher
from Sketcher import Constraint

from .co_cmn import GeoPt, fmt_vec, pt_typ_str
from .co_flag import Cs, ConsTrans
from .co_logger import flow, xps


class Lookup:

    Idx = NewType('Idx', int)

    def __init__(self, obj) -> None:
        self.sketch: Sketcher.SketchObject = obj
        self.geometry = self.sketch.Geometry
        self.constraints: List[Constraint] = self.sketch.Constraints
        self.open_vertices = self.sketch.OpenVertices
        self.Edges: List[Part.Edge] = self.sketch.Shape.Edges
        self.Vertices: List[Part.Vertex] = self.sketch.Shape.Vertexes
        self.vert_idx: Dict[Tuple[int, int], int] = self.geo_vert_idx()
        self.vert_str: Dict[int, List[str]] = self.geo_vert_str(self.vert_idx)

    @flow
    def geo_vert_idx(self) -> Dict[Tuple[int, int], int]:
        idx = 0
        res: Dict[Tuple[int, int], int] = dict()

        while True:
            geo, pos = self.sketch.getGeoVertexIndex(idx)
            if (geo == -2000) and (pos == 0):
                break
            res[(geo, pos)] = idx
            idx += 1
        return res

    @flow
    def geo_vert_str(self, y: Dict[Tuple[int, int], int]) -> Dict[int, List[str]]:
        res = {x[0][0]: list() for x in y.items()}
        for i in y.items():
            res[i[0][0]].append(f'Vertex{i[1] + 1}')
        return res

    @overload
    def lookup(self, vert: GeoPt) -> Tuple[str, str]:
        ...

    @overload
    def lookup(self, geo_id: int) -> Tuple[Set[str], str]:
        ...

    @overload
    def lookup(self, item: ConsTrans) -> Tuple[Set[str], str]:
        ...

    @flow(off=True)
    def lookup(self, *args):
        if len(args) == 1:
            if isinstance(args[0], int):
                geo_idx: int = args[0]
                if self.geometry[geo_idx].TypeId == 'Part::GeomLineSegment':
                    res_set: Set[str] = set()
                    res_set.update(self.vert_str[geo_idx])
                    line: Part.LineSegment = self.geometry[geo_idx]
                    vec1: App.Vector = App.Vector(line.StartPoint)
                    vec2: App.Vector = App.Vector(line.EndPoint)
                    res_set.add(f'Edge{geo_idx + 1}')
                    return res_set, f'Edge{geo_idx + 1} geo_idx: {geo_idx} start: {fmt_vec(vec1)} end: {fmt_vec(vec2)}'
                if self.geometry[geo_idx].TypeId == 'Part::GeomCircle':
                    res_set: Set[str] = set()
                    res_set.update(self.vert_str[geo_idx])
                    cir: Part.Circle = self.geometry[geo_idx]
                    res_set.add(f'Edge{geo_idx + 1}')
                    return res_set, f'geo_idx: {geo_idx} TypeId: {cir.TypeId} Center: {fmt_vec(App.Vector(cir.Center))} Radius: {cir.Radius}'
                if self.geometry[geo_idx].TypeId == 'Part::GeomArcOfCircle':
                    res_set: Set[str] = set()
                    res_set.update(self.vert_str[geo_idx])
                    arc: Part.ArcOfCircle = self.geometry[geo_idx]
                    res_set.add(f'Edge{geo_idx + 1}')
                    return res_set, f'geo_idx: {geo_idx} TypeId: {arc.TypeId} Center: {fmt_vec(App.Vector(arc.Center))} Radius: {arc.Radius}'
                if self.geometry[geo_idx].TypeId == 'Part::GeomPoint':
                    res_set: Set[str] = set()
                    res_set.update(self.vert_str[geo_idx])
                    pt: Part.Point = self.geometry[geo_idx]
                    return res_set, f'geo_idx: {geo_idx} TypeId: {pt.TypeId} Item: {pt}'

                return f'none', f'{geo_idx} {self.geometry[geo_idx].TypeId}'

            elif isinstance(args[0], GeoPt):
                pt: GeoPt = args[0]
                idx = self.vert_idx[(pt.idx, pt.typ)]
                return f'Vertex{idx + 1}', f'Vertex{idx + 1} idx: {idx} geo: ({pt})'

            elif isinstance(args[0], ConsTrans):
                item: ConsTrans = args[0]
                s: str = ''
                set_: Set[str] = set()
                cs: Constraint = self.constraints[item.co_idx]
                if (Cs.F | Cs.FP) in item.sub_type:
                    s1, s2 = self.lookup(GeoPt(cs.First, cs.FirstPos))
                    set_.add(s1)
                    s += f'{s2} '
                elif Cs.F in item.sub_type:
                    s1, s2 = self.lookup(cs.First)
                    set_ = set_.union(s1)
                    s += f'{s2} '
                else:
                    raise ValueError('no first available')

                if (Cs.S | Cs.SP) in item.sub_type:
                    s1, s2 = self.lookup(GeoPt(cs.Second, cs.SecondPos))
                    set_.add(s1)
                    s += f'{s2} '
                elif Cs.S in item.sub_type:
                    s1, s2 = self.lookup(cs.Second)
                    set_ = set_.union(s1)
                    s += f'{s2} '

                if (Cs.T | Cs.TP) in item.sub_type:
                    s1, s2 = self.lookup(GeoPt(cs.Third, cs.ThirdPos))
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

    def lookup_construct(self, item: ConsTrans) -> Tuple[str, str]:
        cs: Constraint = self.constraints[item.co_idx]
        res_n = list()
        res_c = list()
        if Cs.F in item.sub_type:
            s = f'{cs.First}.{pt_typ_str[cs.FirstPos]}' if Cs.FP in item.sub_type else f'{cs.First}'
            res_c.append(s) if self.sketch.getConstruction(cs.First) else res_n.append(s)
        else:
            raise ValueError('no first available')

        if Cs.S in item.sub_type:
            s = f'{cs.Second}.{pt_typ_str[cs.SecondPos]}' if Cs.SP in item.sub_type else f'{cs.Second}'
            res_c.append(s) if self.sketch.getConstruction(cs.Second) else res_n.append(s)

        if Cs.T in item.sub_type:
            s = f'{cs.Third}.{pt_typ_str[cs.ThirdPos]}' if Cs.TP in item.sub_type else f'{cs.Third}'
            res_c.append(s) if self.sketch.getConstruction(cs.Third) else res_n.append(s)

        return ' '.join(res_n), ' '.join(res_c)

    def lookup_open_vert(self) -> List[str]:
        res = list()
        for idx, geo in enumerate(self.geometry):
            if geo.TypeId == 'Part::GeomLineSegment':
                geo: Part.LineSegment
                res.append((idx, 1, geo.StartPoint))
                res.append((idx, 2, geo.EndPoint))
            elif geo.TypeId == 'Part::GeomArcOfCircle':
                geo: Part.ArcOfCircle
                edg = self.sketch.Shape.Edges[idx]
                res.append((idx, 1, edg[0]))
                res.append((idx, 2, edg[1]))

        res2 = list()
        for ptx in self.open_vertices:
            ptx_vec = App.Vector(ptx)
            for idx, typ, pty in res:
                pty_vec = App.Vector(pty)
                if ptx_vec.isEqual(pty_vec, 0.0000001):
                    res2.append((idx, typ))
                    break

        res3 = list()
        for x in res2:
            res3.append(f'Vertex{self.vert_idx[x] + 1}')

        return res3


xps(__name__)

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
