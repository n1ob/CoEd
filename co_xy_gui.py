from typing import List

from PySide2.QtCore import Slot, QItemSelectionModel, QModelIndex, Qt
from PySide2.QtWidgets import QWidget, QGroupBox, QCheckBox, QPushButton, QTableWidget, QBoxLayout, QVBoxLayout, \
    QHBoxLayout, QTableWidgetItem, QHeaderView
import FreeCAD as App
import FreeCADGui as Gui

import co_gui
import co_impl
from co_logger import flow, xp, _xy, _ev, xps
from co_observer import observer_event_provider_get
from co_xy import XyEdges, XyEdge

_QL = QBoxLayout


class XyGui:

    def __init__(self, base):
        self.base: co_gui.CoEdGui = base
        self.impl: co_impl.CoEd = self.base.base
        self.xy: XyEdges = self.impl.xy_edges
        self.tab_xy = QWidget(None)
        # xp('impl.ev.xy_edg_chg.connect(self.on_xy_chg)', **_ev)
        # self.impl.ev.xy_edg_chg.connect(self.on_xy_chg)
        xp('xy.created.connect', **_ev)
        self.xy.created.connect(self.on_xy_create)
        xp('xy.creation_done.connect', **_ev)
        self.xy.creation_done.connect(self.on_xy_create_done)

        self.xy_grp_box: QGroupBox = QGroupBox(None)
        self.xy_chk_box_x: QCheckBox = QCheckBox()
        self.xy_chk_box_y: QCheckBox = QCheckBox()
        self.xy_btn_create: QPushButton = QPushButton()
        self.xy_btn_create.setDisabled(True)
        self.xy_tbl_wid: QTableWidget = QTableWidget()
        self.tab_xy.setLayout(self.lay_get())
        self.update_table()

    @flow
    def lay_get(self) -> QBoxLayout:
        self.xy_grp_box.setTitle(u"X/Y Distance")
        self.xy_chk_box_x.setText('X')
        self.xy_chk_box_x.setChecked(True)
        self.xy_chk_box_x.stateChanged.connect(self.on_xy_chk_x_state_chg)
        self.xy_chk_box_y.setText('Y')
        self.xy_chk_box_y.setChecked(True)
        self.xy_chk_box_y.stateChanged.connect(self.on_xy_chk_y_state_chg)
        self.xy_btn_create.clicked.connect(self.on_xy_create_btn_clk)
        self.xy_btn_create.setText(u"Create")
        self.xy_tbl_wid = self.prep_table(self.xy_grp_box)
        self.xy_tbl_wid.itemSelectionChanged.connect(self.on_xy_tbl_sel_chg)
        # noinspection PyArgumentList
        li = [QVBoxLayout(), self.xy_grp_box,
              [QVBoxLayout(self.xy_grp_box),
               [QHBoxLayout(), self.xy_chk_box_x, self.xy_chk_box_y, _QL.addStretch, self.xy_btn_create],
               self.xy_tbl_wid]]
        return self.base.lay_get(li)

    @flow
    def on_xy_chk_x_state_chg(self, i):
        if not self.xy_chk_box_x.isChecked():
            self.xy_chk_box_y.setChecked(True)
        if self.base.cfg_blubber:
            self.update_table()

    @flow
    def on_xy_chk_y_state_chg(self, i):
        if not self.xy_chk_box_y.isChecked():
            self.xy_chk_box_x.setChecked(True)
        if self.base.cfg_blubber:
            self.update_table()

    # @flow
    # @Slot(str)
    # def on_xy_chg(self, words):
    #     xp('XY changed', words, **_ev)

    @flow
    @Slot(str)
    def on_xy_create_done(self):
        xp('XY creation done', **_ev)

    @flow
    @Slot(str, int, float)
    def on_xy_create(self, typ: str, geo: int, dis: float):
        xp(f'XY created: {typ} {geo} {dis:.2f}', **_ev)


    @flow
    def on_xy_create_btn_clk(self):
        self.create(self.xy_chk_box_x.isChecked(), self.xy_chk_box_y.isChecked())

    @flow
    def on_xy_tbl_sel_chg(self):
        self.selected()

    @flow
    def prep_table(self, obj):
        table_widget = QTableWidget(obj)
        table_widget.setColumnCount(3)
        w_item = QTableWidgetItem(u"Edge")
        table_widget.setHorizontalHeaderItem(0, w_item)
        w_item = QTableWidgetItem(u"X/Y")
        table_widget.setHorizontalHeaderItem(1, w_item)
        self.base.prep_table(table_widget)
        return table_widget

    @flow
    def create(self, x: bool, y: bool):
        mod: QItemSelectionModel = self.xy_tbl_wid.selectionModel()
        rows: List[QModelIndex] = mod.selectedRows(2)
        create_list: List[XyEdge] = [x.data() for x in rows]
        xp('create_list', create_list, **_xy)
        for idx in rows:
            xp('row', idx.row(), ':', idx.data(), **_xy)
        self.xy.dist_create(create_list, x, y)
        self.update_table()

    @flow
    def update_table(self):
        self.xy_tbl_wid.setUpdatesEnabled(False)
        # self.xy_tbl_wid.setEnabled(False)
        # self.xy_tbl_wid.clearContents()
        self.xy_tbl_wid.setRowCount(0)
        __sorting_enabled = self.xy_tbl_wid.isSortingEnabled()
        self.xy_tbl_wid.setSortingEnabled(False)
        edg_list: List[XyEdge] = self.xy.edges
        x: bool = self.xy_chk_box_x.isChecked()
        y: bool = self.xy_chk_box_y.isChecked()
        for idx, item in enumerate(edg_list):
            if self.base.cfg_blubber:
                if x and not y and item.has_x:
                    continue
                if y and not x and item.has_y:
                    continue
                if x and y and item.has_x and item.has_y:
                    continue
            self.xy_tbl_wid.insertRow(0)
            s = "x {:.1f} y {:.1f} \nx {:.1f} y {:.1f}"
            fmt = s.format(item.start.x, item.start.y, item.end.x, item.end.y)
            self.xy_tbl_wid.setItem(0, 0, QTableWidgetItem(fmt))
            fmt2 = "Id: {}\nx {} y {}".format(item.geo_idx, int(item.has_x), int(item.has_y))
            xp(f'geo {item.geo_idx} x {item.has_x} y {item.has_y}', **_xy)
            w_item = QTableWidgetItem(fmt2)
            w_item.setTextAlignment(Qt.AlignCenter)
            self.xy_tbl_wid.setItem(0, 1, w_item)
            w_item = QTableWidgetItem()
            w_item.setData(Qt.DisplayRole, item)
            xp('col 3', item.geo_idx, **_xy)
            self.xy_tbl_wid.setItem(0, 2, w_item)
        self.xy_tbl_wid.setSortingEnabled(__sorting_enabled)
        hh: QHeaderView = self.xy_tbl_wid.horizontalHeader()
        hh.resizeSections(QHeaderView.ResizeToContents)
        # vh: QHeaderView = self.cons_tbl_wid.verticalHeader()
        # self.xy_tbl_wid.setEnabled(True)
        self.xy_tbl_wid.setUpdatesEnabled(True)

    @flow
    def selected(self):
        indexes: List[QModelIndex] = self.xy_tbl_wid.selectionModel().selectedRows(2)
        rows: List = [x.row() for x in sorted(indexes)]
        xp(f'selected: {rows}', **_xy)
        if len(rows) == 0:
            self.xy_btn_create.setDisabled(True)
        else:
            self.xy_btn_create.setDisabled(False)

        doc_name = App.activeDocument().Name
        observer_event_provider_get().blockSignals(True)
        Gui.Selection.clearSelection(doc_name, True)
        observer_event_provider_get().blockSignals(False)
        ed_info = Gui.ActiveDocument.InEditInfo
        sk_name = ed_info[0].Name

        for item in indexes:
            xy: XyEdge = item.data()
            xp(f'row: {str(item.row())} idx: {xy.geo_idx} cons: {xy}', **_xy)
            Gui.Selection.addSelection(doc_name, sk_name, f'Edge{xy.geo_idx + 1}')


xps(__name__)
