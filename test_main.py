import FreeCAD as App
import Part
from main import main_t
import Sketcher
# App.getDocument('Unbenannt').getObject('Sketch').delGeometries([0])


def add_geo(o: object):
    App.getDocument(DOC).getObject('Sketch').addGeometry(o, False)


def make_seg(v1, v2):
    App.getDocument(DOC).getObject('Sketch').addGeometry(Part.LineSegment(App.Vector(v1), App.Vector(v2)), False)

def add_con(o: object):
    App.getDocument(DOC).getObject('Sketch').addConstraint(o)

DOC = "Test"
App.newDocument(DOC)
App.setActiveDocument(DOC)
App.ActiveDocument=App.getDocument(DOC)
App.activeDocument().addObject('Sketcher::SketchObject', 'Sketch')
App.activeDocument().Sketch.Placement = App.Placement(App.Vector(0.000000, 0.000000, 0.000000), App.Rotation(0.000000, 0.000000, 0.000000, 1.000000))
App.activeDocument().Sketch.MapMode = "Deactivated"
ActiveSketch = App.getDocument(DOC).getObject('Sketch')
App.ActiveDocument.recompute()

# make_seg([2, 2, 0], [6, 6, 0])
# make_seg([7, 6, 0], [12, 3, 0])
# make_seg([11, 3, 0], [2, 1, 0])
# add_geo(Part.Circle(App.Vector(7.000000, 6.000000, 0), App.Vector(0, 0, 1), 3.000000))
# add_geo(Part.Circle(App.Vector(2.000000, 4.000000, 0), App.Vector(0, 0, 1), 2.000000))


# a = ActiveSketch
# a.Geometry
# [
# <Line segment (2.5825,4.93631,0) (2.5825,1,0) >,
# <Line segment (2.5825,4.93631,0) (9.52196,4.93631,0) >,
# <Line segment (7.13802,8.57784,0) (10.5255,3.40337,0) >,
# <Line segment (9.16129,8.63208,0) (13.0776,2.64977,0) >,
# <Line segment (10.6699,5.13831,0) (15.966,8.6054,0) >,
# Circle (Radius : 1.46, Position : (4.48441, 3.47631, 0), Direction : (0, 0, 1)),
# <Line segment (15.1784,5.44668,0) (21.0412,3.05995,0) >,
# <Line segment (17.2796,2.21415,0) (19.0838,6.64595,0) >,
# <Line segment (3,7.68499,0) (7.20759,11,0) >,
# <Line segment (20.0046,10,0) (25.7946,5,0) >,
# Circle (Radius : 1.76, Position : (10.4495, 15.5087, 0), Direction : (0, 0, 1)),
# <Line segment (21,7.99992,0) (29.5118,11.6617,0) >,
# <Line segment (35.4233,10.4101,0) (44.4536,13.7029,0) >,
# <Line segment (38.4161,15.7885,0) (39.1259,11.7602,0) >,
# <Line segment (37.2889,16.4162,0) (39.1259,11.7602,0) >
# ]
# a.Constraints
# [
# <Constraint 'Coincident'>,
# <Constraint 'PointOnObject' (1,2)>,
# <Constraint 'Vertical' (0)>,
# <Constraint 'Horizontal' (1)>,
# <Constraint 'Parallel'>,
# <Constraint 'Perpendicular'>,
# <Constraint 'Radius'>,
# <Constraint 'Tangent'>,
# <Constraint 'Equal' (4,6)>,
# <Constraint 'Symmetric'>,
# <Constraint 'Block' (8)>,
# <Constraint 'DistanceX'>,
# <Constraint 'DistanceY'>,
# <Constraint 'DistanceX'>,
# <Constraint 'DistanceY'>,
# <Constraint 'Distance'>,
# <Constraint 'Diameter'>,
# <Constraint 'Angle'>,
# <Constraint 'Coincident'>,
# <Constraint 'PointOnObject' (14,12)>,
# <Constraint 'SnellsLaw'>
# ]
# >>> for i in a.Constraints:
# ... 	    print(i.Content)
# ...
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
# >>>

