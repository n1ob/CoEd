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
from threading import Lock
from typing import List

import FreeCAD as App
import FreeCADGui as Gui
import Sketcher
from PySide2.QtCore import Slot, QItemSelectionModel, QModelIndex, Qt
from PySide2.QtWidgets import QWidget, QBoxLayout, QGroupBox, QTableWidget, QLabel, QDoubleSpinBox, QPushButton, \
    QVBoxLayout, QHBoxLayout, QTableWidgetItem, QHeaderView

from .co_hv import HvEdges, HvEdge
from .. import co_impl, co_gui
from ..co_base.co_cmn import wait_cursor, ColorTableItem, ObjType
from ..co_base.co_logger import flow, xp, _hv, _ev, xps
from ..co_base.co_lookup import Lookup
from ..co_base.co_observer import observer_block, observer_event_provider_get

_QL = QBoxLayout


class HvGui:
    def __init__(self, base):
        self.base: co_gui.CoEdGui = base
        self.sketch: Sketcher.SketchObject = self.base.sketch
        self.impl: co_impl.CoEd = self.base.base
        self.hv: HvEdges = self.impl.hv_edges
        self.tab_hv = QWidget(None)
        xp('hv.created.connect', **_ev)
        self.hv.created.connect(self.on_hv_create)
        xp('hv.creation_done.connect', **_ev)
        self.hv.creation_done.connect(self.on_hv_create_done)
        self.hv_grp_box: QGroupBox = QGroupBox(None)
        self.hv_lbl: QLabel = QLabel()
        self.hv_dbl_sp_box: QDoubleSpinBox = QDoubleSpinBox()
        self.hv_btn_create: QPushButton = QPushButton()
        self.hv_btn_create.setDisabled(True)
        self.hv_tbl_wid: QTableWidget = QTableWidget()
        self.tab_hv.setLayout(self.lay_get())
        self.evo = observer_event_provider_get()
        self.evo.in_edit.connect(self.on_in_edit)
        self.ctrl_up = None
        self.ctrl_lock = Lock()
        self.update_table()

    @flow
    def lay_get(self) -> QBoxLayout:
        self.hv_grp_box.setTitle(u"Horizontal/Vertical")
        self.hv_lbl.setText(u"Snap Angle")
        self.hv_dbl_sp_box = self.base.db_s_box_get(self.hv.tolerance, 1, 0.1, self.on_hv_tol_val_chg)
        self.hv_btn_create.clicked.connect(self.on_hv_create_btn_clk)
        self.hv_btn_create.setText(u"Create")
        self.hv_tbl_wid = self.prep_table(self.hv_grp_box)
        self.hv_tbl_wid.itemSelectionChanged.connect(self.on_hv_tbl_sel_chg)
        # noinspection PyArgumentList
        li = [QVBoxLayout(), self.hv_grp_box,
              [QVBoxLayout(self.hv_grp_box),
               [QHBoxLayout(), self.hv_lbl, self.hv_dbl_sp_box, _QL.addStretch, self.hv_btn_create],
               self.hv_tbl_wid]]
        return self.base.lay_get(li)

    @flow
    @Slot(object)
    def on_in_edit(self, obj):
        if obj.TypeId == ObjType.VIEW_PROVIDER_SKETCH:
            ed_info = Gui.ActiveDocument.InEditInfo
            if (ed_info is not None) and (ed_info[0].TypeId == ObjType.SKETCH_OBJECT):
                self.sketch = ed_info[0]

    @flow
    @Slot()
    def on_hv_create_done(self):
        xp('HV creation done', **_ev)

    @flow
    @Slot(str, int)
    def on_hv_create(self, typ: str, geo: int):
        xp('HV created', typ, geo, **_ev)

    @flow
    def on_hv_create_btn_clk(self):
        self.create()

    @flow
    def on_hv_tbl_sel_chg(self):
        self.selected()

    @flow
    def on_hv_tol_val_chg(self, val):
        value = self.hv_dbl_sp_box.value()
        self.hv.tolerance = value
        self.update_table()

    @flow
    def prep_table(self, obj: QGroupBox) -> QTableWidget:
        table_widget = QTableWidget(obj)
        table_widget.setColumnCount(3)
        w_item = QTableWidgetItem(u"Edge")
        table_widget.setHorizontalHeaderItem(1, w_item)
        w_item = QTableWidgetItem(u"Angle")
        table_widget.setHorizontalHeaderItem(2, w_item)
        self.base.prep_table(table_widget)
        return table_widget

    @flow
    def create(self):
        with wait_cursor():
            mod: QItemSelectionModel = self.hv_tbl_wid.selectionModel()
            rows: List[QModelIndex] = mod.selectedRows(0)
            create_list: List[HvEdge] = [x.data(Qt.UserRole) for x in rows]
            for idx in rows:
                xp('row', idx.row(), ':', idx.data(Qt.UserRole), **_hv)
            res = list()
            # filter extern
            for x in create_list:
                if not x.extern:
                    res.append(x)
            self.hv.create(res)
        self.update_table()

    @flow
    def task_up(self, hv):
        edge_list: List[HvEdge] = self.hv.tolerances
        cs_v, cs_h = self.hv.cons_get()
        return edge_list, cs_v, cs_h

    @flow(short=True)
    def on_result_up(self, result):
        self.hv_btn_create.setDisabled(False)
        self.hv_tbl_wid.setUpdatesEnabled(False)
        self.hv_tbl_wid.setRowCount(0)
        __sorting_enabled = self.hv_tbl_wid.isSortingEnabled()
        self.hv_tbl_wid.setSortingEnabled(False)
        edge_list, cs_v, cs_h = result
        res_lst: List[HvEdge] = list()
        for edge in edge_list:
            if edge.cons_filter(cs_v.union(cs_h)):
                res_lst.append(edge)
        for idx, item in enumerate(res_lst):
            self.hv_tbl_wid.insertRow(0)
            w_item2 = QTableWidgetItem()
            w_item2.setData(Qt.UserRole, item)
            self.hv_tbl_wid.setItem(0, 0, w_item2)

            t = Lookup.translate_ui_name(item.geo_idx)
            fmt = f"{t}"
            w_item = ColorTableItem(item.construct, item.extern, fmt)
            self.hv_tbl_wid.setItem(0, 1, w_item)

            fmt = "xa {:.1f} ya {:.1f}".format(item.x_angel, item.y_angel)
            w_item = ColorTableItem(item.construct, item.extern, fmt)
            w_item.setTextAlignment(Qt.AlignCenter)
            self.hv_tbl_wid.setItem(0, 2, w_item)

        self.hv_tbl_wid.setSortingEnabled(__sorting_enabled)
        hh: QHeaderView = self.hv_tbl_wid.horizontalHeader()
        hh.resizeSections(QHeaderView.ResizeToContents)
        self.hv_tbl_wid.setUpdatesEnabled(True)

    @flow
    def update_table(self):
        # self.ctrl_up = Controller(Worker(self.task_up, self.hv), self.on_result_up, name='HorizontalVertical')
        res = self.task_up(self.hv)
        self.on_result_up(res)

    @flow
    def selected(self):
        indexes: List[QModelIndex] = self.hv_tbl_wid.selectionModel().selectedRows(0)
        rows: List = [x.row() for x in sorted(indexes)]
        xp(f'selected: {rows}', **_hv)
        # not on extern
        show: bool = False
        for item in indexes:
            hv: HvEdge = item.data(Qt.UserRole)
            if not hv.extern:
                show = True
        if show:
            self.hv_btn_create.setDisabled(False)
        else:
            self.hv_btn_create.setDisabled(True)
        doc_name = App.activeDocument().Name
        with observer_block():
            Gui.Selection.clearSelection(doc_name, True)
        ed_info = Gui.ActiveDocument.InEditInfo
        sk_name = ed_info[0].Name
        for item in indexes:
            hv: HvEdge = item.data(Qt.UserRole)
            xp(f'row: {str(item.row())} idx: {hv.geo_idx} cons: {hv}', **_hv)
            t = Lookup.translate_ui_name(hv.geo_idx, False)
            Gui.Selection.addSelection(doc_name, sk_name, f'{t}')


xps(__name__)
