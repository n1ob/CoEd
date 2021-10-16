from threading import Lock
from typing import List, Tuple, Set

import FreeCAD as App
import FreeCADGui as Gui
from PySide2.QtCore import QItemSelectionModel, QModelIndex, Qt, Slot
from PySide2.QtGui import QBrush
from PySide2.QtWidgets import QWidget, QGroupBox, QPushButton, QTableWidget, QBoxLayout, QVBoxLayout, \
    QHBoxLayout, QLabel, QDoubleSpinBox, QTableWidgetItem, QHeaderView

from .co_eq import EqEdges, EqEdge
from .. import co_impl, co_gui
from ..co_base.co_cmn import wait_cursor, Controller, Worker, MyLabel
from ..co_base.co_logger import xp, flow, _eq, _ev, xps
from ..co_base.co_observer import observer_block

_QL = QBoxLayout


class EqGui:
    def __init__(self, base):
        self.base: co_gui.CoEdGui = base
        self.impl: co_impl.CoEd = self.base.base
        self.eq: EqEdges = self.impl.eq_edges
        self.tab_eq = QWidget(None)
        xp('eq.created.connect', **_ev)
        self.eq.created.connect(self.on_eq_created)
        xp('eq.creation_done.connect', **_ev)
        self.eq.creation_done.connect(self.on_eq_create_done)

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
            mod: QItemSelectionModel = self.eq_tbl_wid.selectionModel()
            rows: List[QModelIndex] = mod.selectedRows(0)
            create_list: List[EqEdge] = [x.data() for x in rows]
            for idx in rows:
                xp('row', idx.row(), ':', idx.data(), **_eq)
            self.eq.create(create_list)
        self.update_table()

    @flow
    def task_up(self, eq):
        edge_list: List[EqEdge] = self.eq.tolerances
        cs: Set[Tuple[int, int]] = self.eq.cons_get()
        return edge_list, cs

    @flow(short=True)
    def on_result_up(self, result):
        with self.ctrl_lock:
            self.eq_tbl_wid.setUpdatesEnabled(False)
            self.eq_tbl_wid.setRowCount(0)
            __sorting_enabled = self.eq_tbl_wid.isSortingEnabled()
            self.eq_tbl_wid.setSortingEnabled(False)
            edge_list, cs = result
            res_lst: List[EqEdge] = list()
            for edge in edge_list:
                ed = EqEdge(edge.geo_idx, edge.length, edge.construct)
                ed.edg_differences = edge.cons_filter(cs)
                res_lst.append(ed)
            for idx, item in enumerate(res_lst):
                if self.base.cfg_only_valid and (len(item.edg_differences) == 0):
                    continue
                self.eq_tbl_wid.insertRow(0)
                w_item2 = QTableWidgetItem()
                w_item2.setData(Qt.DisplayRole, item)
                xp('col 3', idx, **_eq)
                self.eq_tbl_wid.setItem(0, 0, w_item2)
                fmt = f"Edge{item.geo_idx + 1} {item.length:.1f}"
                w_item = QTableWidgetItem(fmt)
                if item.construct:
                    w_item.setForeground(QBrush(self.base.construct_color))
                self.eq_tbl_wid.setItem(0, 1, w_item)
                sn = ' '.join(f'{x.geo_idx+1}({x.difference:.2f})'
                              for x in item.edg_differences
                              if not self.eq.base.sketch.getConstruction(x.geo_idx))
                sc = ' '.join(f'{x.geo_idx+1}({x.difference:.2f})'
                              for x in item.edg_differences
                              if self.eq.base.sketch.getConstruction(x.geo_idx))
                xp('norm', sn, 'const', sc, **_eq)
                wid = MyLabel(self.base.construct_color.name(), sn, sc)
                self.eq_tbl_wid.setCellWidget(0, 2, wid)
            self.eq_tbl_wid.setSortingEnabled(__sorting_enabled)
            hh: QHeaderView = self.eq_tbl_wid.horizontalHeader()
            hh.resizeSections(QHeaderView.ResizeToContents)
            self.eq_tbl_wid.setUpdatesEnabled(True)

    @flow
    def update_table(self):
        self.ctrl_up = Controller(Worker(self.task_up, self.eq), self.on_result_up, 'Equal')

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
            eq: EqEdge = item.data()
            xp(f'row: {str(item.row())} idx: {eq.geo_idx} len: {eq.length:.2f} {eq.edg_differences}', **_eq)
            Gui.Selection.addSelection(doc_name, sk_name, f'Edge{eq.geo_idx + 1}')
            for diff in eq.edg_differences:
                Gui.Selection.addSelection(doc_name, sk_name, f'Edge{diff.geo_idx + 1}')


xps(__name__)
