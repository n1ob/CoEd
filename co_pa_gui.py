from typing import List, Tuple, Set

import FreeCAD as App
import FreeCADGui as Gui

from PySide2.QtCore import QItemSelectionModel, QModelIndex, Qt, Slot
from PySide2.QtWidgets import QWidget, QGroupBox, QPushButton, QTableWidget, QBoxLayout, QVBoxLayout, \
    QHBoxLayout, QLabel, QDoubleSpinBox, QTableWidgetItem, QHeaderView

import co_gui
import co_impl
from co_pa import PaEdges, PaEdge
from co_logger import xp, flow, _pa, _ev, xps
from co_observer import observer_event_provider_get

_QL = QBoxLayout


class PaGui:
    def __init__(self, base):
        self.base: co_gui.CoEdGui = base
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
        table_widget.setHorizontalHeaderItem(0, w_item)
        w_item = QTableWidgetItem(u"Info")
        table_widget.setHorizontalHeaderItem(1, w_item)
        self.base.prep_table(table_widget)
        return table_widget

    @flow
    def create(self):
        mod: QItemSelectionModel = self.pa_tbl_wid.selectionModel()
        rows: List[QModelIndex] = mod.selectedRows(2)
        create_list: List[PaEdge] = [x.data() for x in rows]
        for idx in rows:
            xp('row', idx.row(), ':', idx.data(), **_pa)
        self.pa.create(create_list)
        self.update_table()

    @flow
    def update_table(self):
        self.pa_tbl_wid.setUpdatesEnabled(False)
        # self.pa_tbl_wid.setEnabled(False)
        # self.pa_tbl_wid.clearContents()
        self.pa_tbl_wid.setRowCount(0)
        __sorting_enabled = self.pa_tbl_wid.isSortingEnabled()
        self.pa_tbl_wid.setSortingEnabled(False)
        edge_list: List[PaEdge] = self.pa.tolerances
        cs: Set[Tuple[int, int]] = self.pa.cons_get()
        res_lst: List[PaEdge] = list()
        for edge in edge_list:
            ed = PaEdge(edge.geo_idx, edge.y_angel, edge.pt_start, edge.pt_end)
            ed.edg_differences = edge.cons_filter(cs)
            res_lst.append(ed)
        for idx, item in enumerate(res_lst):
            if self.base.cfg_blubber and (len(item.edg_differences) == 0):
                continue
            self.pa_tbl_wid.insertRow(0)
            fmt = f"({item.geo_idx}) {item.y_angel: 5.1f}"
            self.pa_tbl_wid.setItem(0, 0, QTableWidgetItem(fmt))
            fmt = ' '.join(f'({x.geo_idx}) {x.difference:.1f}' for x in item.edg_differences)
            w_item = QTableWidgetItem(fmt)
            w_item.setTextAlignment(Qt.AlignCenter)
            self.pa_tbl_wid.setItem(0, 1, w_item)
            w_item2 = QTableWidgetItem()
            w_item2.setData(Qt.DisplayRole, item)
            xp('col 3', idx, **_pa)
            self.pa_tbl_wid.setItem(0, 2, w_item2)
        self.pa_tbl_wid.setSortingEnabled(__sorting_enabled)
        hh: QHeaderView = self.pa_tbl_wid.horizontalHeader()
        hh.resizeSections(QHeaderView.ResizeToContents)
        # vh: QHeaderView = self.cons_tbl_wid.verticalHeader()
        # self.pa_tbl_wid.setEnabled(True)
        self.pa_tbl_wid.setUpdatesEnabled(True)

    @flow
    def selected(self):
        indexes: List[QModelIndex] = self.pa_tbl_wid.selectionModel().selectedRows(2)
        rows: List = [x.row() for x in sorted(indexes)]
        xp(f'selected: {rows}', **_pa)
        if len(rows) == 0:
            self.pa_btn_create.setDisabled(True)
        else:
            self.pa_btn_create.setDisabled(False)

        doc_name = App.activeDocument().Name
        observer_event_provider_get().blockSignals(True)
        Gui.Selection.clearSelection(doc_name, True)
        observer_event_provider_get().blockSignals(False)
        ed_info = Gui.ActiveDocument.InEditInfo
        sk_name = ed_info[0].Name

        for item in indexes:
            pa: PaEdge = item.data()
            xp(f'row: {str(item.row())} idx: {pa.geo_idx} len: {pa.y_angel:.2f} {pa.edg_differences}', **_pa)
            Gui.Selection.addSelection(doc_name, sk_name, f'Edge{pa.geo_idx + 1}')
            for diff in pa.edg_differences:
                Gui.Selection.addSelection(doc_name, sk_name, f'Edge{diff.geo_idx + 1}')


xps(__name__)
