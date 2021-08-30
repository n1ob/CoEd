import json
import threading
from typing import NamedTuple, Dict, Set

from PySide2.QtCore import QByteArray, QDataStream, QIODevice
from PySide2.QtGui import QFont, QColor

from co_logger import xp, xps, flow


class ClsInfo(NamedTuple):
    cls: type
    inst: object


def cfg_decorator(cls):
    xp(cls)
    cls._cfg_class = cls
    return cls


class CfgBase:

    @flow
    def __init__(self, d=None):
        if d is None:
            d = dict()
        self.data: Dict = d
        if CfgBase.__cfg_base is None:
            _inst = Cfg()
            CfgBase.__cfg_base = ClsInfo(cls=Cfg, inst=_inst)

    @property
    def data(self):
        return self.__data

    @data.setter
    def data(self, value):
        xps('data set', self, value)
        self.__data = value

    @staticmethod
    def cfg_keys() -> Set:
        return CfgBase.__cfg_keys

    @flow
    def __new__(cls, *args, **kwargs):
        # ! singleton
        if not cls.__instance:
            with cls.__lock:
                cls.__instance = super().__new__(cls, *args, **kwargs)
                xp('new instance', cls.__instance, 'cfg class', hasattr(cls, '_cfg_class'))
                # ! otf collect cfg classes
                if hasattr(cls, '_cfg_class'):
                    CfgBase.__cfg_names[cls] = cls.__instance
                    CfgBase.__cfg_keys.add(cls.__name__)

                    # ! delegates
                    def cfg_get(self) -> dict:
                        xp('get_del', self, self.__cfg_base)
                        return self.__cfg_base.inst.get(self)
                    cls.load_delegate = cfg_get

                    def cfg_set(self, val):
                        xp('set_del', self, self.__cfg_base, val)
                        self.__cfg_base.inst.set(self, val)
                    cls.save_delegate = cfg_set
        else:
            # ! init once per inst
            def init_pass(self, *dt, **mp):
                pass
            cls.__init__ = init_pass
        return cls.__instance

    __instance: object = None
    __lock = threading.Lock()
    __cfg_names: Dict = dict()
    __cfg_keys: Set = set()
    __cfg_base: ClsInfo = None

    xps(__qualname__)


class PersistJson(CfgBase):

    @flow
    def __init__(self):
        super(PersistJson, self).__init__()
        # self.mock = json.dumps(dict({'SubA': {'A': 'aaa'}}))

    @flow
    def load(self) -> dict:
        # todo load from file, remove dev code
        #  C:\Users\red\PycharmProjects\FreeCad\log.log
        #  C:/Users/red/AppData/Roaming/JetBrains/PyCharmCE2021.2/scratches/
        #  ../../AppData/Roaming/JetBrains/PyCharmCE2021.2/scratches/coed_config.json
        try:
            with open('C:/Users/red/AppData/Roaming/JetBrains/PyCharmCE2021.2/scratches/coed_config.json', 'r') as file:
                return json.load(file)
        except FileNotFoundError as err:
            xp(err)
            return dict()
        # return json.loads(self.mock)

    @flow
    def save(self, val: Dict):
        # todo save to file, remove dev code
        #  C:\Users\red\AppData\Roaming\JetBrains\PyCharmCE2021.2\scratches\coed_config.json
        with open('C:/Users/red/AppData/Roaming/JetBrains/PyCharmCE2021.2/scratches/coed_config.json', 'w') as file:
            json.dump(val, file)
        # self.mock = json.dumps(val)

    xps(__qualname__)


class Cfg(CfgBase):
    @flow
    def __init__(self):
        super(Cfg, self).__init__()
        _inst = PersistJson()
        self.__cfg_persist: ClsInfo = ClsInfo(cls=_inst.__class__, inst=_inst)
        self.load()

    @staticmethod
    def key_str(key):
        if isinstance(key, type):
            return key.__name__
        return key.__class__.__name__

    @flow
    def get(self, key) -> dict:
        _key = self.key_str(key)
        if _key not in self.cfg_keys():
            raise ValueError(_key)

        if _key in self.data.keys():
            return self.data[_key]
        return dict()

    @flow
    def set(self, key, val):
        _key = self.key_str(key)
        if _key not in self.cfg_keys():
            raise ValueError(_key)
        self.data = {**self.data, **{_key: val}}
        # self.data[_key] = val

    @flow
    def load(self):
        self.data = self.__cfg_persist.inst.load()

    @flow
    def save(self):
        self.__cfg_persist.inst.save(self.data)

    @flow
    def save_deep(self):
        for inst in self.__cfg_names.values():
            inst.save()
        self.__cfg_persist.inst.save(self.data)

    xps(__qualname__)


