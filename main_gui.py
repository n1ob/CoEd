from typing import List

from PySide2.QtCore import Qt, QItemSelectionModel, QModelIndex, Slot
from PySide2.QtGui import QFont
from PySide2.QtWidgets import QComboBox, QWidget, QVBoxLayout, \
    QApplication, QHBoxLayout, QPushButton, QTabWidget, QLabel, QTableWidget, QTableWidgetItem, \
    QAbstractItemView, QHeaderView, QGroupBox, QSizePolicy, QDoubleSpinBox, QSpacerItem, QCheckBox, QBoxLayout, \
    QPlainTextEdit, QFontComboBox, QSpinBox

from main_impl import FixIt
from tools import ConType
from style import XMLHighlighter, my_style
from logger import xp, _cog, _hv_g, _rad, _lay, flow


'''
<!-- Geo Idx 0 ---- Part::GeomLineSegment ------------------------------------>
<GeoExtensions count="0">
</GeoExtensions>
<LineSegment StartX="-7.71125" StartY="-4.73661" StartZ="0" EndX="4" EndY="7" EndZ="0"/>
<!-- Geo Idx 1 ---- Part::GeomLineSegment ------------------------------------>
<GeoExtensions count="0">
</GeoExtensions>
<LineSegment StartX="4.77724" StartY="7" StartZ="0" EndX="6.78156" EndY="-8.48829" EndZ="0"/>
<!-- Geo Idx 2 ---- Part::GeomLineSegment ------------------------------------>
<GeoExtensions count="0">
</GeoExtensions>
<LineSegment StartX="-8.43075" StartY="-6" StartZ="0" EndX="6.78156" EndY="-9.61894" EndZ="0"/>
<!-- Geo Idx 3 ---- Part::GeomLineSegment ------------------------------------>
<GeoExtensions count="0">
</GeoExtensions>
<LineSegment StartX="4.36609" StartY="7.59771" StartZ="0" EndX="20.4521" EndY="10.4757" EndZ="0"/>

'''

