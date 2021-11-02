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
from typing import List, Set, Tuple, Dict

import FreeCAD as App
import FreeCADGui as Gui
import Sketcher
from PySide2.QtCore import Qt, QModelIndex, QItemSelectionModel, Slot
from PySide2.QtWidgets import QWidget, QGroupBox, QLabel, QDoubleSpinBox, QPushButton, QTableWidget, QBoxLayout, \
    QVBoxLayout, QHBoxLayout, QTableWidgetItem, QProxyStyle, QStyle, QHeaderView

from .co_co import CoPoints, CoPoint, GeoId, GeoIdDist
from .. import co_impl, co_gui
from ..co_base.co_cmn import GeoPt, fmt_vec, pt_typ_str, wait_cursor, TableLabel, ColorTableItem, ObjType
from ..co_base.co_logger import flow, xp, _co, _ev, xps, Profile
from ..co_base.co_lookup import Lookup
from ..co_base.co_observer import observer_block, observer_event_provider_get

_QL = QBoxLayout


class CoGui:
    def __init__(self, base):
        self.base: co_gui.CoEdGui = base
        self.sketch: Sketcher.SketchObject = self.base.sketch
        self.impl: co_impl.CoEd = self.base.base
        self.co: CoPoints = self.impl.co_points
        self.tab_co = QWidget(None)
        xp('co.created.connect', **_ev)
        self.co.created.connect(self.on_co_create)
        xp('co.creation_done.connect', **_ev)
        self.co.creation_done.connect(self.on_co_create_done)

        self.co_grp_box: QGroupBox = QGroupBox(None)
        self.co_lbl: QLabel = QLabel()
        self.co_dbl_sp_box: QDoubleSpinBox = QDoubleSpinBox()
        self.co_btn_create: QPushButton = QPushButton()
        self.co_btn_create.setDisabled(True)
        self.co_tbl_wid: QTableWidget = QTableWidget()
        self.tab_co.setLayout(self.lay_get())
        self.evo = observer_event_provider_get()
        self.evo.in_edit.connect(self.on_in_edit)
        self.ctrl_up = None
        self.ctrl_lock = Lock()
        self.update_table()

    @flow
    def lay_get(self) -> QBoxLayout:
        self.co_grp_box.setTitle(u"Coincident")
        self.co_lbl.setText(u"Snap Dist")
        self.co_dbl_sp_box = self.base.db_s_box_get(self.co.tolerance, 2, 0.1, self.on_co_tol_chg)
        self.co_btn_create.clicked.connect(self.on_co_create_btn_clk)
        self.co_btn_create.setText(u"Create")
        self.co_tbl_wid = self.prep_table(self.co_grp_box)
        self.co_tbl_wid.itemSelectionChanged.connect(self.on_co_tbl_sel_chg)
        # noinspection PyArgumentList
        li = [QVBoxLayout(), self.co_grp_box,
              [QVBoxLayout(self.co_grp_box),
               [QHBoxLayout(), self.co_lbl, self.co_dbl_sp_box, _QL.addStretch, self.co_btn_create],
               self.co_tbl_wid]]
        return self.base.lay_get(li)

    @flow
    def prep_table(self, obj: QGroupBox) -> QTableWidget:
        table_widget = QTableWidget(obj)
        table_widget.setColumnCount(3)
        w_item = QTableWidgetItem(u"Point")
        table_widget.setHorizontalHeaderItem(1, w_item)
        w_item = QTableWidgetItem(u"Idx")
        table_widget.setHorizontalHeaderItem(2, w_item)
        self.base.prep_table(table_widget)
        return table_widget

    # -----------------------------------------------------------------------

    @flow
    @Slot(object)
    def on_in_edit(self, obj):
        if obj.TypeId == ObjType.VIEW_PROVIDER_SKETCH:
            ed_info = Gui.ActiveDocument.InEditInfo
            if (ed_info is not None) and (ed_info[0].TypeId == ObjType.SKETCH_OBJECT):
                self.sketch = ed_info[0]

    @flow
    @Slot(tuple, tuple)
    def on_co_create(self, first: tuple, second: tuple):
        xp('Co created:', first, second, **_ev)

    @flow
    @Slot()
    def on_co_create_done(self):
        xp('Co creation done', **_ev)

    @flow
    def on_co_tol_chg(self, val):
        self.co_dbl_sp_box.setEnabled(False)
        with Profile(enable=False):
            self.co.tolerance = val
            self.update_table()
        self.co_dbl_sp_box.setEnabled(True)

    @flow
    def on_co_create_btn_clk(self):
        self.create()

    @flow
    def on_co_tbl_sel_chg(self):
        self.selected()

    # -----------------------------------------------------------------------

    @flow
    def task_up(self, co):
        pt_list: List[CoPoint] = co.tolerances
        cs: Set[Tuple[GeoId, GeoId]] = co.cons_get()
        return pt_list, cs

    @flow(short=True)
    def on_result_up(self, result):
        self.co_tbl_wid.setUpdatesEnabled(False)
        self.co_tbl_wid.setRowCount(0)
        __sorting_enabled = self.co_tbl_wid.isSortingEnabled()
        self.co_tbl_wid.setSortingEnabled(False)
        pt_list, cs = result
        res_lst: List[CoPoint] = list()
        for pt in pt_list:
            pt: CoPoint
            p = CoPoint(pt.geo_id, pt.point, pt.construct, pt.extern)
            p.pt_distance_lst = pt.cons_filter(cs)
            res_lst.append(p)
        self.log_filter(res_lst)
        lo = Lookup(self.sketch)
        for idx, pt in enumerate(res_lst):
            if self.base.cfg_only_valid and (len(pt.pt_distance_lst) == 0):
                continue
            self.co_tbl_wid.insertRow(0)
            w_item = QTableWidgetItem()
            w_item.setData(Qt.UserRole, pt)
            self.co_tbl_wid.setItem(0, 0, w_item)
            # w_item = QTableWidgetItem()
            # if pt.extern:
            #     w_item.setForeground(QBrush(self.base.extern_color))
            # elif pt.construct:
            #     w_item.setForeground(QBrush(self.base.construct_color))
            s1, s2 = lo.lookup_ui_names(GeoPt(pt.geo_id.idx, pt.geo_id.typ))
            t = Lookup.translate_geo_idx(pt.geo_id.idx)
            fmt = f"{s1} {t}.{pt_typ_str[pt.geo_id.typ]}"
            # w_item.setText(fmt)
            w_item = ColorTableItem(pt.construct, pt.extern, fmt)
            self.co_tbl_wid.setItem(0, 1, w_item)
            sn, sc, se = self.split(pt)
            xp('norm', sn, 'const', sc, 'extern', se, **_co)
            wid = TableLabel(sn, sc, se)
            self.co_tbl_wid.setCellWidget(0, 2, wid)
            xp('new row: Id', idx, fmt, sn, sc, **_co)
        self.co_tbl_wid.setSortingEnabled(__sorting_enabled)
        hh: QHeaderView = self.co_tbl_wid.horizontalHeader()
        hh.resizeSections(QHeaderView.ResizeToContents)
        vh: QHeaderView = self.co_tbl_wid.verticalHeader()
        self.co_tbl_wid.setUpdatesEnabled(True)

    def split(self, pt: CoPoint):
        res_n = list()
        res_c = list()
        res_e = list()
        for x in pt.pt_distance_lst:
            x: GeoIdDist
            t = Lookup.translate_geo_idx(x.geo_id.idx)
            s = f'{t}.{pt_typ_str[x.geo_id.typ]}'
            if x.extern:
                res_e.append(s)
            elif x.construct:
                res_c.append(s)
            else:
                res_n.append(s)
        return ' '.join(res_n), ' '.join(res_c), ' '.join(res_e)

    @flow
    def update_table(self):
        # self.ctrl_up = Controller(Worker(self.task_up, self.co), self.on_result_up, name='Coincident')
        res = self.task_up(self.co)
        self.on_result_up(res)
    # -----------------------------------------------------------------------

    @flow
    def create(self):
        with wait_cursor():
            mod: QItemSelectionModel = self.co_tbl_wid.selectionModel()
            rows: List[QModelIndex] = mod.selectedRows(0)
            create_list: List[CoPoint] = [x.data(Qt.UserRole) for x in rows]
            for idx in rows:
                xp(idx.row(), ':', idx.data(Qt.UserRole), **_co)
            self.co.create(create_list)
        self.update_table()

    @flow
    def selected(self):
        indexes: List[QModelIndex] = self.co_tbl_wid.selectionModel().selectedRows(0)
        rows: List = [x.row() for x in sorted(indexes)]
        xp(f'selected: {rows}', **_co)
        if len(rows) == 0:
            self.co_btn_create.setDisabled(True)
        else:
            self.co_btn_create.setDisabled(False)
        doc_name = App.activeDocument().Name
        with observer_block():
            Gui.Selection.clearSelection(doc_name, True)
        ed_info = Gui.ActiveDocument.InEditInfo
        sk_name = ed_info[0].Name
        chk = self.geo_vert_idx()
        res: List[str] = list()
        for item in indexes:
            co: CoPoint = item.data(Qt.UserRole)
            xp(f'row: {str(item.row())} id: {co.geo_id} pt: {fmt_vec(co.point)} {co.pt_distance_lst}', **_co)
            idx, typ = co.geo_id
            if (idx, typ) in chk:
                res.append(f'Vertex{chk[(idx, typ)] + 1}')
                xp(f'Vertex{idx + 1} idx: {chk[(idx, typ)]} geo: ({idx}.{typ})', **_co)
            for diff in co.pt_distance_lst:
                idx, typ = diff.geo_id
                if (idx, typ) in chk:
                    res.append(f'Vertex{chk[(idx, typ)] + 1}')
                    xp(f'Vertex{idx + 1} idx: {chk[(idx, typ)]} geo: ({idx}.{typ})', **_co)
        with observer_block():
            for s in res:
                Gui.Selection.addSelection(doc_name, sk_name, s)

    @flow
    def geo_vert_idx(self) -> Dict[Tuple[int, int], int]:
        idx = 0
        res: Dict[Tuple[int, int], int] = dict()
        while True:
            geo, pos = self.sketch.getGeoVertexIndex(idx)
            if (geo == -2000) and (pos == 0):
                break
            res[(geo, pos)] = idx
            idx += 1
        return res

    def log_filter(self, obj):
        xp(f'filter list', **_co)
        for item in obj:
            xp(item, **_co)


class CustomStyle(QProxyStyle):
    def styleHint(self, hint, option, PySide2_QtWidgets_QStyleOption=None, NoneType=None, *args, **kwargs):
        # def styleHint(self, hint, option=None, widget=None, returnData=None):
        if hint == QStyle.SH_SpinBox_KeyPressAutoRepeatRate:
            return 10**10
        elif hint == QStyle.SH_SpinBox_ClickAutoRepeatRate:
            return 10**10
        elif hint == QStyle.SH_SpinBox_ClickAutoRepeatThreshold:
            # You can use only this condition to avoid the auto-repeat,
            # but better safe than sorry ;-)
            return 10**10
        else:
            return super().styleHint(hint, option, PySide2_QtWidgets_QStyleOption, NoneType, args, kwargs)


xps(__name__)


