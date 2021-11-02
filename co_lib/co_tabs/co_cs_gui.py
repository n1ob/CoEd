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
from typing import List, Set, Callable, Tuple, Dict

import FreeCAD as App
import FreeCADGui as Gui
import Sketcher
from PySide2.QtCore import Slot, QItemSelectionModel, QModelIndex, Qt, QSize, Signal, QPoint
from PySide2.QtGui import QIcon, QCursor, QClipboard
from PySide2.QtWidgets import QBoxLayout, QWidget, QGroupBox, QLabel, QTableWidget, QComboBox, QPushButton, \
    QVBoxLayout, QHBoxLayout, QTableWidgetItem, QHeaderView, QAbstractItemView, QCheckBox, QMenu, QAction, QLineEdit

from .co_cs import Constraints, Constraint
from .. import co_impl, co_gui
from ..co_base.co_cmn import ConType, wait_cursor, TableLabel, pt_typ_str, ObjType, block_signals, DIM_CS, NO_DIM_CS
from ..co_base.co_completer import PathCompleter, Root, Node
from ..co_base.co_flag import ConsTrans, Cs
from ..co_base.co_logger import xp, _cs, flow, _ev, Profile, seq_gen
from ..co_base.co_lookup import Lookup
from ..co_base.co_observer import observer_block, observer_event_provider_get

_QL = QBoxLayout


class TableCheckBox(QCheckBox):
    state_chg = Signal(object, object, int)

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
        pt = self.pos()
        self.state_chg.emit(pt, self.cs_item, state)


class TableLineEdit(QLineEdit):
    edt_finished = Signal(object, object)
    ret_pressed = Signal(object, object)
    txt_edited = Signal(object, object, str)

    def __init__(self, item: Constraint, comp_root: Node, driving: bool, parent=None):
        super().__init__()
        self.item = item
        self.setText(item.exp)
        self.editingFinished.connect(self.re_edt_finished)
        self.textEdited.connect(self.re_txt_edited)
        self.returnPressed.connect(self.re_ret_pressed)
        self.setEnabled(driving)
        self.completer = PathCompleter(comp_root)
        self.setCompleter(self.completer)

    @Slot()
    def re_edt_finished(self):
        pt = self.pos()
        self.edt_finished.emit(self, pt)

    @Slot()
    def re_ret_pressed(self):
        pt = self.pos()
        self.ret_pressed.emit(self, pt)

    @Slot(str)
    def re_txt_edited(self, txt: str):
        pt = self.pos()
        self.txt_edited.emit(self, pt, txt)


