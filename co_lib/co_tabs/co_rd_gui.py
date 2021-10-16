from threading import Lock
from typing import List

import FreeCAD as App
import FreeCADGui as Gui
from PySide2.QtCore import Slot, QItemSelectionModel, QModelIndex, Qt
from PySide2.QtGui import QBrush
from PySide2.QtWidgets import QBoxLayout, QWidget, QGroupBox, QCheckBox, QDoubleSpinBox, QPushButton, QTableWidget, \
    QVBoxLayout, QHBoxLayout, QTableWidgetItem, QHeaderView

from .co_rd import RdCircles, RdCircle
from .. import co_impl, co_gui
from ..co_base.co_cmn import wait_cursor, Controller, Worker
from ..co_base.co_logger import flow, xp, _rd, _ev, xps
from ..co_base.co_observer import observer_block

_QL = QBoxLayout


class RdGui:
    def __init__(self, base):
        self.base: co_gui.CoEdGui = base
        self.impl: co_impl.CoEd = self.base.base
        self.rd: RdCircles = self.impl.rd_circles
        self.tab_rd = QWidget(None)
        xp('rd.created.connect', **_ev)
        self.rd.created.connect(self.on_rd_create)
        xp('rd.creation_done.connect', **_ev)
        self.rd.creation_done.connect(self.on_rd_create_done)
        self.rad_grp_box: QGroupBox = QGroupBox(None)
        self.rad_chk_box: QCheckBox = QCheckBox()
        self.rad_dbl_sp_box: QDoubleSpinBox = QDoubleSpinBox()
        self.rad_btn_create: QPushButton = QPushButton()
        self.rad_btn_create.setDisabled(True)
        self.rad_tbl_wid: QTableWidget = QTableWidget()
        self.tab_rd.setLayout(self.lay_get())
        self.ctrl_up = None
        self.ctrl_lock = Lock()
        self.update_table()

    @flow
    def lay_get(self) -> QBoxLayout:
        self.rad_chk_box.stateChanged.connect(self.on_rd_chk_box_state_chg)
        self.rad_chk_box.setText(u"Radius")
        self.rad_grp_box.setTitle(u"Radius")
        self.rad_dbl_sp_box = self.base.db_s_box_get(self.rd.radius, 1, 0.1, self.on_rd_val_chg)
        self.rad_chk_box.setChecked(True)
        self.rad_btn_create.clicked.connect(self.on_rd_create_btn_clk)
        self.rad_btn_create.setText(u"Create")
        self.rad_tbl_wid: QTableWidget = self.prep_table(self.rad_grp_box)
        self.rad_tbl_wid.itemSelectionChanged.connect(self.on_rd_tbl_sel_chg)
        # noinspection PyArgumentList
        li = [QVBoxLayout(), self.rad_grp_box,
              [QVBoxLayout(self.rad_grp_box),
               [QHBoxLayout(), self.rad_chk_box, self.rad_dbl_sp_box, _QL.addStretch, self.rad_btn_create],
               self.rad_tbl_wid]]
        return self.base.lay_get(li)

    @flow
    @Slot(int, float)
    def on_rd_create(self, geo: int, rad: float):
        xp('rad created', geo, rad, **_ev)

    @flow
    @Slot()
    def on_rd_create_done(self):
        xp('rad creation done', **_ev)

    @flow
    def on_rd_create_btn_clk(self):
        self.create()

    @flow
    def on_rd_chk_box_state_chg(self, obj):
        if self.rad_chk_box.isChecked():
            self.rad_dbl_sp_box.setEnabled(True)
        else:
            self.rad_dbl_sp_box.setEnabled(False)

    @flow
    def on_rd_val_chg(self, obj):
        value = self.rad_dbl_sp_box.value()
        self.base.radius = value

    @flow
    def on_rd_tbl_sel_chg(self):
        self.selected()

    @flow
    def prep_table(self, obj):
        table_widget = QTableWidget(obj)
        table_widget.setColumnCount(3)
        w_item = QTableWidgetItem(u"Circle")
        table_widget.setHorizontalHeaderItem(1, w_item)
        w_item = QTableWidgetItem(u"Radius")
        table_widget.setHorizontalHeaderItem(2, w_item)
        self.base.prep_table(table_widget)
        return table_widget

    @flow
    def create(self):
        with wait_cursor():
            rad = None
            if self.rad_chk_box.isChecked():
                rad = self.rd.radius
            mod: QItemSelectionModel = self.rad_tbl_wid.selectionModel()
            rows: List[QModelIndex] = mod.selectedRows(0)
            create_list: List[RdCircle] = [x.data() for x in rows]
            for idx in rows:
                xp(idx.row(), ':', idx.data(), **_rd)
            self.rd.dia_create(create_list, rad)
        self.update_table()

    @flow
    def task_up(self, hv):
        rad_lst, dia_lst = self.rd.cons_get()
        cir_list: List[RdCircle] = self.rd.circles
        return cir_list, rad_lst, dia_lst

    @flow(short=True)
    def on_result_up(self, result):
        with self.ctrl_lock:
            self.rad_tbl_wid.setUpdatesEnabled(False)
            self.rad_tbl_wid.setRowCount(0)
            __sorting_enabled = self.rad_tbl_wid.isSortingEnabled()
            self.rad_tbl_wid.setSortingEnabled(False)
            cir_list, rad_lst, dia_lst = result
            xp('->', cir_list, **_rd)
            for item in cir_list:
                cs = f'---'
                typ = 'cir' if item.type_id == 'Part::GeomCircle' else 'arc'
                if item.geo_idx in rad_lst:
                    if self.base.cfg_only_valid:
                        continue
                    xp('rad cs', item.geo_idx, **_rd)
                    cs = f'rad'
                if item.geo_idx in dia_lst:
                    if self.base.cfg_only_valid:
                        continue
                    xp('dia cs', item.geo_idx, **_rd)
                    cs = f'dia'
                self.rad_tbl_wid.insertRow(0)
                w_item = QTableWidgetItem()
                w_item.setData(Qt.DisplayRole, item)
                xp('col 3', item.geo_idx, **_rd)
                self.rad_tbl_wid.setItem(0, 0, w_item)
                w_item = QTableWidgetItem(f'Edge{item.geo_idx + 1}')
                if item.construct:
                    w_item.setForeground(QBrush(self.base.construct_color))
                self.rad_tbl_wid.setItem(0, 1, QTableWidgetItem(w_item))
                fmt = f"r {item.radius:.1f} cs {cs} {typ}"
                w_item = QTableWidgetItem(fmt)
                if self.impl.sketch.getConstruction(item.geo_idx):
                    w_item.setForeground(QBrush(self.base.construct_color))
                w_item.setTextAlignment(Qt.AlignCenter)
                self.rad_tbl_wid.setItem(0, 2, w_item)
            self.rad_tbl_wid.setSortingEnabled(__sorting_enabled)
            hh: QHeaderView = self.rad_tbl_wid.horizontalHeader()
            hh.resizeSections(QHeaderView.ResizeToContents)
            self.rad_tbl_wid.setUpdatesEnabled(True)

    @flow
    def update_table(self):
        self.ctrl_up = Controller(Worker(self.task_up, self.rd), self.on_result_up, name='Radius')

    @flow
    def selected(self):
        indexes: List[QModelIndex] = self.rad_tbl_wid.selectionModel().selectedRows(0)
        rows: List = [x.row() for x in sorted(indexes)]
        xp(f'selected: {rows}', **_rd)
        if len(rows) == 0:
            self.rad_btn_create.setDisabled(True)
        else:
            self.rad_btn_create.setDisabled(False)
        doc_name = App.activeDocument().Name
        with observer_block():
            Gui.Selection.clearSelection(doc_name, True)
        ed_info = Gui.ActiveDocument.InEditInfo
        sk_name = ed_info[0].Name
        for item in indexes:
            rad: RdCircle = item.data()
            xp(f'row: {str(item.row())} idx: {rad.geo_idx} cons: {rad}', **_rd)
            Gui.Selection.addSelection(doc_name, sk_name, f'Edge{rad.geo_idx + 1}')
            idx = 0
            while True:
                geo, pos = self.impl.sketch.getGeoVertexIndex(idx)
                if (geo == rad.geo_idx) and (pos == 3):
                    Gui.Selection.addSelection(doc_name, sk_name, f'Vertex{idx + 1}')
                    xp(f'Vertex{idx + 1} idx: {idx} geo: ({geo}.{pos})', **_rd)
                if (geo == -2000) and (pos == 0):
                    xp(f'unexpected, no vertex found', **_rd)
                    break
                idx += 1


xps(__name__)
