import unittest
import FreeCAD as App
import Part
from main import main_t
import Sketcher
from tools import xp, flow
# App.getDocument('Unbenannt').getObject('Sketch').delGeometries([0])

DOC = "Test"


def add_geo(o: object):
    App.getDocument(DOC).getObject('Sketch').addGeometry(o, False)


def make_seg(v1, v2):
    App.getDocument(DOC).getObject('Sketch').addGeometry(Part.LineSegment(App.Vector(v1), App.Vector(v2)), False)


def add_con(o: object):
    App.getDocument(DOC).getObject('Sketch').addConstraint(o)


class MyTest(unittest.TestCase):
    def setUp(self) -> None:
        print("setUp")
        App.newDocument(DOC)
        App.setActiveDocument(DOC)
        App.ActiveDocument = App.getDocument(DOC)
        App.activeDocument().addObject('Sketcher::SketchObject', 'Sketch')
        App.activeDocument().Sketch.Placement = App.Placement(App.Vector(0.000000, 0.000000, 0.000000),
                                                              App.Rotation(0.000000, 0.000000, 0.000000, 1.000000))
        App.activeDocument().Sketch.MapMode = "Deactivated"
        self.ActiveSketch = App.getDocument(DOC).getObject('Sketch')
        App.ActiveDocument.recompute()

    def testConstraint(self):
        print("testConstraint")
        make_seg([2.452832, 4.486332, 0], [3.533459, 1.000000, 0])
        make_seg([2.582505, 5.307610, 0], [7.466946, 6.000000, 0])
        add_con(Sketcher.Constraint('Coincident', 1, 1, 0, 1))
        make_seg([7.423720, 8.722394, 0], [10.000000, 3.448930, 0])
        add_con(Sketcher.Constraint('PointOnObject', 1, 2, 2))
        add_con(Sketcher.Constraint('Vertical', 0))
        add_con(Sketcher.Constraint('Horizontal', 1))
        make_seg([9.498528, 9.000000, 0], [12.740411, 2.281851, 0])
        add_con(Sketcher.Constraint('Parallel', 2, 3))
        make_seg([11.000000, 4.616008, 0], [15.636494, 9.630122, 0])
        add_con(Sketcher.Constraint('Perpendicular', 3, 4))
        add_geo(Part.Circle(App.Vector(4.484411, 3.362479, 0), App.Vector(0, 0, 1), 1.456771))
        add_con(Sketcher.Constraint('Radius', 5, 1.456771))
        App.getDocument(DOC).getObject('Sketch').setDatum(6, App.Units.Quantity('1.460000 mm'))
        add_con(Sketcher.Constraint('Tangent', 5, 1))
        make_seg([15.000000, 5.394060, 0], [21.000000, 3.000000, 0])
        add_con(Sketcher.Constraint('Equal', 4, 6))
        make_seg([16.630672, 2.281851, 0], [19.000000, 6.690814, 0])
        add_con(Sketcher.Constraint('Symmetric', 6, 1, 6, 2, 7))
        make_seg([3.000000, 7.684991, 0], [7.207594, 11.000000, 0])
        add_con(Sketcher.Constraint('Block', 8))
        make_seg([20.000000, 10.000000, 0], [25.794397, 5.000000, 0])
        add_con(Sketcher.Constraint('DistanceX', 9, 1, 7, 2, -0.920818))
        add_con(Sketcher.Constraint('DistanceY', 9, 1, 7, 2, -3.354052))
        add_con(Sketcher.Constraint('DistanceX', 9, 1, 9, 2, 5.794397))
        App.getDocument(DOC).getObject('Sketch').setDatum(13, App.Units.Quantity('5.790000 mm'))
        add_con(Sketcher.Constraint('DistanceY', 9, 2, 9, 1, 5.000000))
        App.getDocument(DOC).getObject('Sketch').setDatum(14, App.Units.Quantity('5.000000 mm'))
        add_con(Sketcher.Constraint('Distance', 4, 6.330670))
        App.getDocument(DOC).getObject('Sketch').setDatum(15, App.Units.Quantity('6.330000 mm'))
        add_geo(Part.Circle(App.Vector(10.449479, 15.508739, 0), App.Vector(0, 0, 1), 1.760755))
        add_con(Sketcher.Constraint('Diameter', 10, 3.521510))
        App.getDocument(DOC).getObject('Sketch').setDatum(16, App.Units.Quantity('3.520000 mm'))
        make_seg([21.000000, 8.000000, 0], [29.511757, 11.661702, 0])
        add_con(Sketcher.Constraint('Angle', 9, 1, 11, 1, 1.118574))
        App.getDocument(DOC).getObject('Sketch').setDatum(17, App.Units.Quantity('64.090000 deg'))
        make_seg([35.260696, 12.655880, 0], [44.554100, 13.000000, 0])
        make_seg([38.000000, 15.508739, 0], [42.652195, 10.000000, 0])
        make_seg([36.000000, 14.773911, 0], [41.000000, 10.000000, 0])
        add_con(Sketcher.Constraint('Coincident', 14, 2, 13, 2))
        add_con(Sketcher.Constraint('PointOnObject', 14, 2, 12))
        add_con(Sketcher.Constraint('SnellsLaw', 14, 2, 13, 2, 12, 0.150000000000))

        main_t(self.ActiveSketch)

    def tearDown(self) -> None:
        print("tearDown")
        App.closeDocument(DOC)





