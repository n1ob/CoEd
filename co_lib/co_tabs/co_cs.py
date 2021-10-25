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
from typing import List, Dict

import FreeCAD as App
import Sketcher
from PySide2.QtCore import Signal, QObject, Slot

from .. import co_impl
from ..co_base.co_cmn import pt_typ_str, ConType, ObjType
from ..co_base.co_flag import Cs, Dirty
from ..co_base.co_logger import xp, _cs, flow, _ev, xps
from ..co_base.co_observer import observer_block, observer_event_provider_get


class Constraint:

    def __init__(self, co_idx: int, type_id: str, **kwargs):
        self.co_idx: int = co_idx
        self.type_id: str = type_id
        self.sub_type: Cs = Cs(0)
        self.first: int = kwargs.get('FIRST', -2000)
        tmp = self.first < 0
        self.first_pos: int = kwargs.get('FIRST_POS', 0)
        self.second: int = kwargs.get('SECOND', -2000)
        tmp = tmp if self.second == -2000 else tmp and self.second < 0
        self.second_pos: int = kwargs.get('SECOND_POS', 0)
        self.third: int = kwargs.get('THIRD', -2000)
        tmp = tmp if self.third == -2000 else tmp and self.third < 0
        self.third_pos: int = kwargs.get('THIRD_POS', 0)
        self.value: float = kwargs.get('VALUE', -0)
        self.fmt = kwargs.get('FMT', "{0} : {1} : {2} : {3} : {4} : {5} : {6} : {7}")
        self.driving: bool = True
        self.active: bool = True
        self.virtual: bool = False
        self.pure_extern = tmp

    def __str__(self):
        return self.fmt.format(self.first, pt_typ_str[self.first_pos],  # (0),(1)
                               self.second, pt_typ_str[self.second_pos],  # (2),(3)
                               self.third, pt_typ_str[self.third_pos],  # (4),(5)
                               self.value, self.co_idx)  # (6),(7)

    def __repr__(self):
        return self.fmt.format(self.first, self.first_pos,  # (0),(1)
                               self.second, self.second_pos,  # (2),(3)
                               self.third, self.third_pos,  # (4),(5)
                               self.value, self.co_idx)  # (6),(7)