# noinspection PyArgumentList
class FixItGui(QWidget):
    # Constraint, Coincident, Horizontal/Vertical
    # Rad()ius, X/Y (Distance)
    @flow(short=True)
    def __init__(self, base: FixIt, parent=None):
        super().__init__(parent)
        self.base: FixIt = base
        flags: Qt.WindowFlags = Qt.Window
        flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.resize(600, 800)
        self.tbl_font = QFont("Consolas", 9)
        self.edt_font = QFont("Consolas", 9)

        self.base.ev.cons_chg.connect(self.say_some_words)

        self.tabs = QTabWidget(None)
        self.tab_cons = QWidget(None)
        self.tab_coin = QWidget(None)
        self.tab_rad = QWidget(None)
        self.tab_hv = QWidget(None)
        self.tab_xy = QWidget(None)
        self.tab_geo = QWidget(None)
        self.tab_xxx = QWidget(None)
        self.tabs.addTab(self.tab_cons, "Cs")
        self.tabs.addTab(self.tab_coin, "Co")
        self.tabs.addTab(self.tab_hv, "H/V")
        self.tabs.addTab(self.tab_rad, "Rad")
        self.tabs.addTab(self.tab_xy, "X/Y")
        self.tabs.addTab(self.tab_geo, "Geo")
        self.tabs.addTab(self.tab_xxx, "xxx")
        # -----------------------------------------------------
        self.xxx_filter_cmb = QComboBox(self)
        self.xxx_filter_cmb.addItems(['all fonts', 'scalable', 'non-scalable', 'monospace', 'equal prop'])
        self.xxx_filter_cmb.currentIndexChanged.connect(self.on_font_filter_changed)
        self.xxx_filter_cmb.setMaximumWidth(200)

        self.xxx_txt_edt = QPlainTextEdit()
        self.xxx_txt_edt.setFont(self.edt_font)
        self.xxx_txt_edt.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.xxx_txt_edt.highlighter = XMLHighlighter(self.xxx_txt_edt.document())
        self.xxx_txt_edt.setPlainText(self.base.geo_get())

        self.xxx_font_box = QFontComboBox()
        # self.xxx_font_box.dumpObjectTree()
        self.xxx_font_box.setCurrentFont(self.edt_font)
        self.xxx_font_box.currentFontChanged.connect(self.on_font_changed)
        self.xxx_font_box.setMaximumWidth(300)

        self.xxx_font_size = QSpinBox()
        self.xxx_font_size.valueChanged.connect(self.on_value_chg)
        self.xxx_font_size.setRange(6, 32)
        self.xxx_font_size.setSingleStep(1)
        self.xxx_font_size.setValue(9)

        self.xxx_btn_geo = QPushButton('geo')
        self.xxx_btn_geo.clicked.connect(self.on_clk_geo)
        self.xxx_btn_tbl = QPushButton('tbl')
        self.xxx_btn_tbl.clicked.connect(self.on_clk_tbl)

        h_lay = QHBoxLayout()
        h_lay.addWidget(self.xxx_filter_cmb)
        h_lay.addStretch()
        h_lay.addWidget(self.xxx_btn_tbl)
        h_lay.addSpacing(10)
        h_lay.addWidget(self.xxx_btn_geo)
        h_lay2 = QHBoxLayout()
        h_lay2.addWidget(self.xxx_font_box)
        h_lay2.addStretch()
        h_lay2.addWidget(self.xxx_font_size)
        v_lay = QVBoxLayout(self)
        v_lay.addLayout(h_lay)
        v_lay.addLayout(h_lay2)
        v_lay.addSpacing(20)
        v_lay.addWidget(self.xxx_txt_edt)

        self.tab_xxx.setLayout(v_lay)
        # -----------------------------------------------------
        self.geo_txt_edt = QPlainTextEdit()
        self.geo_txt_edt.setFont(self.edt_font)
        self.geo_txt_edt.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.geo_txt_edt.highlighter = XMLHighlighter(self.geo_txt_edt.document())
        self.geo_txt_edt.setPlainText(self.base.geo_get())
        lay = QVBoxLayout()
        lay.addWidget(self.geo_txt_edt)
        self.tab_geo.setLayout(lay)
        # -----------------------------------------------------
        self.xy_grp_box = QGroupBox(None)
        self.xy_grp_box.setTitle(u"X/Y Distance")
        self.xy_p_btn = QPushButton(u"Create")
        self.xy_p_btn.clicked.connect(self.xy_create)
        self.xy_p_btn.setText(u"Create")
        self.xy_tbl_wid = self.xy_prep_table(self.xy_grp_box)
        self.xy_h_spacer = QSpacerItem(10, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.tab_xy.setLayout(self.xy_lay_get())
        # -----------------------------------------------------
        self.rad_chk_box = QCheckBox(None)
        self.rad_chk_box.stateChanged.connect(self.rad_state_chg)
        self.rad_chk_box.setText(u"Radius")
        self.rad_grp_box = QGroupBox(None)
        self.rad_grp_box.setTitle(u"Radius")
        self.rad_dbl_sp_box = self.db_s_box_get(self.base.radius, 1, 0.1, self.rad_val_chg)
        self.rad_chk_box.setChecked(True)
        self.rad_p_btn = QPushButton(u"Create")
        self.rad_p_btn.clicked.connect(self.rad_create)
        self.rad_p_btn.setText(u"Create")
        self.rad_tbl_wid: QTableWidget = self.rad_prep_table(self.rad_grp_box)
        self.rad_h_spacer = QSpacerItem(10, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.tab_rad.setLayout(self.rad_lay_get())
        # -----------------------------------------------------
        self.hv_grp_box = QGroupBox(None)
        self.hv_grp_box.setTitle(u"Horizontal/Vertical")
        self.hv_lbl = QLabel(u"Snap Angle")
        self.hv_dbl_sp_box = self.db_s_box_get(base.snap_angel, 1, 0.1, self.hv_val_chg)
        self.hv_p_btn = QPushButton(u"Create")
        self.hv_p_btn.clicked.connect(self.hv_create)
        self.hv_tbl_wid = self.hv_prep_table(self.hv_grp_box)
        self.hv_h_spacer = QSpacerItem(10, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.tab_hv.setLayout(self.hv_lay_get())
        # -----------------------------------------------------
        self.coin_grp_box = QGroupBox(None)
        self.coin_grp_box.setTitle(u"Coincident")
        self.coin_lbl = QLabel(u"Snap Dist")
        self.coin_dbl_sp_box = self.db_s_box_get(base.snap_dist, 2, 0.1, self.coin_val_chg)
        self.coin_p_btn = QPushButton(u"Create")
        self.coin_p_btn.clicked.connect(self.coin_create)
        self.coin_p_btn.setText(u"Create")
        self.coin_tbl_wid = self.coin_prep_table(self.coin_grp_box)
        self.coin_h_spacer = QSpacerItem(10, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.tab_coin.setLayout(self.coin_lay_get())
        # -----------------------------------------------------
        self.cons_grp_box = QGroupBox(None)
        self.cons_grp_box.setTitle(u"Constraints")
        self.cons_lbl_con = QLabel(u"Type")
        self.cons_tbl_wid = self.cons_prep_table(self.cons_grp_box)
        self.cons_cmb_box = self.cons_prep_combo()
        self.cons_cmb_box.currentTextChanged.connect(self.cons_combo_txt_chg)
        self.cons_p_btn = QPushButton(u"Delete")
        self.cons_p_btn.clicked.connect(self.cons_delete)
        self.cons_h_spacer = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.tab_cons.setLayout(self.cons_lay_get())
        # -----------------------------------------------------
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)
        self.setWindowTitle("MyCoEd")
        self.cons_update_table()
        self.coin_update_table()
        self.hv_update_table()
        self.rad_update_table()
        self.xy_update_table()

    def on_value_chg(self, value):
        font: QFont = self.font()
        font.setPointSize(value)
        self.xxx_txt_edt.setFont(font)
        # self.xxx_label_text.setFont(QFont(font.family(), value))

    def on_font_filter_changed(self, index):
        switcher = {
            0: QFontComboBox.AllFonts,
            1: QFontComboBox.ScalableFonts,
            2: QFontComboBox.NonScalableFonts,
            3: QFontComboBox.MonospacedFonts,
            4: QFontComboBox.ProportionalFonts
        }
        self.xxx_font_box.setFontFilters(switcher.get(index))

    def on_clk_tbl(self):
        pass

    def on_clk_geo(self):
        pass

    def on_font_changed(self, font):
        self.xxx_txt_edt.setFont(QFont(font.family(), self.xxx_font_size.value()))

    @flow
    def db_s_box_get(self, val, prec, step, func):
        sb = QDoubleSpinBox(None)
        sb.setDecimals(prec)
        sb.setSingleStep(step)
        sb.setValue(val)
        sb.valueChanged.connect(func)
        return sb

    @flow
    def xy_lay_get(self):
        # noinspection PyArgumentList
        lis = [self.xy_h_spacer, self.xy_p_btn,
               QVBoxLayout(self.xy_grp_box), self.xy_tbl_wid,
               QVBoxLayout(), self.xy_grp_box]
        return self.lay_get(QHBoxLayout(), lis)

    @flow
    def rad_lay_get(self):
        # noinspection PyArgumentList
        lis = [self.rad_chk_box, self.rad_dbl_sp_box, self.rad_h_spacer, self.rad_p_btn,
               QVBoxLayout(self.rad_grp_box), self.rad_tbl_wid,
               QVBoxLayout(), self.rad_grp_box]
        return self.lay_get(QHBoxLayout(), lis)

    @flow
    def hv_lay_get(self):
        # noinspection PyArgumentList
        lis = [self.hv_lbl, self.hv_dbl_sp_box, self.hv_h_spacer, self.hv_p_btn,
               QVBoxLayout(self.hv_grp_box), self.hv_tbl_wid,
               QVBoxLayout(), self.hv_grp_box]
        return self.lay_get(QHBoxLayout(), lis)

    @flow
    def coin_lay_get(self):
        # noinspection PyArgumentList
        lis = [self.coin_lbl, self.coin_dbl_sp_box, self.coin_h_spacer, self.coin_p_btn,
               QVBoxLayout(self.coin_grp_box), self.coin_tbl_wid,
               QVBoxLayout(), self.coin_grp_box]
        return self.lay_get(QHBoxLayout(), lis)

    @flow
    def cons_lay_get(self):
        # noinspection PyArgumentList
        lis = [self.cons_lbl_con, self.cons_cmb_box, self.cons_h_spacer, self.cons_p_btn,
               QVBoxLayout(self.cons_grp_box), self.cons_tbl_wid,
               QVBoxLayout(), self.cons_grp_box]
        return self.lay_get(QHBoxLayout(), lis)

    def lay_get(self, lay: QBoxLayout, obj_list: List):
        for obj in obj_list:
            xp(type(obj), **_lay.k())
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
        mod: QItemSelectionModel = self.rad_tbl_wid.selectionModel()
        rows: List[QModelIndex] = mod.selectedRows(2)
        create_list: List[int] = [x.data() for x in rows]
        for idx in rows:
            xp(idx.row(), ':', idx.data(), **_rad.k())
        self.base.xy_dist_create(create_list)
        self.xy_update_table()

    @flow
    def xy_prep_table(self, obj):
        table_widget = QTableWidget(obj)
        table_widget.setColumnCount(3)
        w_item = QTableWidgetItem(u"Edge")
        table_widget.setHorizontalHeaderItem(0, w_item)
        w_item = QTableWidgetItem(u"X/Y")
        table_widget.setHorizontalHeaderItem(1, w_item)
        self.__prep_table(table_widget)
        return table_widget

    @flow
    def xy_update_table(self):
        self.xy_tbl_wid.setRowCount(0)
        __sorting_enabled = self.xy_tbl_wid.isSortingEnabled()
        self.xy_tbl_wid.setSortingEnabled(False)
        edg_list: List[FixIt.XyEdge] = self.base.xy_edg_get_list()
        xp('->', edg_list, **_rad.k(4))
        for idx, item in enumerate(edg_list):
            self.xy_tbl_wid.insertRow(0)
            s = "x {:.2f} y {:.2f} \nx {:.2f} y {:.2f}"
            fmt = s.format(item.start.x, item.start.y, item.end.x, item.end.y)
            self.xy_tbl_wid.setItem(0, 0, QTableWidgetItem(fmt))
            fmt2 = "Id: {}\nx {} y {}".format(item.geo_id, item.has_x, item.has_y)
            w_item = QTableWidgetItem(fmt2)
            w_item.setTextAlignment(Qt.AlignCenter)
            self.xy_tbl_wid.setItem(0, 1, w_item)
            w_item = QTableWidgetItem('')
            w_item.setData(Qt.DisplayRole, item.geo_id)
            xp('col 3', item.geo_id, **_rad.k(4))
            self.xy_tbl_wid.setItem(0, 2, w_item)
        self.xy_tbl_wid.setSortingEnabled(__sorting_enabled)

    @flow
    def rad_prep_table(self, obj):
        table_widget = QTableWidget(obj)
        table_widget.setColumnCount(3)
        w_item = QTableWidgetItem(u"Circle")
        table_widget.setHorizontalHeaderItem(0, w_item)
        w_item = QTableWidgetItem(u"Radius")
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
            xp(idx.row(), ':', idx.data(), **_rad.k())
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
        cir_list: List[FixIt.Circle] = self.base.circle_get_list()
        xp('->', cir_list, **_rad.k(4))
        for item in cir_list:
            self.rad_tbl_wid.insertRow(0)
            fmt = "x: {:.2f} y: {:.2f}".format(item.center_x, item.center_y)
            self.rad_tbl_wid.setItem(0, 0, QTableWidgetItem(fmt))
            fmt2 = "Id: {} r: {:.2f}".format(item.geo_id, item.radius)
            w_item = QTableWidgetItem(fmt2)
            w_item.setTextAlignment(Qt.AlignCenter)
            self.rad_tbl_wid.setItem(0, 1, w_item)
            w_item = QTableWidgetItem('')
            w_item.setData(Qt.DisplayRole, item.geo_id)
            xp('col 3', item.geo_id, **_rad.k(4))
            self.rad_tbl_wid.setItem(0, 2, w_item)
        self.rad_tbl_wid.setSortingEnabled(__sorting_enabled)

    @flow
    def hv_prep_table(self, obj):
        table_widget = QTableWidget(obj)
        table_widget.setColumnCount(3)
        w_item = QTableWidgetItem(u"Edge")
        table_widget.setHorizontalHeaderItem(0, w_item)
        w_item = QTableWidgetItem(u"Angle")
        table_widget.setHorizontalHeaderItem(1, w_item)

        self.__prep_table(table_widget)
        return table_widget

    @flow
    def hv_create(self):
        mod: QItemSelectionModel = self.hv_tbl_wid.selectionModel()
        rows: List[QModelIndex] = mod.selectedRows(2)
        create_list: List[int] = [x.data() for x in rows]
        for idx in rows:
            xp(idx.row(), ':', idx.data(), **_hv_g.k())
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
        edge_list: List[FixIt.HvEdge] = self.base.hv_edges_get_list()
        for idx, item in enumerate(edge_list):
            if item.has_hv_cons:
                continue
            self.hv_tbl_wid.insertRow(0)
            fmt2 = "x {:.2f} y {:.2f} : x {:.2f} y {:.2f}".format(item.pt_start.x, item.pt_start.y,
                                                                  item.pt_end.x, item.pt_end.y)
            xp('col 1', fmt2, **_hv_g.k(4))
            fmt = "{: 6.2f} {: 6.2f}\n{: 6.2f} {: 6.2f}".format(item.pt_start.x, item.pt_start.y,
                                                                item.pt_end.x, item.pt_end.y)
            self.hv_tbl_wid.setItem(0, 0, QTableWidgetItem(fmt))
            fmt2 = "Id {} xa {:.2f} : ya {:.2f}".format(item.geo_idx + 1, item.x_angel, item.y_angel)
            xp('col 2', fmt2, **_hv_g.k(4))
            fmt = "Id {} \nxa {:.2f} ya {:.2f}".format(item.geo_idx + 1, item.x_angel, item.y_angel)
            w_item = QTableWidgetItem(fmt)
            w_item.setTextAlignment(Qt.AlignCenter)
            self.hv_tbl_wid.setItem(0, 1, w_item)
            w_item2 = QTableWidgetItem()
            w_item2.setData(Qt.DisplayRole, idx)
            xp('col 3', idx, ** _hv_g.k(4))
            self.hv_tbl_wid.setItem(0, 2, w_item2)
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
        create_list: List[int] = [x.data(Qt.DisplayRole) for x in rows]
        for idx in rows:
            xp(idx.row(), ':', idx.data(Qt.DisplayRole), **_cog)
        self.base.coin_create(create_list)
        self.coin_update_table()

    @flow
    def coin_prep_table(self, obj: QGroupBox) -> QTableWidget:
        table_widget = QTableWidget(obj)
        table_widget.setColumnCount(3)
        w_item = QTableWidgetItem(u"Point")
        table_widget.setHorizontalHeaderItem(0, w_item)
        w_item = QTableWidgetItem(u"Idx")
        table_widget.setHorizontalHeaderItem(1, w_item)
        self.__prep_table(table_widget)
        return table_widget

    @flow
    def coin_update_table(self):
        self.coin_tbl_wid.setRowCount(0)
        __sorting_enabled = self.coin_tbl_wid.isSortingEnabled()
        self.coin_tbl_wid.setSortingEnabled(False)
        pt_list: List[FixIt.Point] = self.base.points_get_list()
        # xp('pt list:', pt_list, **_cog)
        for i, pt in enumerate(pt_list):
            if len(pt.coin_pts) == 1:
                continue
            if len(pt.coin_pts) > 1:
                self.coin_tbl_wid.insertRow(0)
                fmt = "{0: 6.2f} {1: 6.2f}".format(pt.geo_item_pt.x, pt.geo_item_pt.y)
                self.coin_tbl_wid.setItem(0, 0, QTableWidgetItem(fmt))
                fm = ''.join("{0:2}.{1} ".format(x.geo_idx + 1, x.pt_type) for x in pt.coin_pts)
                xp('fm:', fm, **_cog)
                self.coin_tbl_wid.setItem(0, 1, QTableWidgetItem(fm))
                w_item = QTableWidgetItem()
                w_item.setData(Qt.DisplayRole, i)
                self.coin_tbl_wid.setItem(0, 2, w_item)
                xp('new row: Id', i, fmt, fm, **_cog)
        self.coin_tbl_wid.setSortingEnabled(__sorting_enabled)

    @flow
    def cons_delete(self):
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
        co_list: List[FixIt.Constraint] = self.base.constraints_get_list()
        for item in co_list:
            if typ == ConType.ALL or typ == ConType(item.type_id):
                self.cons_tbl_wid.insertRow(0)
                self.cons_tbl_wid.setItem(0, 0, QTableWidgetItem(item.type_id))
                self.cons_tbl_wid.setItem(0, 1, QTableWidgetItem(str(item)))
                w_item = QTableWidgetItem()
                w_item.setData(Qt.DisplayRole, item.co_idx)
                self.cons_tbl_wid.setItem(0, 2, w_item)
        self.cons_tbl_wid.setSortingEnabled(__sorting_enabled)

    @staticmethod
    @flow
    def cons_prep_combo() -> QComboBox:
        combo_box = QComboBox(None)
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
        w_item = QTableWidgetItem(u"Type")
        table_widget.setHorizontalHeaderItem(0, w_item)
        w_item = QTableWidgetItem(u"Info")
        table_widget.setHorizontalHeaderItem(1, w_item)
        self.__prep_table(table_widget)
        return table_widget

    @flow
    def __prep_table(self, tbl: QTableWidget):
        tbl.horizontalHeader().setVisible(True)
        tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        tbl.setColumnHidden(2, True)
        tbl.sortItems(0, Qt.AscendingOrder)
        tbl.setSortingEnabled(True)
        hh: QHeaderView = tbl.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        vh: QHeaderView = tbl.verticalHeader()
        # noinspection PyArgumentList
        vh.setSectionResizeMode(QHeaderView.ResizeToContents)
        vh.setMaximumSectionSize(80)
        tbl_style = "QTableView::item {" \
                    "padding-left: 10px; " \
                    "padding-right: 10px; " \
                    "border: none; " \
                    "}"
        tbl.setStyleSheet(tbl_style)
        tbl.setFont(self.tbl_font)

    @Slot(str)
    def say_some_words(self, words):
        xp('Constraints changed', words, **_cog)


if __name__ == '__main__':

    import sys

    app = QApplication()
    my_style(app)
    controller = FixItGui()
    controller.show()
    sys.exit(app.exec_())