class CsGui:
    def __init__(self, base):
        self.base: co_gui.CoEdGui = base
        self.sketch: Sketcher.SketchObject = self.base.sketch
        self.impl: co_impl.CoEd = self.base.base
        self.cs: Constraints = self.impl.cs
        self.tab_cs = QWidget(None)
        self.evo = observer_event_provider_get()
        self.evo.add_selection_ex.connect(self.on_add_selection_ex)
        self.evo.clear_selection.connect(self.on_clear_selection)
        self.evo.in_edit.connect(self.on_in_edit)
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
        self.ctrl_lock = Lock()
        self.update_table()

    @flow
    def lay_get(self) -> QBoxLayout:
        self.cons_grp_box.setTitle(u"Constraints")
        self.cons_lbl_con.setText(u"Type")
        self.cons_tbl_wid = self.prep_table(self.cons_grp_box)
        self.cons_tbl_wid.itemSelectionChanged.connect(self.on_cons_tbl_sel_chg)
        self.cons_tbl_wid.itemChanged.connect(self.on_tbl_itm_chg)
        self.cons_tbl_wid.setEditTriggers(QAbstractItemView.EditKeyPressed | QAbstractItemView.DoubleClicked)

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
               [QHBoxLayout(), self.cons_lbl_con, self.cons_cmb_box, _QL.addStretch, self.cons_btn_del,
                self.cons_btn_ext],
               self.cons_tbl_wid]]
        return self.base.lay_get(li)

    @staticmethod
    @flow
    def prep_combo() -> QComboBox:
        combo_box = QComboBox(None)
        combo_box.addItem(ConType.ALL.value)
        return combo_box

    __COL_CNT = 7
    __DATA_COL = 0
    __TYPE_COL = 1
    __INFO_COL = 2
    __ACT_COL = 3
    __DRV_COL = 4
    __VIRT_COL = 5
    __EXP_COL = 6

    @flow
    def prep_table(self, obj: QGroupBox) -> QTableWidget:
        table_widget = QTableWidget(obj)
        table_widget.setColumnCount(self.__COL_CNT)
        w_item = QTableWidgetItem(u"Type")
        table_widget.setHorizontalHeaderItem(self.__TYPE_COL, w_item)
        w_item = QTableWidgetItem(u"Info")
        table_widget.setHorizontalHeaderItem(self.__INFO_COL, w_item)
        w_item = QTableWidgetItem(u"A")
        table_widget.setHorizontalHeaderItem(self.__ACT_COL, w_item)
        w_item = QTableWidgetItem(u"D")
        table_widget.setHorizontalHeaderItem(self.__DRV_COL, w_item)
        w_item = QTableWidgetItem(u"V")
        table_widget.setHorizontalHeaderItem(self.__VIRT_COL, w_item)
        w_item = QTableWidgetItem(u"Exp")
        table_widget.setHorizontalHeaderItem(self.__EXP_COL, w_item)
        self.prep_table2(table_widget)
        return table_widget

    @flow
    def prep_table2(self, tbl: QTableWidget):
        tbl.setContextMenuPolicy(Qt.CustomContextMenu)
        tbl.customContextMenuRequested.connect(self.on_tbl_ctx_menu)
        tbl.horizontalHeader().setVisible(True)
        tbl.verticalHeader().setVisible(False)
        tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        tbl.setColumnHidden(self.__DATA_COL, True)
        tbl.setColumnHidden(self.__ACT_COL, True)
        tbl.setColumnHidden(self.__DRV_COL, True)
        tbl.setColumnHidden(self.__VIRT_COL, True)
        tbl.setColumnHidden(self.__EXP_COL, True)
        tbl.sortItems(self.__TYPE_COL, Qt.AscendingOrder)
        tbl.setSortingEnabled(True)
        hh: QHeaderView = tbl.horizontalHeader()
        hh.setDefaultSectionSize(10)
        hh.setSectionResizeMode(self.__DATA_COL, QHeaderView.Fixed)
        hh.setSectionResizeMode(self.__TYPE_COL, QHeaderView.Interactive)
        hh.setSectionResizeMode(self.__INFO_COL, QHeaderView.Stretch)
        hh.setSectionResizeMode(self.__ACT_COL, QHeaderView.Fixed)
        hh.setSectionResizeMode(self.__DRV_COL, QHeaderView.Fixed)
        hh.setSectionResizeMode(self.__VIRT_COL, QHeaderView.Fixed)
        hh.setSectionResizeMode(self.__EXP_COL, QHeaderView.Interactive)
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

    @flow
    def handle_ext_table(self):
        si: QSize = self.cons_tbl_wid.size()
        sii: QSize = self.base.size()
        if self.ext_toggle:
            hh: QHeaderView = self.cons_tbl_wid.horizontalHeader()
            hh.setSectionResizeMode(self.__INFO_COL, QHeaderView.Interactive)
            hh.setSectionResizeMode(self.__EXP_COL, QHeaderView.Stretch)
            self.cons_tbl_wid.setColumnHidden(self.__ACT_COL, False)
            self.cons_tbl_wid.setColumnHidden(self.__DRV_COL, False)
            self.cons_tbl_wid.setColumnHidden(self.__VIRT_COL, False)
            self.cons_tbl_wid.setColumnHidden(self.__EXP_COL, False)
            self.cons_tbl_wid.resizeColumnsToContents()
            self.cons_tbl_wid.resizeRowsToContents()
            i = 0
            i += self.cons_tbl_wid.columnWidth(self.__ACT_COL)
            i += self.cons_tbl_wid.columnWidth(self.__DRV_COL)
            i += self.cons_tbl_wid.columnWidth(self.__VIRT_COL)
            i += self.cons_tbl_wid.columnWidth(self.__EXP_COL)
            # self.cons_tbl_wid.setColumnWidth(self.__EXP_COL, 400)
            si.setWidth(si.width() + i)
            self.cons_tbl_wid.resize(si)
            sii.setWidth(sii.width() + i)
            self.base.resize(sii)
            self.cons_btn_ext.setText('<')
        else:
            hh: QHeaderView = self.cons_tbl_wid.horizontalHeader()
            hh.setSectionResizeMode(self.__INFO_COL, QHeaderView.Stretch)
            hh.setSectionResizeMode(self.__EXP_COL, QHeaderView.Interactive)
            i = 0
            i += self.cons_tbl_wid.columnWidth(self.__ACT_COL)
            i += self.cons_tbl_wid.columnWidth(self.__DRV_COL)
            i += self.cons_tbl_wid.columnWidth(self.__VIRT_COL)
            i += self.cons_tbl_wid.columnWidth(self.__EXP_COL)
            self.cons_tbl_wid.setColumnHidden(self.__ACT_COL, True)
            self.cons_tbl_wid.setColumnHidden(self.__DRV_COL, True)
            self.cons_tbl_wid.setColumnHidden(self.__VIRT_COL, True)
            self.cons_tbl_wid.setColumnHidden(self.__EXP_COL, True)
            self.cons_tbl_wid.resizeColumnsToContents()
            self.cons_tbl_wid.resizeRowsToContents()
            si.setWidth(si.width() - i)
            self.cons_tbl_wid.resize(si)
            sii.setWidth(sii.width() - i)
            self.base.resize(sii)
            self.cons_btn_ext.setText('>')
        self.ext_toggle = not self.ext_toggle

    # ------------------------------------------------------------------------------

    @flow
    @Slot(object)
    def on_tbl_ctx_menu(self, pos):
        xp('pos {} column {}'.format(pos, self.cons_tbl_wid.horizontalHeader().logicalIndexAt(pos)))
        xp(self.cons_tbl_wid.indexAt(pos))
        xp(self.cons_tbl_wid.itemAt(pos))
        wi: QTableWidgetItem = self.cons_tbl_wid.itemAt(pos)
        self.context_menu(pos, wi)

    @flow
    @Slot(object)
    def on_ctx_action(self, act):
        act: QAction
        xp('action', act.text(), act.data(), act.objectName())
        w_item: QTableWidgetItem = act.data()
        self.context_action(act, w_item)

    @flow
    @Slot(object)
    def on_tbl_itm_chg(self, w_item):
        w_item: QTableWidgetItem
        xp(w_item.row(), w_item.column(), w_item.text())
        if w_item.column() == CsGui.__TYPE_COL:
            item0: QTableWidgetItem = self.cons_tbl_wid.item(w_item.row(), CsGui.__DATA_COL)
            cs_item: Constraint = item0.data(Qt.UserRole)
            cs_item.name = w_item.text()
            self.sketch.renameConstraint(cs_item.cs_idx, w_item.text())
            self.sketch.recompute()
        elif w_item.column() == CsGui.__EXP_COL:
            pass
        else:
            xp('not expected column with changed item')

    @flow
    @Slot(object)
    def on_in_edit(self, obj):
        if obj.TypeId == ObjType.VIEW_PROVIDER_SKETCH:
            ed_info = Gui.ActiveDocument.InEditInfo
            if (ed_info is not None) and (ed_info[0].TypeId == ObjType.SKETCH_OBJECT):
                self.sketch = ed_info[0]

    @flow
    @Slot(object)
    def on_clear_selection(self, doc):
        xp(f'on_clear_selection: doc:', str(doc), **_cs)
        self.update_table()

    @flow
    @Slot(object)
    def on_add_selection_ex(self, obj, pnt):
        xp(f'on_add_selection_ex: obj:', str(obj), **_ev)
        self.select_constraints(obj, pnt)

    @flow
    @Slot(object, object, int)
    def on_tbl_chk_driving(self, pt, item: Constraint, state):
        xp(f'on_tbl_chk_drv idx {item.cs_idx} state {state}', **_ev)
        model_idx: QModelIndex = self.cons_tbl_wid.indexAt(pt)
        xp(pt, model_idx)
        row = model_idx.row()
        b = True if state else False
        self.sketch.setDriving(item.cs_idx, b)
        item.driving = b
        self.chg_icon(item)
        if item.type_id in DIM_CS:
            xp('toggle item edit', item.type_id, 'row', row, **_cs)
            le: TableLineEdit = self.cons_tbl_wid.cellWidget(row, CsGui.__EXP_COL)
            if item.driving:
                le.setEnabled(True)
            else:
                le.setEnabled(False)
                item.exp = ''
                le.setText('')
        self.sketch.recompute()

    @flow
    @Slot(object, object, int)
    def on_tbl_chk_active(self, pt, item: Constraint, state):
        xp(f'on_tbl_chk_act idx {item.cs_idx} sate {state}', **_ev)
        b = True if state else False
        self.sketch.setActive(item.cs_idx, b)
        item.driving = b

    @flow
    @Slot(object, object, int)
    def on_tbl_chk_virtual(self, pt, item: Constraint, state):
        xp(f'on_tbl_chk_vrt idx {item.cs_idx} sate {state}', **_ev)
        b = True if state else False
        self.sketch.setVirtualSpace(item.cs_idx, b)
        item.virtual = b

    @flow
    @Slot(int)
    def on_cs_del(self, i: int):
        xp('NOP Constraints deleted', i, **_ev)

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
        self.handle_ext_table()

    @flow
    def on_cons_type_cmb_chg(self, txt):
        ct: ConType = ConType(txt)
        with Profile(enable=False):
            self.update_table(typ=ct)

    @flow
    def on_cons_tbl_sel_chg(self):
        xp('on_cons_tbl_sel_chg')
        self.selected()

    @flow
    @Slot(object, object)
    def on_li_edt_finished(self, le: TableLineEdit, pt: QPoint):
        model_idx: QModelIndex = self.cons_tbl_wid.indexAt(pt)
        row, col = model_idx.row(), model_idx.column()
        xp('exp changed: text', le.text(), 'pt', pt, 'ModelIdx', model_idx, 'row', row, 'col', col)
        self.eval_expressions(le)

    @flow
    @Slot(object, object, str)
    def on_li_edt_changed(self, item, pt, txt):
        pass

    # ------------------------------------------------------------------------------

    @flow
    def context_menu(self, pos, wi):
        if wi and (wi.column() == CsGui.__TYPE_COL):
            act_edt = QAction('Edit')
            act_edt.setData(self.cons_tbl_wid.itemAt(pos))
            act_edt.setObjectName('EDIT')
            act_cpy = QAction('Copy')
            act_cpy.setData(self.cons_tbl_wid.itemAt(pos))
            act_cpy.setObjectName('COPY')
            act_pst = QAction('Paste')
            act_pst.setData(self.cons_tbl_wid.itemAt(pos))
            act_pst.setObjectName('PASTE')
            menu = QMenu()
            menu.addAction(act_edt)
            menu.addSeparator()
            menu.addAction(act_cpy)
            menu.addAction(act_pst)
            menu.triggered.connect(self.on_ctx_action)
            menu.exec_(QCursor.pos())
        if wi.column() == CsGui.__EXP_COL:
            # todo handle line edit
            pass

    __seq = seq_gen()

    @flow
    def context_action(self, act, w_item):
        if w_item:
            clip = QClipboard()
            if act.objectName() == 'EDIT':
                xp('row', w_item.row(), 'column', w_item.column())
                self.cons_tbl_wid.editItem(w_item)
            elif act.objectName() == 'COPY':
                xp('row', w_item.row(), 'column', w_item.column())
                clip.setText(w_item.text())
            elif act.objectName() == 'PASTE':
                xp('row', w_item.row(), 'column', w_item.column())
                if w_item.column() == CsGui.__TYPE_COL:
                    w_item.setText(f'{clip.text()}_{next(CsGui.__seq)}')

    @flow
    def eval_expressions(self, le: QLineEdit):
        e = None
        try:
            e = self.sketch.evalExpression(le.text())
            xp('result', e)
        except RuntimeError as err:
            for x in err.args:
                b: Dict[str, str] = x
                xp(b.get('sErrMsg'))
            xp('result', e)
            xp('RuntimeError', err)
            le.setText(str(le.item.exp))
            return
        except Exception as err:
            xp('result', e)
            xp('Exception', err)
            le.setText(str(le.item.exp))
            return
        le.item.exp = le.text()
        if le.item.name:
            s = f'.Constraints.{le.item.name}'
        else:
            s = f'Constraints[{le.item.cs_idx}]'
        try:
            self.sketch.setExpression(s, le.text())
        except RuntimeError as err:
            xp('err msg')
            xp('RuntimeError', err)
            le.setText(str(le.item.exp))
            return
        self.sketch.recompute()

    @flow
    def task_up(self, cs):
        cs_list: List[Constraint] = self.cs.constraints
        return cs_list

    @flow(short=True)
    def on_result_up(self, result, typ, id_lst):
        xp('on_result_up', result, typ, id_lst, **_cs)
        id_lst: List[int]
        self.cons_tbl_wid.setUpdatesEnabled(False)
        self.cons_tbl_wid.setRowCount(0)
        __sorting_enabled = self.cons_tbl_wid.isSortingEnabled()
        self.cons_tbl_wid.setSortingEnabled(False)
        cs_list: List[Constraint] = result
        root = self.exp_tree(cs_list)
        with block_signals(self.cons_tbl_wid):
            for idx, item in enumerate(cs_list):
                xp('idx, item', idx, item, **_cs)
                if (id_lst is None and (typ == ConType.ALL or typ == ConType(item.type_id))) \
                        or (id_lst is not None and idx in id_lst):
                    self.cons_tbl_wid.insertRow(0)
                    w_item = QTableWidgetItem()
                    w_item.setData(Qt.UserRole, item)
                    self.cons_tbl_wid.setItem(0, self.__DATA_COL, w_item)

                    w_item = QTableWidgetItem()
                    # w_item.setFlags(w_item.flags() & ~Qt.ItemIsEditable)
                    w_item.setIcon(QIcon(item.ico_no if item.driving else item.ico_alt_no))
                    s = f'{item.type_id} {item.cs_idx + 1}' if item.name == '' else item.name
                    w_item.setText(s)
                    self.cons_tbl_wid.setItem(0, self.__TYPE_COL, w_item)

                    sn, sc, se = self.split(item.cs_idx, item.sub_type)
                    xp('sn, sc, se', sn, sc, se, **_cs)
                    wid = TableLabel(sn, sc, se)
                    self.cons_tbl_wid.setCellWidget(0, self.__INFO_COL, wid)

                    chk_box = self.create_chk_box(item, (Qt.Checked if item.active else Qt.Unchecked), True,
                                                  self.on_tbl_chk_active)
                    self.cons_tbl_wid.setCellWidget(0, self.__ACT_COL, chk_box)

                    chk_box = self.create_chk_box(item, (Qt.Checked if item.driving else Qt.Unchecked),
                                                  item.type_id in DIM_CS, self.on_tbl_chk_driving)
                    self.cons_tbl_wid.setCellWidget(0, self.__DRV_COL, chk_box)

                    chk_box = self.create_chk_box(item, (Qt.Checked if item.virtual else Qt.Unchecked), True,
                                                  self.on_tbl_chk_virtual)
                    self.cons_tbl_wid.setCellWidget(0, self.__VIRT_COL, chk_box)

                    if item.type_id in NO_DIM_CS:
                        w_item = QTableWidgetItem()
                        w_item.setFlags(w_item.flags() & ~Qt.ItemIsEditable)
                        self.cons_tbl_wid.setItem(0, self.__EXP_COL, w_item)
                    else:
                        le = TableLineEdit(item, root.root(), item.driving)
                        le.txt_edited.connect(self.on_li_edt_changed)
                        le.edt_finished.connect(self.on_li_edt_finished)
                        self.cons_tbl_wid.setCellWidget(0, self.__EXP_COL, le)

        self.cons_tbl_wid.setSortingEnabled(__sorting_enabled)
        self.cons_tbl_wid.resizeColumnsToContents()
        self.cons_tbl_wid.resizeRowsToContents()
        self.cons_tbl_wid.setUpdatesEnabled(True)

    @staticmethod
    def exp_tree(lst: List[Constraint]) -> Root:
        dim_lst = list()
        dim_named_lst = list()
        for item in lst:
            if item.type_id in DIM_CS:
                if item.name:
                    dim_named_lst.append(item)
                else:
                    dim_lst.append(item)
        ro = Root()
        r: Node = ro.root()
        for x in dim_lst:
            r.add_child(Node(f'Constraints[{x.cs_idx}]'))
        if dim_named_lst:
            r1 = r.add_child(Node('Constraints'))
            for y in dim_named_lst:
                r1.add_child(Node(y.name))
        ro.sort()
        return ro

    @flow
    def chg_icon(self, item):
        row_cnt = self.cons_tbl_wid.rowCount()
        for x in range(row_cnt):
            item0: QTableWidgetItem = self.cons_tbl_wid.item(x, CsGui.__DATA_COL)
            da = item0.data(Qt.UserRole)
            if item and da is item:
                xp('if it.data(Qt.UserRole) is item', item.cs_idx, da.cs_idx)
                item1: QTableWidgetItem = self.cons_tbl_wid.item(x, CsGui.__TYPE_COL)
                with block_signals(self.cons_tbl_wid):
                    item1.setIcon(QIcon(item.ico_no if item.driving else item.ico_alt_no))

    @flow
    def split(self, idx, sub_type, gui=True) -> Tuple[str, str, str]:
        sk = self.sketch
        cs: Sketcher.Constraint = sk.Constraints[idx]
        t = (
        (Cs.F, 'First', Cs.FP, 'FirstPos'), (Cs.S, 'Second', Cs.SP, 'SecondPos'), (Cs.T, 'Third', Cs.TP, 'ThirdPos'))
        res_n, res_c, res_e = list(), list(), list()
        for geo, g_name, typ, t_name in t:
            if geo in sub_type:
                r = Lookup.translate_geo_idx(getattr(cs, g_name), gui)
                s = f'{r}.{pt_typ_str[getattr(cs, t_name)]}' if typ in sub_type else f'{r}'
                if getattr(cs, g_name) < 0:
                    res_e.append(s)
                else:
                    res_c.append(s) if sk.getConstruction(getattr(cs, g_name)) else res_n.append(s)
        return ' '.join(res_n), ' '.join(res_c), ' '.join(res_e)

    @flow
    def update_table(self, typ=ConType.ALL, id_lst=None):
        ret = self.task_up(self.cs)
        self.on_result_up(ret, typ, id_lst)
        # self.ctrl_up = Controller(Worker(self.task_up, self.cs), self.on_result_up, 'Constraint', typ, id_lst)

    # ------------------------------------------------------------------------------

    @flow
    def delete(self):
        with wait_cursor():
            mod: QItemSelectionModel = self.cons_tbl_wid.selectionModel()
            rows: List[QModelIndex] = mod.selectedRows(0)
            del_list: List[int] = list()
            for idx in rows:
                xp(str(idx.row()), ':', str(idx.data(Qt.UserRole)), idx.data(Qt.UserRole).cs_idx, **_cs)
                del_list.append(idx.data(Qt.UserRole).cs_idx)
            doc_name = App.activeDocument().Name
            Gui.Selection.clearSelection(doc_name, True)
            self.cs.constraints_delete(del_list)
        self.update_table()

    @flow
    def create_chk_box(self, item: Constraint, state, enable, func):
        # wid.setStyleSheet("QCheckBox {text-align: center; spacing: 0px; margin-left:50%; margin-right:50%;}"
        #                       "QCheckBox::indicator {width: 20px; height: 20px;}")
        wid = QWidget()
        lay = QHBoxLayout(wid)
        # can't enable driving on pure extern constraints
        if item.pure_extern:
            enable = False
        chk = TableCheckBox(item, state, enable, func)
        lay.addWidget(chk)
        lay.setAlignment(Qt.AlignCenter)
        lay.setContentsMargins(10, 0, 0, 0)
        return wid

    @flow
    def selected(self):
        indexes: List[QModelIndex] = self.cons_tbl_wid.selectionModel().selectedRows(0)
        rows: List = [x.row() for x in sorted(indexes)]
        xp(f'selected: {rows}', **_cs)
        if len(rows) == 0:
            self.cons_btn_del.setDisabled(True)
        else:
            self.cons_btn_del.setDisabled(False)
        lo = Lookup(self.sketch)
        doc_name = App.activeDocument().Name
        with observer_block():
            Gui.Selection.clearSelection(doc_name, True)
        ed_info = Gui.ActiveDocument.InEditInfo
        sk_name = ed_info[0].Name
        cs_lst: List[Constraint] = [item.data(Qt.UserRole) for item in indexes]
        xp('cs_lst', cs_lst, **_cs)
        edg_set: Set[str] = Lookup.constraint_connected_edges(cs_lst)
        xp('edg_set', list(edg_set), **_cs)
        edg_set.update({f'Constraint{cs.cs_idx + 1}' for cs in cs_lst})
        xp('edg_set', list(edg_set), **_cs)
        for cs in cs_lst:
            s1, s2 = lo.lookup_ui_names(ConsTrans(cs.cs_idx, cs.type_id, cs.sub_type, cs.fmt))
            edg_set.update(s1)
        xp('edg_set', list(edg_set), **_cs)
        self.select(doc_name, sk_name, edg_set)

    @flow
    def select_constraints(self, obj, pnt):
        xp('select_constraints', obj, pnt, **_cs)
        from_gui: bool = True
        if App.Vector(pnt) == App.Vector(0, 0, 0):
            from_gui = False
        xp('from gui', from_gui, **_cs)
        obj: List[Gui.SelectionObject]
        for sel_ex in obj:
            res: List[int] = list()
            xp('sel_ex', sel_ex.FullName, **_cs)
            if sel_ex.TypeName == ObjType.SKETCH_OBJECT:
                for sub_name in sel_ex.SubElementNames:
                    typ, no = Lookup.deconstruct_ui_name(sub_name)
                    if typ == 'Vertex':
                        geo, pos = self.sketch.getGeoVertexIndex(no)
                        xp(f'received: gui: {from_gui} {typ} {no} geo: ({geo}.{pos})', **_cs)
                    elif typ == 'ExternalEdge':
                        xp(f'received: gui: {from_gui} {typ} {no}', **_cs)
                        res.append(-1 * (no + 2))
                    elif typ == 'Edge':
                        xp(f'received: gui: {from_gui} {typ} {no}', **_cs)
                        res.append(no - 1)
                    elif typ == 'Constraint':
                        xp(f'received: gui: {from_gui} {typ} {no}', **_cs)
                    else:
                        xp(f'received: gui: {from_gui} {typ} {no}', **_cs)
                if not from_gui:
                    xp('ignore if not from gui', **_cs)
                    return
                sk: Sketcher.Sketch = sel_ex.Object
                lst: List[int] = Lookup.matching_constraints(res, sk.Constraints)
                self.update_table(id_lst=lst)

    @flow
    def select(self, doc_name, sk_name, sel_set):
        with observer_block():
            for x in sel_set:
                Gui.Selection.addSelection(doc_name, sk_name, x)

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

    '''
    sel_ex = {SelectionObject} <SelectionObject>
     Document = {Document} <Document object at 00000207C202D330>
     DocumentName = {str} 'Test'
     FullName = {str} '(App.getDocument(\'Test\').getObject(\'Sketch\'),[\'Edge2\',])'
     HasSubObjects = {bool} True
     Module = {str} 'Gui'
     Object = {SketchObject} <Sketcher::SketchObject>
     ObjectName = {str} 'Sketch'
     PickedPoints = {tuple: 1} Vector (7.226385593414307, 5.254661560058594, 0.00800000037997961)
      0 = {Vector: 3} Vector (7.226385593414307, 5.254661560058594, 0.00800000037997961)
      __len__ = {int} 1
     SubElementNames = {tuple: 1} Edge2
      0 = {str} 'Edge2'
      __len__ = {int} 1
     SubObjects = {tuple: 1} <Edge object at 00000207C25B9240>
      0 = {Edge} <Edge object at 000002080354F150>
      __len__ = {int} 1
     TypeId = {str} 'Gui::SelectionObject'
     TypeName = {str} 'Sketcher::SketchObject'
    '''
