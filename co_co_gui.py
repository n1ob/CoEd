from typing import List, Set, Tuple
import FreeCAD as App
import FreeCADGui as Gui
from PySide2.QtCore import Qt, QModelIndex, QItemSelectionModel, Slot
from PySide2.QtWidgets import QWidget, QGroupBox, QLabel, QDoubleSpinBox, QPushButton, QTableWidget, QBoxLayout, \
    QVBoxLayout, QHBoxLayout, QTableWidgetItem

import co_gui
import co_impl
from co_cmn import GeoPtn, pt_typ_int, fmt_vec, pt_typ_str
from co_co import CoPoints, CoPoint, GeoId
from co_logger import flow, xp, _co, _ev, xps

_QL = QBoxLayout


class CoGui:
    def __init__(self, base):
        self.base: co_gui.CoEdGui = base
        self.impl: co_impl.CoEd = self.base.base
        self.co: CoPoints = self.impl.co_points
        self.tab_co = QWidget(None)
        xp('impl.ev.coin_pts_chg.connect(self.on_co_chg)', **_ev)
        self.impl.ev.coin_pts_chg.connect(self.on_co_chg)

        self.co_grp_box: QGroupBox = QGroupBox(None)
        self.co_lbl: QLabel = QLabel()
        self.co_dbl_sp_box: QDoubleSpinBox = QDoubleSpinBox()
        self.co_btn_create: QPushButton = QPushButton()
        self.co_btn_create.setDisabled(True)
        self.co_tbl_wid: QTableWidget = QTableWidget()
        self.tab_co.setLayout(self.lay_get())
        self.update_table()

    @flow
    def lay_get(self) -> QBoxLayout:
        self.co_grp_box.setTitle(u"Coincident")
        self.co_lbl.setText(u"Snap Dist")
        self.co_dbl_sp_box = self.base.db_s_box_get(self.co.tolerance, 2, 0.1, self.on_co_tol_chg)
        self.co_btn_create.clicked.connect(self.on_co_create_btn_clk)
        self.co_btn_create.setText(u"Create")
        self.co_tbl_wid = self.prep_table(self.co_grp_box)
        self.co_tbl_wid.itemSelectionChanged.connect(self.on_co_tbl_sel_chg)
        # noinspection PyArgumentList
        li = [QVBoxLayout(), self.co_grp_box,
              [QVBoxLayout(self.co_grp_box),
               [QHBoxLayout(), self.co_lbl, self.co_dbl_sp_box, _QL.addStretch, self.co_btn_create],
               self.co_tbl_wid]]
        return self.base.lay_get(li)

    @flow
    @Slot(str)
    def on_co_chg(self, words):
        xp('Co changed', words, **_ev)

    @flow
    def on_co_tol_chg(self, val):
        value = self.co_dbl_sp_box.value()
        self.co.tolerance = value
        self.update_table()

    @flow
    def on_co_create_btn_clk(self):
        self.create()

    @flow
    def on_co_tbl_sel_chg(self):
        self.selected()

    @flow
    def prep_table(self, obj: QGroupBox) -> QTableWidget:
        table_widget = QTableWidget(obj)
        table_widget.setColumnCount(3)
        w_item = QTableWidgetItem(u"Point")
        table_widget.setHorizontalHeaderItem(0, w_item)
        w_item = QTableWidgetItem(u"Idx")
        table_widget.setHorizontalHeaderItem(1, w_item)
        self.base.prep_table(table_widget)
        return table_widget

    @flow
    def create(self):
        mod: QItemSelectionModel = self.co_tbl_wid.selectionModel()
        rows: List[QModelIndex] = mod.selectedRows(2)
        create_list: List[CoPoint] = [x.data() for x in rows]
        for idx in rows:
            xp(idx.row(), ':', idx.data(), **_co)
        self.co.create(create_list)
        self.update_table()

    @flow
    def update_table(self):
        self.co_tbl_wid.setRowCount(0)
        __sorting_enabled = self.co_tbl_wid.isSortingEnabled()
        self.co_tbl_wid.setSortingEnabled(False)
        pt_list: List[CoPoint] = self.co.tolerances
        cs: Set[Tuple[GeoId, GeoId]] = self.co.cons_get()
        res_lst: List[CoPoint] = list()
        for pt in pt_list:
            p = CoPoint(pt.geo_id, pt.point)
            p.pt_distance_lst = pt.cons_filter(cs)
            res_lst.append(p)
        self.log_filter(res_lst)
        for idx, pt in enumerate(res_lst):
            self.co_tbl_wid.insertRow(0)
            fmt = f"({pt.geo_id.geo_idx}.{pt_typ_str[pt.geo_id.type_id]}) {pt.point.x: 6.2f} {pt.point.y: 6.2f}"
            self.co_tbl_wid.setItem(0, 0, QTableWidgetItem(fmt))
            fm = ''.join("{0:2}.{1} ".format(x.geo_id.geo_idx, pt_typ_str[x.geo_id.type_id]) for x in pt.pt_distance_lst)
            xp('fm:', fm, **_co)
            self.co_tbl_wid.setItem(0, 1, QTableWidgetItem(fm))
            w_item = QTableWidgetItem()
            w_item.setData(Qt.DisplayRole, pt)
            self.co_tbl_wid.setItem(0, 2, w_item)
            xp('new row: Id', idx, fmt, fm, **_co)
        self.co_tbl_wid.setSortingEnabled(__sorting_enabled)

    @flow
    def selected(self):
        indexes: List[QModelIndex] = self.co_tbl_wid.selectionModel().selectedRows(2)
        rows: List = [x.row() for x in sorted(indexes)]
        xp(f'selected: {rows}', **_co)
        if len(rows) == 0:
            self.co_btn_create.setDisabled(True)
        else:
            self.co_btn_create.setDisabled(False)

        doc_name = App.activeDocument().Name
        Gui.Selection.clearSelection(doc_name, True)
        ed_info = Gui.ActiveDocument.InEditInfo
        sk_name = ed_info[0].Name

        for item in indexes:
            co: CoPoint = item.data()
            xp(f'row: {str(item.row())} id: {co.geo_id} pt: {fmt_vec(co.point)} {co.pt_distance_lst}', **_co)
            ptn: GeoPtn = GeoPtn(co.geo_id.geo_idx, co.geo_id.type_id)
            self.lookup(doc_name, ptn, sk_name)
            for diff in co.pt_distance_lst:
                ptn: GeoPtn = GeoPtn(diff.geo_id.geo_idx, diff.geo_id.type_id)
                self.lookup(doc_name, ptn, sk_name)

    def lookup(self, doc_name, ptn, sk_name):
        idx = 0
        while True:
            geo, pos = self.impl.sketch.getGeoVertexIndex(idx)
            if (geo == ptn.geo_id) and (pos == ptn.type_id):
                Gui.Selection.addSelection(doc_name, sk_name, f'Vertex{idx + 1}')
                xp(f'Vertex{idx + 1} idx: {idx} geo: ({geo}.{pos})', **_co)
            if (geo == -2000) and (pos == 0):
                xp(f'unexpected, no vertex found', **_co)
                break
            idx += 1

    def log_filter(self, obj):
        xp(f'filter list', **_co)
        for item in obj:
            xp(item, **_co)


xps(__name__)


