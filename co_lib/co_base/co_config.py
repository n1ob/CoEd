import json
import os
import threading
from pathlib import Path
from typing import NamedTuple, Dict, Set

from PySide2.QtCore import QByteArray, QDataStream, QIODevice, QObject, Signal
from PySide2.QtGui import QFont, QColor

from .co_logger import xp, xps, flow, _cf


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
        if CfgBase._CFG_BASE is None:
            _inst = Cfg()
            CfgBase._CFG_BASE = ClsInfo(cls=Cfg, inst=_inst)

    @property
    def data(self):
        return self.__data

    @data.setter
    def data(self, value):
        xp('data.setter', self, value, **_cf)
        self.__data = value

    @staticmethod
    def cfg_keys() -> Set:
        return CfgBase._CFG_KEYS

    @flow(short=True)  # don't touch instance until all init's are finished
    def __new__(cls, *args, **kwargs):
        # ! singleton
        if not cls.__INSTANCE:
            with cls.__LOCK:
                cls.__INSTANCE = super().__new__(cls, *args, **kwargs)
                # ! otf collect cfg classes
                if hasattr(cls, '_cfg_class'):
                    CfgBase._CFG_NAMES[cls] = cls.__INSTANCE
                    CfgBase._CFG_KEYS.add(cls.__name__)

                    # ! delegates
                    def cfg_get(self) -> dict:
                        xp('get_del', self, self._CFG_BASE, **_cf)
                        return self._CFG_BASE.inst.get(self)

                    cls.load_delegate = cfg_get

                    def cfg_set(self, val):
                        xp('set_del', self, self._CFG_BASE, val, **_cf)
                        self._CFG_BASE.inst.set(self, val)

                    cls.save_delegate = cfg_set
        else:
            # ! init once per inst
            def init_pass(self, *dt, **mp):
                pass

            cls.__init__ = init_pass
            xp('existing instance', cls.__INSTANCE, **_cf)
        return cls.__INSTANCE

    BASE_DIR = None
    SETTINGS_NAME = 'coed_cfg.json'
    __INSTANCE: object = None
    __LOCK = threading.Lock()
    _CFG_NAMES: Dict = dict()
    _CFG_KEYS: Set = set()
    _CFG_BASE: ClsInfo = None

    xps(__qualname__)


class PersistJson(CfgBase):

    @flow(short=True)
    def __init__(self):
        super(PersistJson, self).__init__()
        xp('init PersistJson', self, **_cf)
        # self.mock = json.dumps(dict({'SubA': {'A': 'aaa'}}))
        if CfgBase.BASE_DIR is None:
            self.path = Path(os.path.dirname(os.path.abspath(__file__)), CfgBasics.SETTINGS_NAME)
        else:
            self.path = Path(CfgBase.BASE_DIR, CfgBasics.SETTINGS_NAME)

    @flow
    def load(self) -> dict:
        try:
            with open(self.path, 'r') as file:
                return json.load(file)
        except FileNotFoundError as err:
            xp('fall through:', err, **_cf)
            return dict()
        # return json.loads(self.mock)

    @flow
    def save(self, val: Dict):
        with open(self.path, 'w') as file:
            json.dump(val, file, indent=2)
        # self.mock = json.dumps(val)

    xps(__qualname__)


class Cfg(CfgBase):

    @staticmethod
    def base_dir_set(dir_: str):
        CfgBase.BASE_DIR = dir_

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
        for inst in CfgBase._CFG_NAMES.values():
            inst.save()
        self.__cfg_persist.inst.save(self.data)

    xps(__qualname__)


@cfg_decorator
class CfgTransient(CfgBase):
    @flow(short=True)
    def __init__(self):
        super(CfgTransient, self).__init__()
        xp('init CfgTransient', self, **_cf)
        self.load()

    @flow
    def get(self, key):
        if key in CfgTransient.__NAMES:
            if key in self.data.keys():
                return self.data[key]
            else:
                return self.default(key)
            # return None
        raise ValueError(key)

    @flow
    def set(self, key, val):
        if key in CfgTransient.__NAMES:
            self.data = {**self.data, **{key: val}}
            self.save()
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
    def default(self, val):
        if val == CfgTransient.CO_TOLERANCE:
            return 0.1
        elif val == CfgTransient.EQ_TOLERANCE:
            return 0.1
        elif val == CfgTransient.HV_TOLERANCE:
            return 0.1
        elif val == CfgTransient.PA_TOLERANCE:
            return 0.1
        elif val == CfgTransient.SHOW_ONLY_VALID:
            return True
        else:
            return None

    CO_TOLERANCE: str = 'co_tolerance'
    EQ_TOLERANCE: str = 'eq_tolerance'
    HV_TOLERANCE: str = 'hv_tolerance'
    PA_TOLERANCE: str = 'pa_tolerance'
    SHOW_ONLY_VALID: str = 'only_valid'
    __NAMES: Set[str] = {CO_TOLERANCE, EQ_TOLERANCE, HV_TOLERANCE, PA_TOLERANCE, SHOW_ONLY_VALID}


