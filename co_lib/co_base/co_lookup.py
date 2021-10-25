from typing import NewType, overload, List, Tuple, Set, Dict

import FreeCAD as App
import Part
import Sketcher

from .co_cmn import GeoPt, fmt_vec, ConType, GeoType, GeoTypeUi, GeoId
from .co_flag import Cs, ConsTrans
from .co_logger import flow, xps, xp


class Lookup:

    Idx = NewType('Idx', int)

    def __init__(self, obj) -> None:
        self.sketch: Sketcher.SketchObject = obj
        self.vert_idx_to_geo_id: Dict[int, Tuple[int, int]] = self.vert_geo_idx(self.sketch)
        self.geo_id_to_vert_idx: Dict[Tuple[int, int], int] = self.geo_vert_idx(self.sketch)
        self.geo_idx_to_vertices: Dict[int, List[str]] = self.geo_vert_str(self.geo_id_to_vert_idx)

    def ui_name_to_geo_id_pt(self, typ, ex_sk: Sketcher.Sketch, ui_name) -> Tuple[GeoId, object]:
        # ui_name -> [sk.GeoId, Point]
        g_typ, no = self.deconstruct_ui_name(ui_name)
        if g_typ == 'Edge':
            geo = ex_sk.Geometry[no-1]
            if typ == 'E':
                ret = [(GeoId(no - 1, -1), geo)]
            else:
                ret = [(GeoId(no-1, 1), geo), (GeoId(no-1, 2), geo)]
        elif g_typ == 'Vertex':
            geo, pos = ex_sk.getGeoVertexIndex(no-1)
            g = ex_sk.Geometry[geo]
            if typ == 'E':
                ret = []
            else:
                ret = [(GeoId(geo, pos), g)]
        else:
            ret = list()
        return ret

    def geo_idx_to_ex_ui_name(self) -> Dict[int, Tuple[Sketcher.Sketch, str]]:
        # local_geo_idx: (ext_ui_name, ext_sketch)
        geo_idx = -3
        res = dict()
        for sk, ex in self.sketch.ExternalGeometry:
            for name in ex:
                res[geo_idx] = (sk, name)
                geo_idx -= 1
        return res

    def extern_points(self, typ):
        res = list()
        dic = self.geo_idx_to_ex_ui_name()
        for idx, sketch_name in dic.items():
            geos = self.ui_name_to_geo_id_pt(typ, sketch_name[0], sketch_name[1])
            for geo in geos:
                geo_id, g = geo
                res.append((GeoId(idx, geo_id.typ), g))
        return res

    def geo_idx_to_geo_ids(self, sketch) -> Dict[int, List[GeoId]]:
        # sk.geo_idx: list(sk.GeoId)
        idx = 0
        res = dict()
        while True:
            geo, pos = sketch.getGeoVertexIndex(idx)
            if geo == -2000:
                break
            if geo not in res.keys():
                res[geo] = list()
            res[geo].append(GeoId(geo, pos))
            idx += 1
        return res

    def decode_external(self):
        for idx, ex in enumerate(self.sketch.ExternalGeometry):
            xp('idx:', idx, 'name:', ex[0].Name, 'ex_list:', list(ex[1]))
            sk: Sketcher.Sketch = ex[0]
            lo_idx = self.vert_geo_idx(sk)
            lst_ext_ui = list(ex[1])
            lst_decon_ui = [self.deconstruct_ui_name(x) for x in lst_ext_ui]
            for typ, no in lst_decon_ui:
                xp('typ, no', typ, no)
                if typ == GeoTypeUi.EDGE:
                    edg = sk.Geometry[no-1]
                    if edg.TypeId == GeoType.LINE_SEGMENT:
                        edg: Part.LineSegment
                        vec1: App.Vector = App.Vector(edg.StartPoint)
                        vec2: App.Vector = App.Vector(edg.EndPoint)
                        xp(f'geo_idx: {no-1} start: {fmt_vec(vec1)} end: {fmt_vec(vec2)}')
                    if edg.TypeId == GeoType.CIRCLE:
                        edg: Part.Circle
                        xp(f'geo_idx: {no-1} TypeId: {edg.TypeId} Center: {fmt_vec(App.Vector(edg.Center))} Radius: {edg.Radius}')
                    if edg.TypeId == GeoType.ARC_OF_CIRCLE:
                        edg: Part.ArcOfCircle
                        xp(f'geo_idx: {no-1} TypeId: {edg.TypeId} Center: {fmt_vec(App.Vector(edg.Center))} Radius: {edg.Radius}')
                if typ == GeoTypeUi.VERTEX:
                    geo, typ = lo_idx[no-1]
                    edg = sk.Geometry[geo]
                    xp('geo, typ, TypeId', geo, typ, edg.TypeId)

    @flow
    def vert_geo_idx(self, sketch) -> Dict[int, Tuple[int, int]]:
        idx = 0
        res: Dict[int, Tuple[int, int]] = dict()
        while True:
            geo, pos = sketch.getGeoVertexIndex(idx)
            if (geo == -2000) and (pos == 0):
                break
            res[idx] = (geo, pos)
            idx += 1
        return res

    @flow
    def geo_vert_idx(self, sketch) -> Dict[Tuple[int, int], int]:
        idx = 0
        res: Dict[Tuple[int, int], int] = dict()
        while True:
            geo, pos = sketch.getGeoVertexIndex(idx)
            if (geo == -2000) and (pos == 0):
                break
            res[(geo, pos)] = idx
            idx += 1
        return res

    @flow
    def geo_vert_str(self, y: Dict[Tuple[int, int], int]) -> Dict[int, List[str]]:
        # y: geo_id_to_vert_idx
        res = {x[0][0]: list() for x in y.items()}
        for i in y.items():
            res[i[0][0]].append(f'{GeoTypeUi.VERTEX}{i[1] + 1}')
        return res

    @overload
    def lookup_ui_names(self, vert: GeoPt) -> Tuple[str, str]:
        ...

    @overload
    def lookup_ui_names(self, geo_id: int) -> Tuple[Set[str], str]:
        ...

    @overload
    def lookup_ui_names(self, item: ConsTrans) -> Tuple[Set[str], str]:
        ...

    @flow(off=True)
    def lookup_ui_names(self, *args):
        # 'H_Axis','V_Axis','RootPoint'
        if len(args) == 1:
            if isinstance(args[0], int):
                geo_idx: int = args[0]
                res_set: Set[str] = set()
                if geo_idx == -1:
                    return {GeoTypeUi.H_AXIS}, f'H_Axis geo_idx {geo_idx}'
                if geo_idx == -2:
                    return {GeoTypeUi.V_AXIS}, f'V_Axis geo_idx {geo_idx}'
                res_set.update(self.geo_idx_to_vertices[geo_idx])
                if geo_idx <= -3:
                    res_set.add(f'{GeoTypeUi.EXTERNAL_EDGE_ABR}{((geo_idx + 2) * -1)}')
                    return res_set, {f'{GeoTypeUi.EXTERNAL_EDGE}{((geo_idx + 2) * -1)} geo_idx: {geo_idx}'}
                type_id = self.sketch.Geometry[geo_idx].TypeId
                if (type_id == GeoType.LINE_SEGMENT) or (type_id == GeoType.CIRCLE) or (type_id == GeoType.ARC_OF_CIRCLE):
                    res_set.add(f'{GeoTypeUi.EDGE}{geo_idx + 1}')
                    return res_set, self._geo_info(geo_idx)
                if type_id == GeoType.POINT:
                    return res_set, self._geo_info(geo_idx)
                return f'none', f'{geo_idx} {type_id}'

            elif isinstance(args[0], GeoPt):
                pt: GeoPt = args[0]
                if pt.idx == -1 and pt.typ == 1:
                    xp('found RootPoint')
                    return f'{GeoTypeUi.ROOT_POINT}', f'RootPoint geo: ({pt})'
                idx = self.geo_id_to_vert_idx[(pt.idx, pt.typ)]
                return f'{GeoTypeUi.VERTEX}{idx + 1}', f'{GeoTypeUi.VERTEX}{idx + 1} idx: {idx} geo: ({pt})'

            elif isinstance(args[0], ConsTrans):
                item: ConsTrans = args[0]
                s: str = ''
                set_: Set[str] = set()
                cs: Sketcher.Constraint = self.sketch.Constraints[item.co_idx]
                if (Cs.F | Cs.FP) in item.sub_type:
                    s1, s2 = self.lookup_ui_names(GeoPt(cs.First, cs.FirstPos))
                    set_.add(s1)
                    s += f'{s2} '
                elif Cs.F in item.sub_type:
                    s1, s2 = self.lookup_ui_names(cs.First)
                    set_ = set_.union(s1)
                    s += f'{s2} '
                else:
                    raise ValueError('no first available')

                if (Cs.S | Cs.SP) in item.sub_type:
                    s1, s2 = self.lookup_ui_names(GeoPt(cs.Second, cs.SecondPos))
                    set_.add(s1)
                    s += f'{s2} '
                elif Cs.S in item.sub_type:
                    s1, s2 = self.lookup_ui_names(cs.Second)
                    set_ = set_.union(s1)
                    s += f'{s2} '

                if (Cs.T | Cs.TP) in item.sub_type:
                    s1, s2 = self.lookup_ui_names(GeoPt(cs.Third, cs.ThirdPos))
                    set_.add(s1)
                    s += f'{s2} '
                elif Cs.T in item.sub_type:
                    s1, s2 = self.lookup_ui_names(cs.Third)
                    set_ = set_.union(s1)
                    s += f'{s2} '
                return set_, s
            else:
                raise TypeError(args[0])
        else:
            raise TypeError(len(args))

    def _geo_info(self, idx) -> str:
        geo = self.sketch.Geometry[idx]
        if geo.TypeId == GeoType.LINE_SEGMENT:
            geo: Part.LineSegment
            vec1: App.Vector = App.Vector(geo.StartPoint)
            vec2: App.Vector = App.Vector(geo.EndPoint)
            return f'{GeoTypeUi.EDGE}{idx + 1} geo_idx: {idx} start: {fmt_vec(vec1)} end: {fmt_vec(vec2)}'
        if geo.TypeId == GeoType.CIRCLE:
            geo: Part.Circle
            return f'geo_idx: {idx} TypeId: {geo.TypeId} Center: {fmt_vec(App.Vector(geo.Center))} Radius: {geo.Radius}'
        if geo.TypeId == GeoType.ARC_OF_CIRCLE:
            geo: Part.ArcOfCircle
            return f'geo_idx: {idx} TypeId: {geo.TypeId} Center: {fmt_vec(App.Vector(geo.Center))} Radius: {geo.Radius}'
        if geo.TypeId == GeoType.POINT:
            geo: Part.Point
            return f'geo_idx: {idx} TypeId: {geo.TypeId} Item: {geo}'

    @staticmethod
    def translate_geo_idx(idx: int, gui=True) -> str:
        n = 1 if gui else 0
        if idx <= -3:
            idg = f'x{((idx+3)*-1)+n}'
        elif idx == -2:
            idg = 'Y'
        elif idx == -1:
            idg = 'X'
        else:  # id >= 0
            idg = f'{idx+n}'
        return idg

    @staticmethod
    def translate_ui_name(idx: int, gui=True) -> str:
        if idx <= -3:
            if gui:
                idg = f'{GeoTypeUi.EXTERNAL_EDGE_ABR}{((idx+3)*-1)+1}'
            else:
                idg = f'{GeoTypeUi.EXTERNAL_EDGE}{((idx+3)*-1)+1}'
        elif idx == -2:
            idg = GeoTypeUi.V_AXIS
        elif idx == -1:
            idg = GeoTypeUi.H_AXIS
        else:  # id >= 0
            idg = f'{GeoTypeUi.EDGE}{idx+1}'
        return idg

    @flow
    def open_vertices(self) -> List[str]:
        geo_vert_set = {(idx, 1) for idx, geo in enumerate(self.sketch.Geometry)
                        if (geo.TypeId == GeoType.LINE_SEGMENT) or (geo.TypeId == GeoType.ARC_OF_CIRCLE)}
        geo_vert_set.update({(idx, 2) for idx, geo in enumerate(self.sketch.Geometry)
                             if (geo.TypeId == GeoType.LINE_SEGMENT) or (geo.TypeId == GeoType.ARC_OF_CIRCLE)})
        xp('geo_vert_set', geo_vert_set)
        co_list: List[Sketcher.Constraint] = self.sketch.Constraints
        cs_id_set = {(item.First, item.FirstPos) for item in co_list if ConType(item.Type) == ConType.COINCIDENT}
        cs_id_set.update({(item.Second, item.SecondPos) for item in co_list if ConType(item.Type) == ConType.COINCIDENT})
        xp('cs_id_set', cs_id_set)
        res = [x for x in geo_vert_set if x not in cs_id_set]
        xp('res', res)
        res2 = [f'{GeoTypeUi.VERTEX}{self.geo_id_to_vert_idx[x] + 1}' for x in res]
        xp('res2', res2)
        return res2
        # for ptx in self.open_vert:
        #     ptx_vec = App.Vector(ptx)
        #     for idx, typ, pty in geo_vert_set:
        #         pty_vec = App.Vector(pty)
        #         if ptx_vec.isEqual(pty_vec, 0.0000001):
        #             res2.append((idx, typ))
        #             break

    @staticmethod
    def matching_constraints(geo_idx_lst: List[int], cs_lst: List[Sketcher.Constraint]) -> List[int]:
        res: List[int] = list()
        for cs_idx, cs in enumerate(cs_lst):
            cs: Sketcher.Constraint
            if cs.First != -2000:
                if cs.First in geo_idx_lst:
                    res.append(cs_idx)
            if cs.Second != -2000:
                if cs.Second in geo_idx_lst:
                    res.append(cs_idx)
            if cs.Third != -2000:
                if cs.Third in geo_idx_lst:
                    res.append(cs_idx)
        return res

    @staticmethod
    def constraint_connected_edges(cs_lst) -> Set[str]:
        res: Set[int] = set()
        for cs in cs_lst:
            if cs.first != -2000:
                res.add(cs.first)
            if cs.second != -2000:
                res.add(cs.second)
            if cs.third != -2000:
                res.add(cs.third)
        res2: Set[str] = set()
        for geo_idx in res:
            if geo_idx <= -3:
                res2.add(f'{GeoTypeUi.EXTERNAL_EDGE_ABR}{((geo_idx + 2) * -1)}')
            elif geo_idx == -1:
                res2.add(GeoTypeUi.H_AXIS)
            elif geo_idx == -2:
                res2.add(GeoTypeUi.V_AXIS)
            else:
                res2.add(f'{GeoTypeUi.EDGE}{geo_idx+1}')
        return res2

    @staticmethod
    def deconstruct_ui_name(name: str) -> Tuple[str, int]:
        # 'H_Axis','V_Axis','RootPoint'
        if name.startswith(GeoTypeUi.VERTEX):
            no = int(name[6:])
            typ = GeoTypeUi.VERTEX
        elif name.startswith(GeoTypeUi.EXTERNAL_EDGE):
            no = int(name[12:])
            typ = GeoTypeUi.EXTERNAL_EDGE
        elif name.startswith(GeoTypeUi.EDGE):
            no = int(name[4:])
            typ = GeoTypeUi.EDGE
        elif name.startswith(GeoTypeUi.CONSTRAINT):
            no = int(name[10:])
            typ = GeoTypeUi.CONSTRAINT
        elif name.startswith(GeoTypeUi.H_AXIS):
            no = -1
            typ = GeoTypeUi.H_AXIS
        elif name.startswith(GeoTypeUi.V_AXIS):
            no = -2
            typ = GeoTypeUi.V_AXIS
        else:
            no = -99
            typ = GeoTypeUi.UNKNOWN
        return typ, no


