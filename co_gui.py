from typing import List, Dict, Tuple, Callable

import FreeCAD as App
from PySide2.QtCore import Qt, Slot
from PySide2.QtWidgets import QComboBox, QWidget, QVBoxLayout, QPlainTextEdit, QApplication, QPushButton, \
    QTabWidget, QLabel, QTableWidget, QSpinBox, \
    QAbstractItemView, QHeaderView, QGroupBox, QDoubleSpinBox, QCheckBox, QBoxLayout, QLineEdit

from co_cfg_gui import CfgGui
from co_co_gui import CoGui
from co_cs_gui import CsGui
from co_eq_gui import EqGui
from co_geo_gui import GeoGui
from co_hv_gui import HvGui
from co_impl import CoEd
from co_logger import xp, flow, _ly, xps, _fl, _ob_s
from co_observer import observer_event_provider_get
from co_pa_gui import PaGui
from co_rd_gui import RdGui
from co_style import my_style
from co_xy_gui import XyGui

_QL = QBoxLayout


# noinspection PyArgumentList
class CoEdGui(QWidget):

    @flow(short=True)
    def __init__(self, base: CoEd, parent=None):
        super().__init__(parent)
        self.base: CoEd = base
        self.evo = observer_event_provider_get()
        self.evo.add_selection.connect(self.on_add_selection)
        self.evo.clear_selection.connect(self.on_clear_selection)
        self.cfg_blubber: bool = True
        flags: Qt.WindowFlags = Qt.Window
        flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.resize(600, 800)
        self.tbl_font = None
        self.geo_edt_font = None
        self.cfg_edt_font = None
        self.cfg_gui = CfgGui(self)
        self.geo_gui = GeoGui(self)
        self.cs_gui = CsGui(self)
        self.eq_gui = EqGui(self)
        self.co_gui = CoGui(self)
        self.hv_gui = HvGui(self)
        self.xy_gui = XyGui(self)
        self.rd_gui = RdGui(self)
        self.pa_gui = PaGui(self)
        self.tabs = QTabWidget(None)
        self.tabs.addTab(self.cs_gui.tab_cs, "Cs")
        self.tabs.addTab(self.co_gui.tab_co, "Co")
        self.tabs.addTab(self.hv_gui.tab_hv, "HV")
        self.tabs.addTab(self.rd_gui.tab_rd, "Rd")
        self.tabs.addTab(self.xy_gui.tab_xy, "XY")
        self.tabs.addTab(self.eq_gui.tab_eq, "Eq")
        self.tabs.addTab(self.pa_gui.tab_pa, "Pa")
        self.tabs.addTab(self.geo_gui.tab_geo, "Geo")
        self.tabs.addTab(self.cfg_gui.tab_cfg, "Cfg")
        self.tabs.currentChanged.connect(self.on_cur_tab_chg)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)
        self.setWindowTitle("MyCoEd")

    @staticmethod
    def db_s_box_get(val, prec, step, func):
        sb = QDoubleSpinBox(None)
        sb.setDecimals(prec)
        sb.setSingleStep(step)
        sb.setValue(val)
        sb.valueChanged.connect(func)
        return sb

    def lay_get(self, obj_list: List) -> QBoxLayout:
        w_list = [QPushButton, QDoubleSpinBox, QTableWidget, QGroupBox, QComboBox, QSpinBox, QPlainTextEdit, QLineEdit]
        layout = None
        for obj in obj_list:
            xp(type(obj).__name__, obj, **_ly)
            if isinstance(obj, QBoxLayout):
                xp('   layout:', **_ly)
                layout = obj
            elif isinstance(obj, list):
                xp('   list:', **_ly)
                layout.addLayout(self.lay_get(obj))
            elif type(obj).__name__ == 'tuple':
                func, param = obj
                xp('   tuple:', func.__name__, param, **_ly)
                if func.__name__ == 'addSpacing':
                    getattr(layout, func.__name__)(param)
            elif type(obj).__name__ == 'method_descriptor':
                xp('   method:', obj.__name__, **_ly)
                if obj.__name__ == 'addStretch':
                    getattr(layout, obj.__name__)()
                else:
                    getattr(layout, obj.__name__)()
            elif isinstance(obj, QCheckBox) or isinstance(obj, QLabel):
                layout.addWidget(obj, 0, Qt.AlignLeft)
            elif any(isinstance(obj, x) for x in w_list):
                layout.addWidget(obj)
            else:
                xp('------ UNEXPECTED OBJECT ----------', obj, **_ly)
        return layout

    # -------------------------------------------------------------------------
    @flow
    @Slot(object, object, object, object)
    def on_add_selection(self, doc, obj, sub, pnt):
        xp(f'on_add_selection: doc:', str(doc), 'obj: ', str(obj), 'sub: ', str(sub), 'pnt: ', str(pnt), **_ob_s)
        self.tbl_clear_select_on_add(sub, pnt)

    @flow
    @Slot(object)
    def on_clear_selection(self, doc):
        xp(f'on_clear_selection: doc:', str(doc), **_ob_s)
        self.tbl_clear_select()

    @flow
    def on_cur_tab_chg(self, index: int):
        xp('cur_tab:', index, **_ly)
        info: Dict[int, Tuple[QTableWidget, Callable]] = {
            0: (self.cs_gui.cons_tbl_wid, self.cs_gui.update_table),
            1: (self.co_gui.co_tbl_wid, self.co_gui.update_table),
            2: (self.hv_gui.hv_tbl_wid, self.hv_gui.update_table),
            3: (self.rd_gui.rad_tbl_wid, self.rd_gui.update_table),
            4: (self.xy_gui.xy_tbl_wid, self.xy_gui.update_table),
            5: (self.eq_gui.eq_tbl_wid, self.eq_gui.update_table),
            6: (self.pa_gui.pa_tbl_wid, self.pa_gui.update_table),
        }
        if index in range(7):
            tbl = info.get(index)[0]
            tbl.blockSignals(True)
            tbl.clearSelection()
            tbl.blockSignals(False)
            info.get(index)[1]()

    def tbl_clear_select(self):
        switcher: Dict[int, QTableWidget] = {
            0: self.cs_gui.cons_tbl_wid,
            1: self.co_gui.co_tbl_wid,
            2: self.hv_gui.hv_tbl_wid,
            3: self.rd_gui.rad_tbl_wid,
            4: self.xy_gui.xy_tbl_wid,
            5: self.eq_gui.eq_tbl_wid,
            6: self.pa_gui.pa_tbl_wid
        }
        for tbl in switcher.values():
            tbl.blockSignals(True)
            tbl.clearSelection()
            tbl.blockSignals(False)

    @flow
    def tbl_clear_select_on_add(self, shape, pnt):
        from_gui: bool = True
        if App.Vector(pnt) == App.Vector(0, 0, 0):
            from_gui = False
        if from_gui:
            self.tbl_clear_select()

        if shape.find('Vertex') != -1:
            no = int(shape[6:])
            typ = 'Vertex'
            geo, pos = self.base.sketch.getGeoVertexIndex(no)
            xp(f'received: gui: {from_gui} {typ} {no} geo: ({geo}.{pos})', **_fl)
        elif shape.find('Edge') != -1:
            no = int(shape[4:])
            typ = 'Edge'
            xp(f'received: gui: {from_gui} {typ} {no}', **_fl)
        elif shape.find('Constraint') != -1:
            no = int(shape[10:])
            typ = 'Constraint'
            xp(f'received: gui: {from_gui} {typ} {no}', **_fl)
        else:
            xp(f'received ?: gui: {from_gui} {shape} {pnt}', **_fl)

    @flow
    def prep_table(self, tbl: QTableWidget):
        tbl.horizontalHeader().setVisible(True)
        tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        tbl.setColumnHidden(2, True)
        tbl.sortItems(0, Qt.AscendingOrder)
        tbl.setSortingEnabled(True)
        hh: QHeaderView = tbl.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Interactive)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.Fixed)
        vh: QHeaderView = tbl.verticalHeader()
        # noinspection PyArgumentList
        vh.setSectionResizeMode(QHeaderView.Interactive)
        vh.setMaximumSectionSize(80)
        tbl_style = "QTableView::item {" \
                    "padding-left: 10px; " \
                    "padding-right: 10px; " \
                    "border: none; " \
                    "}"
        tbl.setStyleSheet(tbl_style)
        tbl.setFont(self.tbl_font)


xps(__name__)
if __name__ == '__main__':
    import sys

    app = QApplication()
    my_style(app)
    controller = CoEdGui()
    controller.show()
    sys.exit(app.exec_())
