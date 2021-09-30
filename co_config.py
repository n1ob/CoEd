import json
import threading
from io import StringIO
from typing import NamedTuple, Dict, Set

from PySide2.QtCore import QByteArray, QDataStream, QIODevice, QObject, Signal
from PySide2.QtGui import QFont, QColor

from co_logger import xp, xps, flow, _cf


class ClsInfo(NamedTuple):
    cls: type
    inst: object


def cfg_decorator(cls):
    xp(cls, **_cf)
    cls._cfg_class = cls
    return cls


class CfgBase(QObject):

    @flow(short=True)
    def __init__(self, d=None):
        super().__init__()
        xp('init CfgBase', self, 'cfg class', hasattr(self, '_cfg_class'), **_cf)
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
        xp('data.setter', self, value, **_cf)
        self.__data = value

    @staticmethod
    def cfg_keys() -> Set:
        return CfgBase.__cfg_keys

    @flow(short=True) # don't touch instance until all init's are finished
    def __new__(cls, *args, **kwargs):
        # ! singleton
        if not cls.__instance:
            with cls.__lock:
                cls.__instance = super().__new__(cls, *args, **kwargs)
                # xp('new instance', cls.__instance, 'cfg class', hasattr(cls, '_cfg_class'), **_cf)
                # ! otf collect cfg classes
                if hasattr(cls, '_cfg_class'):
                    CfgBase.__cfg_names[cls] = cls.__instance
                    CfgBase.__cfg_keys.add(cls.__name__)

                    # ! delegates
                    def cfg_get(self) -> dict:
                        xp('get_del', self, self.__cfg_base, **_cf)
                        return self.__cfg_base.inst.get(self)
                    cls.load_delegate = cfg_get

                    def cfg_set(self, val):
                        xp('set_del', self, self.__cfg_base, val, **_cf)
                        self.__cfg_base.inst.set(self, val)
                    cls.save_delegate = cfg_set
        else:
            # ! init once per inst
            def init_pass(self, *dt, **mp):
                pass
            cls.__init__ = init_pass
            xp('existing instance', cls.__instance, **_cf)
        return cls.__instance

    __instance: object = None
    __lock = threading.Lock()
    __cfg_names: Dict = dict()
    __cfg_keys: Set = set()
    __cfg_base: ClsInfo = None

    xps(__qualname__)


class PersistJson(CfgBase):

    @flow(short=True)
    def __init__(self):
        super(PersistJson, self).__init__()
        xp('init PersistJson', self, **_cf)
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
            xp('fall through:', err, **_cf)
            return dict()
        # return json.loads(self.mock)

    @flow
    def save(self, val: Dict):
        # todo save to file, remove dev code
        #  C:\Users\red\AppData\Roaming\JetBrains\PyCharmCE2021.2\scratches\coed_config.json
        with open('C:/Users/red/AppData/Roaming/JetBrains/PyCharmCE2021.2/scratches/coed_config.json', 'w') as file:
            json.dump(val, file, indent=2)
        # self.mock = json.dumps(val)

    xps(__qualname__)


class Cfg(CfgBase):

    @flow(short=True)
    def __init__(self):
        super(Cfg, self).__init__()
        xp('init Cfg', self, **_cf)
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
class CfgBasics(CfgBase):

    @flow(short=True)
    def __init__(self):
        super(CfgBasics, self).__init__()
        xp('init CfgBasics', self, **_cf)
        self.load()

    @flow
    def get(self, key):
        if key in CfgBasics.__names:
            if key in self.data.keys():
                return self.data[key]
            if key == self.SHOW_ONLY_VALID:
                return self.__SHOW_ONLY_VALID_DEFAULT
            return None
        raise ValueError(key)

    @flow
    def set(self, key, val):
        if key in CfgBasics.__names:
            self.data = {**self.data, **{key: val}}
            # self.data[key] = val
        else:
            raise ValueError(key)

    @flow
    def load(self):
        self.data = self.load_delegate()
        for x in self.data.keys():
            xp('dbg', x, **_cf)

    @flow
    def save(self):
        for x in self.data.keys():
            xp('dbg', x, **_cf)
        self.save_delegate(self.data)

    @flow
    def log_name_get(self) -> str:
        return self.__LOG_NAME_DEFAULT

    LOG_DIR: str = 'log_dir'
    SHOW_ONLY_VALID: str = 'only_valid'
    __names: Set[str] = {LOG_DIR, SHOW_ONLY_VALID}

    __SHOW_ONLY_VALID_DEFAULT = False
    __LOG_NAME_DEFAULT = 'coed.log'


