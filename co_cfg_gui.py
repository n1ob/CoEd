from PySide2.QtGui import QFont
from PySide2.QtWidgets import QWidget, QBoxLayout, QComboBox, QPlainTextEdit, QFontComboBox, QSpinBox, QPushButton, \
    QVBoxLayout, QHBoxLayout

import co_gui
import co_impl
from co_config import CfgFonts
from co_logger import xp, _ev, flow, _ly
from co_style import XMLHighlighter

_QL = QBoxLayout


class CfgGui:
    def __init__(self, base):
        self.base: co_gui.CoEdGui = base
        self.impl: co_impl.CoEd = self.base.base
        self.tab_cfg = QWidget(None)
        self.cfg_fnts = CfgFonts()
        self.cfg_fnts.load()
        self.base.tbl_font = self.cfg_fnts.font_get(CfgFonts.FONT_TABLE)
        self.base.geo_edt_font = self.cfg_fnts.font_get(CfgFonts.FONT_GEO_EDT)
        self.base.cfg_edt_font = self.cfg_fnts.font_get(CfgFonts.FONT_CFG_EDT)

        self.cfg_filter_cmb = QComboBox()
        self.cfg_txt_edt = QPlainTextEdit()
        self.cfg_font_box = QFontComboBox()
        self.cfg_font_size = QSpinBox()
        self.cfg_btn_geo = QPushButton('geo')
        self.cfg_btn_tbl = QPushButton('tbl')
        self.cfg_btn_load = QPushButton('Load')
        self.cfg_btn_save = QPushButton('Save')
        self.tab_cfg.setLayout(self.cfg_lay_get())

    @flow
    def cfg_lay_get(self) -> QBoxLayout:
        self.cfg_filter_cmb.addItems(['all fonts', 'scalable', 'non-scalable', 'monospace', 'equal prop'])
        self.cfg_filter_cmb.currentIndexChanged.connect(self.on_cfg_fnt_fil_chg)
        self.cfg_filter_cmb.setMaximumWidth(200)
        self.cfg_txt_edt.setFont(self.base.cfg_edt_font)
        self.cfg_txt_edt.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.cfg_txt_edt.highlighter = XMLHighlighter(self.cfg_txt_edt.document())
        self.cfg_txt_edt.setPlainText(self.impl.geo_xml_get())
        self.cfg_font_box.setCurrentFont(self.base.cfg_edt_font)
        self.cfg_font_box.currentFontChanged.connect(self.on_cfg_fnt_box_chg)
        self.cfg_font_box.setMaximumWidth(300)
        self.cfg_font_size.setRange(6, 32)
        self.cfg_font_size.setSingleStep(1)
        self.cfg_font_size.setValue(self.base.cfg_edt_font.pointSize())
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
        return self.base.lay_get(lis)


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
        self.base.cs_gui.cons_tbl_wid.setFont(self.cfg_txt_edt.font())
        self.base.co_gui.co_tbl_wid.setFont(self.cfg_txt_edt.font())
        self.base.hv_gui.hv_tbl_wid.setFont(self.cfg_txt_edt.font())
        self.base.xy_gui.xy_tbl_wid.setFont(self.cfg_txt_edt.font())
        self.base.rd_gui.rad_tbl_wid.setFont(self.cfg_txt_edt.font())
        self.cfg_fnts.font_set(CfgFonts.FONT_TABLE, self.cfg_txt_edt.font())

    @flow
    def on_cfg_btn_clk_geo(self):
        xp('geo', self.base.geo_txt_edt.font(), 'cfg', self.cfg_txt_edt.font(), **_ly)
        self.base.geo_txt_edt.setFont(self.cfg_txt_edt.font())
        self.cfg_fnts.font_set(CfgFonts.FONT_GEO_EDT, self.base.geo_txt_edt.font())

    @flow
    def on_cfg_btn_clk_load(self):
        self.base.cfg_fnts.load()
        f_tbl: QFont = self.cfg_fnts.font_get(self.cfg_fnts.FONT_TABLE)
        f_geo: QFont = self.cfg_fnts.font_get(self.cfg_fnts.FONT_GEO_EDT)
        f_cfg: QFont = self.cfg_fnts.font_get(self.cfg_fnts.FONT_CFG_EDT)
        self.base.cs_gui.cons_tbl_wid.setFont(f_tbl)
        self.base.co_gui.co_tbl_wid.setFont(f_tbl)
        self.base.hv_gui.hv_tbl_wid.setFont(f_tbl)
        self.base.xy_gui.xy_tbl_wid.setFont(f_tbl)
        self.base.rd_gui.rad_tbl_wid.setFont(f_tbl)
        self.base.geo_txt_edt.setFont(f_geo)
        self.cfg_txt_edt.setFont(f_cfg)
        xp('geo', f_geo, 'cfg', f_cfg, **_ly)
        self.cfg_font_box.setCurrentFont(f_cfg)
        self.cfg_font_size.setValue(f_cfg.pointSize())

    @flow
    def on_cfg_btn_clk_save(self):
        self.base.cfg_fnts.save()
