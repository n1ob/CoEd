"""
   generated stubs with the help of https://github.com/ostr00000/freecad-stubs
   PyCharm stubs: see https://www.jetbrains.com/help/pycharm/stubs.html
"""
import logging
import os
import pathlib
import sys
import traceback

import FreeCAD as App
import FreeCADGui as Gui
from PySide2 import QtCore
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QWidget, QMessageBox, QApplication

from co_lib.co_base.co_cmn import wait_cursor
from co_lib.co_base.co_config import Cfg
from co_lib.co_base.co_logger import xps, xp, stack_tracer, xp_worker
from co_lib.co_gui import CoEdGui
from co_lib.co_impl import CoEd

try:
    from Sketcher import ActiveSketch
except ImportError:
    pass

# todo renaming constraints
#  set expression


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

    with wait_cursor():
        dir_ = os.path.dirname(os.path.abspath(__file__))
        pth = pathlib.Path(dir_, 'co_lib', 'co-orange.qss')
        with open(pth, "r") as fh:
            app.setStyleSheet(fh.read())
        # set_style(app)
        # set_palette(app)
        c = CoEd(sketch, dir_)
        ex: QWidget = CoEdGui(c)
        ed_info = Gui.ActiveDocument.InEditInfo
        xp('ed_info', ed_info)
        if ed_info is not None:
            if ed_info[0].TypeId == 'Sketcher::SketchObject':
                xp('lets show it')
                ex.show()
    return ex


xps(__name__)

if __name__ == '__main__':

    import Part
    from co_lib.co_base.co_observer import register, unregister


    def add_geo(o: object, b: bool = False):
        App.getDocument(DOC).getObject(SKETCH).addGeometry(o, b)


    def add_geo2(o: object):
        App.getDocument(DOC).getObject(SKETCH).addGeometry(o)

    def blubber():
        xps('about to quit')
        # exq.close()
        # exq.deleteLater()

    DOC = "Test"
    SKETCH = "Sketch"

    def app_state_chg(state):
        state: Qt.ApplicationState
        xps(state)

    try:
        app = QApplication()
        app.aboutToQuit.connect(blubber)
        app.applicationStateChanged.connect(app_state_chg)
        Gui.showMainWindow()
        # let's see what happens
        register()
        App.newDocument(DOC)
        Gui.activeDocument().activeView().viewDefaultOrientation()
        Gui.ActiveDocument.ActiveView.setAxisCross(True)
        Gui.activateWorkbench("SketcherWorkbench")
        App.activeDocument().addObject('Sketcher::SketchObject', SKETCH)
        App.activeDocument().Sketch.Placement = App.Placement(App.Vector(0.000000, 0.000000, 0.000000),
                                                              App.Rotation(0.000000, 0.000000, 0.000000, 1.000000))
        App.activeDocument().Sketch.MapMode = "Deactivated"
        Gui.activeDocument().setEdit(SKETCH)
        ActiveSketch = App.getDocument(DOC).getObject(SKETCH)
        App.getDocument(DOC).recompute()
        exq: QWidget = main_g(ActiveSketch, app)
        app.exec_()
    except:
        logging.error(traceback.format_exc())
        stack_tracer()
        raise