@cfg_decorator
class CfgFonts(CfgBase):

    @flow(short=True)
    def __init__(self):
        super().__init__()
        xp('init CfgFonts', self, **_cf)
        self.load()

    @flow
    def get(self, key):
        if key in CfgFonts.__names:
            if key in self.data.keys():
                return self.data[key]
            return None
        raise ValueError(key)

    @flow
    def set(self, key, val):
        if key in CfgFonts.__names:
            self.data = {**self.data, **{key: val}}
            # self.data[key] = val
        else:
            raise ValueError(key)

    @flow
    def load(self):
        self.data = self.load_delegate()
        for x in self.data.keys():
            xp('dbg font_get', self.font_get(x), **_cf)

    @flow
    def save(self):
        for x in self.data.keys():
            xp('dbg font_get', self.font_get(x), **_cf)
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

    color_changed = Signal(str)

    @flow(short=True)
    def __init__(self):
        super(CfgColors, self).__init__()
        xp('init CfgColors', self, **_cf)
        self.load()

    @flow
    def get(self, key):
        if key in CfgColors.__names.keys():
            if key in self.data.keys():
                return self.data[key]
            return None
        raise ValueError(key)

    @flow
    def set(self, key, val):
        if key in CfgColors.__names.keys():
            # * using the prop
            self.data = {**self.data, **{key: val}}
            self.color_changed.emit(key)
            # self.data[key] = val
        else:
            raise ValueError(key)

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

    __light_green_darker = '#34FEBB'
    __light_blue = '#88B4E7'
    __darker_blue_gray = '#586F89'
    __light_green = '#8CD0D3'
    __very_light_blue = '#D6E9FF'
    __green = '#32AE85'

    # defaults
    __co_xml_elem_def = __very_light_blue  # green
    __co_xml_attr_def = __light_blue  # indigo
    __co_xml_val_def = __green  # light green
    __co_xml_ln_cmt_def = __darker_blue_gray  # cyan
    __co_xml_txt_def = __light_green  # teal
    __co_xml_keyword_def = __light_green_darker  # light blue


    '''
    52/254/187 light green / string
    136/180/231 light blue/ default, attribute
    88/111/137 darker blue gray / comment
    140/208/211 light green / numbers
    214/233/255 very light blue / tag
    50/174/133 green / entity
    '''

    __names: Dict[str, str] = {COLOR_XML_ELEM: __co_xml_elem_def, COLOR_XML_ATTR: __co_xml_attr_def,
                               COLOR_XML_VAL: __co_xml_val_def, COLOR_XML_LN_CMT: __co_xml_ln_cmt_def, 
                               COLOR_XML_TXT: __co_xml_txt_def, COLOR_XML_KEYWORD: __co_xml_keyword_def}

    xps(__qualname__)


xps(__name__)
if __name__ == '__main__':

    m = CfgFonts()
    # xp('xxxx', m.font_get(CfgFonts.FONT_CFG_EDT))



    # xps(__name__)
    # font_9 = QFont('Consolas', 9)
    # font_10 = QFont('Consolas', 10)
    # m = CfgFonts()
    # m.font_set(CfgFonts.FONT_CFG_EDT, font_9)
    # m.save()
    # m.font_set(CfgFonts.FONT_CFG_EDT, font_10)
    # n = CfgFonts()
    # n.load()
    # # xp(n.font_get(CfgFonts.FONT_CFG_EDT))
    # xps()
    # s = '#f57f17'
    # c1 = QColor()
    # c1.setNamedColor(s)
    # # xp(c1.name())
    # c = CfgColors()
    # c.color_set(CfgColors.COLOR_XML_ELEM, c1)
    # c.save()
    #
    # from pathlib import Path
    # s = 'C:/Users/red/AppData/Roaming/JetBrains/PyCharmCE2021.2/scratches/logger.log'
    # p = Path(s)
    # # xp(p)
    # # xp(p.resolve())
    # b = CfgBasics()
    # b.set(CfgBasics.LOG_PATH, str(p))
    # b.save()
    # Cfg().save()


    # m = CfgFonts()
    # # xp(m.get('A'))
    # m.set('B', 'mdncksd')
    # # xp(m.get('B'))
    # # xp(m.get('A'))
    # m.save()
    # m.load()
    # # xp(m.get('B'))
    # # xp(m.get('A'))
    #
    # n = CfgColors()
    # n.set('N', 'nnnnnnnn')
    # n.save()
    # cfg = Cfg()
    # cfg.save()
    # cfg.load()
    # o = CfgFonts()
    # o.load()
    # # xp(o.get('A'))
    # # xp(m.get('A'))

