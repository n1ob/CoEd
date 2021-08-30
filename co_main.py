"""
   generated stubs with the help of https://github.com/ostr00000/freecad-stubs
   PyCharm: see https://www.jetbrains.com/help/pycharm/stubs.html
"""
import os
import sys
import traceback

import FreeCAD as App
import FreeCADGui as Gui
from PySide2 import QtCore
from PySide2.QtCore import QFile
from PySide2.QtWidgets import QApplication, QWidget, QMessageBox

from co_config import Cfg
from co_logger import xps, xp, XpWriter, stack_tracer
from co_gui import CoEdGui
from co_impl import CoEd
from co_style import my_style, set_style, set_palette
from co_cmn import SketcherType

try:
    from Sketcher import ActiveSketch  # hack def in Sketcher.pyi, ActiveSketch is actually in the current local scope
except ImportError:
    pass


# def get_sketch() -> SketcherType:
#     active_workbench = Gui.activeWorkbench()  # StartGui::Workbench, SketcherGui::Workbench
#     if active_workbench.name() == 'SketcherWorkbench':
#         return ActiveSketch
#     else:
#         sel = Gui.Selection.getSelection()
#         if sel[0].TypeId == 'Sketcher::SketchObject':
#             return sel[0]

# ! don't need this for now
def detect_missing_pt_on_pt(snap_dist, sketch):
    print("\n>>>> detect_missing_pt_on_pt -----------------------------")
    s = str(sketch.detectMissingPointOnPointConstraints(snap_dist))
    print("snap: " + str(snap_dist) + "  detected: " + s)
    # id=GeoId, st=start(1), en=end(2), type(1)=coincident
    print("(id1, st/en, id2, st/en, type)")
    print("points" + str(sketch.MissingPointOnPointConstraints))
    print("<<<< detect_missing_pt_on_pt ------------------------------\n")

def main_g(sketch, app):

    if sketch is None:
        App.Console.PrintMessage("No active sketch!\n")
        dialog = QMessageBox(QMessageBox.Warning, 'No active sketch!', "There is no active sketch!")
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()
        sys.exit()

    xp('getcwd:      ', os.getcwd())
    xp('__file__:    ', __file__)
    xp('basename:    ', os.path.basename(__file__))
    xp('dirname:     ', os.path.dirname(__file__))
    xp('abspath:     ', os.path.abspath(__file__))
    xp('abs dirname: ', os.path.dirname(os.path.abspath(__file__)))
    xp('PYTHONPATH   ', os.environ['PYTHONPATH'])

    try:
        style_file = "C:\\Users\\red\PycharmProjects\\FreeCad\\co-orange.qss"
        with open(style_file, "r") as fh:
            app.setStyleSheet(fh.read())
        # set_style(app)
        # set_palette(app)
        c = CoEd(sketch)
        c.snap_dist = 1.01
        c.snap_angel = 5
        ex: QWidget = CoEdGui(c)
        ex.show()
        ex.tabs.setCurrentIndex(1)
        ex.tabs.setCurrentIndex(0)
    except Exception:
        stack_tracer()
        raise
    return ex

# def main_t(sketch: SketcherType = None):  # param used for unittest
#
#     if sketch is None:
#         App.Console.PrintMessage("No active sketch!\n")
#         dialog = QMessageBox(QMessageBox.Warning, 'No active sketch!', "There is no active sketch!")
#         dialog.setWindowModality(QtCore.Qt.ApplicationModal)
#         dialog.exec_()
#         # sketch = get_sketch()
#     else:
#         xp('getcwd:      ', os.getcwd())
#         xp('__file__:    ', __file__)
#         xp('basename:    ', os.path.basename(__file__))
#         xp('dirname:     ', os.path.dirname(__file__))
#         xp('abspath:     ', os.path.abspath(__file__))
#         xp('abs dirname: ', os.path.dirname(os.path.abspath(__file__)))
#         # app = QApplication(sys.argv)
#         app = QApplication()
#         Gui.showMainWindow()
#
#         try:
#             c = CoEd(sketch)
#             c.snap_dist = 1.01
#             c.snap_angel = 5
#             ex: QWidget = CoEdGui(c)
#             # my_style(app)
#             # set_style(app)
#             # set_palette(app)
#             ex.show()
#             # c.stuff()
#             # c.print_coincident_list()
#             # get TableWidget to update geometry
#             ex.tabs.setCurrentIndex(1)
#             ex.tabs.setCurrentIndex(0)
#             # app.exec_()
#             sys.exit(app.exec_())
#         finally:
#             Cfg().save()
#             pass

xps(__name__)
# detect_missing_pt_on_pt(c.snap_dist, sketch)
# App.ActiveDocument.recompute()

if __name__ == '__main__':
    pass

    # main_t()


# def makeDiameters(Sketch):
# 	'''diameter constraints for all circles'''
# 	geoList = Sketch.Geometry
# 	for i in range(Sketch.GeometryCount):
# 		if geoList[i].TypeId == 'Part::GeomCircle':
# 			Sketch.addConstraint(Sketcher.Constraint('Diameter',i,geoList[i].Radius*2))
