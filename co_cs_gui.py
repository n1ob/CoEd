from typing import List, Set

from PySide2.QtCore import Slot, QItemSelectionModel, QModelIndex, Qt
from PySide2.QtWidgets import QBoxLayout, QWidget, QGroupBox, QLabel, QTableWidget, QComboBox, QPushButton, QVBoxLayout, \
    QHBoxLayout, QTableWidgetItem, QHeaderView

import FreeCAD as App
import FreeCADGui as Gui

import co_gui
import co_impl
from co_cmn import ConType, ConsTrans
from co_cs import Constraints, Constraint
from co_logger import xp, _cs, flow, _ev, Profile
from co_lookup import Lookup
from co_observer import observer_event_provider_get

_QL = QBoxLayout


class CsGui:
    def __init__(self, base):
        self.base: co_gui.CoEdGui = base
        self.impl: co_impl.CoEd = self.base.base
        self.cs: Constraints = self.impl.cs
        self.tab_cs = QWidget(None)
        # xp('impl.ev.cons_chg.connect(self.on_cons_chg)', **_ev)
        # self.impl.ev.cons_chg.connect(self.on_cs_chg)
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
        self.tab_cs.setLayout(self.lay_get())
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
        # noinspection PyArgumentList
        li = [QVBoxLayout(), self.cons_grp_box,
              [QVBoxLayout(self.cons_grp_box),
               [QHBoxLayout(), self.cons_lbl_con, self.cons_cmb_box, _QL.addStretch, self.cons_btn_del],
               self.cons_tbl_wid]]
        return self.base.lay_get(li)

    # @flow
    # @Slot(str)
    # def on_cs_chg(self, words):
    #     xp('Constraints changed', words, **_ev)
    #     co_list: List[Constraint] = self.cs.constraints
    #     # co_list: List[Constraint] = self.impl.constraints_get_list()
    #     self.update_combo(co_list)

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
    def on_cons_type_cmb_chg(self, txt):
        ct: ConType = ConType(txt)
        with Profile(enable=False):
            self.update_table(ct)

    @flow
    def on_cons_tbl_sel_chg(self):
        self.selected()

    @flow
    def delete(self):
        mod: QItemSelectionModel = self.cons_tbl_wid.selectionModel()
        rows: List[QModelIndex] = mod.selectedRows(2)
        del_list: List[int] = list()
        for idx in rows:
            xp(str(idx.row()), ':', str(idx.data()), idx.data().co_idx, **_cs)
            del_list.append(idx.data().co_idx)
        self.cs.constraints_delete(del_list)
        self.update_table()

    @flow
    def update_table(self, typ: ConType = ConType.ALL):
        # self.cons_tbl_wid.setEnabled(False)
        self.cons_tbl_wid.setUpdatesEnabled(False)
        # self.cons_tbl_wid.clearContents()
        self.cons_tbl_wid.setRowCount(0)
        __sorting_enabled = self.cons_tbl_wid.isSortingEnabled()
        self.cons_tbl_wid.setSortingEnabled(False)
        co_list: List[Constraint] = self.cs.constraints
        for idx, item in enumerate(co_list):
            if typ == ConType.ALL or typ == ConType(item.type_id):
                li: List[int] = list()
                li.insert(0, idx)
                self.cons_tbl_wid.insertRow(0)
                self.cons_tbl_wid.setItem(0, 0, QTableWidgetItem(item.type_id))
                self.cons_tbl_wid.setItem(0, 1, QTableWidgetItem(str(item)))
                w_item = QTableWidgetItem()
                w_item.setData(Qt.DisplayRole, item)
                self.cons_tbl_wid.setItem(0, 2, w_item)
        self.cons_tbl_wid.setSortingEnabled(__sorting_enabled)
        hh: QHeaderView = self.cons_tbl_wid.horizontalHeader()
        hh.resizeSections(QHeaderView.ResizeToContents)
        # vh: QHeaderView = self.cons_tbl_wid.verticalHeader()
        # self.cons_tbl_wid.setEnabled(True)
        self.cons_tbl_wid.setUpdatesEnabled(True)

    @flow
    def selected(self):
        indexes: List[QModelIndex] = self.cons_tbl_wid.selectionModel().selectedRows(2)
        rows: List = [x.row() for x in sorted(indexes)]
        xp(f'selected: {rows}', **_cs)
        if len(rows) == 0:
            self.cons_btn_del.setDisabled(True)
        else:
            self.cons_btn_del.setDisabled(False)

        lo = Lookup(self.impl.sketch)
        doc_name = App.activeDocument().Name
        observer_event_provider_get().blockSignals(True)
        Gui.Selection.clearSelection(doc_name, True)
        observer_event_provider_get().blockSignals(False)
        ed_info = Gui.ActiveDocument.InEditInfo
        sk_name = ed_info[0].Name

        for item in indexes:
            co: Constraint = item.data()
            xp(f'row: {str(item.row())} idx: {co.co_idx} cons: {co}', **_cs)
            s1, s2 = lo.lookup(ConsTrans(co.co_idx, co.type_id, co.sub_type, co.fmt))
            xp(' ', s2, **_cs)
            Gui.Selection.addSelection(doc_name, sk_name, f'Constraint{co.co_idx + 1}')
            for thing in s1:
                Gui.Selection.addSelection(doc_name, sk_name, thing)

            # sk_name = ed_info[0].Name
            # Gui.Selection.addSelection(doc_name, sk_name, 'Edge1')
            # Gui.Selection.clearSelection()
            # Gui.Selection.addSelection('Test','Sketch','Constraint7')

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
        table_widget.setColumnCount(3)
        w_item = QTableWidgetItem(u"Type")
        table_widget.setHorizontalHeaderItem(0, w_item)
        w_item = QTableWidgetItem(u"Info")
        table_widget.setHorizontalHeaderItem(1, w_item)
        self.base.prep_table(table_widget)
        return table_widget