class Constraints(QObject):
    deleted = Signal(int)
    deletion_done = Signal()
    update_done = Signal()

    def __init__(self, base):
        super(Constraints, self).__init__()
        self.base: co_impl.CoEd = base
        self.sketch: Sketcher.SketchObject = self.base.sketch
        self.evo = observer_event_provider_get()
        self.evo.in_edit.connect(self.on_in_edit)
        self.__constraints: List[Constraint] = list()

    @property
    def constraints(self):
        if self.base.flags.has(Dirty.CONSTRAINTS):
            self.constraints_update()
        return self.__constraints

    @flow
    @Slot(object)
    def on_in_edit(self, obj):
        if obj.TypeId == ObjType.VIEW_PROVIDER_SKETCH:
            ed_info = App.Gui.ActiveDocument.InEditInfo
            if (ed_info is not None) and (ed_info[0].TypeId == ObjType.SKETCH_OBJECT):
                self.sketch = ed_info[0]

    @flow
    def constraints_update(self):
        self.__constraints.clear()
        # noinspection PyUnresolvedReferences
        co_list: List[Sketcher.Constraint] = self.sketch.Constraints
        xp('App.ActiveDocument.ActiveObject', id(App.ActiveDocument.ActiveObject), 'self.sketch',  id(self.sketch))

        xp('co_lst', co_list, **_cs)
        for idx, item in enumerate(co_list):
            ct: ConType = ConType(item.Type)
            xp('ConType', ct.name, ct.value, **_cs)
            if ct == ConType.COINCIDENT:
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2
                if item.Third == -2000:
                    cs: Cs = Cs.F | Cs.FP | Cs.S | Cs.SP
                    kwargs = self.__get_kwargs(cs, item, "{0}.{1} {2}.{3}")
                else:
                    xp('unexpected case:', ct, **_cs)
                    raise ValueError(item)

                con = Constraint(idx, ct.value, **kwargs)
                con.sub_type = cs
                con.driving = item.Driving
                con.active = item.IsActive
                con.virtual = item.InVirtualSpace
                self.__constraints.append(con)

            elif ct == ConType.HORIZONTAL or ct == ConType.VERTICAL:
                # ConstraintType, GeoIndex
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2
                if item.Second == -2000:
                    cs: Cs = Cs.F
                    kwargs = self.__get_kwargs(cs, item, "{0}")
                elif item.Third == -2000:
                    cs: Cs = Cs.F | Cs.FP | Cs.S | Cs.SP
                    kwargs = self.__get_kwargs(cs, item, "{0}.{1} {2}.{3}")
                else:
                    xp('unexpected case:', ct, **_cs)
                    raise ValueError(item)

                con = Constraint(idx, ct.value, **kwargs)
                con.sub_type = cs
                con.driving = item.Driving
                con.active = item.IsActive
                con.virtual = item.InVirtualSpace
                self.__constraints.append(con)

            elif ct == ConType.PARALLEL or ct == ConType.EQUAL:
                # ConstraintType, GeoIndex1, GeoIndex2
                if item.Third == -2000:
                    cs: Cs = Cs.F | Cs.S
                    kwargs = self.__get_kwargs(cs, item, "{0} {2}")
                else:
                    xp('unexpected case:', ct, **_cs)
                    raise ValueError(item)

                con = Constraint(idx, ct.value, **kwargs)
                con.sub_type = cs
                con.driving = item.Driving
                con.active = item.IsActive
                con.virtual = item.InVirtualSpace
                self.__constraints.append(con)

            elif ct == ConType.TANGENT or ct == ConType.PERPENDICULAR:
                # ConstraintType, GeoIndex1, GeoIndex2
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2
                if item.FirstPos == 0:  # e.g. edge on edge
                    cs: Cs = Cs.F | Cs.S
                    kwargs = self.__get_kwargs(cs, item, "{0} {2}")
                elif item.SecondPos == 0:  # e.g. vertex on edge
                    cs: Cs = Cs.F | Cs.FP | Cs.S
                    kwargs = self.__get_kwargs(cs, item, "{0}.{1} {2}")
                elif item.Third == -2000:  # e.g. vertex on vertex
                    cs: Cs = Cs.F | Cs.FP | Cs.S | Cs.SP
                    kwargs = self.__get_kwargs(cs, item, "{0}.{1} {2}.{3}")
                else:
                    xp('unexpected case:', ct, **_cs)
                    raise ValueError(item)

                con = Constraint(idx, ct.value, **kwargs)
                con.sub_type = cs
                con.driving = item.Driving
                con.active = item.IsActive
                con.virtual = item.InVirtualSpace
                self.__constraints.append(con)

            elif ct == ConType.DISTANCE:
                # ConstraintType, GeoIndex, Value
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, Value
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2, Value
                if item.FirstPos == 0:
                    cs: Cs = Cs.F | Cs.V
                    kwargs = self.__get_kwargs(cs, item, "{0} v: {6:.2f}")
                elif item.SecondPos == 0:
                    cs: Cs = Cs.F | Cs.FP | Cs.S | Cs.V
                    kwargs = self.__get_kwargs(cs, item, "{0}.{1} {2} v: {6:.2f}")
                elif item.Third == -2000:
                    cs: Cs = Cs.F | Cs.FP | Cs.S | Cs.SP | Cs.V
                    kwargs = self.__get_kwargs(cs, item, "{0}.{1} {2}.{3} v: {6:.2f}")
                else:
                    xp('unexpected case:', ct, **_cs)
                    raise ValueError(item)

                con = Constraint(idx, ct.value, **kwargs)
                con.sub_type = cs
                con.driving = item.Driving
                con.active = item.IsActive
                con.virtual = item.InVirtualSpace
                self.__constraints.append(con)

            elif ct == ConType.DISTANCEX or ct == ConType.DISTANCEY:
                if item.FirstPos == 0:
                    cs: Cs = Cs.F | Cs.V
                    kwargs = self.__get_kwargs(cs, item, "{0} v: {6:.2f}")
                elif item.Second == -2000:
                    cs: Cs = Cs.F | Cs.FP | Cs.V
                    kwargs = self.__get_kwargs(cs, item, "{0}.{1} v: {6:.2f}")
                elif item.Third == -2000:
                    cs: Cs = Cs.F | Cs.FP | Cs.S | Cs.SP | Cs.V
                    kwargs = self.__get_kwargs(cs, item, "{0}.{1} {2}.{3} v: {6:.2f}")
                else:
                    xp('unexpected case:', ct, **_cs)
                    raise ValueError(item)

                con = Constraint(idx, ct.value, **kwargs)
                con.sub_type = cs
                con.driving = item.Driving
                con.active = item.IsActive
                con.virtual = item.InVirtualSpace
                self.__constraints.append(con)

            elif ct == ConType.ANGLE:
                # ConstraintType, GeoIndex, Value
                # ConstraintType, GeoIndex1, GeoIndex2, Value
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2, Value
                if item.FirstPos == 0:
                    cs: Cs = Cs.F | Cs.V
                    kwargs = self.__get_kwargs(cs, item, "{0} v: {6:.2f}")
                elif item.SecondPos == 0:
                    cs: Cs = Cs.F | Cs.S | Cs.V
                    kwargs = self.__get_kwargs(cs, item, "{0} {2} v: {6:.2f}")
                elif item.Third == -2000:
                    cs: Cs = Cs.F | Cs.FP | Cs.S | Cs.SP | Cs.V
                    kwargs = self.__get_kwargs(cs, item, "{0}.{1} {2}.{3} v: {6:.2f}")
                else:
                    xp('unexpected case:', ct, **_cs)
                    raise ValueError(item)

                con = Constraint(idx, ct.value, **kwargs)
                con.sub_type = cs
                con.driving = item.Driving
                con.active = item.IsActive
                con.virtual = item.InVirtualSpace
                self.__constraints.append(con)

            elif ct == ConType.RADIUS or ct == ConType.DIAMETER or ct == ConType.WEIGHT:
                # ConstraintType, GeoIndex, Value
                if item.FirstPos == 0:
                    cs: Cs = Cs.F | Cs.V
                    kwargs = self.__get_kwargs(cs, item, "{0} v: {6:.2f}")
                else:
                    xp('unexpected case:', ct, **_cs)
                    raise ValueError(item)

                con = Constraint(idx, ct.value, **kwargs)
                con.sub_type = cs
                con.driving = item.Driving
                con.active = item.IsActive
                con.virtual = item.InVirtualSpace
                self.__constraints.append(con)

            elif ct == ConType.POINTONOBJECT:
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2
                if item.SecondPos == 0:
                    cs: Cs = Cs.F | Cs.FP | Cs.S
                    kwargs = self.__get_kwargs(cs, item, "{0}.{1} {2}")
                else:
                    xp('unexpected case:', ct, **_cs)
                    raise ValueError(item)

                con = Constraint(idx, ct.value, **kwargs)
                con.sub_type = cs
                con.driving = item.Driving
                con.active = item.IsActive
                con.virtual = item.InVirtualSpace
                self.__constraints.append(con)

            elif ct == ConType.SYMMETRIC:
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2, GeoIndex3
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2, GeoIndex3, PosIndex3
                if item.ThirdPos == 0:
                    cs: Cs = Cs.F | Cs.FP | Cs.S | Cs.SP | Cs.T
                    kwargs = self.__get_kwargs(cs, item, "{0}.{1} {2}.{3} {4}")
                else:
                    cs: Cs = Cs.F | Cs.FP | Cs.S | Cs.SP | Cs.T | Cs.ST
                    kwargs = self.__get_kwargs(cs, item, "{0}.{1} {2}.{3} {4}.{5}")
                con = Constraint(idx, ct.value, **kwargs)
                con.sub_type = cs
                con.driving = item.Driving
                con.active = item.IsActive
                con.virtual = item.InVirtualSpace
                self.__constraints.append(con)

            elif ct == ConType.INTERNALALIGNMENT:
                # ConstraintType, GeoIndex1, GeoIndex2
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2
                if item.FirstPos == 0:
                    cs: Cs = Cs.F | Cs.S
                    kwargs = self.__get_kwargs(cs, item, "{0}) {2}")
                elif item.SecondPos == 0:
                    cs: Cs = Cs.F | Cs.FP | Cs.S
                    kwargs = self.__get_kwargs(cs, item, "{0}.{1} {2}")
                elif item.Third == -2000:
                    cs: Cs = Cs.F | Cs.FP | Cs.S | Cs.SP
                    kwargs = self.__get_kwargs(cs, item, "{0}.{1} {2}.{3}")
                else:
                    xp('unexpected case:', ct, **_cs)
                    raise ValueError(item)

                con = Constraint(idx, ct.value, **kwargs)
                con.sub_type = cs
                con.driving = item.Driving
                con.active = item.IsActive
                con.virtual = item.InVirtualSpace
                self.__constraints.append(con)

            elif ct == ConType.SNELLSLAW:
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2, GeoIndex3 ????
                # ConstraintType, GeoIndex1, PosIndex1, GeoIndex2, PosIndex2, GeoIndex3, PosIndex3
                if item.ThirdPos == 0:
                    cs: Cs = Cs.F | Cs.FP | Cs.S | Cs.SP | Cs.T
                    kwargs = self.__get_kwargs(cs, item, "{0}.{1} {2}.{3} {4}")
                else:
                    cs: Cs = Cs.F | Cs.FP | Cs.S | Cs.SP | Cs.T | Cs.TP
                    kwargs = self.__get_kwargs(cs, item, "{0}.{1} {2}.{3} {4}.{5}")

                con = Constraint(idx, ct.value, **kwargs)
                con.sub_type = cs
                con.driving = item.Driving
                con.active = item.IsActive
                con.virtual = item.InVirtualSpace
                self.__constraints.append(con)

            elif ct == ConType.BLOCK:
                # ConstraintType, GeoIndex
                cs: Cs = Cs.F
                kwargs = self.__get_kwargs(cs, item, "{0}")
                con = Constraint(idx, ct.value, **kwargs)
                con.sub_type = cs
                con.driving = item.Driving
                con.active = item.IsActive
                con.virtual = item.InVirtualSpace
                self.__constraints.append(con)
        self.base.flags.reset(Dirty.CONSTRAINTS)
        xp('update_done.emit', **_ev)
        self.update_done.emit()

    @staticmethod
    def __get_kwargs(cont: Cs, item: Sketcher.Constraint, fmt: str) -> dict:
        d: Dict = dict()
        if Cs.F in cont:
            d['FIRST'] = item.First
        if Cs.FP in cont:
            d['FIRST_POS'] = item.FirstPos
        if Cs.S in cont:
            d['SECOND'] = item.Second
        if Cs.SP in cont:
            d['SECOND_POS'] = item.SecondPos
        if Cs.T in cont:
            d['THIRD'] = item.Third
        if Cs.TP in cont:
            d['THIRD_POS'] = item.ThirdPos
        if Cs.V in cont:
            d['VALUE'] = item.Value
        d['FMT'] = fmt
        return d

    @flow
    def constraints_delete(self, idx_list: List[int]):
        doc: App.Document = App.ActiveDocument
        if len(idx_list):
            del_list: [int] = idx_list
            del_list.sort(reverse=True)
            doc.openTransaction('coed: delete constraint')
            # todo block signal reminder
            with observer_block():
                for i in del_list:
                    xp('del: ' + str(i), **_cs)
                    self.sketch.delConstraint(i)
                    self.sketch.solve()
                    xp('deleted.emit', i, **_ev)
                    self.deleted.emit(i)
            doc.commitTransaction()
            self.base.flags.set(Dirty.CONSTRAINTS)
            doc.openTransaction('coed: obj recompute')
            sk: Sketcher.SketchObject = self.sketch
            sk.addProperty('App::PropertyString', 'coed')
            sk.coed = 'cons_recompute'
            sk.recompute()
            doc.commitTransaction()
            xp('deletion_done.emit', **_ev)
            self.base.flags.all()
            self.deletion_done.emit()


xps(__name__)
