"""
   generated stubs with the help of https://github.com/ostr00000/freecad-stubs
   PyCharm: see https://www.jetbrains.com/help/pycharm/stubs.html

"""
import sys

import FreeCAD as App
import FreeCADGui as Gui
import Sketcher
from PySide2.QtWidgets import QApplication

from main_impl import FixIt
from main_gui import FixItGui, my_style

try:
    from Sketcher import ActiveSketch  # hack def in Sketcher.pyi, ActiveSketch is actually in the current local scope
except ImportError:
    pass

from tools import xp, XpConf
# XpConf.topics.add('flow')
# XpConf.topics.add('')



try:
    SketcherType = Sketcher.SketchObject  # Hack for code completion
except AttributeError:
    SketcherType = Sketcher.Sketch


def get_sketch() -> SketcherType:
    active_workbench = Gui.activeWorkbench()  # StartGui::Workbench, SketcherGui::Workbench
    if active_workbench.name() == 'SketcherWorkbench':
        return ActiveSketch
    else:
        sel = Gui.Selection.getSelection()
        if sel[0].TypeId == 'Sketcher::SketchObject':
            return sel[0]


def detect_missing_pt_on_pt(snap_dist, sketch):
    print("\n>>>> detect_missing_pt_on_pt -----------------------------")
    s = str(sketch.detectMissingPointOnPointConstraints(snap_dist))
    print("snap: " + str(snap_dist) + "  detected: " + s)
    # id=GeoId, st=start(1), en=end(2), type(1)=coincident
    print("(id1, st/en, id2, st/en, type)")
    print("points" + str(sketch.MissingPointOnPointConstraints))
    print("<<<< detect_missing_pt_on_pt ------------------------------\n")


def main_t(sketch: SketcherType = None):  # param used for test and dbg

    if sketch is None:
        sketch = get_sketch()
    # print("-------------------------------------------------")
    if sketch is not None:
        c = FixIt(sketch)
        c.snap_dist = 1.01
        c.snap_angel = 5
        # detect_missing_pt_on_pt(c.snap_dist, sketch)
        # c.print_geo()
        # c.detect_missing_coincident()
        # c.detect_missing_h_v()
        # c.print_coincident_list()
        # c.print_build_co_pts()
        # c.print_edge_angel_list()

        # print("-------------------------------------------------")
        # c.make_coincident()
        # c.make_hor_vert()
        # c.make_diameters()
        # print("-------------------------------------------------")
        # c.detect_constraints()
        # c.print_constraints()
        # c.print_geo()
        # App.ActiveDocument.recompute()
    else:
        print("No Sketch")

    app = QApplication([])
    my_style(app)
    ex = FixItGui(c)
    ex.show()
    app.exec_()
    # print("after exec")
    # sys.exit(app.exec_())


if __name__ == '__main__':
    main_t()


# def main():
#     app = QApplication(sys.argv)
#
#     ex = FixIt()
#     ex.show()
#     sys.exit(app.exec_())
#



# Sketch.addConstraint(Sketcher.Constraint('DistanceX', Pt.Ident[0][0], Pt.Ident[0][1], Pt.Pos.x))
# Sketch.addConstraint(Sketcher.Constraint('DistanceY', Pt.Ident[0][0], Pt.Ident[0][1], Pt.Pos.y))

# App.getDocument('Unbenannt').getObject('Sketch').addGeometry(Part.Circle(App.Vector(7.000000,7.000000,0),App.Vector(0,0,1),3.000000),False)

# def makeDiameters(Sketch):
# 	'''diameter constraints for all circles'''
# 	geoList = Sketch.Geometry
# 	for i in range(Sketch.GeometryCount):
# 		if geoList[i].TypeId == 'Part::GeomCircle':
# 			Sketch.addConstraint(Sketcher.Constraint('Diameter',i,geoList[i].Radius*2))