@cfg_decorator
class CfgFonts(CfgBase):
    @flow
    def __init__(self):
        super(CfgFonts, self).__init__()
        self.load()

    @flow
    def get(self, key):
        if key in self.data.keys():
            return self.data[key]
        return None

    @flow
    def set(self, key, val):
        self.data = {**self.data, **{key: val}}
        # self.data[key] = val

    @flow
    def load(self):
        self.data = self.load_delegate()
        for x in self.data.keys():
            xp('dbg font_get', self.font_get(x))

    @flow
    def save(self):
        for x in self.data.keys():
            xp('dbg font_get', self.font_get(x))
        self.save_delegate(self.data)

    @flow
    def font_get(self, key: str) -> QFont:
        if key in CfgFonts.__names:
            dec = self.get(key)
            if dec is None:
                return CfgFonts.__font_def
            enc = dec.encode('UTF-8')
            qb = QByteArray.fromBase64(enc)
            stream = QDataStream(qb, QIODevice.ReadOnly)
            font = QFont()
            stream >> font
            return font
        raise ValueError(key)

    @flow
    def font_get_default(self) -> QFont:
        _font_def = CfgFonts.__font_def
        return _font_def

    @flow
    def font_set(self, key, f: QFont):
        if key in CfgFonts.__names:
            qb = QByteArray()
            out = QDataStream(qb, QIODevice.WriteOnly)
            out << f
            qb64: QByteArray() = qb.toBase64()
            dec = bytes(qb64).decode('UTF-8')
            self.set(key, dec)
        else:
            raise ValueError(key)

    # FONT_TABLE_CONS: str = 'font_tbl_cons'
    # FONT_TABLE_COIN: str = 'font_tbl'
    # FONT_TABLE_HV: str = 'font_tbl'
    # FONT_TABLE_XY: str = 'font_tbl'
    # FONT_TABLE_RAD: str = 'font_tbl'
    FONT_TABLE: str = 'font_tbl'
    FONT_GEO_EDT: str = 'font_geo_edt'
    FONT_CFG_EDT: str = 'font_cfg_edt'
    __names: Set[str] = {FONT_CFG_EDT, FONT_GEO_EDT, FONT_TABLE}

    __font_def = QFont('Consolas', 9)

    xps(__qualname__)


@cfg_decorator
class CfgColors(CfgBase):
    @flow
    def __init__(self):
        super(CfgColors, self).__init__()
        self.load()

    @flow
    def get(self, key):
        if key in self.data.keys():
            return self.data[key]
        return None

    @flow
    def set(self, key, val):
        # * using the prop
        self.data = {**self.data, **{key: val}}
        # self.data[key] = val

    @flow
    def load(self):
        self.data = self.load_delegate()

    @flow
    def save(self):
        self.save_delegate(self.data)

    @flow
    def color_get(self, key) -> QColor:
        if key in CfgColors.__names.keys():
            sc = self.get(key)
            if sc is None:
                sc = CfgColors.__names[key]
            co = QColor()
            co.setNamedColor(sc)
            return co
        raise ValueError(key)
        
    @flow
    def color_set(self, key, co: QColor) -> None:
        if key in CfgColors.__names.keys():
            sc = co.name()
            self.set(key, sc)
        else:
            raise ValueError(key)

    COLOR_XML_ELEM = 'color_xml_elem' 
    COLOR_XML_ATTR = 'color_xml_attr'
    COLOR_XML_VAL = 'color_xml_val'
    COLOR_XML_LN_CMT = 'color_xml_ln_cmt'
    COLOR_XML_TXT = 'color_xml_txt'
    COLOR_XML_KEYWORD = 'color_xml_keyword'

    # material colors
    __material_red = '#b71c1c'  # red
    __material_pink = '#880e4f'  # pink
    __material_purple = '#aa00ff'  # purple
    __material_deep_purple = '#311b92'  # deep purple
    __material_indigo = '#3d5afe'  # indigo
    __material_blue = '#0d47a1'  # blue
    __material_light_blue = '#01579b'  # light blue
    __material_cyan = '#00b8d4'  # cyan
    __material_teal = '#004d40'  # teal
    __material_green = '#1b5e20'  # green
    __material_light_green = '#64dd17'  # light green
    __material_lime = '#827717'  # lime
    __material_yellow = '#f57f17'  # yellow
    __material_amber = '#ff6f00'  # amber
    __material_orange = '#e65100'  # orange
    __material_deep_orange = '#bf360c'  # deep orange

    # defaults
    __co_xml_elem_def = __material_green  # green
    __co_xml_attr_def = __material_indigo  # indigo
    __co_xml_val_def = __material_light_green  # light green
    __co_xml_ln_cmt_def = __material_cyan  # cyan
    __co_xml_txt_def = __material_teal  # teal
    __co_xml_keyword_def = __material_light_blue  # light blue

    __names: Dict[str, str] = {COLOR_XML_ELEM: __co_xml_elem_def, COLOR_XML_ATTR: __co_xml_attr_def, 
                               COLOR_XML_VAL: __co_xml_val_def, COLOR_XML_LN_CMT: __co_xml_ln_cmt_def, 
                               COLOR_XML_TXT: __co_xml_txt_def, COLOR_XML_KEYWORD: __co_xml_keyword_def}

    xps(__qualname__)



xps(__name__)
if __name__ == '__main__':

    xps(__name__)

    font_9 = QFont('Consolas', 9)
    font_10 = QFont('Consolas', 10)

    m = CfgFonts()
    m.font_set(CfgFonts.FONT_CFG_EDT, font_9)
    m.save()
    m.font_set(CfgFonts.FONT_CFG_EDT, font_10)
    n = CfgFonts()
    n.load()
    xp(n.font_get(CfgFonts.FONT_CFG_EDT))

    xps()

    s = '#f57f17'
    c1 = QColor()
    c1.setNamedColor(s)
    xp(c1.name())



    # m = CfgFonts()
    # xp(m.get('A'))
    # m.set('B', 'mdncksd')
    # xp(m.get('B'))
    # xp(m.get('A'))
    # m.save()
    # m.load()
    # xp(m.get('B'))
    # xp(m.get('A'))
    #
    # n = CfgColors()
    # n.set('N', 'nnnnnnnn')
    # n.save()
    # cfg = Cfg()
    # cfg.save()
    # cfg.load()
    # o = CfgFonts()
    # o.load()
    # xp(o.get('A'))
    # xp(m.get('A'))

