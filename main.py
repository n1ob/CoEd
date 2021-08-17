"""
   generated stubs with the help of https://github.com/ostr00000/freecad-stubs
   PyCharm: see https://www.jetbrains.com/help/pycharm/stubs.html
"""

import FreeCADGui as Gui
from PySide2.QtWidgets import QApplication

from config import Cfg
from logger import xps
from main_gui import CoEdGui
from main_impl import CoEd
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

# ! don't need this for now
def detect_missing_pt_on_pt(snap_dist, sketch):
    print("\n>>>> detect_missing_pt_on_pt -----------------------------")
    s = str(sketch.detectMissingPointOnPointConstraints(snap_dist))
    print("snap: " + str(snap_dist) + "  detected: " + s)
    # id=GeoId, st=start(1), en=end(2), type(1)=coincident
    print("(id1, st/en, id2, st/en, type)")
    print("points" + str(sketch.MissingPointOnPointConstraints))
    print("<<<< detect_missing_pt_on_pt ------------------------------\n")


def main_t(sketch: SketcherType = None):  # param used for unittest

    if sketch is None:
        sketch = get_sketch()
    else:
        app = QApplication([])

    if sketch is not None:
        try:
            c = CoEd(sketch)
            c.snap_dist = 1.01
            c.snap_angel = 5
            my_style(app)
            ex = CoEdGui(c)
            ex.show()
            # get TableWidget to update geometry
            ex.tabs.setCurrentIndex(1)
            ex.tabs.setCurrentIndex(0)
            app.exec_()
        finally:
            Cfg().save()
            pass
    else:
        raise ValueError("No Sketch selected")

    xps(__name__)
# detect_missing_pt_on_pt(c.snap_dist, sketch)
# App.ActiveDocument.recompute()

if __name__ == '__main__':
    main_t()


# def makeDiameters(Sketch):
# 	'''diameter constraints for all circles'''
# 	geoList = Sketch.Geometry
# 	for i in range(Sketch.GeometryCount):
# 		if geoList[i].TypeId == 'Part::GeomCircle':
# 			Sketch.addConstraint(Sketcher.Constraint('Diameter',i,geoList[i].Radius*2))
