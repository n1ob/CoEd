import json
import threading
from typing import Dict, Set

from PySide2.QtCore import QByteArray, QDataStream, QIODevice
from PySide2.QtGui import QFont, QFontDatabase
from PySide2.QtWidgets import QApplication

from logger import flow, xp, xps, xp_eof


def cfg_decorator(cls):
    xp('def decorator')
    cls._cfg_class = cls
    return cls


class CfgBase:

    @flow
    def __init__(self):
        xp('__init__ once', self)
        self.data: Dict = dict()

    @staticmethod
    def cfg_classes():
        return CfgBase.__cfg_classes

    @property
    def data(self):
        return self.__data

    @data.setter
    def data(self, value):
        self.__data = value

    @flow
    def __new__(cls, *args, **kwargs):
        xp('__new__', cls, args)
        # ! singleton
        if not cls.__instance:
            with cls.__lock:
                cls.__instance = super(CfgBase, cls).__new__(cls, *args, **kwargs)
                xp('New instance created', cls.__instance)
        else:
            # ! init once per inst
            def init_pass(self, *dt, **mp):
                pass
            cls.__init__ = init_pass
        # ! otf collect cfg classes
        if hasattr(cls, '_cfg_class'):
            cls.__instance.__cfg_classes.add(cls)
        return cls.__instance

    @flow
    def data_load(self):
        self.data = Cfg.persist_load(self)

    @flow
    def data_save(self):
        Cfg.persist_save(self, self.data)

    xp('class CfgBase body')
    __instance = None
    __lock = threading.Lock()
    __cfg_classes: Set = set()


class Cfg(CfgBase):
    class PersistJson(CfgBase):

        @flow
        def __init__(self):
            xp('__init__ once', self)
            super().__init__()
            self.load()

        # no flow
        def __del__(self):
            pass

        @flow
        def get(self, key):
            xp('get', key)
            if key in self.data.keys():
                return self.data[key]
            return dict()

        @flow
        def set(self, key, val):
            xp('set', key, val)
            self.data[key] = val

        @flow
        def load(self):
            # todo load from file
            #  C:\Users\red\PycharmProjects\FreeCad\log.log
            #  C:\Users\red\AppData\Roaming\JetBrains\PyCharmCE2021.2\scratches\notebook.txt
            try:
                with open('../../AppData/Roaming/JetBrains/PyCharmCE2021.2/scratches/coed_config.json', 'r') as file:
                    self.data = json.load(file)
            except FileNotFoundError as err:
                xp(err)
            xp('load', self.data)

        @flow
        def save(self):
            # todo save to file
            with open('../../AppData/Roaming/JetBrains/PyCharmCE2021.2/scratches/coed_config.json', 'w') as file:
                json.dump(self.data, file)
            xp('save', self.data)

    @staticmethod
    def persist_load(self):
        xp('persist_load', self.__class__.__name__)
        persist = Cfg.PersistJson()
        persist.load()
        # return persist.get(self.__class__.__name__)

    @staticmethod
    def persist_save(self):
        xp('persist_save', self.__class__.__name__)
        persist = Cfg.PersistJson()
        persist.save()
        # persist.set(self.__class__.__name__, val)

    @flow
    def __init__(self):
        xp('__init__ once', self)
        super().__init__()
        # ! inject the funcs directly into cfg classes or use base class funcs
        # for x in _NAMES.values():
        #    x.load = Cfg.persist_load
        #    x.save = Cfg.persist_save
        # ! don't need this for now
        # self.inst = [x() for x in _NAMES.values()]
        # xps(self.inst)
        xp('__init__ done', self)

    xp('class Cfg body')


@cfg_decorator
class CfgColor(CfgBase):

    @flow
    def __init__(self):
        xp('__init__ once', self)
        super().__init__()

    @flow
    def get(self, key):
        xp(self.data)
        if key in self.data.keys():
            return self.data[key]

    @flow
    def set(self, key, val):
        self.data[key] = val

    @flow
    def deserialize(self):
        xp('deserialize:', self)
        self.data_load()

    @flow
    def serialize(self):
        xp('serialize:', self)
        self.data_save()

    xp('class CfgColor body')


@cfg_decorator
class CfgFonts(CfgBase):

    @flow
    def __init__(self):
        xp('__init__ once', self)
        super().__init__()

    @flow
    def get(self, key):
        xp(self.data)
        if key in self.data.keys():
            return self.data[key]
        return None

    @flow
    def set(self, key, val):
        self.data[key] = val

    @flow
    def load(self):
        xp('deserialize:', self)
        self.data_load()

    @flow
    def save(self):
        xp('serialize:', self)
        self.data_save()

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
            raise ValueError

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
        raise ValueError

    @flow
    def font_get_default(self) -> QFont:
        self.font_def = CfgFonts.__font_def
        return self.font_def

    FONT_TABLE_CONS: str = 'font_tbl_cons'
    FONT_TABLE_COIN: str = 'font_tbl'
    FONT_TABLE_HV: str = 'font_tbl'
    FONT_TABLE_XY: str = 'font_tbl'
    FONT_TABLE_RAD: str = 'font_tbl'
    FONT_GEO_EDT: str = 'font_geo_edt'
    __names: Set[str] = [FONT_GEO_EDT, FONT_TABLE_RAD, FONT_TABLE_XY,
                         FONT_TABLE_HV, FONT_TABLE_COIN, FONT_TABLE_CONS]
    __font_def = QFont('Consolas', 9)
    xp('class CfgFonts body')

xps(__name__)
if __name__ == '__main__':

    def xxx():
        xps('xxx')
        xp(hasattr(CfgFonts, '_cfg_class'))
        if hasattr(a1, '_cfg_class'):
            xp(a1._cfg_class)
        xp('cfg_classes', list(CfgBase.cfg_classes()))


    font1 = QFont('Consolas', 9)
    font2 = QFont('Blubber', 19)

    xps('deco end')
    xps('Cfg')
    cfg = Cfg()
    xps('a1')

    a1 = CfgFonts()
    a1.load()
    f = a1.font_get(CfgFonts.FONT_GEO_EDT)
    xp(f)
    a1.font_set(CfgFonts.FONT_GEO_EDT, font2)
    a2 = CfgFonts()
    f2 = a2.font_get(CfgFonts.FONT_GEO_EDT)
    xp(f2)

    xxx()


    # xp(a1.get(CfgFonts.F1))
    # a1.set('font2', {'f2': 'bwcbcbjbj'})
    # a1.serialize()
    # a1.deserialize()
    # xp(a1.get('font2'))

    # xps('a2')
    # a2 = CfgFonts()
    # xp(isinstance(a2, CfgFonts), a2)
    # xp(a2.deserialize())
    # xp('cfg_classes', list(CfgBase.cfg_classes()))
    # xps('b1')
    # b1 = CfgColor()
    # xp(isinstance(b1, CfgColor), b1)
    # xp(b1.deserialize())
    # xp('cfg_classes', list(CfgBase.cfg_classes()))



    xp_eof()
