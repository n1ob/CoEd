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

from .co_eq import EqEdges, EqEdge, GeoDiff
from .. import co_impl, co_gui
from ..co_base.co_cmn import wait_cursor, TableLabel, ColorTableItem, ObjType
from ..co_base.co_config import CfgTransient
from ..co_base.co_logger import xp, flow, _eq, _ev, xps
from ..co_base.co_lookup import Lookup
from ..co_base.co_observer import observer_block, observer_event_provider_get

_QL = QBoxLayout


class EqGui:
    def __init__(self, base):
        self.base: co_gui.CoEdGui = base
        # self.sketch: Sketcher.SketchObject = self.base.sketch
        self.impl: co_impl.CoEd = self.base.base
        self.eq: EqEdges = self.impl.eq_edges
        self.tab_eq = QWidget(None)
        xp('eq.created.connect', **_ev)
        self.eq.created.connect(self.on_eq_created)
        xp('eq.creation_done.connect', **_ev)
        self.eq.creation_done.connect(self.on_eq_create_done)
        self.cfg = CfgTransient()
        self.evo = observer_event_provider_get()
        self.evo.add_selection_ex.connect(self.on_add_selection_ex)
        self.evo.clear_selection.connect(self.on_clear_selection)

        self.eq_grp_box: QGroupBox = QGroupBox(None)
        self.eq_lbl: QLabel = QLabel()
        self.eq_dbl_sp_box: QDoubleSpinBox = QDoubleSpinBox()
        self.eq_btn_create: QPushButton = QPushButton()
        self.eq_btn_create.setDisabled(True)
        self.eq_tbl_wid: QTableWidget = QTableWidget()
        self.tab_eq.setLayout(self.lay_get())
        self.ctrl_up = None
        self.ctrl_lock = Lock()
        self.update_table()

    @flow
    def lay_get(self) -> QBoxLayout:
        self.eq_grp_box.setTitle(u"Equal")
        self.eq_lbl.setText(u"Tolerance")
        self.eq_dbl_sp_box = self.base.db_s_box_get(self.eq.tolerance, 1, 0.1, self.on_eq_tol_val_chg)
        self.eq_btn_create.clicked.connect(self.on_eq_create_btn_clk)
        self.eq_btn_create.setText(u"Create")
        self.eq_tbl_wid = self.prep_table(self.eq_grp_box)
        self.eq_tbl_wid.itemSelectionChanged.connect(self.on_eq_tbl_sel_chg)
        # noinspection PyArgumentList
        li = [QVBoxLayout(), self.eq_grp_box,
              [QVBoxLayout(self.eq_grp_box),
               [QHBoxLayout(), self.eq_lbl, self.eq_dbl_sp_box, _QL.addStretch, self.eq_btn_create],
               self.eq_tbl_wid]]
        return self.base.lay_get(li)

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
    @Slot(object)
    def on_clear_selection(self, doc):
        xp(f'on_clear_selection: doc:', str(doc), **_eq)
        self.update_table()

    @flow
    @Slot(object, object)
    def on_add_selection_ex(self, obj, pnt):
        xp(f'on_add_selection_ex: obj:', str(obj), **_ev)
        self.select(obj, pnt)

    @flow
    @Slot(int, int)
    def on_eq_created(self, i, j):
        xp('Eq created', i, j, **_ev)

    @flow
    @Slot()
    def on_eq_create_done(self):
        xp('Eq creation done', **_ev)

    @flow
    def on_eq_create_btn_clk(self):
        self.create()
    
    @flow
    def on_eq_tbl_sel_chg(self):
        self.selected()

    @flow
    def on_eq_tol_val_chg(self, val):
        value = self.eq_dbl_sp_box.value()
        self.eq.tolerance = value
        self.update_table()
    
    @flow
    def task_up(self, eq):
        edge_list: List[EqEdge] = self.eq.tolerances
        cs: Set[Tuple[int, int]] = self.eq.cons_get()
        return edge_list, cs

    @flow(short=True)
    def on_result_up(self, result, id_lst: List[int]):
        self.eq_btn_create.setDisabled(True)
        self.eq_tbl_wid.setUpdatesEnabled(False)
        self.eq_tbl_wid.setRowCount(0)
        __sorting_enabled = self.eq_tbl_wid.isSortingEnabled()
        self.eq_tbl_wid.setSortingEnabled(False)
        edge_list, cs = result
        res_lst: List[EqEdge] = list()
        for edge in edge_list:
            ed = EqEdge(edge.geo_idx, edge.length, edge.construct, edge.extern)
            ed.edg_differences = edge.cons_filter(cs)
            res_lst.append(ed)
        for idx, item in enumerate(res_lst):
            if self.base.cfg_only_valid and (len(item.edg_differences) == 0):
                continue
            if not self.check(item, id_lst):
                continue
            self.eq_tbl_wid.insertRow(0)
            w_item2 = QTableWidgetItem()
            w_item2.setData(Qt.UserRole, item)
            self.eq_tbl_wid.setItem(0, 0, w_item2)
            t = Lookup.translate_ui_name(item.geo_idx)
            fmt = f"{t} {item.length:.1f}"
            w_item = ColorTableItem(item.construct, item.extern, fmt)
            self.eq_tbl_wid.setItem(0, 1, w_item)
            sn, sc, se = self.split(item)
            xp('norm', sn, 'const', sc, 'extern', se, **_eq)
            wid = TableLabel(sn, sc, se)
            self.eq_tbl_wid.setCellWidget(0, 2, wid)
        self.eq_tbl_wid.setSortingEnabled(__sorting_enabled)
        hh: QHeaderView = self.eq_tbl_wid.horizontalHeader()
        hh.resizeSections(QHeaderView.ResizeToContents)
        self.eq_tbl_wid.setUpdatesEnabled(True)

    def check(self, item: EqEdge, id_lst: List[int]):
        if id_lst is None:
            return True
        xp('edg idx', item.geo_idx, 'id lst', repr(id_lst))
        xp('dst lst', [x.geo_idx for x in item.edg_differences])
        lst = [x.geo_idx in id_lst for x in item.edg_differences]
        if item.geo_idx in id_lst:
            return True
        if self.cfg.get(CfgTransient.CO_EXT_MATCH) and any(lst):
            return True
        return False

    def split(self, pt: EqEdge):
        res_n, res_c, res_e = list(), list(), list()
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
    def update_table(self, id_lst=None):
        # self.ctrl_up = Controller(Worker(self.task_up, self.eq), self.on_result_up, 'Equal')
        res = self.task_up(self.eq)
        self.on_result_up(res, id_lst)

    @flow
    def create(self):
        with wait_cursor():
            mod: QItemSelectionModel = self.eq_tbl_wid.selectionModel()
            rows: List[QModelIndex] = mod.selectedRows(0)
            create_list: List[EqEdge] = [x.data(Qt.UserRole) for x in rows]
            for idx in rows:
                xp('row', idx.row(), ':', idx.data(Qt.UserRole), **_eq)
            self.eq.create(create_list)
        self.update_table()

    @flow
    def select(self, obj, pnt):
        xp('select_eq', obj, pnt, **_eq)
        from_gui: bool = True
        if App.Vector(pnt) == App.Vector(0, 0, 0):
            from_gui = False
        xp('from gui', from_gui, **_eq)
        obj: List[Gui.SelectionObject]
        for sel_ex in obj:
            res: List[int] = list()
            xp('sel_ex', sel_ex.FullName, **_eq)
            if sel_ex.TypeName == ObjType.SKETCH_OBJECT:
                for sub_name in sel_ex.SubElementNames:
                    typ, no = Lookup.deconstruct_ui_name(sub_name)
                    if typ == 'Vertex':
                        geo, pos = self.sketch.getGeoVertexIndex(no-1)
                        xp(f'received: gui: {from_gui} {typ} {no} geo: ({geo}.{pos})', **_eq)
                    elif typ == 'ExternalEdge':
                        xp(f'received: gui: {from_gui} {typ} {no}', **_eq)
                    elif typ == 'Edge':
                        res.append(no-1)
                        xp(f'received: gui: {from_gui} {typ} {no}', **_eq)
                    elif typ == 'Constraint':
                        xp(f'received: gui: {from_gui} {typ} {no}', **_eq)
                    else:
                        xp(f'received: gui: {from_gui} {typ} {no}', **_eq)
                if not from_gui:
                    xp('ignore if not from gui', **_eq)
                    return
                self.update_table(id_lst=res)

    @flow
    def selected(self):
        indexes: List[QModelIndex] = self.eq_tbl_wid.selectionModel().selectedRows(0)
        rows: List = [x.row() for x in sorted(indexes)]
        xp(f'selected: {rows}', **_eq)
        if len(rows) == 0:
            self.eq_btn_create.setDisabled(True)
        else:
            self.eq_btn_create.setDisabled(False)
        doc_name = App.activeDocument().Name
        with observer_block():
            Gui.Selection.clearSelection(doc_name, True)
        ed_info = Gui.ActiveDocument.InEditInfo
        sk_name = ed_info[0].Name
        for item in indexes:
            eq: EqEdge = item.data(Qt.UserRole)
            xp(f'row: {str(item.row())} idx: {eq.geo_idx} len: {eq.length:.2f} {eq.edg_differences}', **_eq)
            t = Lookup.translate_ui_name(eq.geo_idx, False)
            Gui.Selection.addSelection(doc_name, sk_name, f'{t}')
            for diff in eq.edg_differences:
                t = Lookup.translate_ui_name(diff.geo_idx, False)
                Gui.Selection.addSelection(doc_name, sk_name, f'{t}')


xps(__name__)
