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
from typing import List, Tuple, Set

import FreeCAD as App
import FreeCADGui as Gui
from PySide2.QtCore import QItemSelectionModel, QModelIndex, Qt, Slot
from PySide2.QtWidgets import QWidget, QGroupBox, QPushButton, QTableWidget, QBoxLayout, QVBoxLayout, \
    QHBoxLayout, QLabel, QDoubleSpinBox, QTableWidgetItem, QHeaderView

from .co_pa import PaEdges, PaEdge, GeoDiff
from .. import co_impl, co_gui
from ..co_base.co_cmn import wait_cursor, TableLabel, ColorTableItem
from ..co_base.co_logger import xp, flow, _pa, _ev, xps
from ..co_base.co_lookup import Lookup
from ..co_base.co_observer import observer_block

_QL = QBoxLayout


class PaGui:
    def __init__(self, base):
        self.base: co_gui.CoEdGui = base
        # self.sketch: Sketcher.SketchObject = self.base.sketch
        self.impl: co_impl.CoEd = self.base.base
        self.pa: PaEdges = self.impl.pa_edges
        self.tab_pa = QWidget(None)
        xp('eq.created.connect', **_ev)
        self.pa.created.connect(self.on_pa_created)
        xp('eq.creation_done.connect', **_ev)
        self.pa.creation_done.connect(self.on_pa_create_done)
        self.pa_grp_box: QGroupBox = QGroupBox(None)
        self.pa_lbl: QLabel = QLabel()
        self.pa_dbl_sp_box: QDoubleSpinBox = QDoubleSpinBox()
        self.pa_btn_create: QPushButton = QPushButton()
        self.pa_btn_create.setDisabled(True)
        self.pa_tbl_wid: QTableWidget = QTableWidget()
        self.tab_pa.setLayout(self.lay_get())
        self.ctrl_up = None
        self.ctrl_lock = Lock()
        self.update_table()

    @flow
    def lay_get(self) -> QBoxLayout:
        self.pa_grp_box.setTitle(u"Parallel")
        self.pa_lbl.setText(u"Tolerance")
        self.pa_dbl_sp_box = self.base.db_s_box_get(self.pa.tolerance, 1, 0.1, self.on_pa_tol_val_chg)
        self.pa_btn_create.clicked.connect(self.on_pa_create_btn_clk)
        self.pa_btn_create.setText(u"Create")
        self.pa_tbl_wid = self.prep_table(self.pa_grp_box)
        self.pa_tbl_wid.itemSelectionChanged.connect(self.on_pa_tbl_sel_chg)
        # noinspection PyArgumentList
        li = [QVBoxLayout(), self.pa_grp_box,
              [QVBoxLayout(self.pa_grp_box),
               [QHBoxLayout(), self.pa_lbl, self.pa_dbl_sp_box, _QL.addStretch, self.pa_btn_create],
               self.pa_tbl_wid]]
        return self.base.lay_get(li)

    @flow
    @Slot(int, int)
    def on_pa_created(self, i, j):
        xp('Pa created', i, j, **_ev)

    @flow
    @Slot()
    def on_pa_create_done(self):
        xp('Pa creation done', **_ev)

    @flow
    def on_pa_create_btn_clk(self):
        self.create()

    @flow
    def on_pa_tbl_sel_chg(self):
        self.selected()

    @flow
    def on_pa_tol_val_chg(self, val):
        value = self.pa_dbl_sp_box.value()
        self.pa.tolerance = value
        self.update_table()

    @flow
    def prep_table(self, obj: QGroupBox) -> QTableWidget:
        table_widget = QTableWidget(obj)
        table_widget.setColumnCount(3)
        w_item = QTableWidgetItem(u"Type")
        table_widget.setHorizontalHeaderItem(1, w_item)
        w_item = QTableWidgetItem(u"Info")
        table_widget.setHorizontalHeaderItem(2, w_item)
        self.base.prep_table(table_widget)
        return table_widget

    @flow
    def create(self):
        with wait_cursor():
            mod: QItemSelectionModel = self.pa_tbl_wid.selectionModel()
            rows: List[QModelIndex] = mod.selectedRows(0)
            create_list: List[PaEdge] = [x.data() for x in rows]
            for idx in rows:
                xp('row', idx.row(), ':', idx.data(), **_pa)
            self.pa.create(create_list)
        self.update_table()

    @flow
    def task_up(self, pa):
        edge_list: List[PaEdge] = self.pa.tolerances
        cs: Set[Tuple[int, int]] = self.pa.cons_get()
        return edge_list, cs

    @flow(short=True)
    def on_result_up(self, result):
        self.pa_tbl_wid.setUpdatesEnabled(False)
        self.pa_tbl_wid.setRowCount(0)
        __sorting_enabled = self.pa_tbl_wid.isSortingEnabled()
        self.pa_tbl_wid.setSortingEnabled(False)
        edge_list, cs = result
        res_lst: List[PaEdge] = list()
        for edge in edge_list:
            ed = PaEdge(edge.geo_idx, edge.y_angel, edge.pt_start, edge.pt_end, edge.construct, edge.extern)
            ed.edg_differences = edge.cons_filter(cs)
            res_lst.append(ed)
        for idx, item in enumerate(res_lst):
            if self.base.cfg_only_valid and (len(item.edg_differences) == 0):
                continue
            self.pa_tbl_wid.insertRow(0)
            w_item2 = QTableWidgetItem()
            w_item2.setData(Qt.DisplayRole, item)
            self.pa_tbl_wid.setItem(0, 0, w_item2)

            t = Lookup.translate_ui_name(item.geo_idx)
            fmt = f"{t} {item.y_angel:.1f}"
            w_item = ColorTableItem(item.construct, item.extern, fmt)
            self.pa_tbl_wid.setItem(0, 1, w_item)

            sn, sc, se = self.split(item)
            xp('norm', sn, 'const', sc, 'extern', se, **_pa)
            wid = TableLabel(sn, sc, se)
            self.pa_tbl_wid.setCellWidget(0, 2, wid)
        self.pa_tbl_wid.setSortingEnabled(__sorting_enabled)
        hh: QHeaderView = self.pa_tbl_wid.horizontalHeader()
        hh.resizeSections(QHeaderView.ResizeToContents)
        self.pa_tbl_wid.setUpdatesEnabled(True)

    def split(self, pt: PaEdge):
        res_n = list()
        res_c = list()
        res_e = list()
        for x in pt.edg_differences:
            x: GeoDiff
            t = Lookup.translate_geo_idx(x.geo_idx)
            s = f'{t}({x.difference:.2f})'
            if x.extern:
                res_e.append(s)
            elif x.construct:
                res_c.append(s)
            else:
                res_n.append(s)
        return ' '.join(res_n), ' '.join(res_c), ' '.join(res_e)

    @flow
    def update_table(self):
        # self.ctrl_up = Controller(Worker(self.task_up, self.pa), self.on_result_up, name='Parallel')
        res = self.task_up(self.pa)
        self.on_result_up(res)

    @flow
    def selected(self):
        indexes: List[QModelIndex] = self.pa_tbl_wid.selectionModel().selectedRows(0)
        rows: List = [x.row() for x in sorted(indexes)]
        xp(f'selected: {rows}', **_pa)
        if len(rows) == 0:
            self.pa_btn_create.setDisabled(True)
        else:
            self.pa_btn_create.setDisabled(False)
        doc_name = App.activeDocument().Name
        with observer_block():
            Gui.Selection.clearSelection(doc_name, True)
        ed_info = Gui.ActiveDocument.InEditInfo
        sk_name = ed_info[0].Name
        for item in indexes:
            pa: PaEdge = item.data()
            xp(f'row: {str(item.row())} idx: {pa.geo_idx} len: {pa.y_angel:.2f} {pa.edg_differences}', **_pa)
            t = Lookup.translate_ui_name(pa.geo_idx, False)
            Gui.Selection.addSelection(doc_name, sk_name, f'{t}')
            for diff in pa.edg_differences:
                t = Lookup.translate_ui_name(diff.geo_idx, False)
                Gui.Selection.addSelection(doc_name, sk_name, f'{t}')


xps(__name__)
