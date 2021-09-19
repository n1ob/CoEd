from typing import List
from xml.dom.minidom import Element, Document

import FreeCAD as App
import Part
import Sketcher
from PySide2.QtCore import Slot

import co_co
import co_cs
import co_eq
import co_hv
import co_rd
import co_xy
from co_cmn import SketchType, fmt_vec, ConsTrans
from co_flag import DataChgEvent, Dirty, Flags
from co_logger import xp, _geo, flow, xps, _ob_s, _ev
from co_lookup import Lookup
from co_observer import EventProvider


class CoEd:

    @flow
    def __init__(self, sk, parent=None):
        super().__init__()
        self.__init = False
        self.flags: Flags = Flags(Dirty)
        self.flags.all()
        self.sketch: Sketcher.SketchObject = sk
        self.cs: co_cs.Constraints = co_cs.Constraints(self)
        self.co_points: co_co.CoPoints = co_co.CoPoints(self)
        self.eq_edges: co_eq.EqEdges = co_eq.EqEdges(self)
        self.hv_edges: co_hv.HvEdges = co_hv.HvEdges(self)
        self.xy_edges: co_xy.XyEdges = co_xy.XyEdges(self)
        self.rd_circles: co_rd.RdCircles = co_rd.RdCircles(self)
        self.ev = DataChgEvent()
        self.evo = EventProvider.evo
        self.evo.obj_recomputed.connect(self.on_obj_recomputed)
        self.evo.open_transact.connect(self.on_open_transact)
        self.__init = True

    @property
    def sketch(self) -> SketchType:
        return self.__sketch

    @sketch.setter
    def sketch(self, value: SketchType):
        self.__sketch: Sketcher.SketchObject = value
        self.flags.all()

    @flow
    def constraints_get_list(self):
        if self.flags.has(Dirty.CONSTRAINTS):
            self.cs.constraints_detect()
            xp('detect cons_chg.emit', **_ev)
            self.ev.cons_chg.emit('cons detect finish')
        return self.cs.constraints

    @flow
    def constraints_delete(self, idx_list: List[int]):
        self.cs.constraints_delete(idx_list)
        xp('delete cons_chg.emit', **_ev)
        self.ev.cons_chg.emit('cons delete finish')

    @flow
    @Slot(object)
    def on_obj_recomputed(self, obj):
        xp(f'on_obj_recomputed obj:', str(obj), **_ob_s)
        self.flags.all()

    @flow
    @Slot(object, str)
    def on_open_transact(self, doc, name):
        xp(f'on_open_transact doc: {doc} name: {name}', **_ob_s)
        if 'coed' in name:
            xp('ignore own', **_ob_s)
        else:
            self.flags.all()

    '''
    | idx: 0 type_id: Part::GeomLineSegment start: (4.00, 8.00, 0.00) end: (20.00, 10.00, 0.00)
    | idx: 1 type_id: Part::GeomPoint item: <Point (17.6509,4.76469,0) >
    | idx: 2 type_id: Part::GeomArcOfCircle item: ArcOfCircle (Radius : 3, Position : (9, 14, 0), Direction : (0, 0, 1), Parameter : (1.5708, 3.14159))
    | idx: 3 type_id: Part::GeomCircle center: (16.21, 20.24, 0.00) radius: 1.793571
    '''

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
            xp(' ' * i, 'ShapeType', obj.ShapeType, 'TypeId', obj.TypeId, 'Tag', obj.Tag)
            self.sub_shapes(obj.SubShapes, i + 2)
        if isinstance(obj, list):
            for idx, sub in enumerate(obj):
                # xp(f"{' ' *i}  idx: {idx} ShapeType: {sub.ShapeType} TypeId: {sub.TypeId} Tag: {sub.Tag} ")
                if isinstance(sub, Part.Wire):
                    xp(f"{' ' * i}  idx: {idx} Part.Wire")
                elif isinstance(sub, Part.Edge):
                    xp(f"{' ' * i}  idx: {idx} Part.Edge")
                elif isinstance(sub, Part.Vertex):
                    xp(f"{' ' * i}  idx: {idx} Part.Vertex pt: {fmt_vec(sub.Point)}")
                else:
                    xp(f"{' ' * i}  idx: {idx} unexpected type: {type(sub)}")

                if hasattr(sub, 'Curve'):
                    # xp(f"{' ' *i}  idx: {idx} hasattr(sub, 'Curve')")
                    if isinstance(sub.Curve, Part.Circle):
                        xp(f"{' ' * i}  idx: {idx} Curve: Part.Circle Center: {fmt_vec(App.Vector(sub.Curve.Center))} Radius: {sub.Curve.Radius} TypeId: {sub.Curve.TypeId} Tag: {sub.Curve.Tag}")
                    elif isinstance(sub.Curve, Part.Line):
                        xp(f"{' ' * i}  idx: {idx} Curve: Part.Line Location: {fmt_vec(App.Vector(sub.Curve.Location))} TypeId: {sub.Curve.TypeId} Tag: {sub.Curve.Tag}")
                    else:
                        xp(f"{' ' * i}  idx: {idx} Curve: unexpected type: {type(sub)}")

                self.sub_shapes(sub.SubShapes, i + 2)

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
