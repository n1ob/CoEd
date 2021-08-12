"""
   generated stubs with the help of https://github.com/ostr00000/freecad-stubs
   PyCharm: see https://www.jetbrains.com/help/pycharm/stubs.html

"""

import FreeCADGui as Gui
from PySide2.QtWidgets import QApplication

from config import Cfg
from logger import xp_eof, xps
from main_impl import FixIt
from main_gui import FixItGui
from style import my_style
from tools import SketcherType

try:
    from Sketcher import ActiveSketch  # hack def in Sketcher.pyi, ActiveSketch is actually in the current local scope
except ImportError:
    pass


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
        # App.ActiveDocument.recompute()
    else:
        print("No Sketch")

    app = QApplication([])
    my_style(app)
    ex = FixItGui(c)
    ex.show()
    # get TableWidget to update geometry
    ex.tabs.setCurrentIndex(1)
    ex.tabs.setCurrentIndex(0)
    # ex.resize(ex.sizeHint())
    app.exec_()

    ex.cfg.persist_save()
    xps(__name__)
    xp_eof()
if __name__ == '__main__':
    main_t()


# def makeDiameters(Sketch):
# 	'''diameter constraints for all circles'''
# 	geoList = Sketch.Geometry
# 	for i in range(Sketch.GeometryCount):
# 		if geoList[i].TypeId == 'Part::GeomCircle':
# 			Sketch.addConstraint(Sketcher.Constraint('Diameter',i,geoList[i].Radius*2))
