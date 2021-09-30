from typing import List, Tuple, Set

import FreeCAD as App
import FreeCADGui as Gui

from PySide2.QtCore import QItemSelectionModel, QModelIndex, Qt, Slot
from PySide2.QtWidgets import QWidget, QGroupBox, QPushButton, QTableWidget, QBoxLayout, QVBoxLayout, \
    QHBoxLayout, QLabel, QDoubleSpinBox, QTableWidgetItem, QHeaderView

import co_gui
import co_impl
from co_eq import EqEdges, EqEdge
from co_logger import xp, flow, _eq, _ev, xps
from co_observer import observer_event_provider_get

_QL = QBoxLayout


class EqGui:
    def __init__(self, base):
        self.base: co_gui.CoEdGui = base
        self.impl: co_impl.CoEd = self.base.base
        self.eq: EqEdges = self.impl.eq_edges
        self.tab_eq = QWidget(None)
        # xp('impl.ev.eq_chg.connect(self.on_eq_chg)', **_ev)
        # self.impl.ev.eq_chg.connect(self.on_eq_chg)
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

    # @flow
    # @Slot(str)
    # def on_eq_chg(self, words):
    #     xp('Eq changed', words, **_ev)
    
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
        table_widget.setHorizontalHeaderItem(0, w_item)
        w_item = QTableWidgetItem(u"Info")
        table_widget.setHorizontalHeaderItem(1, w_item)
        self.base.prep_table(table_widget)
        return table_widget

    @flow
    def create(self):
        mod: QItemSelectionModel = self.eq_tbl_wid.selectionModel()
        rows: List[QModelIndex] = mod.selectedRows(2)
        create_list: List[EqEdge] = [x.data() for x in rows]
        for idx in rows:
            xp('row', idx.row(), ':', idx.data(), **_eq)
        self.eq.create(create_list)
        self.update_table()

    @flow
    def update_table(self):
        self.eq_tbl_wid.setUpdatesEnabled(False)
        # self.eq_tbl_wid.setEnabled(False)
        # self.eq_tbl_wid.clearContents()
        self.eq_tbl_wid.setRowCount(0)
        __sorting_enabled = self.eq_tbl_wid.isSortingEnabled()
        self.eq_tbl_wid.setSortingEnabled(False)
        edge_list: List[EqEdge] = self.eq.tolerances
        cs: Set[Tuple[int, int]] = self.eq.cons_get()
        res_lst: List[EqEdge] = list()
        for edge in edge_list:
            ed = EqEdge(edge.geo_idx, edge.length)
            ed.edg_differences = edge.cons_filter(cs)
            res_lst.append(ed)
        for idx, item in enumerate(res_lst):
            if self.base.cfg_blubber and (len(item.edg_differences) == 0):
                continue
            self.eq_tbl_wid.insertRow(0)
            fmt = f"({item.geo_idx}) {item.length: 5.1f}"
            self.eq_tbl_wid.setItem(0, 0, QTableWidgetItem(fmt))
            fmt = ' '.join(f'({x.geo_idx}) {x.difference:.1f}' for x in item.edg_differences)
            w_item = QTableWidgetItem(fmt)
            w_item.setTextAlignment(Qt.AlignCenter)
            self.eq_tbl_wid.setItem(0, 1, w_item)
            w_item2 = QTableWidgetItem()
            w_item2.setData(Qt.DisplayRole, item)
            xp('col 3', idx, **_eq)
            self.eq_tbl_wid.setItem(0, 2, w_item2)
        self.eq_tbl_wid.setSortingEnabled(__sorting_enabled)
        hh: QHeaderView = self.eq_tbl_wid.horizontalHeader()
        hh.resizeSections(QHeaderView.ResizeToContents)
        # vh: QHeaderView = self.cons_tbl_wid.verticalHeader()
        # self.eq_tbl_wid.setEnabled(True)
        self.eq_tbl_wid.setUpdatesEnabled(True)

    @flow
    def selected(self):
        indexes: List[QModelIndex] = self.eq_tbl_wid.selectionModel().selectedRows(2)
        rows: List = [x.row() for x in sorted(indexes)]
        xp(f'selected: {rows}', **_eq)
        if len(rows) == 0:
            self.eq_btn_create.setDisabled(True)
        else:
            self.eq_btn_create.setDisabled(False)

        doc_name = App.activeDocument().Name
        observer_event_provider_get().blockSignals(True)
        Gui.Selection.clearSelection(doc_name, True)
        observer_event_provider_get().blockSignals(False)
        ed_info = Gui.ActiveDocument.InEditInfo
        sk_name = ed_info[0].Name

        for item in indexes:
            eq: EqEdge = item.data()
            xp(f'row: {str(item.row())} idx: {eq.geo_idx} len: {eq.length:.2f} {eq.edg_differences}', **_eq)
            Gui.Selection.addSelection(doc_name, sk_name, f'Edge{eq.geo_idx + 1}')
            for diff in eq.edg_differences:
                Gui.Selection.addSelection(doc_name, sk_name, f'Edge{diff.geo_idx + 1}')


xps(__name__)
