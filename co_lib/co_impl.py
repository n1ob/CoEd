# ***************************************************************************
# *   Copyright (c) 2021 n1ob <niob@gmx.com>                                *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# ***************************************************************************
from typing import List
from xml.dom.minidom import Element, Document

import FreeCAD as App
import Part
import Sketcher
from PySide2.QtCore import Slot

from .co_base.co_cmn import fmt_vec, GeoType, ObjType
from .co_base.co_config import Cfg
from .co_base.co_flag import Dirty, Flags, ConsTrans
from .co_base.co_logger import xp, flow, xps, _ob_s, _go
from .co_base.co_lookup import Lookup
from .co_base.co_observer import observer_event_provider_get
from .co_tabs import co_pa, co_rd, co_xy, co_hv, co_eq, co_cs, co_co


class CoEd:

    @flow
    def __init__(self, sk, base_dir=None, parent=None):
        super().__init__()
        self.__init = False
        self.flags: Flags = Flags(Dirty)
        self.flags.all()
        self.sketch: Sketcher.SketchObject = sk
        self.base_dir = base_dir
        if base_dir is not None:
            Cfg.base_dir_set(base_dir)
        self.cs: co_cs.Constraints = co_cs.Constraints(self)
        self.co_points: co_co.CoPoints = co_co.CoPoints(self)
        self.eq_edges: co_eq.EqEdges = co_eq.EqEdges(self)
        self.hv_edges: co_hv.HvEdges = co_hv.HvEdges(self)
        self.xy_edges: co_xy.XyEdges = co_xy.XyEdges(self)
        self.rd_circles: co_rd.RdCircles = co_rd.RdCircles(self)
        self.pa_edges: co_pa.PaEdges = co_pa.PaEdges(self)
        self.evo = observer_event_provider_get()
        self.evo.obj_recomputed.connect(self.on_obj_recomputed)
        self.evo.open_transact.connect(self.on_open_transact)
        self.evo.commit_transact.connect(self.on_commit_transact)
        self.evo.in_edit.connect(self.on_in_edit)
        self.__init = True

    @property
    def sketch(self):
        return self.__sketch

    @sketch.setter
    def sketch(self, value):
        self.__sketch: Sketcher.SketchObject = value
        self.flags.all()

    @flow
    @Slot(object)
    def on_in_edit(self, obj):
        xp('on_in_edit', obj, obj.TypeId)
        if obj.TypeId == ObjType.VIEW_PROVIDER_SKETCH:
            ed_info = App.Gui.ActiveDocument.InEditInfo
            xps(App.Gui.ActiveDocument)
            xp('ed_info', ed_info)
            if ed_info is not None:
                if ed_info[0].TypeId == ObjType.SKETCH_OBJECT:
                    xp('ed_info[0]', id(ed_info[0]), 'self.sketch', id(self.sketch))
                    xp('self.sketch is ed_info', self.sketch is ed_info[0])
                    if self.sketch is not ed_info[0]:
                        self.sketch = ed_info[0]

    @flow
    @Slot(object)
    def on_obj_recomputed(self, obj):
        xp(f'on_obj_recomputed obj:', str(obj), **_ob_s)
        if not self.sketch.isValid():
            xp(f'Status: {self.sketch.getStatusString()}')
            # self.impl.sketch.autoRemoveRedundants(True)
            # self.impl.sketch.autoconstraint()

    @flow
    @Slot(object, str)
    def on_open_transact(self, doc, name):
        xp(f'NOP on_open_transact doc: {doc} name: {name}', **_ob_s)

    @flow
    @Slot(object, str)
    def on_commit_transact(self, doc, name):
        xp(f'on_commit_transact doc: {doc} name: {name}', **_ob_s)
        if 'coed' in name:
            xp('ignore own', **_ob_s)
        else:
            self.flags.all()

    @flow(short=True)
    def geo_xml_get(self) -> str:
        # for xml display in ui
        s: List[str] = list()
        for idx, item in enumerate(self.sketch.Geometry):
            s.append('<!-- Geo Idx {} ---- {} ------------------------------------>\n'.format(idx, item.TypeId))
            if item.TypeId == GeoType.CIRCLE:
                circle: Part.Circle = item
                s.append(circle.Content)
            elif item.TypeId == GeoType.LINE_SEGMENT:
                line: Part.LineSegment = item
                s.append(line.Content)
            elif item.TypeId == GeoType.POINT:
                pt: Part.Point = item
                s.append(pt.Content)
            elif item.TypeId == GeoType.ARC_OF_CIRCLE:
                arc: Part.ArcOfCircle = item
                s.append(f'{arc.Content}\n')
            else:
                xp('geo_xml_get unexpected', item.TypeId, **_go)
                s.append(str(item))
        return ''.join(s)

    @flow(short=True)
    def sketch_info_xml_get(self) -> str:
        from xml.dom import minidom
        doc: Document = minidom.Document()
        try:
            lo = Lookup(self.sketch)
            obj = self.sketch
            root: Element = doc.createElement(obj.TypeId)
            if obj.TypeId == ObjType.SKETCH_OBJECT:
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
                leaf_item: Element = doc.createElement('translated')
                text: Element = doc.createTextNode(' '.join(lo.open_vertices()))
                leaf_item.appendChild(text)
                leaf_op_vert.appendChild(leaf_item)
                root.appendChild(leaf_op_vert)

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

                leaf_geo: Element = doc.createElement('Geometry')
                self.xml_geometry(doc, leaf_geo, sk)
                root.appendChild(leaf_geo)

                leaf_ex_idx: Element = doc.createElement('ExternalGeometry')
                for idx, ex in enumerate(sk.ExternalGeometry):
                    leaf_vert: Element = doc.createElement('GeoVertexIndex')
                    leaf_geo: Element = doc.createElement('Geometry')
                    leaf_item: Element = doc.createElement('item')
                    leaf_item.setAttribute('idx', str(idx))
                    leaf_item.setAttribute('name', f'{ex[0].FullName}')
                    text: Element = doc.createTextNode(f'{list(ex[1])}')
                    leaf_item.appendChild(text)
                    leaf_ex_idx.appendChild(leaf_item)
                    idx = 0
                    while True:
                        geo, pos = ex[0].getGeoVertexIndex(idx)
                        if (geo == -2000) and (pos == 0):
                            break
                        leaf_item: Element = doc.createElement('item')
                        leaf_item.setAttribute('idx', str(idx))
                        leaf_item.setAttribute('geo', f'({geo}.{pos})')
                        leaf_vert.appendChild(leaf_item)
                        idx += 1
                    leaf_ex_idx.appendChild(leaf_vert)
                    self.xml_geometry(doc, leaf_geo, ex[0])
                    leaf_ex_idx.appendChild(leaf_geo)
                root.appendChild(leaf_ex_idx)

                leaf_cons: Element = doc.createElement('constraints_get_list')
                co_list = self.cs.constraints
                lo = Lookup(sk)
                for idx, item in enumerate(co_list):
                    s1, s2 = lo.lookup_ui_names(ConsTrans(item.co_idx, item.type_id, item.sub_type, item.fmt))
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
        except Exception as ex:
            xp(ex)
            return ''
        xml_str = doc.toprettyxml(indent="  ")
        return xml_str

    def xml_geometry(self, doc, leaf_geo, sk):
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
                s: str = f'Arc: {arc} start {fmt_vec(App.Vector(arc.StartPoint))} end {fmt_vec(App.Vector(arc.EndPoint))}'
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

    def xml_sub_shapes(self, obj, leaf: Element, doc: Document):
        if isinstance(obj, Part.Compound):
            leaf_item: Element = doc.createElement('item')
            leaf_item.setAttribute('ShapeType', obj.ShapeType)
            leaf_item.setAttribute('TypeId', obj.TypeId)
            leaf_item.setAttribute('Tag', obj.Tag)
            leaf.appendChild(leaf_item)
            self.xml_sub_shapes(obj.SubShapes, leaf_item, doc)
        elif isinstance(obj, list):
            for idx, sub in enumerate(obj):
                self.log_sub(doc, idx, leaf, sub)
        else:
            self.log_sub(doc, 0, leaf, obj)

    def log_sub(self, doc, idx, leaf, sub):
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
        ob = list()
        ob.append(self.sketch)
        lo = Lookup(self.sketch)
        for obj in ob:
            xps('obj.TypeId:', obj.TypeId, **_go)
            if obj.TypeId == ObjType.SKETCH_OBJECT:
                sk: Sketcher.Sketch = obj
                xp('full_name:', sk.FullName, **_go)
                xp('GeometryWithDependentParameters:', obj.getGeometryWithDependentParameters(), **_go)
                xps('OpenVertices', **_go)
                for idx, item in enumerate(sk.OpenVertices):
                    xp('idx:', idx, 'item:', fmt_vec(App.Vector(item)), **_go)
                xps('OpenVerticesEx', **_go)
                lst = lo.open_vertices()
                xp(lst, **_go)
                xps('Geometry', **_go)
                for idx, item in enumerate(sk.Geometry):
                    if item.TypeId == GeoType.LINE_SEGMENT:
                        line: Part.LineSegment = item
                        xp('idx:', idx, 'TypeId:', item.TypeId, 'Start:',
                           fmt_vec(App.Vector(line.StartPoint)), 'End:', fmt_vec(App.Vector(line.EndPoint)), **_go)
                    elif item.TypeId == GeoType.CIRCLE:
                        cir: Part.Circle = item
                        xp(f'idx: {idx} TypeId: {cir.TypeId} Center: {fmt_vec(App.Vector(cir.Center))} '
                           f'Radius: {cir.Radius}', **_go)
                    elif item.TypeId == GeoType.ARC_OF_CIRCLE:
                        cir: Part.ArcOfCircle = item
                        xp('idx:', idx, 'TypeId:', item.TypeId, 'item:', item, **_go)
                        xp(f'idx: {idx} TypeId: {cir.TypeId} Center: {fmt_vec(App.Vector(cir.Center))} '
                           f'Radius: {cir.Radius} Circle: {cir.Circle} StartPt: {cir.StartPoint} EndPt: {cir.EndPoint} '
                           f'FirstPara: {cir.FirstParameter} LastPara: {cir.LastParameter}', **_go)
                    elif item.TypeId == GeoType.POINT:
                        pt: Part.Point = item
                        xp(f'idx: {idx} TypeId: {pt.TypeId} Point: {fmt_vec(App.Vector(pt.X, pt.Y, pt.Z))}', **_go)
                    else:
                        xp('idx:', idx, 'TypeId:', item.TypeId, 'item:', item, **_go)
                xps('ExternalGeometry', **_go)
                lo.decode_external()
                # for idx, ex in enumerate(sk.ExternalGeometry):
                #     xp('idx:', idx, 'name:', ex[0].Name, 'ex_list:', list(ex[1]))
                xps('getGeoVertexIndex', **_go)
                idx = 0
                while True:
                    geo, pos = self.sketch.getGeoVertexIndex(idx)
                    if (geo == -2000) and (pos == 0):
                        break
                    xp(f'idx: {idx} ({geo}.{pos})', **_go)
                    idx += 1

                xps('constraints_get_list', **_go)
                co_list = self.cs.constraints
                lo = Lookup(sk)
                for idx, item in enumerate(co_list):
                    xp(f"idx: '{idx}' type_id: '{item.type_id}' sub_type: '{item.sub_type}' item: {item}", **_go)
                    # ct = ConType(item.type_id)
                    s1, s2 = lo.lookup_ui_names(ConsTrans(item.co_idx, item.type_id, item.sub_type, item.fmt))
                    xp(' ', s2, **_go)
                    xp(' ', list(s1), **_go)
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

                xps('Shape.Edges', **_go)
                for idx, edg in enumerate(obj.Shape.Edges):
                    xp('idx', idx, 'shape_type:', edg.ShapeType, **_go)
                    if edg.ShapeType == 'Edge':
                        if hasattr(edg, 'Curve'):
                            if isinstance(edg.Curve, Part.Circle):
                                xp(f"  idx: {idx} Curve: Part.Circle Center: {fmt_vec(App.Vector(edg.Curve.Center))} "
                                   f"Radius: {edg.Curve.Radius} TypeId: {edg.Curve.TypeId} Tag: {edg.Curve.Tag}", **_go)
                            elif isinstance(edg.Curve, Part.Line):
                                xp(f"  idx: {idx} Curve: Part.Line Location: {fmt_vec(App.Vector(edg.Curve.Location))} "
                                   f"TypeId: {edg.Curve.TypeId} Tag: {edg.Curve.Tag}", **_go)
                            else:
                                xp(f"  idx: {idx} Curve: unexpected type: {type(edg)}", **_go)
                        for idy, vert in enumerate(edg.SubShapes):
                            xp(f'    idx: {idy} shape: {vert.ShapeType} pt: {fmt_vec(vert.Point)}', **_go)
                    else:
                        xp('not an edge', **_go)
                xps('Shape.Vertexes', **_go)
                for idx, vert in enumerate(obj.Shape.Vertexes):
                    xp(f'idx: {idx} shape: {vert.ShapeType} pt: {fmt_vec(vert.Point)}', **_go)
                xps('sub_shapes', **_go)
                self.sub_shapes(obj.Shape)
                xps('open_vertices')
                lo = Lookup(self.sketch)
                ls = lo.open_vertices()
                xp(ls)
        xps(**_go)

    def sub_shapes(self, obj, i=0):
        if isinstance(obj, Part.Compound):
            xp(' ' * i, 'ShapeType', obj.ShapeType, 'TypeId', obj.TypeId, 'Tag', obj.Tag, **_go)
            self.sub_shapes(obj.SubShapes, i + 2)
        elif isinstance(obj, list):
            for idx, sub in enumerate(obj):
                self.log_element(i, idx, sub)
                self.sub_shapes(sub.SubShapes, i + 2)
        else:
            self.log_element(i, 0, obj)
            self.sub_shapes(obj.SubShapes, i + 2)

    def log_element(self, i, idx, sub):
        if isinstance(sub, Part.Wire):
            xp(f"{' ' * i}  idx: {idx} Part.Wire", **_go)
        elif isinstance(sub, Part.Edge):
            xp(f"{' ' * i}  idx: {idx} Part.Edge", **_go)
        elif isinstance(sub, Part.Vertex):
            xp(f"{' ' * i}  idx: {idx} Part.Vertex pt: {fmt_vec(sub.Point)}", **_go)
        else:
            xp(f"{' ' * i}  idx: {idx} unexpected type: {type(sub)}", **_go)
        if hasattr(sub, 'Curve'):
            if isinstance(sub.Curve, Part.Circle):
                xp(f"{' ' * i}  idx: {idx} Curve: Part.Circle Center: {fmt_vec(App.Vector(sub.Curve.Center))} "
                   f"Radius: {sub.Curve.Radius} TypeId: {sub.Curve.TypeId} Tag: {sub.Curve.Tag}", **_go)
            elif isinstance(sub.Curve, Part.Line):
                xp(f"{' ' * i}  idx: {idx} Curve: Part.Line Location: {fmt_vec(App.Vector(sub.Curve.Location))} "
                   f"TypeId: {sub.Curve.TypeId} Tag: {sub.Curve.Tag}", **_go)
            else:
                xp(f"{' ' * i}  idx: {idx} Curve: unexpected type: {type(sub)}", **_go)

    @flow
    def print_geo(self):
        for idx, item in enumerate(self.sketch.Geometry):
            xp('-- Geo Idx {} ---- {} ---------------------------------------'.format(idx, item.TypeId), **_go)
            if item.TypeId == GeoType.CIRCLE:
                circle: Part.Circle = item
                xp(circle.Content, **_go)
            elif item.TypeId == GeoType.LINE_SEGMENT:
                line: Part.LineSegment = item
                xp(line.Content, **_go)
            else:
                xp(item, **_go)

    @flow
    def print_constraints(self):
        obj = self.cs.constraints
        # noinspection PyUnresolvedReferences
        xp(self.sketch.Constraints, **_go)
        xp(', '.join(str(x) for x in obj), **_go)
        # noinspection PyUnresolvedReferences
        for item in self.sketch.Constraints:
            xp(item.Content, **_go)


xps(__name__)

if __name__ == '__main__':
    pass
