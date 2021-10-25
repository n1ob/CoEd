# ***************************************************************************
# *   Copyright (c) 2021 n1ob <niob@gmx.com>                                *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# ***************************************************************************
import threading
from contextlib import contextmanager
from enum import Enum
from typing import NamedTuple, List, Iterable, Callable

import FreeCAD as App
from PySide2 import QtCore
from PySide2.QtCore import QObject, Signal, Slot, QThread
from PySide2.QtGui import QCursor, QFont, QBrush
from PySide2.QtWidgets import QApplication, QWidget, QLabel, QHBoxLayout, QTableWidgetItem

from co_lib.co_base.co_config import CfgFonts, CfgColors
from co_lib.co_base.co_logger import xps, _ti

# ! PointPos lets us refer to different aspects of a piece of geometry.  sketcher::none refers
#  * to an edge itself (eg., for a Perpendicular constraint on two lines). sketcher::start and
#  * sketcher::end denote the endpoints of lines or bounded curves.  sketcher::mid denotes
#  * geometries with geometrical centers (eg., circle, ellipse). Bare points use 'start'.  More
#  * complex geometries like parabola focus or b-spline knots use InternalAlignment constraints
#  * in addition to PointPos.
#
# enum PointPos { none    = 0,
#                 start   = 1,
#                 end     = 2,
#                 mid     = 3 };


pt_typ_str = {0: 'n', 1: 's', 2: 'e', 3: 'm'}
pt_typ_int = {y: x for x, y in pt_typ_str.items()}


def fmt_vec(vec: App.Vector) -> str:
    return f'({vec.x:.1f}, {vec.y:.1f}, {vec.z:.1f})'


# noinspection SpellCheckingInspection,PyPep8
class ConType(Enum):
    NONE: str              = "None"
    COINCIDENT: str        = "Coincident"
    HORIZONTAL: str        = "Horizontal"
    VERTICAL: str          = "Vertical"
    PARALLEL: str          = "Parallel"
    TANGENT: str           = "Tangent"
    DISTANCE: str          = "Distance"
    DISTANCEX: str         = "DistanceX"
    DISTANCEY: str         = "DistanceY"
    ANGLE: str             = "Angle"
    PERPENDICULAR: str     = "Perpendicular"
    RADIUS: str            = "Radius"
    EQUAL: str             = "Equal"
    POINTONOBJECT: str     = "PointOnObject"
    SYMMETRIC: str         = "Symmetric"
    INTERNALALIGNMENT: str = "InternalAlignment"
    SNELLSLAW: str         = "SnellsLaw"
    BLOCK: str             = "Block"
    DIAMETER: str          = "Diameter"
    WEIGHT: str            = "Weight"
    ALL: str               = "All"


class GeoType:
    LINE_SEGMENT: str = 'Part::GeomLineSegment'
    CIRCLE: str = 'Part::GeomCircle'
    ARC_OF_CIRCLE: str = 'Part::GeomArcOfCircle'
    POINT: str = 'Part::GeomPoint'


class GeoTypeUi:
    VERTEX: str = 'Vertex'
    EDGE: str = 'Edge'
    EXTERNAL_EDGE: str = 'ExternalEdge'
    EXTERNAL_EDGE_ABR: str = 'ExEdge'
    CONSTRAINT: str = 'Constraint'
    H_AXIS: str = 'H_Axis'
    V_AXIS: str = 'V_Axis'
    ROOT_POINT: str = 'RootPoint'
    UNKNOWN: str = 'Unknown'


class ObjType:
    SKETCH_OBJECT: str = 'Sketcher::SketchObject'
    VIEW_PROVIDER_SKETCH: str = 'SketcherGui::ViewProviderSketch'


class GeoId(NamedTuple):
    idx: int
    typ: int

    def __str__(self) -> str:
        return f'({self.idx}.{pt_typ_str[self.typ]})'

    def __repr__(self) -> str:
        return f'({self.idx}.{self.typ})'


class GeoPt(NamedTuple):
    idx: int
    typ: int

    def __str__(self) -> str:
        return f'({self.idx}.{self.typ})'

    def __repr__(self) -> str:
        return self.__str__()


class ConsCoin(NamedTuple):
    first: GeoPt
    second: GeoPt

    def __str__(self):
        return "GeoIds {}, {}".format(self.first, self.second)


class Singleton:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                # another thread could have created the instance
                # before we acquired the lock. So check that the
                # instance is still nonexistent.
                if not cls._instance:
                    cls._instance = super(Singleton, cls).__new__(cls)
        return cls._instance


def get_class_that_defined_method(method):
    method_name = method.__name__
    if method.__self__:
        classes = [method.__self__.__class__]
    else:
        classes = [method.im_class]
    while classes:
        c = classes.pop()
        if method_name in c.__dict__:
            return c
        else:
            classes = list(c.__bases__) + classes
    return None


@contextmanager
def wait_cursor():
    QApplication.setOverrideCursor(QCursor(QtCore.Qt.WaitCursor))
    try:
        yield
    finally:
        QApplication.restoreOverrideCursor()


def complement_color(rgb: str) -> str:
    s1 = rgb.replace('#', '0x')
    # f'{0xffffff - 0x110011:06x}'
    return f'#{0xffffff - int(s1, 16):06x}'


