from threading import Lock
from typing import List

import FreeCAD as App
import FreeCADGui as Gui
from PySide2.QtCore import Slot, QItemSelectionModel, QModelIndex, Qt
from PySide2.QtGui import QBrush
from PySide2.QtWidgets import QWidget, QBoxLayout, QGroupBox, QTableWidget, QLabel, QDoubleSpinBox, QPushButton, \
    QVBoxLayout, QHBoxLayout, QTableWidgetItem, QHeaderView

from .co_hv import HvEdges, HvEdge
from .. import co_impl, co_gui
from ..co_base.co_cmn import wait_cursor, Controller, Worker
from ..co_base.co_logger import flow, xp, _hv, _ev, xps
from ..co_base.co_observer import observer_block

_QL = QBoxLayout


class HvGui:
    def __init__(self, base):
        self.base: co_gui.CoEdGui = base
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
            create_list: List[HvEdge] = [x.data() for x in rows]
            for idx in rows:
                xp('row', idx.row(), ':', idx.data(), **_hv)
            self.hv.create(create_list)
        self.update_table()

    @flow
    def task_up(self, hv):
        edge_list: List[HvEdge] = self.hv.tolerances
        cs_v, cs_h = self.hv.cons_get()
        return edge_list, cs_v, cs_h

    @flow(short=True)
    def on_result_up(self, result):
        with self.ctrl_lock:
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
                w_item2.setData(Qt.DisplayRole, item)
                xp('col 3', idx, **_hv)
                self.hv_tbl_wid.setItem(0, 0, w_item2)
                w_item = QTableWidgetItem(f'Edge{item.geo_idx + 1}')
                if item.construct:
                    w_item.setForeground(QBrush(self.base.construct_color))
                self.hv_tbl_wid.setItem(0, 1, w_item)
                fmt = "xa {:.1f} ya {:.1f}".format(item.x_angel, item.y_angel)
                w_item = QTableWidgetItem(fmt)
                if self.impl.sketch.getConstruction(item.geo_idx):
                    w_item.setForeground(QBrush(self.base.construct_color))
                w_item.setTextAlignment(Qt.AlignCenter)
                self.hv_tbl_wid.setItem(0, 2, w_item)
            self.hv_tbl_wid.setSortingEnabled(__sorting_enabled)
            hh: QHeaderView = self.hv_tbl_wid.horizontalHeader()
            hh.resizeSections(QHeaderView.ResizeToContents)
            self.hv_tbl_wid.setUpdatesEnabled(True)

    @flow
    def update_table(self):
        self.ctrl_up = Controller(Worker(self.task_up, self.hv), self.on_result_up, name='HorizontalVertical')

    @flow
    def selected(self):
        indexes: List[QModelIndex] = self.hv_tbl_wid.selectionModel().selectedRows(0)
        rows: List = [x.row() for x in sorted(indexes)]
        xp(f'selected: {rows}', **_hv)
        if len(rows) == 0:
            self.hv_btn_create.setDisabled(True)
        else:
            self.hv_btn_create.setDisabled(False)
        doc_name = App.activeDocument().Name
        with observer_block():
            Gui.Selection.clearSelection(doc_name, True)
        ed_info = Gui.ActiveDocument.InEditInfo
        sk_name = ed_info[0].Name
        for item in indexes:
            hv: HvEdge = item.data()
            xp(f'row: {str(item.row())} idx: {hv.geo_idx} cons: {hv}', **_hv)
            Gui.Selection.addSelection(doc_name, sk_name, f'Edge{hv.geo_idx + 1}')


xps(__name__)
