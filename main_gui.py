from typing import List

from PySide2.QtCore import Qt, QItemSelectionModel, QModelIndex
from PySide2.QtWidgets import QComboBox, QWidget, QVBoxLayout, \
    QApplication, QHBoxLayout, QPushButton, QTabWidget, QLabel, QTableWidget, QTableWidgetItem, \
    QAbstractItemView, QHeaderView, QGroupBox, QSizePolicy, QDoubleSpinBox, QSpacerItem, QCheckBox, QBoxLayout

from main_impl import FixIt, ConType, pt_pos_str
from tools import xp, XpConf, flow, my_style

_coin = XpConf('coin', 'ui-coi')
_hv = XpConf('hv', 'ui-hv ')
_rad = XpConf('rad', 'ui-rad')
_lay = XpConf('lay', 'ui-lay')

XpConf.topics.add('lay')
XpConf.topics.add('rad')
XpConf.topics.add('coin')
XpConf.topics.add('hv')
XpConf.topics.add('flow')


class FixItGui(QWidget):
    # Constraint, Coincident, Horizontal/Vertical
    # Rad()ius, X/Y (Distance)
    #
    # geo list filter?
    # quit_button = QPushButton("&Quit")
    # quit_button.clicked.connect(self.close)
    @flow
    def __init__(self, base: FixIt):
        super().__init__()
        self.base: FixIt = base
        flags: Qt.WindowFlags = Qt.Window
        flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)

        self.tabs = QTabWidget()
        self.tab_cons = QWidget()
        self.tab_coin = QWidget()
        self.tab_rad = QWidget()
        self.tab_hv = QWidget()
        self.tab_xy = QWidget()
        self.tabs.addTab(self.tab_cons, "Cs")
        self.tabs.addTab(self.tab_coin, "Co")
        self.tabs.addTab(self.tab_hv, "H/V")
        self.tabs.addTab(self.tab_rad, "Rad")
        self.tabs.addTab(self.tab_xy, "X/Y")
        # -----------------------------------------------------
        self.xy_grp_box = QGroupBox()
        self.xy_grp_box.setTitle(u"X/Y Distance")
        self.xy_p_btn = QPushButton()
        self.xy_p_btn.clicked.connect(self.xy_create)
        self.xy_p_btn.setText(u"Create")
        self.xy_tbl_wid = self.xy_prep_table(self.xy_grp_box)
        self.xy_h_spacer = QSpacerItem(10, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.tab_xy.setLayout(self.xy_lay_get())
        # -----------------------------------------------------
        self.rad_chk_box = QCheckBox()
        self.rad_chk_box.stateChanged.connect(self.rad_state_chg)
        self.rad_chk_box.setText(u"Radius")
        self.rad_grp_box = QGroupBox()
        self.rad_grp_box.setTitle(u"Radius")
        self.rad_dbl_sp_box = self.db_s_box_get(self.base.radius, 1, 0.1, self.rad_val_chg)
        self.rad_chk_box.setChecked(True)
        self.rad_p_btn = QPushButton()
        self.rad_p_btn.clicked.connect(self.rad_create)
        self.rad_p_btn.setText(u"Create")
        self.rad_tbl_wid: QTableWidget = self.rad_prep_table(self.rad_grp_box)
        self.rad_h_spacer = QSpacerItem(10, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.tab_rad.setLayout(self.rad_lay_get())
        # -----------------------------------------------------
        self.hv_grp_box = QGroupBox()
        self.hv_grp_box.setTitle(u"Horizontal/Vertical")
        self.hv_lbl = QLabel()
        self.hv_lbl.setText(u"Snap Angle")
        self.hv_dbl_sp_box = self.db_s_box_get(base.snap_angel, 1, 0.1, self.hv_val_chg)
        self.hv_p_btn = QPushButton()
        self.hv_p_btn.clicked.connect(self.hv_create)
        self.hv_p_btn.setText(u"Create")
        self.hv_tbl_wid = self.hv_prep_table(self.hv_grp_box)
        self.hv_h_spacer = QSpacerItem(10, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.tab_hv.setLayout(self.hv_lay_get())
        # -----------------------------------------------------
        self.coin_grp_box = QGroupBox()
        self.coin_grp_box.setTitle(u"Coincident")
        self.coin_lbl = QLabel()
        self.coin_lbl.setText(u"Snap Dist")
        self.coin_dbl_sp_box = self.db_s_box_get(base.snap_dist, 2, 0.1, self.coin_val_chg)
        self.coin_p_btn = QPushButton()
        self.coin_p_btn.clicked.connect(self.coin_create)
        self.coin_p_btn.setText(u"Create")
        self.coin_tbl_wid = self.coin_prep_table(self.coin_grp_box)
        self.coin_h_spacer = QSpacerItem(10, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.tab_coin.setLayout(self.coin_lay_get())
        # -----------------------------------------------------
        self.cons_grp_box = QGroupBox()
        self.cons_grp_box.setTitle(u"Constraints")
        self.cons_lbl_con = QLabel(u"Type")
        self.cons_tbl_wid = self.cons_prep_table(self.cons_grp_box)
        self.cons_cmb_box = self.cons_prep_combo()
        self.cons_cmb_box.currentTextChanged.connect(self.cons_combo_txt_chg)
        self.cons_p_btn = QPushButton(u"Delete")
        self.cons_p_btn.clicked.connect(self.cons_constraint)
        self.cons_h_spacer = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.tab_cons.setLayout(self.cons_lay_get())
        # -----------------------------------------------------
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

        self.setWindowTitle("MyCoEd")
        self.resize(600, 800)
        self.cons_update_table()
        self.coin_update_table()
        self.hv_update_table()
        self.rad_update_table()

    def db_s_box_get(self, val, prec, step, func):
        sb = QDoubleSpinBox()
        sb.setDecimals(prec)
        sb.setSingleStep(step)
        sb.setValue(val)
        sb.valueChanged.connect(func)
        return sb

    def xy_lay_get(self):
        lis = [self.xy_h_spacer, self.xy_p_btn,
               QVBoxLayout(self.xy_grp_box), self.xy_tbl_wid,
               QVBoxLayout(), self.xy_grp_box]
        return self.lay_get(QHBoxLayout(), lis)

    def rad_lay_get(self):
        lis = [self.rad_chk_box, self.rad_dbl_sp_box, self.rad_h_spacer, self.rad_p_btn,
               QVBoxLayout(self.rad_grp_box), self.rad_tbl_wid,
               QVBoxLayout(), self.rad_grp_box]
        return self.lay_get(QHBoxLayout(), lis)

    def hv_lay_get(self):
        lis = [self.hv_lbl, self.hv_dbl_sp_box, self.hv_h_spacer, self.hv_p_btn,
               QVBoxLayout(self.hv_grp_box), self.hv_tbl_wid,
               QVBoxLayout(), self.hv_grp_box]
        return self.lay_get(QHBoxLayout(), lis)

    def coin_lay_get(self):
        lis = [self.coin_lbl, self.coin_dbl_sp_box, self.coin_h_spacer, self.coin_p_btn,
               QVBoxLayout(self.coin_grp_box), self.coin_tbl_wid,
               QVBoxLayout(), self.coin_grp_box]
        return self.lay_get(QHBoxLayout(), lis)

    def cons_lay_get(self):
        lis = [self.cons_lbl_con, self.cons_cmb_box, self.cons_h_spacer, self.cons_p_btn,
               QVBoxLayout(self.cons_grp_box), self.cons_tbl_wid,
               QVBoxLayout(), self.cons_grp_box]
        return self.lay_get(QHBoxLayout(), lis)

    @flow
    def lay_get(self, lay: QBoxLayout, obj_list: List):
        for obj in obj_list:
            xp(type(obj), **_lay.kw())
            if isinstance(obj, QBoxLayout):
                obj.addLayout(lay)
                lay = obj
            elif isinstance(obj, QCheckBox) or isinstance(obj, QLabel):
                lay.addWidget(obj, 0, Qt.AlignLeft)
            elif isinstance(obj, QPushButton) or isinstance(obj, QDoubleSpinBox) or isinstance(obj, QTableWidget) \
                    or isinstance(obj, QGroupBox) or isinstance(obj, QComboBox):
                lay.addWidget(obj)
            elif isinstance(obj, QSpacerItem):
                lay.addSpacerItem(obj)
        return lay

    def xy_create(self):
        pass

    @flow
    def xy_prep_table(self, obj):
        table_widget = QTableWidget(obj)
        table_widget.setColumnCount(3)
        w_item = QTableWidgetItem()
        w_item.setText(u"Edge")
        table_widget.setHorizontalHeaderItem(0, w_item)
        w_item = QTableWidgetItem()
        w_item.setText(u"X/Y")
        table_widget.setHorizontalHeaderItem(1, w_item)
        self.__prep_table(table_widget)
        return table_widget

    def xy_update_table(self):
        pass

    @flow
    def rad_prep_table(self, obj):
        table_widget = QTableWidget(obj)
        table_widget.setColumnCount(3)
        w_item = QTableWidgetItem()
        w_item.setText(u"Circle")
        table_widget.setHorizontalHeaderItem(0, w_item)
        w_item = QTableWidgetItem()
        w_item.setText(u"Radius")
        table_widget.setHorizontalHeaderItem(1, w_item)
        self.__prep_table(table_widget)
        return table_widget

    @flow
    def rad_state_chg(self, obj):
        if self.rad_chk_box.isChecked():
            self.rad_dbl_sp_box.setEnabled(True)
        else:
            self.rad_dbl_sp_box.setEnabled(False)

    @flow
    def rad_create(self):
        rad = None
        if self.rad_chk_box.isChecked():
            rad = self.base.radius
        mod: QItemSelectionModel = self.rad_tbl_wid.selectionModel()
        rows: List[QModelIndex] = mod.selectedRows(2)
        create_list: List[int] = [x.data() for x in rows]
        for idx in rows:
            xp(idx.row(), ':', idx.data(), **_rad.kw())
        self.base.diameter_create(create_list, rad)
        self.rad_update_table()

    @flow
    def rad_val_chg(self, obj):
        value = self.rad_dbl_sp_box.value()
        self.base.radius = value

    @flow
    def rad_update_table(self):
        self.hv_tbl_wid.setRowCount(0)
        __sorting_enabled = self.hv_tbl_wid.isSortingEnabled()
        self.hv_tbl_wid.setSortingEnabled(False)
        cir_list: List[FixIt.CircleTu] = self.base.circle_get_list()
        xp('->', cir_list, **_rad.kw(4))
        for item in cir_list:
            self.rad_tbl_wid.insertRow(0)
            fmt = "x: {:.2f} y: {:.2f}".format(item.center_x, item.center_y)
            self.rad_tbl_wid.setItem(0, 0, QTableWidgetItem(fmt))
            fmt2 = "Id: {} r: {:.2f}".format(item.geo_id, item.radius)
            w_item = QTableWidgetItem(fmt2)
            w_item.setTextAlignment(Qt.AlignCenter)
            self.rad_tbl_wid.setItem(0, 1, w_item)
            w_item = QTableWidgetItem()
            w_item.setData(Qt.EditRole, item.geo_id)
            xp('col 3', item.geo_id, **_rad.kw(4))
            self.rad_tbl_wid.setItem(0, 2, w_item)
        self.rad_tbl_wid.setSortingEnabled(__sorting_enabled)

    @flow
    def hv_prep_table(self, obj):
        table_widget = QTableWidget(obj)
        table_widget.setColumnCount(3)
        w_item = QTableWidgetItem()
        w_item.setText(u"Edge")
        table_widget.setHorizontalHeaderItem(0, w_item)
        w_item = QTableWidgetItem()
        w_item.setText(u"Angle")
        table_widget.setHorizontalHeaderItem(1, w_item)

        self.__prep_table(table_widget)
        return table_widget

    @flow
    def hv_create(self):
        mod: QItemSelectionModel = self.hv_tbl_wid.selectionModel()
        rows: List[QModelIndex] = mod.selectedRows(2)
        create_list: List[int] = [x.data() for x in rows]
        for idx in rows:
            xp(idx.row(), ':', idx.data(), **_hv.kw())
        self.base.hv_create(create_list)
        self.hv_update_table()

    @flow
    def hv_val_chg(self, obj):
        value = self.hv_dbl_sp_box.value()
        self.base.snap_angel = value
        self.hv_update_table()
        xp("Current Value :", value)

    @flow
    def hv_update_table(self):
        self.hv_tbl_wid.setRowCount(0)
        __sorting_enabled = self.hv_tbl_wid.isSortingEnabled()
        self.hv_tbl_wid.setSortingEnabled(False)
        edge_list: List[FixIt.Edge] = self.base.hv_edges_get_list()
        for idx, item in enumerate(edge_list):
            if item.has_hv_cons:
                continue
            self.hv_tbl_wid.insertRow(0)
            fmt2 = "x {:.2f} y {:.2f} : x {:.2f} y {:.2f}".format(item.seg.StartPoint.x, item.seg.StartPoint.y, item.seg.EndPoint.x, item.seg.EndPoint.y)
            xp('col 1', fmt2, **_hv.kw(4))
            fmt = "x {:.2f} y {:.2f} \nx {:.2f} y {:.2f}".format(item.seg.StartPoint.x, item.seg.StartPoint.y, item.seg.EndPoint.x, item.seg.EndPoint.y)
            self.hv_tbl_wid.setItem(0, 0, QTableWidgetItem(fmt))
            fmt2 = "Id {} xa {:.2f} : ya {:.2f}".format(item.geo_idx + 1, item.x_angel, item.y_angel)
            xp('col 2', fmt2, **_hv.kw(4))
            fmt = "Id {} \nxa {:.2f} : ya {:.2f}".format(item.geo_idx + 1, item.x_angel, item.y_angel)
            w_item = QTableWidgetItem(fmt)
            w_item.setTextAlignment(Qt.AlignCenter)
            self.hv_tbl_wid.setItem(0, 1, w_item)
            w_item = QTableWidgetItem()
            w_item.setData(Qt.EditRole, idx)
            xp('col 3', idx, ** _hv.kw(4))
            self.hv_tbl_wid.setItem(0, 2, w_item)
        self.hv_tbl_wid.setSortingEnabled(__sorting_enabled)

    @flow
    def coin_val_chg(self, obj):
        value = self.coin_dbl_sp_box.value()
        self.base.snap_dist = value
        self.coin_update_table()
        xp("Current Value :", value)

    @flow
    def coin_create(self):
        mod: QItemSelectionModel = self.coin_tbl_wid.selectionModel()
        rows: List[QModelIndex] = mod.selectedRows(2)
        create_list: List[int] = [x.data() for x in rows]
        for idx in rows:
            xp(idx.row(), ':', idx.data(), **_coin.kw())
        self.base.coin_create(create_list)
        self.coin_update_table()

    @flow
    def coin_prep_table(self, obj: QGroupBox) -> QTableWidget:
        table_widget = QTableWidget(obj)
        table_widget.setColumnCount(3)
        __table_widget_item = QTableWidgetItem()
        __table_widget_item.setText(u"Point")
        table_widget.setHorizontalHeaderItem(0, __table_widget_item)
        __table_widget_item = QTableWidgetItem()
        __table_widget_item.setText(u"Idx")
        table_widget.setHorizontalHeaderItem(1, __table_widget_item)
        self.__prep_table(table_widget)
        return table_widget

    @flow
    def coin_update_table(self):
        self.coin_tbl_wid.setRowCount(0)
        __sorting_enabled = self.coin_tbl_wid.isSortingEnabled()
        self.coin_tbl_wid.setSortingEnabled(False)
        pt_list: List[FixIt.Point] = self.base.points_get_list()
        for i in range(len(pt_list)):
            pt: FixIt.Point = pt_list[i]
            if len(pt.coin_pts) == 1:
                continue
            if len(pt.coin_pts) > 1:
                xp(pt.geo_item_pt, " : ", pt.coin_pts, **_coin.kw(4))
                self.coin_tbl_wid.insertRow(0)
                fmt = "{0:.2f} : {1:.2f}".format(pt.geo_item_pt.x, pt.geo_item_pt.y)
                self.coin_tbl_wid.setItem(0, 0, QTableWidgetItem(fmt))
                w_item = QTableWidgetItem()
                w_item.setData(Qt.EditRole, i)
                self.cons_tbl_wid.setItem(0, 2, w_item)
                fmt = ""
                for j in range(len(pt.coin_pts)):
                    cpt: FixIt.Point.CoinPt = pt.coin_pts[j]
                    fmt += "{0}.{1}  ".format(cpt.geo_idx + 1, pt_pos_str[cpt.pt_type])
                    self.coin_tbl_wid.setItem(0, 1, QTableWidgetItem(fmt))
        self.coin_tbl_wid.setSortingEnabled(__sorting_enabled)

    @flow
    def cons_constraint(self):
        mod: QItemSelectionModel = self.cons_tbl_wid.selectionModel()
        rows: List[QModelIndex] = mod.selectedRows(2)
        del_list: List[int] = []
        for idx in rows:
            xp(str(idx.row()) + ' : ' + str(idx.data()))
            del_list.append(idx.data())
        self.base.constraints_delete(del_list)
        self.cons_update_table()

    @flow
    def cons_combo_txt_chg(self, txt):
        ct: ConType = ConType(txt)
        self.cons_update_table(ct)

    @flow
    def cons_update_table(self, typ: ConType = ConType.ALL):
        self.cons_tbl_wid.setRowCount(0)
        __sorting_enabled = self.cons_tbl_wid.isSortingEnabled()
        self.cons_tbl_wid.setSortingEnabled(False)
        con_list: List[FixIt.Constraint] = self.base.constraints_get_list()
        for item in con_list:
            if typ == ConType.ALL or typ == ConType(item.type_id):
                self.cons_tbl_wid.insertRow(0)
                self.cons_tbl_wid.setItem(0, 0, QTableWidgetItem(str(item.type_id)))
                self.cons_tbl_wid.setItem(0, 1, QTableWidgetItem(str(item)))
                w_item = QTableWidgetItem()
                w_item.setData(Qt.EditRole, item.co_idx)
                self.cons_tbl_wid.setItem(0, 2, w_item)
        self.cons_tbl_wid.setSortingEnabled(__sorting_enabled)

    @staticmethod
    @flow
    def cons_prep_combo() -> QComboBox:
        combo_box = QComboBox()
        combo_box.addItem(ConType.ALL.value)
        li: List[str] = []
        for ct in ConType:
            if ct == ConType.NONE or ct == ConType.ALL:
                continue
            else:
                li.append(ct.value)
        li.sort()
        for it in li:
            combo_box.addItem(it)
        return combo_box

    @flow
    def cons_prep_table(self, obj: QGroupBox) -> QTableWidget:
        table_widget = QTableWidget(obj)
        table_widget.setColumnCount(3)
        w_item = QTableWidgetItem()
        w_item.setText(u"Type")
        table_widget.setHorizontalHeaderItem(0, w_item)
        w_item = QTableWidgetItem()
        w_item.setText(u"Info")
        table_widget.setHorizontalHeaderItem(1, w_item)
        self.__prep_table(table_widget)
        return table_widget

    @flow
    def __prep_table(self, tbl: QTableWidget):
        tbl.horizontalHeader().setVisible(True)
        tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        tbl.setColumnHidden(2, True)
        # tbl.sortByColumn(0)
        tbl.sortItems(0, Qt.AscendingOrder)
        tbl.setSortingEnabled(True)
        hh: QHeaderView = tbl.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        vh: QHeaderView = tbl.verticalHeader()
        vh.setSectionResizeMode(QHeaderView.ResizeToContents)
        vh.setMaximumSectionSize(80)
        tbl_style = "QTableView::item {" \
                    "padding-left: 10px; " \
                    "padding-right: 10px; " \
                    "border: none; " \
                    "}"
        tbl.setStyleSheet(tbl_style)


if __name__ == '__main__':

    import sys

    app = QApplication()
    my_style(app)
    controller = FixItGui()
    controller.show()
    sys.exit(app.exec_())