"""
   generated stubs with the help of https://github.com/ostr00000/freecad-stubs
   PyCharm stubs: see https://www.jetbrains.com/help/pycharm/stubs.html
"""
import os
import pathlib

import FreeCAD as App
import FreeCADGui as Gui
from PySide2 import QtCore
from PySide2.QtWidgets import QMessageBox, QWidget, QApplication

from co_lib.co_base.co_cmn import wait_cursor
from co_lib.co_base.co_config import Cfg
from co_lib.co_base.co_logger import xp, stack_tracer
from co_lib.co_base.co_observer import register, unregister
from co_lib.co_gui import CoEdGui
from co_lib.co_impl import CoEd


def show_hint():
    App.Console.PrintMessage("No active sketch!\n")
    dialog = QMessageBox(QMessageBox.Warning, 'No active sketch!', "There is no active sketch!")
    dialog.setWindowModality(QtCore.Qt.ApplicationModal)
    dialog.exec_()


if App.activeDocument():

    xp('getcwd:      ', os.getcwd())
    xp('__file__:    ', __file__)
    xp('basename:    ', os.path.basename(__file__))
    xp('dirname:     ', os.path.dirname(__file__))
    xp('abspath:     ', os.path.abspath(__file__))
    xp('abs dirname: ', os.path.dirname(os.path.abspath(__file__)))
    # xp('PYTHONPATH   ', os.environ['PYTHONPATH'])

    try:
        app: QApplication = QApplication.instance()
        ad: App.Document = App.activeDocument()
        xp('activeWorkbench.name', Gui.activeWorkbench().name())
        xp('findObjects', ad.findObjects('Sketcher::SketchObject'))
        with wait_cursor():
            register()
            dir_ = os.path.dirname(os.path.abspath(__file__))
            pth = pathlib.Path(dir_, 'co_lib', 'co-orange.qss')
            # with open(pth, "r") as fh:
            #     app.setStyleSheet(fh.read())
            # set_style(app)
            # set_palette(app)
            c = CoEd(ActiveSketch, dir_)
            ex: QWidget = CoEdGui(c)
            ed_info = Gui.ActiveDocument.InEditInfo
            xp('ed_info', ed_info)
            if ed_info and ed_info[0].TypeId == 'Sketcher::SketchObject':
                xp('lets show it')
                ex.show()
            else:
                show_hint()
            Cfg().save()
            unregister()  # Uninstall the resident function

    except Exception:
        stack_tracer()
        raise
else:
    show_hint()