# <Constrain Name="" Type="1" Value="0" First="1" FirstPos="1" Second="0" SecondPos="1" Third="-2000" ThirdPos="0" LabelDistance="10" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
# <Constrain Name="" Type="13" Value="0" First="1" FirstPos="2" Second="2" SecondPos="0" Third="-2000" ThirdPos="0" LabelDistance="10" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
# <Constrain Name="" Type="3" Value="0" First="0" FirstPos="0" Second="-2000" SecondPos="0" Third="-2000" ThirdPos="0" LabelDistance="10" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
# <Constrain Name="" Type="2" Value="0" First="1" FirstPos="0" Second="-2000" SecondPos="0" Third="-2000" ThirdPos="0" LabelDistance="10" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
# <Constrain Name="" Type="4" Value="0" First="2" FirstPos="0" Second="3" SecondPos="0" Third="-2000" ThirdPos="0" LabelDistance="10" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
# <Constrain Name="" Type="10" Value="0" First="3" FirstPos="0" Second="4" SecondPos="0" Third="-2000" ThirdPos="0" LabelDistance="10" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
# <Constrain Name="" Type="11" Value="1.46" First="5" FirstPos="0" Second="-2000" SecondPos="0" Third="-2000" ThirdPos="0" LabelDistance="2.01429" LabelPosition="10" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
# <Constrain Name="" Type="5" Value="0" First="5" FirstPos="0" Second="1" SecondPos="0" Third="-2000" ThirdPos="0" LabelDistance="10" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
# <Constrain Name="" Type="12" Value="0" First="4" FirstPos="0" Second="6" SecondPos="0" Third="-2000" ThirdPos="0" LabelDistance="10" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
# <Constrain Name="" Type="14" Value="0" First="6" FirstPos="1" Second="6" SecondPos="2" Third="7" ThirdPos="0" LabelDistance="10" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
# <Constrain Name="" Type="17" Value="0" First="8" FirstPos="0" Second="-2000" SecondPos="0" Third="-2000" ThirdPos="0" LabelDistance="10" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
# <Constrain Name="" Type="7" Value="-0.920818" First="9" FirstPos="1" Second="7" SecondPos="2" Third="-2000" ThirdPos="0" LabelDistance="10" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
# <Constrain Name="" Type="8" Value="-3.35405" First="9" FirstPos="1" Second="7" SecondPos="2" Third="-2000" ThirdPos="0" LabelDistance="10" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
# <Constrain Name="" Type="7" Value="5.79" First="9" FirstPos="1" Second="9" SecondPos="2" Third="-2000" ThirdPos="0" LabelDistance="2.01429" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
# <Constrain Name="" Type="8" Value="5" First="9" FirstPos="2" Second="9" SecondPos="1" Third="-2000" ThirdPos="0" LabelDistance="2.01429" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
# <Constrain Name="" Type="6" Value="6.33" First="4" FirstPos="0" Second="-2000" SecondPos="0" Third="-2000" ThirdPos="0" LabelDistance="2.01429" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
# <Constrain Name="" Type="18" Value="3.52" First="10" FirstPos="0" Second="-2000" SecondPos="0" Third="-2000" ThirdPos="0" LabelDistance="2.01429" LabelPosition="10" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
# <Constrain Name="" Type="9" Value="1.11858" First="9" FirstPos="1" Second="11" SecondPos="1" Third="-2000" ThirdPos="0" LabelDistance="2.01429" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
# <Constrain Name="" Type="1" Value="0" First="14" FirstPos="2" Second="13" SecondPos="2" Third="-2000" ThirdPos="0" LabelDistance="10" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
# <Constrain Name="" Type="13" Value="0" First="14" FirstPos="2" Second="12" SecondPos="0" Third="-2000" ThirdPos="0" LabelDistance="10" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />
# <Constrain Name="" Type="16" Value="0.15" First="14" FirstPos="2" Second="13" SecondPos="2" Third="12" ThirdPos="0" LabelDistance="10" LabelPosition="0" IsDriving="1" IsInVirtualSpace="0" IsActive="1" />

