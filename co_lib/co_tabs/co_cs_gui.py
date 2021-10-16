from threading import Lock, RLock
from typing import List, Set, Callable

import FreeCAD as App
import FreeCADGui as Gui
from PySide2.QtCore import Slot, QItemSelectionModel, QModelIndex, Qt, QSize, QSignalMapper, Signal
from PySide2.QtWidgets import QBoxLayout, QWidget, QGroupBox, QLabel, QTableWidget, QComboBox, QPushButton, QVBoxLayout, \
    QHBoxLayout, QTableWidgetItem, QHeaderView, QAbstractItemView, QCheckBox

from .co_cs import Constraints, Constraint
from .. import co_impl, co_gui
from ..co_base.co_cmn import ConType, wait_cursor, Controller, Worker, MyLabel
from ..co_base.co_flag import ConsTrans
from ..co_base.co_logger import xp, _cs, flow, _ev, Profile
from ..co_base.co_lookup import Lookup
from ..co_base.co_observer import observer_block

_QL = QBoxLayout


class TableCheckBox(QCheckBox):

    state_chg = Signal(object, int)

    def __init__(self, item: Constraint, state: bool, enable: bool, func: Callable, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.cs_item = item
        self.stateChanged.connect(self.re_emit)
        self.setStyleSheet("QCheckBox::indicator {width: 20px; height: 20px;}")
        self.setEnabled(enable)
        self.setChecked(state)
        self.state_chg.connect(func)

    @Slot(int)
    def re_emit(self, state: int):
        self.state_chg.emit(self.cs_item, state)


class CsGui:
    def __init__(self, base):
        self.base: co_gui.CoEdGui = base
        self.impl: co_impl.CoEd = self.base.base
        self.cs: Constraints = self.impl.cs
        self.tab_cs = QWidget(None)
        xp('cs.deleted.connect', **_ev)
        self.cs.deleted.connect(self.on_cs_del)
        xp('cs.deletion_done.connect', **_ev)
        self.cs.deletion_done.connect(self.on_cs_del_done)
        xp('cs.update_done.connect', **_ev)
        self.cs.update_done.connect(self.on_cs_up_done)
        self.cons_grp_box: QGroupBox = QGroupBox(None)
        self.cons_lbl_con: QLabel = QLabel()
        self.cons_tbl_wid: QTableWidget = QTableWidget()
        self.cons_cmb_box: QComboBox = QComboBox()
        self.cons_btn_del: QPushButton = QPushButton()
        self.cons_btn_ext: QPushButton = QPushButton()
        self.ext_toggle = True
        self.tab_cs.setLayout(self.lay_get())
        self.ctrl_up = None
        self.ctrl_lock = RLock()
        self.update_table()

    @flow
    def lay_get(self) -> QBoxLayout:
        self.cons_grp_box.setTitle(u"Constraints")
        self.cons_lbl_con.setText(u"Type")
        self.cons_tbl_wid = self.prep_table(self.cons_grp_box)
        self.cons_tbl_wid.itemSelectionChanged.connect(self.on_cons_tbl_sel_chg)
        self.cons_cmb_box = self.prep_combo()
        self.cons_cmb_box.currentTextChanged.connect(self.on_cons_type_cmb_chg)
        self.cons_btn_del.clicked.connect(self.on_cons_delete_btn_clk)
        self.cons_btn_del.setText(u"Delete")
        self.cons_btn_del.setDisabled(True)
        self.cons_btn_ext.clicked.connect(self.on_cons_ext_btn_clk)
        self.cons_btn_ext.setText(u">")
        self.cons_btn_ext.setContentsMargins(0, 0, 0, 0)
        # noinspection PyArgumentList
        li = [QVBoxLayout(), self.cons_grp_box,
              [QVBoxLayout(self.cons_grp_box),
               [QHBoxLayout(), self.cons_lbl_con, self.cons_cmb_box, _QL.addStretch, self.cons_btn_del, self.cons_btn_ext],
               self.cons_tbl_wid]]
        return self.base.lay_get(li)

    @flow
    @Slot(int)
    def on_cs_del(self, i: int):
        xp('Constraints deleted', i, **_ev)

    @flow
    @Slot()
    def on_cs_del_done(self):
        xp('Constraints deletion done', **_ev)
        co_list: List[Constraint] = self.cs.constraints
        self.update_combo(co_list)

    @flow
    @Slot()
    def on_cs_up_done(self):
        xp('Constraints update done', **_ev)
        co_list: List[Constraint] = self.cs.constraints
        self.update_combo(co_list)

    @flow
    def on_cons_delete_btn_clk(self):
        self.delete()

    @flow
    def on_cons_ext_btn_clk(self):
        si: QSize = self.cons_tbl_wid.size()
        if self.ext_toggle:
            self.cons_tbl_wid.setColumnHidden(3, False)
            self.cons_tbl_wid.setColumnHidden(4, False)
            self.cons_tbl_wid.setColumnHidden(5, False)
            self.cons_btn_ext.setText('<')
            si.setWidth(si.width() + 100)
        else:
            self.cons_tbl_wid.setColumnHidden(3, True)
            self.cons_tbl_wid.setColumnHidden(4, True)
            self.cons_tbl_wid.setColumnHidden(5, True)
            self.cons_btn_ext.setText('>')
            si.setWidth(si.width() - 100)
        self.ext_toggle = not self.ext_toggle
        self.cons_tbl_wid.resizeColumnsToContents()
        self.cons_tbl_wid.resizeRowsToContents()
        self.cons_tbl_wid.resize(si)

    @flow
    def on_cons_type_cmb_chg(self, txt):
        ct: ConType = ConType(txt)
        with Profile(enable=False):
            self.update_table(ct)

    @flow
    def on_cons_tbl_sel_chg(self):
        self.selected()

    @flow
    def delete(self):
        with wait_cursor():
            mod: QItemSelectionModel = self.cons_tbl_wid.selectionModel()
            rows: List[QModelIndex] = mod.selectedRows(0)
            del_list: List[int] = list()
            for idx in rows:
                xp(str(idx.row()), ':', str(idx.data()), idx.data().co_idx, **_cs)
                del_list.append(idx.data().co_idx)
            doc_name = App.activeDocument().Name
            # todo clear selection reminder
            Gui.Selection.clearSelection(doc_name, True)
            self.cs.constraints_delete(del_list)
        self.update_table()

    @flow
    def task_up(self, cs):
        cs_list: List[Constraint] = self.cs.constraints
        return cs_list

    @flow(short=True)
    def on_result_up(self, result, typ):
        with self.ctrl_lock:
            lo = Lookup(self.cs.base.sketch)
            self.cons_tbl_wid.setUpdatesEnabled(False)
            self.cons_tbl_wid.setRowCount(0)
            __sorting_enabled = self.cons_tbl_wid.isSortingEnabled()
            self.cons_tbl_wid.setSortingEnabled(False)
            cs_list: List[Constraint] = result
            for idx, item in enumerate(cs_list):
                if typ == ConType.ALL or typ == ConType(item.type_id):
                    self.cons_tbl_wid.insertRow(0)
                    w_item = QTableWidgetItem()
                    w_item.setData(Qt.DisplayRole, item)
                    self.cons_tbl_wid.setItem(0, 0, w_item)
                    self.cons_tbl_wid.setItem(0, 1, QTableWidgetItem(f'{item.type_id} {item.co_idx+1}'))
                    sn, sc = lo.lookup_construct(ConsTrans(item.co_idx, item.type_id, item.sub_type, item.fmt))
                    wid = MyLabel(self.base.construct_color.name(), sn, sc)
                    self.cons_tbl_wid.setCellWidget(0, 2, wid)
                    chk_box = self.create_chk_box(item, (Qt.Checked if item.active else Qt.Unchecked), True, self.on_tbl_chk_act)
                    self.cons_tbl_wid.setCellWidget(0, 3, chk_box)
                    lst = ['Horizontal', 'Vertical', 'Parallel', 'Perpendicular', 'PointOnObject', 'Coincident', 'Tangent', 'Equal', 'Symmetric', 'Block']
                    chk_box = self.create_chk_box(item, (Qt.Checked if item.driving else Qt.Unchecked), item.type_id not in lst, self.on_tbl_chk_drv)
                    self.cons_tbl_wid.setCellWidget(0, 4, chk_box)
                    chk_box = self.create_chk_box(item, (Qt.Checked if item.virtual else Qt.Unchecked), True, self.on_tbl_chk_vrt)
                    self.cons_tbl_wid.setCellWidget(0, 5, chk_box)
            self.cons_tbl_wid.setSortingEnabled(__sorting_enabled)
            self.cons_tbl_wid.resizeColumnsToContents()
            self.cons_tbl_wid.resizeRowsToContents()
            self.cons_tbl_wid.setUpdatesEnabled(True)

    @flow
    def update_table(self, typ: ConType = ConType.ALL):
        self.ctrl_up = Controller(Worker(self.task_up, self.cs), self.on_result_up, 'Constraint', typ)

    def create_chk_box(self, item: Constraint, state, enable, func):
        # wid.setStyleSheet("QCheckBox {text-align: center; spacing: 0px; margin-left:50%; margin-right:50%;}"
        #                       "QCheckBox::indicator {width: 20px; height: 20px;}")
        wid = QWidget()
        lay = QHBoxLayout(wid)
        chk = TableCheckBox(item, state, enable, func)
        lay.addWidget(chk)
        lay.setAlignment(Qt.AlignCenter)
        lay.setContentsMargins(10, 0, 0, 0)
        return wid

    @Slot(object, int)
    def on_tbl_chk_drv(self, item: Constraint, state):
        xp(f'on_tbl_chk_drv idx {item.co_idx} sate {state}')
        self.cs.base.sketch.setDriving(item.co_idx, True if state else False)

    @Slot(object, int)
    def on_tbl_chk_act(self, item: Constraint, state):
        xp(f'on_tbl_chk_act idx {item.co_idx} sate {state}')
        self.cs.base.sketch.setActive(item.co_idx, True if state else False)

    @Slot(object, int)
    def on_tbl_chk_vrt(self, item: Constraint, state):
        xp(f'on_tbl_chk_vrt idx {item.co_idx} sate {state}')
        self.cs.base.sketch.setVirtualSpace(item.co_idx, True if state else False)

    @flow
    def selected(self):
        indexes: List[QModelIndex] = self.cons_tbl_wid.selectionModel().selectedRows(0)
        rows: List = [x.row() for x in sorted(indexes)]
        xp(f'selected: {rows}', **_cs)
        if len(rows) == 0:
            self.cons_btn_del.setDisabled(True)
        else:
            self.cons_btn_del.setDisabled(False)
        lo = Lookup(self.impl.sketch)
        doc_name = App.activeDocument().Name
        with observer_block():
            Gui.Selection.clearSelection(doc_name, True)
        ed_info = Gui.ActiveDocument.InEditInfo
        sk_name = ed_info[0].Name
        sel_list = []
        for item in indexes:
            co: Constraint = item.data()
            xp(f'row: {str(item.row())} idx: {co.co_idx} cons: {co}', **_cs)
            s1, s2 = lo.lookup(ConsTrans(co.co_idx, co.type_id, co.sub_type, co.fmt))
            xp(' ', s2, **_cs)
            # todo block signal reminder
            sel_list.append((doc_name, sk_name, f'Constraint{co.co_idx + 1}'))
            for thing in s1:
                sel_list.append((doc_name, sk_name, thing))
            self.select(sel_list)

    @flow
    def select(self, sel_list):
        with observer_block():
            for x, y, z in sel_list:
                Gui.Selection.addSelection(x, y, z)

    @flow
    def update_combo(self, co_list: List[Constraint]) -> None:
        co_set: Set[str] = set()
        co_set.add(ConType.ALL.value)
        for item in co_list:
            ct = ConType(item.type_id)
            co_set.add(ct.value)
        li = list(co_set)
        li.sort()
        xp('cmb text items', li, **_cs)
        self.cons_cmb_box.blockSignals(True)
        self.cons_cmb_box.clear()
        self.cons_cmb_box.addItems(li)
        self.cons_cmb_box.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.cons_cmb_box.blockSignals(False)

    @staticmethod
    @flow
    def prep_combo() -> QComboBox:
        combo_box = QComboBox(None)
        combo_box.addItem(ConType.ALL.value)
        return combo_box

    @flow
    def prep_table(self, obj: QGroupBox) -> QTableWidget:
        table_widget = QTableWidget(obj)
        table_widget.setColumnCount(6)
        w_item = QTableWidgetItem(u"Type")
        table_widget.setHorizontalHeaderItem(1, w_item)
        w_item = QTableWidgetItem(u"Info")
        table_widget.setHorizontalHeaderItem(2, w_item)
        w_item = QTableWidgetItem(u"A")
        table_widget.setHorizontalHeaderItem(3, w_item)
        w_item = QTableWidgetItem(u"D")
        table_widget.setHorizontalHeaderItem(4, w_item)
        w_item = QTableWidgetItem(u"V")
        table_widget.setHorizontalHeaderItem(5, w_item)
        self.prep_table2(table_widget)
        return table_widget

    @flow
    def prep_table2(self, tbl: QTableWidget):
        tbl.horizontalHeader().setVisible(True)
        tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        tbl.setColumnHidden(0, True)
        tbl.setColumnHidden(3, True)
        tbl.setColumnHidden(4, True)
        tbl.setColumnHidden(5, True)
        tbl.sortItems(1, Qt.AscendingOrder)
        tbl.setSortingEnabled(True)
        hh: QHeaderView = tbl.horizontalHeader()
        hh.setDefaultSectionSize(10)
        hh.setSectionResizeMode(0, QHeaderView.Fixed)
        hh.setSectionResizeMode(1, QHeaderView.Interactive)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.Fixed)
        hh.setSectionResizeMode(4, QHeaderView.Fixed)
        hh.setSectionResizeMode(5, QHeaderView.Fixed)
        vh: QHeaderView = tbl.verticalHeader()
        # noinspection PyArgumentList
        vh.setSectionResizeMode(QHeaderView.Interactive)
        vh.setMaximumSectionSize(80)
        tbl_style = "QTableView::item {" \
                    "padding-left: 5px; " \
                    "padding-right: 5px; " \
                    "border: none; " \
                    "}"
        tbl.setStyleSheet(tbl_style)
        tbl.setFont(self.base.tbl_font)

