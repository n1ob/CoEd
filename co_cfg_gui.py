from pathlib import Path

from PySide2 import QtCore
from PySide2.QtCore import QObject, Qt, Slot
from PySide2.QtGui import QFont, QPalette, QColor
from PySide2.QtWidgets import QWidget, QBoxLayout, QComboBox, QPlainTextEdit, QFontComboBox, QSpinBox, QPushButton, \
    QVBoxLayout, QHBoxLayout, QLineEdit, QFileDialog, QMessageBox, QLabel, QCheckBox
import FreeCAD as App
import co_gui
import co_impl
import co_logger
from co_cmn import contrast_color, lumi, split_rgb, complement_color
from co_config import CfgFonts, CfgBasics, CfgColors, Cfg
from co_logger import xp, _ev, flow, _ly, _cf
from co_style import XMLHighlighter

_QL = QBoxLayout


class CfgGui:
    def __init__(self, base):
        self.base: co_gui.CoEdGui = base
        self.impl: co_impl.CoEd = self.base.base
        self.tab_cfg = QWidget(None)
        self.cfg_fnts = CfgFonts()
        self.cfg_basic = CfgBasics()
        self.cfg_color = CfgColors()
        self.cfg_color.color_changed.connect(self.on_color_changed)
        self.cfg_log_dir = self.cfg_basic.get(CfgBasics.LOG_DIR)
        if self.cfg_log_dir is None:
            self.cfg_log_path = self.cfg_basic.log_name_get()
        else:
            self.cfg_log_path = str(Path(self.cfg_log_dir, self.cfg_basic.log_name_get()))
        co_logger.xp_worker.log_path_set(self.cfg_log_path)
        # log_path_set(self.cfg_log_path)
        # co_logger.xp_thread_event.set()
        self.base.cfg_blubber = self.cfg_basic.get(self.cfg_basic.SHOW_ONLY_VALID)

        self.base.tbl_font = self.cfg_fnts.font_get(CfgFonts.FONT_TABLE)
        self.base.geo_edt_font = self.cfg_fnts.font_get(CfgFonts.FONT_GEO_EDT)
        self.base.cfg_edt_font = self.cfg_fnts.font_get(CfgFonts.FONT_CFG_EDT)

        self.cfg_filter_cmb = QComboBox()
        self.cfg_txt_edt = QPlainTextEdit()
        self.cfg_txt_edt_high = XMLHighlighter(self.cfg_txt_edt.document())
        self.cfg_font_box = QFontComboBox()
        self.cfg_font_size = QSpinBox()
        self.cfg_btn_geo = QPushButton('geo')
        self.cfg_btn_tbl = QPushButton('tbl')
        self.cfg_btn_load = QPushButton('Load')
        self.cfg_btn_save = QPushButton('Save')
        self.cfg_chk_box_sel = QCheckBox()

        self.cfg_ln_edt_col_1 = QLineEdit()
        self.cfg_ln_edt_col_2 = QLineEdit()
        self.cfg_ln_edt_col_3 = QLineEdit()
        self.cfg_ln_edt_col_4 = QLineEdit()
        self.cfg_ln_edt_col_5 = QLineEdit()
        self.cfg_ln_edt_col_6 = QLineEdit()
        self.cfg_ln_edt_sav = [''] * 6

        self.cfg_lbl_log = QLabel('Log Dir')

        self.cfg_log_ln_edt = QLineEdit()
        self.cfg_btn_log_file_dlg = QPushButton('...')
        self.tab_cfg.setLayout(self.cfg_lay_get())

    @flow
    def cfg_lay_get(self) -> QBoxLayout:
        self.cfg_filter_cmb.addItems(['all fonts', 'scalable', 'non-scalable', 'monospace', 'equal prop'])
        self.cfg_filter_cmb.currentIndexChanged.connect(self.on_fnt_fil_chg)
        self.cfg_filter_cmb.setMaximumWidth(200)
        self.cfg_txt_edt.setFont(self.base.cfg_edt_font)
        self.cfg_txt_edt.setLineWrapMode(QPlainTextEdit.NoWrap)
        # self.cfg_txt_edt.highlighter = XMLHighlighter(self.cfg_txt_edt.document())
        self.cfg_txt_edt.setPlainText(self.impl.geo_xml_get())
        self.cfg_font_box.setCurrentFont(self.base.cfg_edt_font)
        self.cfg_font_box.currentFontChanged.connect(self.on_fnt_box_chg)
        self.cfg_font_box.setMaximumWidth(300)
        self.cfg_font_size.setRange(6, 32)
        self.cfg_font_size.setSingleStep(1)
        self.cfg_font_size.setValue(self.base.cfg_edt_font.pointSize())
        self.cfg_font_size.valueChanged.connect(self.on_fnt_size_val_chg)
        self.cfg_btn_geo.clicked.connect(self.on_btn_clk_geo)
        self.cfg_btn_tbl.clicked.connect(self.on_btn_clk_tab)
        self.cfg_btn_load.clicked.connect(self.on_btn_clk_load)
        self.cfg_btn_save.clicked.connect(self.on_btn_clk_save)
        self.cfg_btn_log_file_dlg.clicked.connect(self.on_btn_log_file_dlg)
        if self.cfg_log_dir is None:
            self.cfg_log_ln_edt.setPlaceholderText('log file directory')
        else:
            self.cfg_log_ln_edt.setText(self.cfg_log_dir)
        self.cfg_log_ln_edt.editingFinished.connect(self.on_log_edt_finish)
        self.cfg_chk_box_sel.setText('show only possible')
        self.cfg_chk_box_sel.setChecked(self.base.cfg_blubber)
        self.cfg_chk_box_sel.stateChanged.connect(self.on_chk_box_sel_chg)

        self.cfg_ln_edt_col_1.setInputMask('\#HHHHHH;_')
        self.cfg_ln_edt_col_2.setInputMask('\#HHHHHH;_')
        self.cfg_ln_edt_col_3.setInputMask('\#HHHHHH;_')
        self.cfg_ln_edt_col_4.setInputMask('\#HHHHHH;_')
        self.cfg_ln_edt_col_5.setInputMask('\#HHHHHH;_')
        self.cfg_ln_edt_col_6.setInputMask('\#HHHHHH;_')

        self.cfg_ln_edt_sav[0] = self.cfg_color.color_get(CfgColors.COLOR_XML_KEYWORD).name()
        xp('COLOR_XML_KEYWORD', self.cfg_ln_edt_sav[0], **_cf)
        self.cfg_ln_edt_col_1.setText(self.cfg_ln_edt_sav[0].lstrip('#'))
        self.set_style(self.cfg_ln_edt_col_1)

        self.cfg_ln_edt_sav[1] = self.cfg_color.color_get(CfgColors.COLOR_XML_TXT).name()
        xp('COLOR_XML_TXT', self.cfg_ln_edt_sav[1], **_cf)
        self.cfg_ln_edt_col_2.setText(self.cfg_ln_edt_sav[1].lstrip('#'))
        self.set_style(self.cfg_ln_edt_col_2)

        self.cfg_ln_edt_sav[2] = self.cfg_color.color_get(CfgColors.COLOR_XML_LN_CMT).name()
        xp('COLOR_XML_LN_CMT', self.cfg_ln_edt_sav[2], **_cf)
        self.cfg_ln_edt_col_3.setText(self.cfg_ln_edt_sav[2].lstrip('#'))
        self.set_style(self.cfg_ln_edt_col_3)

        self.cfg_ln_edt_sav[3] = self.cfg_color.color_get(CfgColors.COLOR_XML_VAL).name()
        xp('COLOR_XML_VAL', self.cfg_ln_edt_sav[3], **_cf)
        self.cfg_ln_edt_col_4.setText(self.cfg_ln_edt_sav[3].lstrip('#'))
        self.set_style(self.cfg_ln_edt_col_4)

        self.cfg_ln_edt_sav[4] = self.cfg_color.color_get(CfgColors.COLOR_XML_ATTR).name()
        xp('COLOR_XML_ATTR', self.cfg_ln_edt_sav[4], **_cf)
        self.cfg_ln_edt_col_5.setText(self.cfg_ln_edt_sav[4].lstrip('#'))
        self.set_style(self.cfg_ln_edt_col_5)

        self.cfg_ln_edt_sav[5] = self.cfg_color.color_get(CfgColors.COLOR_XML_ELEM).name()
        xp('COLOR_XML_ELEM', self.cfg_ln_edt_sav[5], **_cf)
        self.cfg_ln_edt_col_6.setText(self.cfg_ln_edt_sav[5].lstrip('#'))
        self.set_style(self.cfg_ln_edt_col_6)

        self.cfg_ln_edt_col_1.editingFinished.connect(self.on_ed_color_finish_1)
        self.cfg_ln_edt_col_2.editingFinished.connect(self.on_ed_color_finish_2)
        self.cfg_ln_edt_col_3.editingFinished.connect(self.on_ed_color_finish_3)
        self.cfg_ln_edt_col_4.editingFinished.connect(self.on_ed_color_finish_4)
        self.cfg_ln_edt_col_5.editingFinished.connect(self.on_ed_color_finish_5)
        self.cfg_ln_edt_col_6.editingFinished.connect(self.on_ed_color_finish_6)

        lis = [QVBoxLayout(),
               [QHBoxLayout(), self.cfg_ln_edt_col_1, self.cfg_ln_edt_col_2, self.cfg_ln_edt_col_3],
               [QHBoxLayout(), self.cfg_ln_edt_col_4, self.cfg_ln_edt_col_5, self.cfg_ln_edt_col_6],
               [QHBoxLayout(), self.cfg_lbl_log, self.cfg_log_ln_edt, self.cfg_btn_log_file_dlg],
               [QHBoxLayout(), self.cfg_filter_cmb, _QL.addStretch, self.cfg_btn_tbl, (_QL.addSpacing, 20), self.cfg_btn_geo],
               [QHBoxLayout(), self.cfg_font_box, _QL.addStretch, self.cfg_font_size],
               (_QL.addSpacing, 10), self.cfg_txt_edt, (_QL.addSpacing, 10),
               [QHBoxLayout(), self.cfg_chk_box_sel, _QL.addStretch, self.cfg_btn_load, (_QL.addSpacing, 20), self.cfg_btn_save]]
        return self.base.lay_get(lis)

    @flow
    @Slot(int)
    def on_chk_box_sel_chg(self, state: int):
        xp('on_chk_box_sel_chg', **_cf)
        self.base.cfg_blubber = state

    @flow
    @Slot(str)
    def on_color_changed(self, cid: str):
        xp('on_color_changed', cid, **_cf)

    @flow
    def on_ed_color_finish_1(self):
        self.do_ed_finish(self.cfg_ln_edt_col_1, 0, CfgColors.COLOR_XML_KEYWORD)

    @flow
    def on_ed_color_finish_2(self):
        self.do_ed_finish(self.cfg_ln_edt_col_2, 1, CfgColors.COLOR_XML_TXT)

    @flow
    def on_ed_color_finish_3(self):
        self.do_ed_finish(self.cfg_ln_edt_col_3, 2, CfgColors.COLOR_XML_LN_CMT)

    @flow
    def on_ed_color_finish_4(self):
        self.do_ed_finish(self.cfg_ln_edt_col_4, 3, CfgColors.COLOR_XML_VAL)

    @flow
    def on_ed_color_finish_5(self):
        self.do_ed_finish(self.cfg_ln_edt_col_5, 4, CfgColors.COLOR_XML_ATTR)

    @flow
    def on_ed_color_finish_6(self):
        self.do_ed_finish(self.cfg_ln_edt_col_6, 5, CfgColors.COLOR_XML_ELEM)

    @flow
    def do_ed_finish(self, ed: QLineEdit, idx: int, cid: str):
        if self.cfg_ln_edt_sav[idx] != ed.text():
            self.cfg_ln_edt_sav[idx] = ed.text()
            co = QColor()
            co.setNamedColor(ed.text())
            self.cfg_color.color_set(cid, co)
            self.set_style(ed)
        else:
            xp('skip')

    @flow
    def set_style(self, ed: QLineEdit):
        xp('styleSheet before', ed.styleSheet(), **_cf)
        cc1 = contrast_color(lumi(split_rgb(ed.text())))
        cp1 = complement_color(ed.text())
        cc2 = contrast_color(lumi(split_rgb(cp1)))
        xp(f'ed.text {ed.text()} contrast {cc1} complement {cp1} contrast {cc2}', **_cf)
        s = f'color: {cc1}; background-color: {ed.text()}; selection-color: {cc2}; selection-background-color: {cp1};'
        ed.setStyleSheet(s)
        xp('styleSheet after', ed.styleSheet(), **_cf)

    @flow
    def on_log_edt_finish(self):
        dir_ = self.cfg_log_ln_edt.text()
        xp('edt text', dir_, **_cf)

        if not Path.is_dir(Path(dir_)):
            self.cfg_log_ln_edt.setText('')
            dialog = QMessageBox(QMessageBox.Warning, 'Not a Directory!', "That's not a valid directory!")
            dialog.setWindowModality(QtCore.Qt.ApplicationModal)
            dialog.setWindowState(QtCore.Qt.WindowActive)
            flags: Qt.WindowFlags = Qt.Dialog
            flags |= Qt.WindowStaysOnTopHint
            dialog.setWindowFlags(flags)
            dialog.exec_()
        else:
            self.cfg_log_dir = dir_
            pth = Path(dir_, 'coed.log')
            self.cfg_log_path = str(pth)
            xp('passed is_dir', pth, **_cf)
            self.cfg_basic.set(CfgBasics.LOG_DIR, self.cfg_log_dir)

    @flow
    def on_btn_log_file_dlg(self):
        dir_ = QFileDialog.getExistingDirectory(None, "Open Directory",
                                                "/home",
                                                QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        self.cfg_log_ln_edt.setText(dir_)
        self.cfg_log_dir = dir_
        self.cfg_basic.set(CfgBasics.LOG_DIR, dir_)
        pth = Path(dir_, self.cfg_basic.log_name_get())
        self.cfg_log_path = str(pth)
        xp(pth, **_cf)

    @flow
    def on_fnt_fil_chg(self, index):
        switcher = {
            0: QFontComboBox.AllFonts,
            1: QFontComboBox.ScalableFonts,
            2: QFontComboBox.NonScalableFonts,
            3: QFontComboBox.MonospacedFonts,
            4: QFontComboBox.ProportionalFonts
        }
        self.cfg_font_box.setFontFilters(switcher.get(index))

    @flow
    def on_fnt_size_val_chg(self, value):
        xp('fnt size', value, **_ly)
        f: QFont = self.cfg_txt_edt.font()
        f.setPointSize(value)
        xp('new', f, 'old', self.cfg_txt_edt.font(), **_ly)
        self.cfg_txt_edt.setFont(f)
        self.cfg_fnts.font_set(self.cfg_fnts.FONT_CFG_EDT, self.cfg_txt_edt.font())

    @flow
    def on_fnt_box_chg(self, font: QFont):
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
    def on_btn_clk_tab(self):
        xp('tab', '', 'cfg', self.cfg_txt_edt.font(), **_ly)
        self.base.cs_gui.cons_tbl_wid.setFont(self.cfg_txt_edt.font())
        self.base.co_gui.co_tbl_wid.setFont(self.cfg_txt_edt.font())
        self.base.hv_gui.hv_tbl_wid.setFont(self.cfg_txt_edt.font())
        self.base.xy_gui.xy_tbl_wid.setFont(self.cfg_txt_edt.font())
        self.base.rd_gui.rad_tbl_wid.setFont(self.cfg_txt_edt.font())
        self.cfg_fnts.font_set(CfgFonts.FONT_TABLE, self.cfg_txt_edt.font())

    @flow
    def on_btn_clk_geo(self):
        xp('geo', self.base.geo_txt_edt.font(), 'cfg', self.cfg_txt_edt.font(), **_ly)
        self.base.geo_txt_edt.setFont(self.cfg_txt_edt.font())
        self.cfg_fnts.font_set(CfgFonts.FONT_GEO_EDT, self.base.geo_txt_edt.font())

    @flow
    def on_btn_clk_load(self):
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
    def on_btn_clk_save(self):
        Cfg().save_deep()