@cfg_decorator
class CfgBasics(CfgBase):

    @flow(short=True)
    def __init__(self):
        super(CfgBasics, self).__init__()
        xp('init CfgBasics', self, **_cf)
        self.load()

    @flow
    def get(self, key):
        if key in CfgBasics.__NAMES:
            if key in self.data.keys():
                return self.data[key]
            if key == self.SHOW_ONLY_VALID:
                return CfgBasics.__SHOW_ONLY_VALID_DEFAULT
            return None
        raise ValueError(key)

    @flow
    def set(self, key, val):
        if key in CfgBasics.__NAMES:
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
    def log_path_default_get(self) -> str:
        if Cfg.BASE_DIR is None:
            return CfgBasics.__LOG_NAME_DEFAULT
        else:
            p = Path(CfgBase.BASE_DIR, CfgBasics.__LOG_NAME_DEFAULT)
            return str(p)

    @flow
    def log_name_get(self):
        return CfgBasics.__LOG_NAME_DEFAULT

    LOG_DIR: str = 'log_dir'
    SHOW_ONLY_VALID: str = 'only_valid'
    __NAMES: Set[str] = {LOG_DIR, SHOW_ONLY_VALID}

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
        if key in CfgFonts.__NAMES:
            if key in self.data.keys():
                return self.data[key]
            return None
        raise ValueError(key)

    @flow
    def set(self, key, val):
        if key in CfgFonts.__NAMES:
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
        if key in CfgFonts.__NAMES:
            dec = self.get(key)
            if dec is None:
                return CfgFonts.__FONT_DEF
            enc = dec.encode('UTF-8')
            qb = QByteArray.fromBase64(enc)
            stream = QDataStream(qb, QIODevice.ReadOnly)
            font = QFont()
            stream >> font
            return font
        raise ValueError(key)

    @flow
    def font_get_default(self) -> QFont:
        _font_def = CfgFonts.__FONT_DEF
        return _font_def

    @flow
    def font_set(self, key, f: QFont):
        if key in CfgFonts.__NAMES:
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
    __NAMES: Set[str] = {FONT_CFG_EDT, FONT_GEO_EDT, FONT_TABLE}

    __FONT_DEF = QFont('Consolas', 9)

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
        if key in CfgColors.__NAMES.keys():
            if key in self.data.keys():
                return self.data[key]
            return None
        raise ValueError(key)

    @flow
    def set(self, key, val):
        if key in CfgColors.__NAMES.keys():
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
        if key in CfgColors.__NAMES.keys():
            sc = self.get(key)
            if sc is None:
                sc = CfgColors.__NAMES[key]
            co = QColor()
            co.setNamedColor(sc)
            return co
        raise ValueError(key)

    @flow
    def color_set(self, key, co: QColor) -> None:
        if key in CfgColors.__NAMES.keys():
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
    COLOR_CONSTRUCT = 'color_construct'
    COLOR_EXTERN = 'color_extern'

    # material colors
    __MATERIAL_RED = '#b71c1c'  # red
    __MATERIAL_PINK = '#880e4f'  # pink
    __MATERIAL_PURPLE = '#aa00ff'  # purple
    __MATERIAL_DEEP_PURPLE = '#311b92'  # deep purple
    __MATERIAL_INDIGO = '#3d5afe'  # indigo
    __MATERIAL_BLUE = '#0d47a1'  # blue
    __MATERIAL_LIGHT_BLUE = '#01579b'  # light blue
    __MATERIAL_CYAN = '#00b8d4'  # cyan
    __MATERIAL_TEAL = '#004d40'  # teal
    __MATERIAL_GREEN = '#1b5e20'  # green
    __MATERIAL_LIGHT_GREEN = '#64dd17'  # light green
    __MATERIAL_LIME = '#827717'  # lime
    __MATERIAL_YELLOW = '#f57f17'  # yellow
    __MATERIAL_AMBER = '#ff6f00'  # amber
    __MATERIAL_ORANGE = '#e65100'  # orange
    __MATERIAL_DEEP_ORANGE = '#bf360c'  # deep orange

    __LIGHT_GREEN_DARKER = '#34FEBB'
    __LIGHT_BLUE = '#88B4E7'
    __DARKER_BLUE_GRAY = '#586F89'
    __LIGHT_GREEN = '#8CD0D3'
    __VERY_LIGHT_BLUE = '#D6E9FF'
    __GREEN = '#32AE85'

    __LIGHT_PURPLE = '#959cff'

    # defaults
    __CO_XML_ELEM_DEF = __VERY_LIGHT_BLUE  # green
    __CO_XML_ATTR_DEF = __LIGHT_BLUE  # indigo
    __CO_XML_VAL_DEF = __GREEN  # light green
    __CO_XML_LN_CMT_DEF = __DARKER_BLUE_GRAY  # cyan
    __CO_XML_TXT_DEF = __LIGHT_GREEN  # teal
    __CO_XML_KEYWORD_DEF = __LIGHT_GREEN_DARKER  # light blue
    __CO_CONSTRUCT_DEF = __LIGHT_PURPLE
    __CO_EXTERN_DEF = __LIGHT_GREEN

    '''
    52/254/187 light green / string
    136/180/231 light blue/ default, attribute
    88/111/137 darker blue gray / comment
    140/208/211 light green / numbers
    214/233/255 very light blue / tag
    50/174/133 green / entity
    '''

    __NAMES: Dict[str, str] = {COLOR_XML_ELEM: __CO_XML_ELEM_DEF, COLOR_XML_ATTR: __CO_XML_ATTR_DEF,
                               COLOR_XML_VAL: __CO_XML_VAL_DEF, COLOR_XML_LN_CMT: __CO_XML_LN_CMT_DEF,
                               COLOR_XML_TXT: __CO_XML_TXT_DEF, COLOR_XML_KEYWORD: __CO_XML_KEYWORD_DEF,
                               COLOR_CONSTRUCT: __CO_CONSTRUCT_DEF, COLOR_EXTERN: __CO_EXTERN_DEF}

    xps(__qualname__)


xps(__name__)

if __name__ == '__main__':
    pass