# Gui.runCommand('Sketcher_CreateLine',0)
make_seg([2.452832,4.486332, 0], [3.533459,1.000000, 0])
# Gui.runCommand('Sketcher_CreateLine',0)
make_seg([2.582505,5.307610, 0], [7.466946,6.000000, 0])
# Gui.Selection.addSelection(DOC,'Sketch','Vertex3',2.5825,5.30761,0.012,False)
# Gui.Selection.addSelection(DOC,'Sketch','Vertex1',2.45283,4.48633,0.012,False)
### Begin command Sketcher_ConstrainCoincident
add_con(Sketcher.Constraint('Coincident',1,1,0,1)) 
### End command Sketcher_ConstrainCoincident
# Gui.Selection.clearSelection()
# Gui.runCommand('Sketcher_CreateLine',0)
make_seg([7.423720,8.722394, 0], [10.000000,3.448930, 0])
# Gui.Selection.addSelection(DOC,'Sketch','Vertex4',7.46695,6,0.012,False)
# Gui.Selection.addSelection(DOC,'Sketch','Edge3',8.63778,6.2373,0.008,False)
### Begin command Sketcher_ConstrainPointOnObject
add_con(Sketcher.Constraint('PointOnObject',1,2,2)) 
### End command Sketcher_ConstrainPointOnObject
# Gui.Selection.clearSelection()
# Gui.runCommand('Sketcher_ConstrainVertical',0)
# Gui.Selection.addSelection(DOC,'Sketch','Edge1',3,3,0)
add_con(Sketcher.Constraint('Vertical',0)) 
# Gui.Selection.clearSelection()
# Gui.runCommand('Sketcher_ConstrainHorizontal',0)
# Gui.Selection.addSelection(DOC,'Sketch','Edge2',6,5.69664,0)
add_con(Sketcher.Constraint('Horizontal',1)) 
# Gui.Selection.addSelection(DOC,'Sketch','Edge1')
# Gui.Selection.clearSelection()
# Gui.runCommand('Sketcher_CreateLine',0)
make_seg([9.498528,9.000000, 0], [12.740411,2.281851, 0])
# Gui.Selection.addSelection(DOC,'Sketch','Edge3',9.22762,4.58883,0.008,False)
# Gui.Selection.addSelection(DOC,'Sketch','Edge4',11.4541,4.94749,0.008,False)
### Begin command Sketcher_ConstrainParallel
add_con(Sketcher.Constraint('Parallel',2,3)) 
### End command Sketcher_ConstrainParallel
# Gui.Selection.clearSelection()
# Gui.runCommand('Sketcher_CreateLine',0)
make_seg([11.000000,4.616008, 0], [15.636494,9.630122, 0])
# Gui.Selection.addSelection(DOC,'Sketch','Edge5',14.6595,8.57357,0.008,False)
# Gui.runCommand('Sketcher_ConstrainPerpendicular',0)
# Gui.Selection.addSelection(DOC,'Sketch','Edge4',10.6811,6.54928,0.008,False)
### Begin command Sketcher_ConstrainPerpendicular
add_con(Sketcher.Constraint('Perpendicular',3,4)) 
### End command Sketcher_ConstrainPerpendicular
# Gui.Selection.clearSelection()
# Gui.runCommand('Sketcher_CompCreateCircle',0)
add_geo(Part.Circle(App.Vector(4.484411,3.362479,0),App.Vector(0,0,1),1.456771))
# Gui.Selection.addSelection(DOC,'Sketch','Edge6',5.41299,2.24002,0.008,False)
### Begin command Sketcher_CompConstrainRadDia
add_con(Sketcher.Constraint('Radius',5,1.456771)) 
App.getDocument(DOC).getObject('Sketch').setDatum(6,App.Units.Quantity('1.460000 mm'))
### End command Sketcher_CompConstrainRadDia
# Gui.Selection.clearSelection()
# Gui.Selection.addSelection(DOC,'Sketch','Edge6',4.97897,4.73617,0.008,False)
# Gui.Selection.addSelection(DOC,'Sketch','Edge2',5.91084,5.35176,0.008,False)
### Begin command Sketcher_ConstrainTangent
add_con(Sketcher.Constraint('Tangent',5,1)) 
### End command Sketcher_ConstrainTangent
# Gui.Selection.clearSelection()
# Gui.runCommand('Sketcher_CreateLine',0)
make_seg([15.000000,5.394060, 0], [21.000000,3.000000, 0])
# Gui.Selection.addSelection(DOC,'Sketch','Edge5',14.1566,7.42087,0.008,False)
# Gui.Selection.addSelection(DOC,'Sketch','Edge7',19.0902,3.76203,0.008,False)
### Begin command Sketcher_ConstrainEqual
add_con(Sketcher.Constraint('Equal',4,6)) 
### End command Sketcher_ConstrainEqual
# Gui.Selection.clearSelection()
# Gui.runCommand('Sketcher_CreateLine',0)
make_seg([16.630672,2.281851, 0], [19.000000,6.690814, 0])
# Gui.Selection.addSelection(DOC,'Sketch','Vertex12',15.0763,5.37553,0.012,False)
# Gui.Selection.addSelection(DOC,'Sketch','Vertex13',20.9536,3.01853,0.012,False)
# Gui.Selection.addSelection(DOC,'Sketch','Edge8',17.1254,3.20246,0.008,False)
### Begin command Sketcher_ConstrainSymmetric
add_con(Sketcher.Constraint('Symmetric',6,1,6,2,7)) 
### End command Sketcher_ConstrainSymmetric
# Gui.Selection.clearSelection()
# Gui.runCommand('Sketcher_CreateLine',0)
make_seg([3.000000,7.684991, 0], [7.207594,11.000000, 0])
# Gui.Selection.addSelection(DOC,'Sketch','Edge9',6.85928,10.7256,0.008,False)
### Begin command Sketcher_ConstrainBlock
add_con(Sketcher.Constraint('Block',8)) 
### End command Sketcher_ConstrainBlock
# Gui.Selection.clearSelection()
# Gui.runCommand('Sketcher_CreateLine',0)
make_seg([20.000000,10.000000, 0], [25.794397,5.000000, 0])
# Gui.Selection.addSelection(DOC,'Sketch','Vertex18',20,10,0.012,False)
# Gui.Selection.addSelection(DOC,'Sketch','Vertex15',19.0792,6.64595,0.012,False)
### Begin command Sketcher_ConstrainLock
add_con(Sketcher.Constraint('DistanceX',9,1,7,2,-0.920818)) 
add_con(Sketcher.Constraint('DistanceY',9,1,7,2,-3.354052)) 
### End command Sketcher_ConstrainLock
# Gui.Selection.clearSelection()
# Gui.Selection.addSelection(DOC,'Sketch','Edge10',24.8654,5.80165,0.008,False)
### Begin command Sketcher_ConstrainDistanceX
add_con(Sketcher.Constraint('DistanceX',9,1,9,2,5.794397)) 
App.getDocument(DOC).getObject('Sketch').setDatum(13,App.Units.Quantity('5.790000 mm'))
### End command Sketcher_ConstrainDistanceX
# Gui.Selection.clearSelection()
# Gui.Selection.addSelection(DOC,'Sketch','Edge10',21.4129,8.78371,0.008,False)
### Begin command Sketcher_ConstrainDistanceY
add_con(Sketcher.Constraint('DistanceY',9,2,9,1,5.000000)) 
App.getDocument(DOC).getObject('Sketch').setDatum(14,App.Units.Quantity('5.000000 mm'))
### End command Sketcher_ConstrainDistanceY
# Gui.Selection.clearSelection()
# Gui.Selection.addSelection(DOC,'Sketch','Edge5',13.8749,7.23647,0.008,False)
### Begin command Sketcher_ConstrainDistance
add_con(Sketcher.Constraint('Distance',4,6.330670)) 
App.getDocument(DOC).getObject('Sketch').setDatum(15,App.Units.Quantity('6.330000 mm'))
### End command Sketcher_ConstrainDistance
# Gui.Selection.clearSelection()
# Gui.runCommand('Sketcher_CompCreateCircle',0)
add_geo(Part.Circle(App.Vector(10.449479,15.508739,0),App.Vector(0,0,1),1.760755))
# Gui.Selection.addSelection(DOC,'Sketch','Edge11',11.5718,14.1521,0.008,False)
### Begin command Sketcher_CompConstrainRadDia
add_con(Sketcher.Constraint('Diameter',10,3.521510)) 
App.getDocument(DOC).getObject('Sketch').setDatum(16,App.Units.Quantity('3.520000 mm'))
### End command Sketcher_CompConstrainRadDia
# Gui.Selection.clearSelection()
# Gui.runCommand('Sketcher_CreateLine',0)
make_seg([21.000000,8.000000, 0], [29.511757,11.661702, 0])
# Gui.Selection.addSelection(DOC,'Sketch','Edge10',22.7725,7.6098,0.008,False)
# Gui.Selection.addSelection(DOC,'Sketch','Edge12',23.5317,9.0891,0.008,False)
### Begin command Sketcher_ConstrainAngle
add_con(Sketcher.Constraint('Angle',9,1,11,1,1.118574)) 
App.getDocument(DOC).getObject('Sketch').setDatum(17,App.Units.Quantity('64.090000 deg'))
### End command Sketcher_ConstrainAngle
# Gui.Selection.clearSelection()
# Gui.Selection.addSelection(DOC,'Sketch','Edge4',12.1125,4.12407,0.008,False)
# Gui.Selection.addSelection(DOC,'Sketch','Edge5',13.6037,7.05891,0.008,False)
# Gui.runCommand('Sketcher_CreateLine',0)
# Gui.Selection.clearSelection()
make_seg([35.260696,12.655880, 0], [44.554100,13.000000, 0])
make_seg([38.000000,15.508739, 0], [42.652195,10.000000, 0])
# Gui.Selection.addSelection(DOC,'Sketch','Edge13',42.2584,12.915,0.008,False)
# Gui.Selection.addSelection(DOC,'Sketch','Edge14',41.4504,11.423,0.008,False)
# Gui.runCommand('Sketcher_ConstrainSnellsLaw',0)
# Gui.Selection.clearSelection()
# Gui.runCommand('Sketcher_CreateLine',0)
make_seg([36.000000,14.773911, 0], [41.000000,10.000000, 0])
# Gui.Selection.addSelection(DOC,'Sketch','Vertex28',41,10,0.012,False)
# Gui.Selection.addSelection(DOC,'Sketch','Vertex26',42.6522,10,0.012,False)
# Gui.Selection.addSelection(DOC,'Sketch','Edge13',42.7268,12.9323,0.008,False)
### Begin command Sketcher_ConstrainSnellsLaw
add_con(Sketcher.Constraint('Coincident',14,2,13,2)) 
add_con(Sketcher.Constraint('PointOnObject',14,2,12)) 
add_con(Sketcher.Constraint('SnellsLaw',14,2,13,2,12,0.150000000000)) 
### End command Sketcher_ConstrainSnellsLaw
# Gui.Selection.clearSelection()

main_t(ActiveSketch)
App.closeDocument(DOC)