def split_rgb(color: str) -> (int, int, int):
    strip = color.lstrip('#')
    r = int(strip[:2], 16)
    g = int(strip[2:4], 16)
    b = int(strip[4:6], 16)
    return r, g, b


# https://stackoverflow.com/questions/3942878/how-to-decide-font-color-in-white-or-black-depending-on-background-color
def lumi(rgb: Iterable) -> float:  # iterable contains [r, g, b]
    res: List[float] = list()
    for c in rgb:
        c = c / 255.0
        if c <= 0.03928:
            c = c / 12.92
        else:
            c = ((c+0.055) / 1.055) ** 2.4
        res.append(c)
    lu = 0.2126 * res[0] + 0.7152 * res[1] + 0.0722 * res[2]
    return lu


def contrast_color(lu: float) -> str:
    if lu > 0.179:  # use #000000 else use #ffffff
        return '#000000'
    else:
        return '#ffffff'


# class ReadWriteLock:
#     """ A lock object that allows many simultaneous "read locks", but
#     only one "write lock." without starvation guard """
#
#     def __init__(self):
#         self._read_ready = threading.Condition(threading.Lock())
#         self._readers = 0
#
#     def acquire_read(self):
#         """ Acquire a read lock. Blocks only if a thread has
#         acquired the write lock. """
#         self._read_ready.acquire()
#         try:
#             self._readers += 1
#         finally:
#             self._read_ready.release()
#
#     def release_read(self):
#         """ Release a read lock. """
#         self._read_ready.acquire()
#         try:
#             self._readers -= 1
#             if not self._readers:
#                 self._read_ready.notifyAll()
#         finally:
#             self._read_ready.release()
#
#     def acquire_write(self):
#         """ Acquire a write lock. Blocks until there are no
#         acquired read or write locks. """
#         self._read_ready.acquire()
#         while self._readers > 0:
#             self._read_ready.wait()
#
#     def release_write(self):
#         """ Release a write lock. """
#         self._read_ready.release()


class Worker(QObject):
    result = Signal(object)
    finished = Signal()

    def __init__(self, func: Callable, *args) -> None:
        super().__init__()
        self.func = func
        self.args = args

    @Slot()
    def process(self):
        self.result.emit(self.func(*self.args))
        self.finished.emit()


class Controller(QObject):
    def __init__(self, worker: Worker, func: Callable, name='blubber', *args, **kwargs) -> None:
        super().__init__()
        self.func = func
        self.args = args
        self.thread = QThread()
        self.worker: Worker = worker
        self.worker.moveToThread(self.thread)
        self.worker.result.connect(self.on_result)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.finished.connect(self.thread.quit)
        self.thread.started.connect(self.worker.process)
        self.thread.finished.connect(self.on_thread_finished)
        self.setObjectName(name)
        self.thread.start()
        xps('Thread Controller', self.objectName(), **_ti)

    @Slot(object)
    def on_result(self, o):
        self.func(o, *self.args)

    @Slot()
    def on_worker_finished(self):
        pass

    @Slot()
    def on_thread_finished(self):
        xps('on_thread_finished', self.objectName(), **_ti)


class ColorTableItem(QTableWidgetItem):
    def __init__(self, co, ex, txt):
        super(ColorTableItem, self).__init__()
        cfg_c = CfgColors()
        c1 = cfg_c.color_get(CfgColors.COLOR_CONSTRUCT)
        c2 = cfg_c.color_get(CfgColors.COLOR_EXTERN)
        if ex:
            self.setForeground(QBrush(c2))
        elif co:
            self.setForeground(QBrush(c1))
        self.setText(txt)


class TableLabel(QWidget):
    def __init__(self, normal_txt, construct_txt, extern_txt):
        super(TableLabel, self).__init__()
        cfg_f = CfgFonts()
        f: QFont = cfg_f.font_get(cfg_f.FONT_TABLE)
        cfg_c = CfgColors()
        c1 = cfg_c.color_get(CfgColors.COLOR_CONSTRUCT)
        c2 = cfg_c.color_get(CfgColors.COLOR_EXTERN)
        self.lbl_normal = QLabel(normal_txt)
        self.lbl_normal.setFont(f)
        self.lbl_normal.setMinimumWidth(0)
        self.lbl_normal.setContentsMargins(0, 0, 0, 0)
        if normal_txt == '':
            self.lbl_normal.hide()
        self.lbl_construct = QLabel(construct_txt)
        style = f'color: {c1.name()}'
        # style = f'color: {c_color}; border-width: 0px; border-style: none; min-width: 0px; padding: 0px'
        self.lbl_construct.setStyleSheet(style)
        self.lbl_construct.setFont(f)
        self.lbl_construct.setContentsMargins(0, 0, 0, 0)
        if construct_txt == '':
            self.lbl_construct.hide()
        self.lbl_extern = QLabel(extern_txt)
        style = f'color: {c2.name()}'
        self.lbl_extern.setStyleSheet(style)
        self.lbl_extern.setFont(f)
        self.lbl_extern.setContentsMargins(0, 0, 0, 0)
        if extern_txt == '':
            self.lbl_extern.hide()
        lay = QHBoxLayout(self)
        lay.addWidget(self.lbl_normal)
        lay.addWidget(self.lbl_construct)
        lay.addWidget(self.lbl_extern)
        lay.addStretch()
        lay.setContentsMargins(0, 0, 0, 0)


xps(__name__)

if __name__ == '__main__':
    pass

