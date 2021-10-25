import FreeCAD as App
import FreeCADGui as Gui
import Sketcher
from PySide2.QtCore import QObject, Slot
from PySide2.QtWidgets import QBoxLayout, QWidget, QPlainTextEdit, QPushButton, QVBoxLayout, QHBoxLayout

from co_lib.co_base.co_cmn import Controller, Worker, ObjType
from co_lib.co_base.co_lookup import Lookup
from co_lib.co_base.co_observer import observer_block, observer_event_provider_get
from .. import co_impl, co_gui
from ..co_base.co_logger import flow, xp, _tr
from ..co_base.co_style import XMLHighlighter

_QL = QBoxLayout


class GeoGui(QObject):
    def __init__(self, base):
        super().__init__()
        self.base: co_gui.CoEdGui = base
        self.sketch: Sketcher.SketchObject = self.base.sketch
        self.impl: co_impl.CoEd = self.base.base
        self.tab_geo = QWidget(None)
        self.geo_txt_edt = QPlainTextEdit()
        self.geo_btn_geo = QPushButton('Geo')
        self.geo_btn_ext = QPushButton('Ext')
        self.geo_btn_vert = QPushButton('Open Vert')
        self.tab_geo.setLayout(self.geo_lay_get())
        self.evo = observer_event_provider_get()
        self.evo.in_edit.connect(self.on_in_edit)
        self.controller_ext = None
        self.controller_geo = None

    @flow
    def geo_lay_get(self) -> QBoxLayout:
        self.geo_txt_edt.setFont(self.base.geo_edt_font)
        self.geo_txt_edt.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.geo_txt_edt.highlighter = XMLHighlighter(self.geo_txt_edt.document())
        self.geo_txt_edt.setPlainText(self.impl.geo_xml_get())
        self.geo_btn_geo.clicked.connect(self.on_geo_btn_clk_geo)
        self.geo_btn_ext.clicked.connect(self.on_geo_btn_clk_ext)
        self.geo_btn_vert.clicked.connect(self.on_geo_btn_clk_vert)
        lis = [QVBoxLayout(),
               self.geo_txt_edt,
               [QHBoxLayout(), self.geo_btn_vert, _QL.addStretch, self.geo_btn_geo, (_QL.addSpacing, 20), self.geo_btn_ext]]
        return self.base.lay_get(lis)

    @flow
    def task_ext(self, impl):
        xp('task_ext', **_tr)
        impl.analyse_sketch()
        return impl.sketch_info_xml_get()

    @flow
    @Slot(object)
    def on_in_edit(self, obj):
        if obj.TypeId == ObjType.VIEW_PROVIDER_SKETCH:
            ed_info = Gui.ActiveDocument.InEditInfo
            if (ed_info is not None) and (ed_info[0].TypeId == ObjType.SKETCH_OBJECT):
                self.sketch = ed_info[0]

    @flow(short=True)
    def on_result_ext(self, result):
        xp('on_result_ext', **_tr)
        self.geo_txt_edt.setPlainText(result)
        self.geo_btn_ext.setDisabled(False)

    @flow
    def on_geo_btn_clk_ext(self):
        self.geo_btn_ext.setDisabled(True)
        self.controller_ext = Controller(Worker(self.task_ext, self.impl), self.on_result_ext, 'GeoExtended')

    @flow
    def task_geo(self, impl):
        xp('task_geo', **_tr)
        return impl.geo_xml_get()

    @flow(short=True)
    def on_result_geo(self, result):
        xp('on_result_geo', **_tr)
        self.geo_txt_edt.setPlainText(result)
        self.geo_btn_geo.setDisabled(False)

    @flow
    def on_geo_btn_clk_geo(self):
        self.geo_btn_geo.setDisabled(True)
        self.controller_geo = Controller(Worker(self.task_geo, self.impl), self.on_result_geo, 'Geometry')

    @flow
    def on_geo_btn_clk_vert(self):
        lo = Lookup(self.sketch)
        ls = lo.open_vertices()
        doc_name = App.activeDocument().Name
        with observer_block():
            Gui.Selection.clearSelection(doc_name, True)
        ed_info = Gui.ActiveDocument.InEditInfo
        sk_name = ed_info[0].Name
        for x in ls:
            Gui.Selection.addSelection(doc_name, sk_name, x)


if __name__ == '__main__':
    pass

