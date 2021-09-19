from PySide2.QtWidgets import QBoxLayout, QWidget, QPlainTextEdit, QPushButton, QVBoxLayout, QHBoxLayout

import co_gui
import co_impl
from co_logger import flow
from co_style import XMLHighlighter

_QL = QBoxLayout


class GeoGui:

    def __init__(self, base):
        self.base: co_gui.CoEdGui = base
        self.impl: co_impl.CoEd = self.base.base

        self.tab_geo = QWidget(None)
        self.geo_txt_edt = QPlainTextEdit()
        self.geo_btn_geo = QPushButton('geo')
        self.geo_btn_ext = QPushButton('ext')
        self.tab_geo.setLayout(self.geo_lay_get())

    @flow
    def geo_lay_get(self) -> QBoxLayout:
        self.geo_txt_edt.setFont(self.base.geo_edt_font)
        self.geo_txt_edt.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.geo_txt_edt.highlighter = XMLHighlighter(self.geo_txt_edt.document())
        self.geo_txt_edt.setPlainText(self.impl.geo_xml_get())
        self.geo_btn_geo.clicked.connect(self.on_geo_btn_clk_geo)
        self.geo_btn_ext.clicked.connect(self.on_geo_btn_clk_ext)
        lis = [QVBoxLayout(),
               self.geo_txt_edt,
               [QHBoxLayout(), _QL.addStretch, self.geo_btn_geo, (_QL.addSpacing, 20), self.geo_btn_ext]]
        return self.base.lay_get(lis)

    @flow
    def on_geo_btn_clk_geo(self):
        self.geo_txt_edt.setPlainText(self.impl.geo_xml_get())

    @flow
    def on_geo_btn_clk_ext(self):
        self.impl.analyse_sketch()
        self.geo_txt_edt.setPlainText(self.impl.sketch_info_xml_get())
