from typing import List, Set, Dict, Tuple, Callable

import FreeCAD as App
import FreeCADGui as Gui

from PySide2.QtCore import Qt, QItemSelectionModel, QModelIndex, Slot
from PySide2.QtGui import QFont
from PySide2.QtWidgets import QComboBox, QWidget, QVBoxLayout, QPlainTextEdit, QFontComboBox, \
    QApplication, QHBoxLayout, QPushButton, QTabWidget, QLabel, QTableWidget, QTableWidgetItem, QSpinBox, \
    QAbstractItemView, QHeaderView, QGroupBox, QDoubleSpinBox, QCheckBox, QBoxLayout


from co_config import CfgFonts
from co_impl import CoEd
from co_cmn import ConType, ConsTrans, GeoPt, GeoPtn, pt_typ_int
from co_lookup import Lookup
from co_observer import EventProvider
from co_style import XMLHighlighter, my_style
from co_logger import xp, _co, _hv, _rd, flow, _ly, xps, _cs, Profile, _xy, _fl, _ob_s

_QL = QBoxLayout


# noinspection PyArgumentList
class CoEdGui(QWidget):

    @flow(short=True)
    def __init__(self, base: CoEd, parent=None):
        super().__init__(parent)
        self.base: CoEd = base
        # selection_observer_receiver(self)
        self.ev = EventProvider.ev
        self.ev.add_selection.connect(self.on_sel_chg_event)
        flags: Qt.WindowFlags = Qt.Window
        flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.resize(600, 800)
        self.cfg_fnts = CfgFonts()
        self.cfg_fnts.load()
        self.tbl_font = self.cfg_fnts.font_get(CfgFonts.FONT_TABLE)
        self.geo_edt_font = self.cfg_fnts.font_get(CfgFonts.FONT_GEO_EDT)
        self.cfg_edt_font = self.cfg_fnts.font_get(CfgFonts.FONT_CFG_EDT)

        self.tabs = QTabWidget(None)
        self.tab_cons = QWidget(None)
        self.tab_coin = QWidget(None)
        self.tab_rad = QWidget(None)
        self.tab_hv = QWidget(None)
        self.tab_xy = QWidget(None)
        self.tab_geo = QWidget(None)
        self.tab_cfg = QWidget(None)
        self.tab_lay_set()

        self.base.ev.cons_chg.connect(self.on_cons_chg)
        self.base.ev.coin_pts_chg.connect(self.on_coin_chg)
        self.base.ev.xy_edg_chg.connect(self.on_xy_chg)
        self.base.ev.rad_chg.connect(self.on_rad_chg)
        self.base.ev.hv_edg_chg.connect(self.on_hv_chg)
        self.tabs.currentChanged.connect(self.on_cur_tab_chg)

        # -----------------------------------------------------
        self.cfg_filter_cmb = QComboBox(self)
        self.cfg_txt_edt = QPlainTextEdit()
        self.cfg_font_box = QFontComboBox()
        self.cfg_font_size = QSpinBox()
        self.cfg_btn_geo = QPushButton('geo')
        self.cfg_btn_tbl = QPushButton('tbl')
        self.cfg_btn_load = QPushButton('Load')
        self.cfg_btn_save = QPushButton('Save')
        self.tab_cfg.setLayout(self.cfg_lay_get())
        # -----------------------------------------------------
        self.geo_txt_edt = QPlainTextEdit()
        self.geo_btn_geo = QPushButton('geo')
        self.geo_btn_ext = QPushButton('ext')
        self.tab_geo.setLayout(self.geo_lay_get())
        # -----------------------------------------------------
        self.xy_grp_box: QGroupBox = QGroupBox(None)
        self.xy_chk_box_x: QCheckBox = QCheckBox()
        self.xy_chk_box_y: QCheckBox = QCheckBox()
        self.xy_btn_create: QPushButton = QPushButton()
        self.xy_btn_create.setDisabled(True)
        self.xy_tbl_wid: QTableWidget = QTableWidget()
        self.tab_xy.setLayout(self.xy_lay_get())
        # -----------------------------------------------------
        self.rad_grp_box: QGroupBox = QGroupBox(None)
        self.rad_chk_box: QCheckBox = QCheckBox()
        self.rad_dbl_sp_box: QDoubleSpinBox = QDoubleSpinBox()
        self.rad_btn_create: QPushButton = QPushButton()
        self.rad_btn_create.setDisabled(True)
        self.rad_tbl_wid: QTableWidget = QTableWidget()
        self.tab_rad.setLayout(self.rad_lay_get())
        # -----------------------------------------------------
        self.hv_grp_box: QGroupBox = QGroupBox(None)
        self.hv_lbl: QLabel = QLabel()
        self.hv_dbl_sp_box: QDoubleSpinBox = QDoubleSpinBox()
        self.hv_btn_create: QPushButton = QPushButton()
        self.hv_btn_create.setDisabled(True)
        self.hv_tbl_wid: QTableWidget = QTableWidget()
        self.tab_hv.setLayout(self.hv_lay_get())
        # -----------------------------------------------------
        self.coin_grp_box: QGroupBox = QGroupBox(None)
        self.coin_lbl: QLabel = QLabel()
        self.coin_dbl_sp_box: QDoubleSpinBox = QDoubleSpinBox()
        self.coin_btn_create: QPushButton = QPushButton()
        self.coin_btn_create.setDisabled(True)
        self.coin_tbl_wid: QTableWidget = QTableWidget()
        self.tab_coin.setLayout(self.coin_lay_get())
        # -----------------------------------------------------
        self.cons_grp_box: QGroupBox = QGroupBox(None)
        self.cons_lbl_con: QLabel = QLabel()
        self.cons_tbl_wid: QTableWidget = QTableWidget()
        self.cons_cmb_box: QComboBox = QComboBox()
        self.cons_btn_del: QPushButton = QPushButton()
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

    def tab_lay_set(self):
        self.tabs.addTab(self.tab_cons, "Cs")
        self.tabs.addTab(self.tab_coin, "Co")
        self.tabs.addTab(self.tab_hv, "H/V")
        self.tabs.addTab(self.tab_rad, "Rad")
        self.tabs.addTab(self.tab_xy, "X/Y")
        self.tabs.addTab(self.tab_geo, "Geo")
        self.tabs.addTab(self.tab_cfg, "Cfg")

    @flow
    def cfg_lay_get(self) -> QBoxLayout:
        self.cfg_filter_cmb.addItems(['all fonts', 'scalable', 'non-scalable', 'monospace', 'equal prop'])
        self.cfg_filter_cmb.currentIndexChanged.connect(self.on_cfg_fnt_fil_chg)
        self.cfg_filter_cmb.setMaximumWidth(200)
        self.cfg_txt_edt.setFont(self.cfg_edt_font)
        self.cfg_txt_edt.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.cfg_txt_edt.highlighter = XMLHighlighter(self.cfg_txt_edt.document())
        self.cfg_txt_edt.setPlainText(self.base.geo_xml_get())
        self.cfg_font_box.setCurrentFont(self.cfg_edt_font)
        self.cfg_font_box.currentFontChanged.connect(self.on_cfg_fnt_box_chg)
        self.cfg_font_box.setMaximumWidth(300)
        self.cfg_font_size.setRange(6, 32)
        self.cfg_font_size.setSingleStep(1)
        self.cfg_font_size.setValue(self.cfg_edt_font.pointSize())
        self.cfg_font_size.valueChanged.connect(self.on_cfg_fnt_size_val_chg)
        self.cfg_btn_geo.clicked.connect(self.on_cfg_btn_clk_geo)
        self.cfg_btn_tbl.clicked.connect(self.on_cfg_btn_clk_tab)
        self.cfg_btn_load.clicked.connect(self.on_cfg_btn_clk_load)
        self.cfg_btn_save.clicked.connect(self.on_cfg_btn_clk_save)
        lis = [QVBoxLayout(),
               [QHBoxLayout(), self.cfg_filter_cmb, _QL.addStretch, self.cfg_btn_tbl, (_QL.addSpacing, 20),
                self.cfg_btn_geo],
               [QHBoxLayout(), self.cfg_font_box, _QL.addStretch, self.cfg_font_size],
               (_QL.addSpacing, 10), self.cfg_txt_edt, (_QL.addSpacing, 10),
               [QHBoxLayout(), _QL.addStretch, self.cfg_btn_load, (_QL.addSpacing, 20), self.cfg_btn_save]]
        return self.lay_get(lis)

    @flow
    def geo_lay_get(self) -> QBoxLayout:
        self.geo_txt_edt.setFont(self.geo_edt_font)
        self.geo_txt_edt.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.geo_txt_edt.highlighter = XMLHighlighter(self.geo_txt_edt.document())
        self.geo_txt_edt.setPlainText(self.base.geo_xml_get())
        self.geo_btn_geo.clicked.connect(self.on_geo_btn_clk_geo)
        self.geo_btn_ext.clicked.connect(self.on_geo_btn_clk_ext)
        lis = [QVBoxLayout(),
               self.geo_txt_edt,
               [QHBoxLayout(), _QL.addStretch, self.geo_btn_geo, (_QL.addSpacing, 20), self.geo_btn_ext]]
        return self.lay_get(lis)

    @flow
    def xy_lay_get(self) -> QBoxLayout:
        self.xy_grp_box.setTitle(u"X/Y Distance")
        self.xy_chk_box_x.setText('X')
        self.xy_chk_box_x.setChecked(True)
        self.xy_chk_box_x.stateChanged.connect(self.on_xy_chk_x_state_chg)
        self.xy_chk_box_y.setText('Y')
        self.xy_chk_box_y.setChecked(True)
        self.xy_chk_box_y.stateChanged.connect(self.on_xy_chk_y_state_chg)
        self.xy_btn_create.clicked.connect(self.on_xy_create_btn_clk)
        self.xy_btn_create.setText(u"Create")
        self.xy_tbl_wid = self.xy_prep_table(self.xy_grp_box)
        self.xy_tbl_wid.itemSelectionChanged.connect(self.on_xy_tbl_sel_chg)
        # noinspection PyArgumentList
        li = [QVBoxLayout(), self.xy_grp_box,
              [QVBoxLayout(self.xy_grp_box),
               [QHBoxLayout(), self.xy_chk_box_x, self.xy_chk_box_y, _QL.addStretch, self.xy_btn_create],
               self.xy_tbl_wid]]
        return self.lay_get(li)

    @flow
    def rad_lay_get(self) -> QBoxLayout:
        self.rad_chk_box.stateChanged.connect(self.on_rad_chk_box_state_chg)
        self.rad_chk_box.setText(u"Radius")
        self.rad_grp_box.setTitle(u"Radius")
        self.rad_dbl_sp_box = self.db_s_box_get(self.base.radius, 1, 0.1, self.on_rad_val_chg)
        self.rad_chk_box.setChecked(True)
        self.rad_btn_create.clicked.connect(self.on_rad_create_btn_clk)
        self.rad_btn_create.setText(u"Create")
        self.rad_tbl_wid: QTableWidget = self.rad_prep_table(self.rad_grp_box)
        self.rad_tbl_wid.itemSelectionChanged.connect(self.on_rad_tbl_sel_chg)
        # noinspection PyArgumentList
        li = [QVBoxLayout(), self.rad_grp_box,
              [QVBoxLayout(self.rad_grp_box),
               [QHBoxLayout(), self.rad_chk_box, self.rad_dbl_sp_box, _QL.addStretch, self.rad_btn_create],
               self.rad_tbl_wid]]
        return self.lay_get(li)

    @flow
    def hv_lay_get(self) -> QBoxLayout:
        self.hv_grp_box.setTitle(u"Horizontal/Vertical")
        self.hv_lbl.setText(u"Snap Angle")
        self.hv_dbl_sp_box = self.db_s_box_get(self.base.snap_angel, 1, 0.1, self.on_hv_snap_val_chg)
        self.hv_btn_create.clicked.connect(self.on_hv_create_btn_clk)
        self.hv_btn_create.setText(u"Create")
        self.hv_tbl_wid = self.hv_prep_table(self.hv_grp_box)
        self.hv_tbl_wid.itemSelectionChanged.connect(self.on_hv_tbl_sel_chg)
        # noinspection PyArgumentList
        li = [QVBoxLayout(), self.hv_grp_box,
              [QVBoxLayout(self.hv_grp_box),
               [QHBoxLayout(), self.hv_lbl, self.hv_dbl_sp_box, _QL.addStretch, self.hv_btn_create],
               self.hv_tbl_wid]]
        return self.lay_get(li)

    @flow
    def coin_lay_get(self) -> QBoxLayout:
        self.coin_grp_box.setTitle(u"Coincident")
        self.coin_lbl.setText(u"Snap Dist")
        self.coin_dbl_sp_box = self.db_s_box_get(self.base.snap_dist, 2, 0.1, self.on_coin_snap_val_chg)
        self.coin_btn_create.clicked.connect(self.on_coin_create_btn_clk)
        self.coin_btn_create.setText(u"Create")
        self.coin_tbl_wid = self.coin_prep_table(self.coin_grp_box)
        self.coin_tbl_wid.itemSelectionChanged.connect(self.on_coin_tbl_sel_chg)
        # noinspection PyArgumentList
        li = [QVBoxLayout(), self.coin_grp_box,
              [QVBoxLayout(self.coin_grp_box),
               [QHBoxLayout(), self.coin_lbl, self.coin_dbl_sp_box, _QL.addStretch, self.coin_btn_create],
               self.coin_tbl_wid]]
        return self.lay_get(li)

    @flow
    def cons_lay_get(self) -> QBoxLayout:
        self.cons_grp_box.setTitle(u"Constraints")
        self.cons_lbl_con.setText(u"Type")
        self.cons_tbl_wid = self.cons_prep_table(self.cons_grp_box)
        self.cons_tbl_wid.itemSelectionChanged.connect(self.on_cons_tbl_sel_chg)
        self.cons_cmb_box = self.cons_prep_combo()
        self.cons_cmb_box.currentTextChanged.connect(self.on_cons_type_cmb_chg)
        self.cons_btn_del.clicked.connect(self.on_cons_delete_btn_clk)
        self.cons_btn_del.setText(u"Delete")
        self.cons_btn_del.setDisabled(True)
        # noinspection PyArgumentList
        li = [QVBoxLayout(), self.cons_grp_box,
              [QVBoxLayout(self.cons_grp_box),
               [QHBoxLayout(), self.cons_lbl_con, self.cons_cmb_box, _QL.addStretch, self.cons_btn_del],
               self.cons_tbl_wid]]
        return self.lay_get(li)

    @staticmethod
    def db_s_box_get(val, prec, step, func):
        sb = QDoubleSpinBox(None)
        sb.setDecimals(prec)
        sb.setSingleStep(step)
        sb.setValue(val)
        sb.valueChanged.connect(func)
        return sb

    def lay_get(self, obj_list: List) -> QBoxLayout:
        w_list = [QPushButton, QDoubleSpinBox, QTableWidget, QGroupBox, QComboBox, QSpinBox, QPlainTextEdit]
        layout = None
        for obj in obj_list:
            xp(type(obj).__name__, obj, **_ly)
            if isinstance(obj, QBoxLayout):
                xp('   layout:', **_ly)
                layout = obj
            elif isinstance(obj, list):
                xp('   list:', **_ly)
                layout.addLayout(self.lay_get(obj))
            elif type(obj).__name__ == 'tuple':
                func, param = obj
                xp('   tuple:', func.__name__, param, **_ly)
                if func.__name__ == 'addSpacing':
                    getattr(layout, func.__name__)(param)
            elif type(obj).__name__ == 'method_descriptor':
                xp('   method:', obj.__name__, **_ly)
                if obj.__name__ == 'addStretch':
                    getattr(layout, obj.__name__)()
                else:
                    getattr(layout, obj.__name__)()
            elif isinstance(obj, QCheckBox) or isinstance(obj, QLabel):
                layout.addWidget(obj, 0, Qt.AlignLeft)
            elif any(isinstance(obj, x) for x in w_list):
                layout.addWidget(obj)
            else:
                xp('------ UNEXPECTED OBJECT ----------', obj, **_ly)
        return layout

    # -------------------------------------------------------------------------
    @flow
    @Slot(object, object, object, object)
    def on_sel_chg_event(self, doc, obj, sub, pnt):
        xp(f'on_sel_chg_event doc:', str(doc), 'obj:', str(obj), 'sub:', str(sub), 'pnt', str(pnt), **_ob_s)
        self.tbl_clear_select(sub, pnt)

    @flow
    @Slot(str)
    def on_cons_chg(self, words):
        xp('Constraints changed', words, **_cs)
        co_list: List[CoEd.Constraint] = self.base.constraints_get_list()
        self.cons_update_combo(co_list)

    @flow
    @Slot(str)
    def on_coin_chg(self, words):
        xp('Coincident changed', words, **_co)

    @flow
    @Slot(str)
    def on_hv_chg(self, words):
        xp('HV changed', words, **_co)

    @flow
    @Slot(str)
    def on_xy_chg(self, words):
        xp('XY changed', words, **_co)

    @flow
    @Slot(str)
    def on_rad_chg(self, words):
        xp('XY changed', words, **_co)

    @flow
    def on_cur_tab_chg(self, index: int):
        xp('cur_tab:', index, **_ly)
        info: Dict[int, Tuple[QTableWidget, Callable]] = {
            0: (self.cons_tbl_wid, self.cons_update_table),
            1: (self.coin_tbl_wid, self.coin_update_table),
            2: (self.hv_tbl_wid, self.hv_update_table),
            3: (self.rad_tbl_wid, self.rad_update_table),
            4: (self.xy_tbl_wid, self.xy_update_table),
        }
        if index in range(5):
            tbl = info.get(index)[0]
            tbl.blockSignals(True)
            tbl.clearSelection()
            tbl.blockSignals(False)
            info.get(index)[1]()

    # ---------

    @flow
    def on_cfg_fnt_fil_chg(self, index):
        switcher = {
            0: QFontComboBox.AllFonts,
            1: QFontComboBox.ScalableFonts,
            2: QFontComboBox.NonScalableFonts,
            3: QFontComboBox.MonospacedFonts,
            4: QFontComboBox.ProportionalFonts
        }
        self.cfg_font_box.setFontFilters(switcher.get(index))

    @flow
    def on_cfg_fnt_size_val_chg(self, value):
        xp('fnt size', value, **_ly)
        f: QFont = self.cfg_txt_edt.font()
        f.setPointSize(value)
        xp('new', f, 'old', self.cfg_txt_edt.font(), **_ly)
        self.cfg_txt_edt.setFont(f)
        self.cfg_fnts.font_set(self.cfg_fnts.FONT_CFG_EDT, self.cfg_txt_edt.font())

    @flow
    def on_cfg_fnt_box_chg(self, font: QFont):
        xp('fnt', font, **_ly)
        # ! some mysterious problem forcing to do the following
        a_font = QFont()
        a_font.fromString(font.toString())
        a_font.setPointSize(self.cfg_font_size.value())
        xp('new', font, 'old', self.cfg_txt_edt.font(), **_ly)
        self.cfg_txt_edt.setFont(a_font)
        xp('after', self.cfg_txt_edt.font(), **_ly)
        self.cfg_fnts.font_set(self.cfg_fnts.FONT_CFG_EDT, self.cfg_txt_edt.font())

    @flow
    def on_cfg_btn_clk_tab(self):
        xp('tab', '', 'cfg', self.cfg_txt_edt.font(), **_ly)
        self.cons_tbl_wid.setFont(self.cfg_txt_edt.font())
        self.coin_tbl_wid.setFont(self.cfg_txt_edt.font())
        self.hv_tbl_wid.setFont(self.cfg_txt_edt.font())
        self.xy_tbl_wid.setFont(self.cfg_txt_edt.font())
        self.rad_tbl_wid.setFont(self.cfg_txt_edt.font())
        self.cfg_fnts.font_set(CfgFonts.FONT_TABLE, self.cfg_txt_edt.font())

    @flow
    def on_cfg_btn_clk_geo(self):
        xp('geo', self.geo_txt_edt.font(), 'cfg', self.cfg_txt_edt.font(), **_ly)
        self.geo_txt_edt.setFont(self.cfg_txt_edt.font())
        self.cfg_fnts.font_set(CfgFonts.FONT_GEO_EDT, self.geo_txt_edt.font())

    @flow
    def on_cfg_btn_clk_load(self):
        self.cfg_fnts.load()
        f_tbl: QFont = self.cfg_fnts.font_get(self.cfg_fnts.FONT_TABLE)
        f_geo: QFont = self.cfg_fnts.font_get(self.cfg_fnts.FONT_GEO_EDT)
        f_cfg: QFont = self.cfg_fnts.font_get(self.cfg_fnts.FONT_CFG_EDT)
        self.cons_tbl_wid.setFont(f_tbl)
        self.coin_tbl_wid.setFont(f_tbl)
        self.hv_tbl_wid.setFont(f_tbl)
        self.xy_tbl_wid.setFont(f_tbl)
        self.rad_tbl_wid.setFont(f_tbl)
        self.geo_txt_edt.setFont(f_geo)
        self.cfg_txt_edt.setFont(f_cfg)
        xp('geo', f_geo, 'cfg', f_cfg, **_ly)
        self.cfg_font_box.setCurrentFont(f_cfg)
        self.cfg_font_size.setValue(f_cfg.pointSize())

    @flow
    def on_cfg_btn_clk_save(self):
        self.cfg_fnts.save()

    @flow
    def on_geo_btn_clk_geo(self):
        self.geo_txt_edt.setPlainText(self.base.geo_xml_get())

    @flow
    def on_geo_btn_clk_ext(self):
        self.base.analyse_sketch()
        self.geo_txt_edt.setPlainText(self.base.sketch_info_xml_get())

    # ---------

    @flow
    def on_xy_chk_x_state_chg(self, obj):
        if not self.xy_chk_box_x.isChecked():
            self.xy_chk_box_y.setChecked(True)

    @flow
    def on_xy_chk_y_state_chg(self, obj):
        if not self.xy_chk_box_y.isChecked():
            self.xy_chk_box_x.setChecked(True)

    @flow
    def on_xy_create_btn_clk(self):
        self.xy_create(self.xy_chk_box_x.isChecked(), self.xy_chk_box_y.isChecked())

    @flow
    def on_xy_tbl_sel_chg(self):
        self.xy_selected()

    @flow
    def on_rad_create_btn_clk(self):
        self.rad_create()

    @flow
    def on_rad_chk_box_state_chg(self, obj):
        if self.rad_chk_box.isChecked():
            self.rad_dbl_sp_box.setEnabled(True)
        else:
            self.rad_dbl_sp_box.setEnabled(False)

    @flow
    def on_rad_val_chg(self, obj):
        value = self.rad_dbl_sp_box.value()
        self.base.radius = value

    @flow
    def on_rad_tbl_sel_chg(self):
        self.rad_selected()

    @flow
    def on_hv_create_btn_clk(self):
        self.hv_create()

    @flow
    def on_hv_snap_val_chg(self, obj):
        value = self.hv_dbl_sp_box.value()
        self.base.snap_angel = value
        self.hv_update_table()
        xp("Current Value :", value)

    @flow
    def on_hv_tbl_sel_chg(self):
        self.hv_selected()

    @flow
    def on_coin_create_btn_clk(self):
        self.coin_create()

    @flow
    def on_coin_snap_val_chg(self, obj):
        value = self.coin_dbl_sp_box.value()
        self.base.snap_dist = value
        self.coin_update_table()
        xp("Current Value :", value)

    @flow
    def on_coin_tbl_sel_chg(self):
        self.coin_selected()

    @flow
    def on_cons_delete_btn_clk(self):
        self.cons_delete()

    @flow
    def on_cons_type_cmb_chg(self, txt):
        ct: ConType = ConType(txt)
        with Profile(enable=False):
            self.cons_update_table(ct)

    @flow
    def on_cons_tbl_sel_chg(self):
        self.cons_selected()
    # -------------------------------------------------------------------------

    @flow
    def xy_create(self, x: bool, y: bool):
        mod: QItemSelectionModel = self.xy_tbl_wid.selectionModel()
        rows: List[QModelIndex] = mod.selectedRows(2)
        create_list: List[int] = [x.data().geo_id for x in rows]
        xp('create_list', create_list, **_xy)
        for idx in rows:
            xp('row', idx.row(), ':', idx.data(), **_xy)
        self.base.xy_dist_create(create_list, x, y)
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
        edg_list: List[CoEd.XyEdge] = self.base.xy_edg_get_list()
        # xp('->', edg_list, **_rd_g)
        for idx, item in enumerate(edg_list):
            self.xy_tbl_wid.insertRow(0)
            s = "x {:.2f} y {:.2f} \nx {:.2f} y {:.2f}"
            fmt = s.format(item.start.x, item.start.y, item.end.x, item.end.y)
            self.xy_tbl_wid.setItem(0, 0, QTableWidgetItem(fmt))
            fmt2 = "Id: {}\nx {} y {}".format(item.geo_id, item.has_x, item.has_y)
            xp(f'geo {item.geo_id} x {item.has_x} y {item.has_y}', **_xy)
            w_item = QTableWidgetItem(fmt2)
            w_item.setTextAlignment(Qt.AlignCenter)
            self.xy_tbl_wid.setItem(0, 1, w_item)
            w_item = QTableWidgetItem('')
            w_item.setData(Qt.DisplayRole, item)
            # w_item.setData(Qt.DisplayRole, item.geo_id)
            xp('col 3', item.geo_id, **_xy)
            self.xy_tbl_wid.setItem(0, 2, w_item)
        self.xy_tbl_wid.setSortingEnabled(__sorting_enabled)

    @flow
    def xy_selected(self):
        indexes: List[QModelIndex] = self.xy_tbl_wid.selectionModel().selectedRows(2)
        rows: List = [x.row() for x in sorted(indexes)]
        xp(f'selected: {rows}', **_xy)
        if len(rows) == 0:
            self.xy_btn_create.setDisabled(True)
        else:
            self.xy_btn_create.setDisabled(False)

        doc_name = App.activeDocument().Name
        Gui.Selection.clearSelection(doc_name, True)
        ed_info = Gui.ActiveDocument.InEditInfo
        sk_name = ed_info[0].Name

        for item in indexes:
            xy: CoEd.XyEdge = item.data()
            xp(f'row: {str(item.row())} idx: {xy.geo_id} cons: {xy}', **_xy)
            Gui.Selection.addSelection(doc_name, sk_name, f'Edge{xy.geo_id + 1}')

    # -------------------------------------------------------------------------

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
    def rad_create(self):
        rad = None
        if self.rad_chk_box.isChecked():
            rad = self.base.radius
        mod: QItemSelectionModel = self.rad_tbl_wid.selectionModel()
        rows: List[QModelIndex] = mod.selectedRows(2)
        create_list: List[CoEd.Circle] = [x.data() for x in rows]
        for idx in rows:
            xp(idx.row(), ':', idx.data(), **_rd)
        self.base.rad_dia_create(create_list, rad)
        self.rad_update_table()

    @flow
    def rad_update_table(self):
        self.rad_tbl_wid.setRowCount(0)
        __sorting_enabled = self.rad_tbl_wid.isSortingEnabled()
        self.rad_tbl_wid.setSortingEnabled(False)
        cir_list: List[CoEd.Circle] = self.base.circle_get_list()
        xp('->', cir_list, **_rd)
        for item in cir_list:
            self.rad_tbl_wid.insertRow(0)
            fmt = "x: {:.2f} y: {:.2f}".format(item.center_x, item.center_y)
            self.rad_tbl_wid.setItem(0, 0, QTableWidgetItem(fmt))
            fmt2 = "Id: {} r: {:.2f}".format(item.geo_id, item.radius)
            w_item = QTableWidgetItem(fmt2)
            w_item.setTextAlignment(Qt.AlignCenter)
            self.rad_tbl_wid.setItem(0, 1, w_item)
            w_item = QTableWidgetItem('')
            w_item.setData(Qt.DisplayRole, item)
            xp('col 3', item.geo_id, **_rd)
            self.rad_tbl_wid.setItem(0, 2, w_item)
        self.rad_tbl_wid.setSortingEnabled(__sorting_enabled)

    @flow
    def rad_selected(self):
        indexes: List[QModelIndex] = self.rad_tbl_wid.selectionModel().selectedRows(2)
        rows: List = [x.row() for x in sorted(indexes)]
        xp(f'selected: {rows}', **_rd)
        if len(rows) == 0:
            self.rad_btn_create.setDisabled(True)
        else:
            self.rad_btn_create.setDisabled(False)

        doc_name = App.activeDocument().Name
        Gui.Selection.clearSelection(doc_name, True)
        ed_info = Gui.ActiveDocument.InEditInfo
        sk_name = ed_info[0].Name

        for item in indexes:
            rad: CoEd.Circle = item.data()
            xp(f'row: {str(item.row())} idx: {rad.geo_id} cons: {rad}', **_rd)
            Gui.Selection.addSelection(doc_name, sk_name, f'Edge{rad.geo_id + 1}')
            idx = 0
            while True:
                geo, pos = self.base.sketch.getGeoVertexIndex(idx)
                if (geo == rad.geo_id) and (pos == 3):
                    Gui.Selection.addSelection(doc_name, sk_name, f'Vertex{idx + 1}')
                    xp(f'Vertex{idx + 1} idx: {idx} geo: ({geo}.{pos})', **_rd)
                if (geo == -2000) and (pos == 0):
                    xp(f'unexpected, no vertex found', **_rd)
                    break
                idx += 1

    # -------------------------------------------------------------------------

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
        create_list: List[CoEd.HvEdge] = [x.data() for x in rows]
        for idx in rows:
            xp('row', idx.row(), ':', idx.data(), **_hv)
        self.base.hv_create(create_list)
        self.hv_update_table()

    @flow
    def hv_update_table(self):
        self.hv_tbl_wid.setRowCount(0)
        __sorting_enabled = self.hv_tbl_wid.isSortingEnabled()
        self.hv_tbl_wid.setSortingEnabled(False)
        edge_list: List[CoEd.HvEdge] = self.base.hv_edges_get_list()
        for idx, item in enumerate(edge_list):
            if item.has_hv_cons:
                continue
            self.hv_tbl_wid.insertRow(0)
            fmt2 = "x {:.2f} y {:.2f} : x {:.2f} y {:.2f}".format(item.pt_start.x, item.pt_start.y,
                                                                  item.pt_end.x, item.pt_end.y)
            xp('col 1', fmt2, **_hv)
            fmt = "{: 6.2f} {: 6.2f}\n{: 6.2f} {: 6.2f}".format(item.pt_start.x, item.pt_start.y,
                                                                item.pt_end.x, item.pt_end.y)
            self.hv_tbl_wid.setItem(0, 0, QTableWidgetItem(fmt))
            fmt2 = "Id {} xa {:.2f} : ya {:.2f}".format(item.geo_idx, item.x_angel, item.y_angel)
            xp('col 2', fmt2, **_hv)
            fmt = "Id {} \nxa {:.2f} ya {:.2f}".format(item.geo_idx, item.x_angel, item.y_angel)
            w_item = QTableWidgetItem(fmt)
            w_item.setTextAlignment(Qt.AlignCenter)
            self.hv_tbl_wid.setItem(0, 1, w_item)
            w_item2 = QTableWidgetItem()
            w_item2.setData(Qt.DisplayRole, item)
            xp('col 3', idx, **_hv)
            self.hv_tbl_wid.setItem(0, 2, w_item2)
        self.hv_tbl_wid.setSortingEnabled(__sorting_enabled)

    @flow
    def hv_selected(self):
        indexes: List[QModelIndex] = self.hv_tbl_wid.selectionModel().selectedRows(2)
        rows: List = [x.row() for x in sorted(indexes)]
        xp(f'selected: {rows}', **_hv)
        if len(rows) == 0:
            self.hv_btn_create.setDisabled(True)
        else:
            self.hv_btn_create.setDisabled(False)

        doc_name = App.activeDocument().Name
        Gui.Selection.clearSelection(doc_name, True)
        ed_info = Gui.ActiveDocument.InEditInfo
        sk_name = ed_info[0].Name

        for item in indexes:
            hv: CoEd.HvEdge = item.data()
            xp(f'row: {str(item.row())} idx: {hv.geo_idx} cons: {hv}', **_hv)
            Gui.Selection.addSelection(doc_name, sk_name, f'Edge{hv.geo_idx + 1}')

    # -------------------------------------------------------------------------

    @flow
    def coin_create(self):
        mod: QItemSelectionModel = self.coin_tbl_wid.selectionModel()
        rows: List[QModelIndex] = mod.selectedRows(2)
        create_list: List[CoEd.Point] = [x.data() for x in rows]
        for idx in rows:
            xp(idx.row(), ':', idx.data(), **_co)
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
        # todo find transitive coins
        self.coin_tbl_wid.setRowCount(0)
        __sorting_enabled = self.coin_tbl_wid.isSortingEnabled()
        self.coin_tbl_wid.setSortingEnabled(False)
        pt_list: List[CoEd.Point] = self.base.points_get_list()
        # xp('pt list:', pt_list, **_cog)
        for i, pt in enumerate(pt_list):
            if len(pt.coin_pts) == 1:
                continue
            if len(pt.coin_pts) > 1:
                self.coin_tbl_wid.insertRow(0)
                fmt = "{0: 6.2f} {1: 6.2f}".format(pt.geo_item_pt.x, pt.geo_item_pt.y)
                self.coin_tbl_wid.setItem(0, 0, QTableWidgetItem(fmt))
                fm = ''.join("{0:2}.{1} ".format(x.geo_id, x.type_id) for x in pt.coin_pts)
                xp('fm:', fm, **_co)
                self.coin_tbl_wid.setItem(0, 1, QTableWidgetItem(fm))
                w_item = QTableWidgetItem()
                w_item.setData(Qt.DisplayRole, pt)
                # w_item.setData(Qt.DisplayRole, i)
                self.coin_tbl_wid.setItem(0, 2, w_item)
                xp('new row: Id', i, fmt, fm, **_co)
        self.coin_tbl_wid.setSortingEnabled(__sorting_enabled)

    @flow
    def coin_selected(self):
        indexes: List[QModelIndex] = self.coin_tbl_wid.selectionModel().selectedRows(2)
        rows: List = [x.row() for x in sorted(indexes)]
        xp(f'selected: {rows}', **_co)
        if len(rows) == 0:
            self.coin_btn_create.setDisabled(True)
        else:
            self.coin_btn_create.setDisabled(False)

        doc_name = App.activeDocument().Name
        Gui.Selection.clearSelection(doc_name, True)
        ed_info = Gui.ActiveDocument.InEditInfo
        sk_name = ed_info[0].Name

        for item in indexes:
            coin: CoEd.Point = item.data()
            xp(f'row: {str(item.row())} coin: {coin}', **_co)
            lst: List[GeoPt] = coin.coin_pts
            for pt in lst:
                ptn: GeoPtn = GeoPtn(pt.geo_id, pt_typ_int[pt.type_id])
                idx = 0
                while True:
                    geo, pos = self.base.sketch.getGeoVertexIndex(idx)
                    if (geo == ptn.geo_id) and (pos == ptn.type_id):
                        Gui.Selection.addSelection(doc_name, sk_name, f'Vertex{idx + 1}')
                        xp(f'Vertex{idx + 1} idx: {idx} geo: ({geo}.{pos})', **_co)
                    if (geo == -2000) and (pos == 0):
                        xp(f'unexpected, no vertex found', **_co)
                        break
                    idx += 1

    # -------------------------------------------------------------------------

    @flow
    def cons_delete(self):
        mod: QItemSelectionModel = self.cons_tbl_wid.selectionModel()
        rows: List[QModelIndex] = mod.selectedRows(2)
        del_list: List[int] = list()
        for idx in rows:
            xp(str(idx.row()), ':', str(idx.data()), idx.data().co_idx)
            del_list.append(idx.data().co_idx)
        self.base.constraints_delete(del_list)
        self.cons_update_table()

    @flow
    def cons_update_table(self, typ: ConType = ConType.ALL):
        self.cons_tbl_wid.setRowCount(0)
        __sorting_enabled = self.cons_tbl_wid.isSortingEnabled()
        self.cons_tbl_wid.setSortingEnabled(False)
        co_list: List[CoEd.Constraint] = self.base.constraints_get_list()
        for idx, item in enumerate(co_list):
            if typ == ConType.ALL or typ == ConType(item.type_id):
                li: List[int] = list()
                li.insert(0, idx)
                self.cons_tbl_wid.insertRow(0)
                self.cons_tbl_wid.setItem(0, 0, QTableWidgetItem(item.type_id))
                self.cons_tbl_wid.setItem(0, 1, QTableWidgetItem(str(item)))
                w_item = QTableWidgetItem()
                w_item.setData(Qt.DisplayRole, item)
                # w_item.setData(Qt.DisplayRole, item.co_idx)
                self.cons_tbl_wid.setItem(0, 2, w_item)
        self.cons_tbl_wid.setSortingEnabled(__sorting_enabled)

    @flow
    def cons_selected(self):
        indexes: List[QModelIndex] = self.cons_tbl_wid.selectionModel().selectedRows(2)
        rows: List = [x.row() for x in sorted(indexes)]
        xp(f'selected: {rows}', **_cs)
        if len(rows) == 0:
            self.cons_btn_del.setDisabled(True)
        else:
            self.cons_btn_del.setDisabled(False)

        lo = Lookup(self.base.sketch)
        doc_name = App.activeDocument().Name
        Gui.Selection.clearSelection(doc_name, True)
        ed_info = Gui.ActiveDocument.InEditInfo
        sk_name = ed_info[0].Name

        for item in indexes:
            co: CoEd.Constraint = item.data()
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
    def cons_update_combo(self, co_list: List[CoEd.Constraint]) -> None:
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
    def cons_prep_combo() -> QComboBox:
        combo_box = QComboBox(None)
        combo_box.addItem(ConType.ALL.value)
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

    # -------------------------------------------------------------------------

    @flow
    def tbl_clear_select(self, shape, pnt):

        from_gui: bool = True
        if App.Vector(pnt) == App.Vector(0, 0, 0):
            from_gui = False

        if from_gui:
            switcher: Dict[int, QTableWidget] = {
                0: self.cons_tbl_wid,
                1: self.coin_tbl_wid,
                2: self.hv_tbl_wid,
                3: self.rad_tbl_wid,
                4: self.xy_tbl_wid,
            }
            for tbl in switcher.values():
                tbl.blockSignals(True)
                tbl.clearSelection()
                tbl.blockSignals(False)

        if shape.find('Vertex') != -1:
            no = int(shape[6:])
            typ = 'Vertex'
            geo, pos = self.base.sketch.getGeoVertexIndex(no)
            xp(f'received: gui: {from_gui} {typ} {no} geo: ({geo}.{pos})', **_fl)
        elif shape.find('Edge') != -1:
            no = int(shape[4:])
            typ = 'Edge'
            xp(f'received: gui: {from_gui} {typ} {no}', **_fl)
        elif shape.find('Constraint') != -1:
            no = int(shape[10:])
            typ = 'Constraint'
            xp(f'received: gui: {from_gui} {typ} {no}', **_fl)
        else:
            xp(f'received ?: gui: {from_gui} {shape} {pnt}', **_fl)

    # Constraint2

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


xps(__name__)
if __name__ == '__main__':
    import sys

    app = QApplication()
    my_style(app)
    controller = CoEdGui()
    controller.show()
    sys.exit(app.exec_())
