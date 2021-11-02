# ***************************************************************************
# *   Copyright (c) 2021 n1ob <niob@gmx.com>                                *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# ***************************************************************************
from typing import List, Dict, Tuple, Callable

import FreeCAD as App
import FreeCADGui as Gui
import Sketcher
from PySide2.QtCore import Qt, Slot, QTimer, QSettings
from PySide2.QtGui import QFont, QColor
from PySide2.QtWidgets import QComboBox, QWidget, QVBoxLayout, QPlainTextEdit, QPushButton, \
    QTabWidget, QLabel, QTableWidget, QSpinBox, \
    QAbstractItemView, QHeaderView, QGroupBox, QDoubleSpinBox, QCheckBox, QBoxLayout, QLineEdit

from co_lib.co_base.co_cmn import ObjType
from co_lib.co_base.co_config import Cfg, CfgTransient
from co_lib.co_base.co_lookup import Lookup
from .co_base.co_logger import xp, flow, _ly, xps, _fl, _ob_s, _ob_a, stack_tracer, xp_worker, _ob_g
from .co_base.co_observer import observer_event_provider_get, unregister
from .co_impl import CoEd
from .co_tabs.co_cfg_gui import CfgGui
from .co_tabs.co_co_gui import CoGui
from .co_tabs.co_cs_gui import CsGui
from .co_tabs.co_eq_gui import EqGui
from .co_tabs.co_geo_gui import GeoGui
from .co_tabs.co_hv_gui import HvGui
from .co_tabs.co_pa_gui import PaGui
from .co_tabs.co_rd_gui import RdGui
from .co_tabs.co_xy_gui import XyGui

_QL = QBoxLayout


class SkHint(QWidget):
    def __init__(self):
        super().__init__()
        flags: Qt.WindowFlags = Qt.Window
        flags |= Qt.WindowStaysOnTopHint
        flags |= Qt.FramelessWindowHint
        self.setWindowFlags(flags)
        self.label = QLabel(self)
        font: QFont = self.label.font()
        i = font.pointSize()
        font.setPointSize(i+2)
        self.label.setFont(font)
        self.label.setText('No active sketch')
        self.label.adjustSize()
        self.label.setAlignment(Qt.AlignCenter)