xps(__name__)

"""
<?xml version="1.0" ?>
<Sketcher::SketchObject FullName="Test#Sketch2">
  <GeometryWithDependentParameters>[(0, 1), (0, 1), (1, 1), (1, 1), (2, 1), (2, 1), (3, 1), (3, 1), (4, 1), (4, 1), (5, 1), (5, 1), (6, 0), (6, 1)]</GeometryWithDependentParameters>
  <OpenVertices>
    <translated></translated>
  </OpenVertices>
  <Geometry>
    <Line>
      <item idx="0" TypeId="Part::GeomLineSegment">start (11.7, 2.0, 0.0) end (13.5, 4.1, 0.0)</item>
      <item idx="1" TypeId="Part::GeomLineSegment">start (13.5, 4.1, 0.0) end (12.6, 6.8, 0.0)</item>
      <item idx="2" TypeId="Part::GeomLineSegment">start (12.6, 6.8, 0.0) end (9.8, 7.2, 0.0)</item>
      <item idx="3" TypeId="Part::GeomLineSegment">start (9.8, 7.2, 0.0) end (8.0, 5.1, 0.0)</item>
      <item idx="4" TypeId="Part::GeomLineSegment">start (8.0, 5.1, 0.0) end (9.0, 2.4, 0.0)</item>
      <item idx="5" TypeId="Part::GeomLineSegment">start (9.0, 2.4, 0.0) end (11.7, 2.0, 0.0)</item>
    </Line>
    <Circle>
      <item idx="6" TypeId="Part::GeomCircle">Center: (10.8, 4.6, 0.0) Radius: 2.805751327242595</item>
    </Circle>
    <ArcOfCircle/>
    <Point/>
    <Other/>
  </Geometry>
  <ExternalGeometry>
    <item idx="0" name="Sketch">['Edge2', 'Edge6', 'Edge8', 'Vertex1', 'Edge5']</item>
  </ExternalGeometry>
  <getGeoVertexIndex>
    <item idx="0" geo="(0.1)"/>
    <item idx="1" geo="(0.2)"/>
    <item idx="2" geo="(1.1)"/>
    <item idx="3" geo="(1.2)"/>
    <item idx="4" geo="(2.1)"/>
    <item idx="5" geo="(2.2)"/>
    <item idx="6" geo="(3.1)"/>
    <item idx="7" geo="(3.2)"/>
    <item idx="8" geo="(4.1)"/>
    <item idx="9" geo="(4.2)"/>
    <item idx="10" geo="(5.1)"/>
    <item idx="11" geo="(5.2)"/>
    <item idx="12" geo="(6.3)"/>
    <item idx="13" geo="(-7.3)"/>
    <item idx="14" geo="(-6.1)"/>
    <item idx="15" geo="(-5.1)"/>
    <item idx="16" geo="(-5.2)"/>
    <item idx="17" geo="(-5.3)"/>
    <item idx="18" geo="(-4.1)"/>
    <item idx="19" geo="(-4.2)"/>
    <item idx="20" geo="(-3.1)"/>
    <item idx="21" geo="(-3.2)"/>
  </getGeoVertexIndex>
  <constraints_get_list>
    <item idx="0" type_id="Coincident" sub_type="Cs.SP|S|FP|F" item="0.e 1.s">Vertex2 idx: 1 geo: ((0.2)) Vertex3 idx: 2 geo: ((1.1))  {'Vertex3', 'Vertex2'}</item>
    <item idx="1" type_id="Coincident" sub_type="Cs.SP|S|FP|F" item="1.e 2.s">Vertex4 idx: 3 geo: ((1.2)) Vertex5 idx: 4 geo: ((2.1))  {'Vertex4', 'Vertex5'}</item>
    <item idx="2" type_id="Coincident" sub_type="Cs.SP|S|FP|F" item="2.e 3.s">Vertex6 idx: 5 geo: ((2.2)) Vertex7 idx: 6 geo: ((3.1))  {'Vertex7', 'Vertex6'}</item>
    <item idx="3" type_id="Coincident" sub_type="Cs.SP|S|FP|F" item="3.e 4.s">Vertex8 idx: 7 geo: ((3.2)) Vertex9 idx: 8 geo: ((4.1))  {'Vertex9', 'Vertex8'}</item>
    <item idx="4" type_id="Coincident" sub_type="Cs.SP|S|FP|F" item="4.e 5.s">Vertex10 idx: 9 geo: ((4.2)) Vertex11 idx: 10 geo: ((5.1))  {'Vertex10', 'Vertex11'}</item>
    <item idx="5" type_id="Coincident" sub_type="Cs.SP|S|FP|F" item="5.e 0.s">Vertex12 idx: 11 geo: ((5.2)) Vertex1 idx: 0 geo: ((0.1))  {'Vertex1', 'Vertex12'}</item>
    <item idx="6" type_id="Equal" sub_type="Cs.S|F" item="0 1">Edge1 geo_idx: 0 start: (11.7, 2.0, 0.0) end: (13.5, 4.1, 0.0) Edge2 geo_idx: 1 start: (13.5, 4.1, 0.0) end: (12.6, 6.8, 0.0)  {'Vertex1', 'Vertex4', 'Vertex2', 'Edge2', 'Vertex3', 'Edge1'}</item>
    <item idx="7" type_id="Equal" sub_type="Cs.S|F" item="0 2">Edge1 geo_idx: 0 start: (11.7, 2.0, 0.0) end: (13.5, 4.1, 0.0) Edge3 geo_idx: 2 start: (12.6, 6.8, 0.0) end: (9.8, 7.2, 0.0)  {'Vertex1', 'Vertex2', 'Edge3', 'Vertex5', 'Vertex6', 'Edge1'}</item>
    <item idx="8" type_id="Equal" sub_type="Cs.S|F" item="0 3">Edge1 geo_idx: 0 start: (11.7, 2.0, 0.0) end: (13.5, 4.1, 0.0) Edge4 geo_idx: 3 start: (9.8, 7.2, 0.0) end: (8.0, 5.1, 0.0)  {'Vertex1', 'Vertex2', 'Edge4', 'Vertex7', 'Vertex8', 'Edge1'}</item>
    <item idx="9" type_id="Equal" sub_type="Cs.S|F" item="0 4">Edge1 geo_idx: 0 start: (11.7, 2.0, 0.0) end: (13.5, 4.1, 0.0) Edge5 geo_idx: 4 start: (8.0, 5.1, 0.0) end: (9.0, 2.4, 0.0)  {'Vertex1', 'Vertex10', 'Vertex2', 'Edge5', 'Vertex9', 'Edge1'}</item>
    <item idx="10" type_id="Equal" sub_type="Cs.S|F" item="0 5">Edge1 geo_idx: 0 start: (11.7, 2.0, 0.0) end: (13.5, 4.1, 0.0) Edge6 geo_idx: 5 start: (9.0, 2.4, 0.0) end: (11.7, 2.0, 0.0)  {'Vertex1', 'Edge6', 'Vertex2', 'Vertex11', 'Vertex12', 'Edge1'}</item>
    <item idx="11" type_id="PointOnObject" sub_type="Cs.S|FP|F" item="0.e 6">Vertex2 idx: 1 geo: ((0.2)) geo_idx: 6 TypeId: Part::GeomCircle Center: (10.8, 4.6, 0.0) Radius: 2.805751327242595  {'Edge7', 'Vertex13', 'Vertex2'}</item>
    <item idx="12" type_id="PointOnObject" sub_type="Cs.S|FP|F" item="1.e 6">Vertex4 idx: 3 geo: ((1.2)) geo_idx: 6 TypeId: Part::GeomCircle Center: (10.8, 4.6, 0.0) Radius: 2.805751327242595  {'Edge7', 'Vertex4', 'Vertex13'}</item>
    <item idx="13" type_id="PointOnObject" sub_type="Cs.S|FP|F" item="2.e 6">Vertex6 idx: 5 geo: ((2.2)) geo_idx: 6 TypeId: Part::GeomCircle Center: (10.8, 4.6, 0.0) Radius: 2.805751327242595  {'Edge7', 'Vertex13', 'Vertex6'}</item>
    <item idx="14" type_id="PointOnObject" sub_type="Cs.S|FP|F" item="3.e 6">Vertex8 idx: 7 geo: ((3.2)) geo_idx: 6 TypeId: Part::GeomCircle Center: (10.8, 4.6, 0.0) Radius: 2.805751327242595  {'Edge7', 'Vertex13', 'Vertex8'}</item>
    <item idx="15" type_id="PointOnObject" sub_type="Cs.S|FP|F" item="4.e 6">Vertex10 idx: 9 geo: ((4.2)) geo_idx: 6 TypeId: Part::GeomCircle Center: (10.8, 4.6, 0.0) Radius: 2.805751327242595  {'Vertex13', 'Edge7', 'Vertex10'}</item>
    <item idx="16" type_id="PointOnObject" sub_type="Cs.S|FP|F" item="5.e 6">Vertex12 idx: 11 geo: ((5.2)) geo_idx: 6 TypeId: Part::GeomCircle Center: (10.8, 4.6, 0.0) Radius: 2.805751327242595  {'Edge7', 'Vertex13', 'Vertex12'}</item>
    <item idx="17" type_id="PointOnObject" sub_type="Cs.S|FP|F" item="3.e -3">Vertex8 idx: 7 geo: ((3.2)) {'ExternalEdge1 geo_idx: -3'}  {'ExternalEdge1', 'Vertex22', 'Vertex21', 'Vertex8'}</item>
  </constraints_get_list>
  <Shape.Edges>
    <item idx="0" ShapeType="Edge">
      <Part.Line TypeId="Part::GeomLine">Curve: Part.Line Location: (11.7, 2.0, 0.0) Tag: 88f92d00-7b65-4a4d-8d08-763a2a864c5a</Part.Line>
      <shape idx="0" ShapeType="Vertex">Point: (11.7, 2.0, 0.0)</shape>
      <shape idx="1" ShapeType="Vertex">Point: (13.5, 4.1, 0.0)</shape>
    </item>
    <item idx="1" ShapeType="Edge">
      <Part.Line TypeId="Part::GeomLine">Curve: Part.Line Location: (13.5, 4.1, 0.0) Tag: e82cd2d3-56ed-4f0c-9815-8a87b93320e1</Part.Line>
      <shape idx="0" ShapeType="Vertex">Point: (13.5, 4.1, 0.0)</shape>
      <shape idx="1" ShapeType="Vertex">Point: (12.6, 6.8, 0.0)</shape>
    </item>
    <item idx="2" ShapeType="Edge">
      <Part.Line TypeId="Part::GeomLine">Curve: Part.Line Location: (12.6, 6.8, 0.0) Tag: cf2b7964-b65b-426f-be74-e8ca216a9a9d</Part.Line>
      <shape idx="0" ShapeType="Vertex">Point: (12.6, 6.8, 0.0)</shape>
      <shape idx="1" ShapeType="Vertex">Point: (9.8, 7.2, 0.0)</shape>
    </item>
    <item idx="3" ShapeType="Edge">
      <Part.Line TypeId="Part::GeomLine">Curve: Part.Line Location: (9.8, 7.2, 0.0) Tag: 3fa96157-9449-46ec-b91f-3047c9f516fb</Part.Line>
      <shape idx="0" ShapeType="Vertex">Point: (9.8, 7.2, 0.0)</shape>
      <shape idx="1" ShapeType="Vertex">Point: (8.0, 5.1, 0.0)</shape>
    </item>
    <item idx="4" ShapeType="Edge">
      <Part.Line TypeId="Part::GeomLine">Curve: Part.Line Location: (8.0, 5.1, 0.0) Tag: dc5868ea-1341-4464-94d2-d7bc51729e7c</Part.Line>
      <shape idx="0" ShapeType="Vertex">Point: (8.0, 5.1, 0.0)</shape>
      <shape idx="1" ShapeType="Vertex">Point: (9.0, 2.4, 0.0)</shape>
    </item>
    <item idx="5" ShapeType="Edge">
      <Part.Line TypeId="Part::GeomLine">Curve: Part.Line Location: (9.0, 2.4, 0.0) Tag: 6ad82cb0-4cfc-4174-b922-c4dd2aaf381c</Part.Line>
      <shape idx="0" ShapeType="Vertex">Point: (9.0, 2.4, 0.0)</shape>
      <shape idx="1" ShapeType="Vertex">Point: (11.7, 2.0, 0.0)</shape>
    </item>
  </Shape.Edges>
  <Shape.Vertex>
    <item idx="0" ShapeType="Vertex">Point (11.7, 2.0, 0.0)</item>
    <item idx="1" ShapeType="Vertex">Point (13.5, 4.1, 0.0)</item>
    <item idx="2" ShapeType="Vertex">Point (12.6, 6.8, 0.0)</item>
    <item idx="3" ShapeType="Vertex">Point (9.8, 7.2, 0.0)</item>
    <item idx="4" ShapeType="Vertex">Point (8.0, 5.1, 0.0)</item>
    <item idx="5" ShapeType="Vertex">Point (9.0, 2.4, 0.0)</item>
  </Shape.Vertex>
  <sub_shapes>
    <item Idx="0" Type="Part.Wire">
      <item Idx="0" Type="Part.Edge"/>
      <item Idx="0" Type="Part.Line" TypeId="Part::GeomLine" Tag="edbd42cf-d897-46e8-bd51-f8b72d980771">
        Location: (11.7, 2.0, 0.0)
        <item Idx="0" Type="Part.Vertex" Point="(11.7, 2.0, 0.0)"/>
        <item Idx="1" Type="Part.Vertex" Point="(13.5, 4.1, 0.0)"/>
      </item>
      <item Idx="1" Type="Part.Edge"/>
      <item Idx="1" Type="Part.Line" TypeId="Part::GeomLine" Tag="7cc39386-6c90-45b6-bbc2-4dd0c874e808">
        Location: (13.5, 4.1, 0.0)
        <item Idx="0" Type="Part.Vertex" Point="(13.5, 4.1, 0.0)"/>
        <item Idx="1" Type="Part.Vertex" Point="(12.6, 6.8, 0.0)"/>
      </item>
      <item Idx="2" Type="Part.Edge"/>
      <item Idx="2" Type="Part.Line" TypeId="Part::GeomLine" Tag="380096db-3337-4640-bc33-e133833a3a6f">
        Location: (12.6, 6.8, 0.0)
        <item Idx="0" Type="Part.Vertex" Point="(12.6, 6.8, 0.0)"/>
        <item Idx="1" Type="Part.Vertex" Point="(9.8, 7.2, 0.0)"/>
      </item>
      <item Idx="3" Type="Part.Edge"/>
      <item Idx="3" Type="Part.Line" TypeId="Part::GeomLine" Tag="0d06d2c7-52c9-42ca-bb0b-a12ca02785ed">
        Location: (9.8, 7.2, 0.0)
        <item Idx="0" Type="Part.Vertex" Point="(9.8, 7.2, 0.0)"/>
        <item Idx="1" Type="Part.Vertex" Point="(8.0, 5.1, 0.0)"/>
      </item>
      <item Idx="4" Type="Part.Edge"/>
      <item Idx="4" Type="Part.Line" TypeId="Part::GeomLine" Tag="44e3824c-3d77-4145-ac2c-91455611b309">
        Location: (8.0, 5.1, 0.0)
        <item Idx="0" Type="Part.Vertex" Point="(8.0, 5.1, 0.0)"/>
        <item Idx="1" Type="Part.Vertex" Point="(9.0, 2.4, 0.0)"/>
      </item>
      <item Idx="5" Type="Part.Edge"/>
      <item Idx="5" Type="Part.Line" TypeId="Part::GeomLine" Tag="80e1a4ff-79a5-40c2-bde4-a37eab3fc5b5">
        Location: (9.0, 2.4, 0.0)
        <item Idx="0" Type="Part.Vertex" Point="(9.0, 2.4, 0.0)"/>
        <item Idx="1" Type="Part.Vertex" Point="(11.7, 2.0, 0.0)"/>
      </item>
    </item>
  </sub_shapes>
</Sketcher::SketchObject>
"""
