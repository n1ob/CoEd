import functools
import json
import threading
from typing import Dict, List

from PySide2.QtGui import QFont

from logger import flow, sep, _cf, xp

flow_off = False


@flow(off=flow_off)
class _CfgCls:

    names: Dict = dict()

    def __init__(self, cls):
        _CfgCls.names[cls.__name__] = cls


@flow(off=flow_off)
def _singleton(cls):
    """Make a class a Singleton class (only one instance)"""
    @functools.wraps(cls)
    def wrapper_singleton(*args, **kwargs):
        xp(cls.__name__, cls, _cf)
        if not wrapper_singleton.instance:
            wrapper_singleton.instance = cls(*args, **kwargs)
            Cfg.__handlers[cls.__name__] = wrapper_singleton.instance
        return wrapper_singleton.instance
    wrapper_singleton.instance = None
    return wrapper_singleton


@flow(off=flow_off)
@_singleton
@_CfgCls
class CfgFonts:
    @flow(off=flow_off)
    def __init__(self):
        self.__cfg_store: Dict = dict()
        self.FONT_TABLE: str = 'tbl'
        self.FONT_GEO_EDT: str = 'geo'
        self.names: List[str] = [self.FONT_TABLE, self.FONT_GEO_EDT]
        self.def_font = QFont('Consolas', 9)

    @flow(off=flow_off)
    def serialize(self, func):
        func('fonts', self.__cfg_store)

    @flow(off=flow_off)
    def deserialize(self, func):
        self.__cfg_store = func('fonts')

    @flow(off=flow_off)
    def set(self, key: str, fon: QFont):
        if key in self.names:
            self.__cfg_store[key] = {'name': fon.family(), 'size': fon.pointSize()}
        else:
            raise ValueError

    @flow(off=flow_off)
    def get(self, key: str) -> QFont:
        if key in self.__cfg_store:
            fo: dict = self.__cfg_store[key]   # = {'name': font.family(), 'size': font.pointSize()}
            return QFont(fo['name'], fo['size'])
        else:
            return CfgFonts.def_font


@flow(off=flow_off)
class Cfg:
    @flow(off=flow_off)
    class CfgJson:
        @flow(off=flow_off)
        def __init__(self):
            self.__store: Dict = dict()
            self.load()

        @flow(off=flow_off)
        def load(self):
            try:
                with open('../../AppData/Roaming/JetBrains/PyCharmCE2021.2/scratches/coed_config.json', 'r') as file:
                    self.__store = json.load(file)
            except FileNotFoundError as err:
                xp(err, _cf)

        @flow(off=flow_off)
        def dump(self):
            with open('../../AppData/Roaming/JetBrains/PyCharmCE2021.2/scratches/coed_config.json', 'w') as file:
                json.dump(self.__store, file)

        @flow(off=flow_off)
        def add(self, key: str, val: object):
            self.__store[key] = val

        @flow(off=flow_off)
        def get(self, key: str) -> object:
            if key in self.__store.keys():
                return self.__store[key]
            return None

        @flow(off=flow_off)
        def clear(self):
            self.__store = dict()

    __class_insts: Dict = dict()
    __handlers: Dict = dict()
    __single_instance = None
    __lock = threading.Lock()

    @flow(off=flow_off)
    def __init__(self):
        self.my_json = Cfg.CfgJson()
        for j, k in _CfgCls.names.items():
            Cfg.__class_insts[j] = k()
            xp(_CfgCls.names, _cf)
        self.load()

    @flow(off=flow_off)
    def __new__(cls, *args, **kwargs):
        if not cls.__single_instance:
            with cls.__lock:
                cls.__single_instance = super().__new__(cls)
        return cls.__single_instance

    @flow(off=flow_off)
    def exit(self):
        self.save()
        self.my_json.dump()

    @flow(off=flow_off)
    def load(self):
        for name in Cfg.__handlers.keys():
            Cfg.__handlers[name].deserialize(self.my_json.get)

    @flow(off=flow_off)
    def save(self):
        for name in Cfg.__handlers:
            Cfg.__handlers[name].serialize(self.my_json.add)

    @flow(off=flow_off)
    def get_inst(self):
        return Cfg.__class_insts


cfg: Cfg = Cfg()


if __name__ == '__main__':

    font = QFont('Blubber', 19)
    sep()
    ff = None
    for key in _CfgCls.names.keys():
        fo = _CfgCls.names[key]
        xp(key, fo, _cf)
        ff = fo()
    sep()
    xp(ff, _cf)
    sep()
    ins = cfg.get_inst()
    for x, y in ins.items():
        xp(x, y, _cf)


    # fo.set(fo.FONT_TABLE, font)
    # fo.set(fo.FONT_GEO_EDT, fo.def_font)
    # cfg.save()
    # cfg.exit()
    # cfg.load()
    # print(fo.get(fo.FONT_TABLE))

    # s = json.dumps(fonts, indent=2, separators=(", ", ": "))
    # print(s)
    # s = json.dumps(fonts, indent=2, separators=(",", ":"))
    # print(s)