# noinspection PyArgumentList
class CoEdGui(QWidget):
    @flow(short=True)
    def __init__(self, base: CoEd, exit: bool, parent=None):
        super().__init__(parent)
        self.base: CoEd = base
        self.exit = exit
        self.sketch: Sketcher.SketchObject = self.base.sketch
        self.evo = observer_event_provider_get()
        self.evo.add_selection.connect(self.on_add_selection)
        self.evo.clear_selection.connect(self.on_clear_selection)
        self.evo.open_transact.connect(self.on_open_transact)
        self.evo.commit_transact.connect(self.on_commit_transact)
        self.evo.undo_doc.connect(self.on_undo_doc)
        self.evo.obj_recomputed.connect(self.on_obj_recomputed)
        self.cfg_only_valid: bool = True
        flags: Qt.WindowFlags = Qt.Window
        flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.resize(600, 800)
        self.tbl_font = None
        self.geo_edt_font = None
        self.cfg_edt_font = None
        self.construct_color: QColor = QColor()
        self.extern_color: QColor = QColor()
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
        self.info: Dict[int, Tuple[QTableWidget, Callable]] = {
            0: (self.cs_gui.cons_tbl_wid, self.cs_gui.update_table),
            1: (self.co_gui.co_tbl_wid, self.co_gui.update_table),
            2: (self.hv_gui.hv_tbl_wid, self.hv_gui.update_table),
            3: (self.rd_gui.rad_tbl_wid, self.rd_gui.update_table),
            4: (self.xy_gui.xy_tbl_wid, self.xy_gui.update_table),
            5: (self.eq_gui.eq_tbl_wid, self.eq_gui.update_table),
            6: (self.pa_gui.pa_tbl_wid, self.pa_gui.update_table),
            7: (None, None),
            8: (None, None),
        }
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)
        self.setWindowTitle("MyCoEd")
        self.evo.in_edit.connect(self.on_in_edit)
        self.evo.reset_edit.connect(self.on_reset_edit)
        self.sk_hint = None
        self.sk_hint_tim = QTimer()
        self.sk_hint_tim.setSingleShot(True)
        self.sk_hint_tim.timeout.connect(self.on_timer)
        cfg = CfgTransient()
        geo = cfg.get(cfg.GEOMETRY)
        if geo:
            self.restoreGeometry(geo)

    def closeEvent(self, event):
        super().closeEvent(event)
        if not self.cs_gui.ext_toggle:
            self.cs_gui.on_cons_ext_btn_clk()
        cfg = CfgTransient()
        cfg.set(cfg.GEOMETRY, self.saveGeometry())
        Cfg().save()
        unregister()  # Uninstall the resident function
        xp_worker.keep_running = False
        if self.exit:
            exit(0)

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
    @Slot(object, str)
    def on_open_transact(self, doc, name):
        xp(f'NOP on_open_transact doc: {doc} name: {name}', **_ob_s)

    @flow
    @Slot(object, str)
    def on_commit_transact(self, doc, name):
        xp(f'on_commit_transact doc: {doc} name: {name}', **_ob_s)
        if 'coed' in name:
            xp('ignore own', **_ob_s)
        else:
            self.up_cur_table()

    @flow
    @Slot(object)
    def on_undo_doc(self, doc):
        xp(f'on_undo_doc doc: {doc}', **_ob_a)
        if doc.TypeId == 'App::Document':
            doc: App.Document
            if doc.ActiveObject.TypeId == ObjType.SKETCH_OBJECT:
                self.base.flags.all()
                self.up_cur_table()

    @flow
    @Slot(object)
    def on_in_edit(self, obj):
        xp('on_in_edit', obj, obj.TypeId, **_ob_g)
        if obj.TypeId == ObjType.VIEW_PROVIDER_SKETCH:
            ed_info = Gui.ActiveDocument.InEditInfo
            xp('ed_info', ed_info, **_ob_g)
            if (ed_info is not None) and (ed_info[0].TypeId == ObjType.SKETCH_OBJECT):
                xp('ed_info[0]', id(ed_info[0]), 'self.sketch', id(self.sketch), **_ob_g)
                xp('self.sketch is ed_info', self.sketch is ed_info[0], **_ob_g)
                if self.sketch is not ed_info[0]:
                    self.up_cur_table()
            # self.show()
            self.showNormal()

    @flow
    @Slot(object)
    def on_reset_edit(self, obj):
        xp('on_reset_edit', obj, obj.TypeId, **_ob_g)
        ed_info = Gui.ActiveDocument.InEditInfo
        xp('ed_info', ed_info, **_ob_g)
        if obj.TypeId == ObjType.VIEW_PROVIDER_SKETCH:
            # self.hide()
            self.showMinimized()
            self.sk_hint = SkHint()
            pos = self.sk_hint.pos()
            if pos.x() < 0:
                pos.setX(0)
            if pos.y() < 0:
                pos.setY(0)
            self.sk_hint.move(pos)
            self.sk_hint.show()
            self.sk_hint_tim.start(3000)

    @flow
    @Slot(object)
    def on_obj_recomputed(self, obj):
        xp(f'NOP on_obj_recomputed obj:', str(obj), **_ob_s)

    @flow
    @Slot()
    def on_timer(self):
        if self.sk_hint is not None:
            self.sk_hint: SkHint
            self.sk_hint.close()

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
    def up_cur_table(self):
        try:
            tbl_idx = self.tabs.currentIndex()
            if tbl_idx in range(7):
                self.info.get(tbl_idx)[1]()
        except Exception as ex:
            xp(ex)
            stack_tracer()
            raise

    @flow
    def on_cur_tab_chg(self, index: int):
        xp('cur_tab:', index, **_ly)
        if index in range(7):
            tbl = self.info.get(index)[0]
            tbl.blockSignals(True)
            tbl.clearSelection()
            tbl.blockSignals(False)
            self.info.get(index)[1]()

    @flow
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
        for tbl in self.info.values():
            if tbl[0] is None:
                continue
            tbl[0].blockSignals(True)
            tbl[0].clearSelection()
            tbl[0].blockSignals(False)

    @flow
    def tbl_clear_select_on_add(self, shape, pnt):
        from_gui: bool = True
        if App.Vector(pnt) == App.Vector(0, 0, 0):
            from_gui = False
        if from_gui:
            self.tbl_clear_select()
        typ, no = Lookup.deconstruct_ui_name(shape)
        if typ == 'Vertex':
            geo, pos = self.sketch.getGeoVertexIndex(no)
            xp(f'received: gui: {from_gui} {typ} {no} geo: ({geo}.{pos})', **_fl)
        else:
            xp(f'received: gui: {from_gui} {typ} {no}', **_fl)

    @flow
    def prep_table(self, tbl: QTableWidget):
        tbl.horizontalHeader().setVisible(True)
        tbl.verticalHeader().setVisible(False)
        tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        tbl.setColumnHidden(0, True)
        tbl.sortItems(1, Qt.AscendingOrder)
        tbl.setSortingEnabled(True)
        hh: QHeaderView = tbl.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Fixed)
        hh.setSectionResizeMode(1, QHeaderView.Interactive)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
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
    pass
