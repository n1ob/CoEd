from threading import Lock
from typing import List, Set, Callable, Tuple

import FreeCAD as App
import FreeCADGui as Gui
import Sketcher
from PySide2.QtCore import Slot, QItemSelectionModel, QModelIndex, Qt, QSize, Signal
from PySide2.QtWidgets import QBoxLayout, QWidget, QGroupBox, QLabel, QTableWidget, QComboBox, QPushButton, QVBoxLayout, \
    QHBoxLayout, QTableWidgetItem, QHeaderView, QAbstractItemView, QCheckBox

from .co_cs import Constraints, Constraint
from .. import co_impl, co_gui
from ..co_base.co_cmn import ConType, wait_cursor, TableLabel, pt_typ_str, ObjType
from ..co_base.co_flag import ConsTrans, Cs
from ..co_base.co_logger import xp, _cs, flow, _ev, Profile
from ..co_base.co_lookup import Lookup
from ..co_base.co_observer import observer_block, observer_event_provider_get

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
        tbl.verticalHeader().setVisible(False)
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

    # ------------------------------------------------------------------------------

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

    @Slot(object, int)
    def on_tbl_chk_drv(self, item: Constraint, state):
        xp(f'on_tbl_chk_drv idx {item.co_idx} sate {state}')
        self.sketch.setDriving(item.co_idx, True if state else False)

    @Slot(object, int)
    def on_tbl_chk_act(self, item: Constraint, state):
        xp(f'on_tbl_chk_act idx {item.co_idx} sate {state}')
        self.sketch.setActive(item.co_idx, True if state else False)

    @Slot(object, int)
    def on_tbl_chk_vrt(self, item: Constraint, state):
        xp(f'on_tbl_chk_vrt idx {item.co_idx} sate {state}')
        self.sketch.setVirtualSpace(item.co_idx, True if state else False)

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
            self.update_table(typ=ct)

    @flow
    def on_cons_tbl_sel_chg(self):
        self.selected()

    # ------------------------------------------------------------------------------

    @flow
    def task_up(self, cs):
        cs_list: List[Constraint] = self.cs.constraints
        return cs_list

    @flow(short=True)
    def on_result_up(self, result, typ, id_lst):
        xp('on_result_up', result, typ, id_lst)
        id_lst: List[int]
        # lo = Lookup(self.cs.base.sketch)
        self.cons_tbl_wid.setUpdatesEnabled(False)
        self.cons_tbl_wid.setRowCount(0)
        __sorting_enabled = self.cons_tbl_wid.isSortingEnabled()
        self.cons_tbl_wid.setSortingEnabled(False)
        cs_list: List[Constraint] = result
        for idx, item in enumerate(cs_list):
            xp('idx, item', idx, item)
            if (id_lst is None and (typ == ConType.ALL or typ == ConType(item.type_id))) \
                    or (id_lst is not None and idx in id_lst):
                self.cons_tbl_wid.insertRow(0)
                w_item = QTableWidgetItem()
                w_item.setData(Qt.DisplayRole, item)
                self.cons_tbl_wid.setItem(0, 0, w_item)
                self.cons_tbl_wid.setItem(0, 1, QTableWidgetItem(f'{item.type_id} {item.co_idx + 1}'))
                sn, sc, se = self.split(item.co_idx, item.sub_type)
                # sn, sc, se = lo.split_cs_geo_types(ConsTrans(item.co_idx, item.type_id, item.sub_type, item.fmt))
                xp('sn, sc, se', sn, sc, se)
                wid = TableLabel(sn, sc, se)
                self.cons_tbl_wid.setCellWidget(0, 2, wid)
                chk_box = self.create_chk_box(item, (Qt.Checked if item.active else Qt.Unchecked), True,
                                              self.on_tbl_chk_act)
                self.cons_tbl_wid.setCellWidget(0, 3, chk_box)
                lst = ['Horizontal', 'Vertical', 'Parallel', 'Perpendicular', 'PointOnObject', 'Coincident',
                       'Tangent', 'Equal', 'Symmetric', 'Block']
                chk_box = self.create_chk_box(item, (Qt.Checked if item.driving else Qt.Unchecked),
                                              item.type_id not in lst, self.on_tbl_chk_drv)
                self.cons_tbl_wid.setCellWidget(0, 4, chk_box)
                chk_box = self.create_chk_box(item, (Qt.Checked if item.virtual else Qt.Unchecked), True,
                                              self.on_tbl_chk_vrt)
                self.cons_tbl_wid.setCellWidget(0, 5, chk_box)
        self.cons_tbl_wid.setSortingEnabled(__sorting_enabled)
        self.cons_tbl_wid.resizeColumnsToContents()
        self.cons_tbl_wid.resizeRowsToContents()
        self.cons_tbl_wid.setUpdatesEnabled(True)

    def split(self, idx, sub_type, gui=True) -> Tuple[str, str, str]:
        sk = self.sketch
        cs: Sketcher.Constraint = sk.Constraints[idx]
        t = ((Cs.F, 'First', Cs.FP, 'FirstPos'), (Cs.S, 'Second', Cs.SP, 'SecondPos'), (Cs.T, 'Third', Cs.TP, 'ThirdPos'))
        res_n = list()
        res_c = list()
        res_e = list()
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
                xp(str(idx.row()), ':', str(idx.data()), idx.data().co_idx, **_cs)
                del_list.append(idx.data().co_idx)
            doc_name = App.activeDocument().Name
            # todo clear selection reminder
            Gui.Selection.clearSelection(doc_name, True)
            self.cs.constraints_delete(del_list)
        self.update_table()

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
        cs_lst: List[Constraint] = [item.data() for item in indexes]
        xp('cs_lst', cs_lst, **_cs)
        edg_set: Set[str] = Lookup.constraint_connected_edges(cs_lst)
        xp('edg_set', list(edg_set), **_cs)
        edg_set.update({f'Constraint{cs.co_idx + 1}' for cs in cs_lst})
        xp('edg_set', list(edg_set), **_cs)
        for cs in cs_lst:
            s1, s2 = lo.lookup_ui_names(ConsTrans(cs.co_idx, cs.type_id, cs.sub_type, cs.fmt))
            edg_set.update(s1)
        xp('edg_set', list(edg_set), **_cs)
        self.select(doc_name, sk_name, edg_set)

    @flow
    def select_constraints(self, obj, pnt):
        xp('select_constraints', obj, pnt, **_cs)
        from_gui: bool = True
        if App.Vector(pnt) == App.Vector(0, 0, 0):
            from_gui = False
        xp('from gui', from_gui)
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
                        res.append(-1*(no+2))
                    elif typ == 'Edge':
                        xp(f'received: gui: {from_gui} {typ} {no}', **_cs)
                        res.append(no - 1)
                    elif typ == 'Constraint':
                        xp(f'received: gui: {from_gui} {typ} {no}', **_cs)
                    else:
                        xp(f'received: gui: {from_gui} {typ} {no}', **_cs)
                if not from_gui:
                    xp('ignore if not from gui')
                    return
                sk: Sketcher.Sketch = sel_ex.Object
                lst: List[int] = Lookup.matching_constraints(res, sk.Constraints)
                self.update_table(id_lst=lst)

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

