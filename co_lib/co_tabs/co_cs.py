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
import pathlib
from typing import List, Dict, Union

import FreeCAD as App
import Sketcher
from PySide2.QtCore import Signal, QObject, Slot

from .. import co_impl
from ..co_base.co_cmn import pt_typ_str, ConType, ObjType
from ..co_base.co_config import CfgBase
from ..co_base.co_flag import Cs, Dirty
from ..co_base.co_logger import xp, _cs, flow, _ev, xps
from ..co_base.co_observer import observer_block, observer_event_provider_get


class Constraint:

    def __init__(self, cs_idx: int, type_id: str, **kwargs):
        self.cs_idx: int = cs_idx
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
        self.ico_no = ''
        self.ico_alt_no = ''
        self.name = ''
        self.exp = ''

    def __str__(self):
        return self.fmt.format(self.first, pt_typ_str[self.first_pos],  # (0),(1)
                               self.second, pt_typ_str[self.second_pos],  # (2),(3)
                               self.third, pt_typ_str[self.third_pos],  # (4),(5)
                               self.value, self.cs_idx)  # (6),(7)

    def __repr__(self):
        return self.fmt.format(self.first, self.first_pos,  # (0),(1)
                               self.second, self.second_pos,  # (2),(3)
                               self.third, self.third_pos,  # (4),(5)
                               self.value, self.cs_idx)  # (6),(7)


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

    ico = {
        'Block': 'co_lib/Icon/Constraint_Block.svg',
        'Icon2': 'co_lib/Icon/Constraint_Concentric.svg',
        'Diameter': 'co_lib/Icon/Constraint_Diameter.svg',
        'Diameter_Driven': 'co_lib/Icon/Constraint_Diameter_Driven.svg',
        'Icon5': 'co_lib/Icon/Constraint_Ellipse_Axis_Angle.svg',
        'Icon6': 'co_lib/Icon/Constraint_Ellipse_Major_Radius.svg',
        'Icon7': 'co_lib/Icon/Constraint_Ellipse_Minor_Radius.svg',
        'Icon8': 'co_lib/Icon/Constraint_Ellipse_Radii.svg',
        'EqualLength': 'co_lib/Icon/Constraint_EqualLength.svg',
        'Icon10': 'co_lib/Icon/Constraint_ExternalAngle.svg',
        'Horizontal': 'co_lib/Icon/Constraint_Horizontal.svg',
        'HorizontalDistance': 'co_lib/Icon/Constraint_HorizontalDistance.svg',
        'HorizontalDistance_Driven': 'co_lib/Icon/Constraint_HorizontalDistance_Driven.svg',
        'InternalAlignment': 'co_lib/Icon/Constraint_InternalAlignment.svg',
        'Icon15': 'co_lib/Icon/Constraint_InternalAlignment_Ellipse_Focus1.svg',
        'Icon16': 'co_lib/Icon/Constraint_InternalAlignment_Ellipse_Focus2.svg',
        'Icon17': 'co_lib/Icon/Constraint_InternalAlignment_Ellipse_MajorAxis.svg',
        'Icon18': 'co_lib/Icon/Constraint_InternalAlignment_Ellipse_MinorAxis.svg',
        'InternalAngle': 'co_lib/Icon/Constraint_InternalAngle.svg',
        'InternalAngle_Driven': 'co_lib/Icon/Constraint_InternalAngle_Driven.svg',
        'Length': 'co_lib/Icon/Constraint_Length.svg',
        'Length_Driven': 'co_lib/Icon/Constraint_Length_Driven.svg',
        'Icon23': 'co_lib/Icon/Constraint_Lock.svg',
        'Icon24': 'co_lib/Icon/Constraint_Lock_Driven.svg',
        'Parallel': 'co_lib/Icon/Constraint_Parallel.svg',
        'Perpendicular': 'co_lib/Icon/Constraint_Perpendicular.svg',
        'Icon27': 'co_lib/Icon/Constraint_PointOnEnd.svg',
        'Icon28': 'co_lib/Icon/Constraint_PointOnMidPoint.svg',
        'PointOnObject': 'co_lib/Icon/Constraint_PointOnObject.svg',
        'PointOnPoint': 'co_lib/Icon/Constraint_PointOnPoint.svg',
        'Icon31': 'co_lib/Icon/Constraint_PointOnStart.svg',
        'Icon32': 'co_lib/Icon/Constraint_PointToObject.svg',
        'Icon33': 'co_lib/Icon/Constraint_Radiam.svg',
        'Icon34': 'co_lib/Icon/Constraint_Radiam_Driven.svg',
        'Radius': 'co_lib/Icon/Constraint_Radius.svg',
        'Radius_Driven': 'co_lib/Icon/Constraint_Radius_Driven.svg',
        'SnellsLaw': 'co_lib/Icon/Constraint_SnellsLaw.svg',
        'SnellsLaw_Driven': 'co_lib/Icon/Constraint_SnellsLaw_Driven.svg',
        'Symmetric': 'co_lib/Icon/Constraint_Symmetric.svg',
        'Tangent': 'co_lib/Icon/Constraint_Tangent.svg',
        'Icon41': 'co_lib/Icon/Constraint_TangentToEnd.svg',
        'Icon42': 'co_lib/Icon/Constraint_TangentToStart.svg',
        'Vertical': 'co_lib/Icon/Constraint_Vertical.svg',
        'VerticalDistance': 'co_lib/Icon/Constraint_VerticalDistance.svg',
        'VerticalDistance_Driven': 'co_lib/Icon/Constraint_VerticalDistance_Driven.svg',
        'Icon46': 'co_lib/Icon/Sketcher_Crosshair.svg',
        'Icon47': 'co_lib/Icon/Sketcher_ToggleActiveConstraint.svg',
        'Icon48': 'co_lib/Icon/Sketcher_ToggleConstraint.svg',
        'Icon49': 'co_lib/Icon/Sketcher_Toggle_Constraint_Driven.svg',
        'Icon50': 'co_lib/Icon/Sketcher_Toggle_Constraint_Driving.svg',
    }

    @flow
    def constraints_update(self):
        self.__constraints.clear()
        # noinspection PyUnresolvedReferences
        co_list: List[Sketcher.Constraint] = self.sketch.Constraints
        # [('Constraints[6]', '2 * 4'), ('.Constraints.test', '2 * 4.5')]
        # >> > txt = "h3110 23 cat 444.4 rabbit 11 2 dog"
        # >> > [int(s) for s in txt.split() if s.isdigit()]
        # [23, 11, 2]
        exp_list = self.sketch.ExpressionEngine
        d_exp: Dict[Union[str, int], str] = dict()
        for idx_, exp in exp_list:
            idx: str
            exp: str
            if idx_.startswith('Constraints['):
                i = int(''.join(filter(str.isdigit, idx_)))
                d_exp[i] = exp
            else:
                i = idx_.rfind('.')
                s = idx_[i + 1:]
                d_exp[s] = exp

        xp('App.ActiveDocument.ActiveObject', id(App.ActiveDocument.ActiveObject), 'self.sketch',  id(self.sketch), **_cs)
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
                con.ico_no = str(pathlib.Path(CfgBase.BASE_DIR, self.ico['PointOnPoint']))

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
                no = 'Vertical' if ct == ConType.VERTICAL else 'Horizontal'
                con.ico_no = str(pathlib.Path(CfgBase.BASE_DIR, self.ico[no]))

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
                no = 'Parallel' if ct == ConType.PARALLEL else 'EqualLength'
                con.ico_no = str(pathlib.Path(CfgBase.BASE_DIR, self.ico[no]))

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
                no = 'Tangent' if ct == ConType.TANGENT else 'Perpendicular'
                con.ico_no = str(pathlib.Path(CfgBase.BASE_DIR, self.ico[no]))

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
                con.ico_no = str(pathlib.Path(CfgBase.BASE_DIR, self.ico['Length']))
                con.ico_alt_no = str(pathlib.Path(CfgBase.BASE_DIR, self.ico['Length_Driven']))

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
                if ct == ConType.DISTANCEX:
                    con.ico_no = str(pathlib.Path(CfgBase.BASE_DIR, self.ico['HorizontalDistance']))
                    con.ico_alt_no = str(pathlib.Path(CfgBase.BASE_DIR, self.ico['HorizontalDistance_Driven']))
                else:
                    con.ico_no = str(pathlib.Path(CfgBase.BASE_DIR, self.ico['VerticalDistance']))
                    con.ico_alt_no = str(pathlib.Path(CfgBase.BASE_DIR, self.ico['VerticalDistance_Driven']))

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
                con.ico_no = str(pathlib.Path(CfgBase.BASE_DIR, self.ico['InternalAngle']))
                con.ico_alt_no = str(pathlib.Path(CfgBase.BASE_DIR, self.ico['InternalAngle_Driven']))

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
                if ct == ConType.RADIUS or ct == ConType.WEIGHT:
                    con.ico_no = str(pathlib.Path(CfgBase.BASE_DIR, self.ico['Radius']))
                    con.ico_alt_no = str(pathlib.Path(CfgBase.BASE_DIR, self.ico['Radius_Driven']))
                if ct == ConType.DIAMETER:
                    con.ico_no = str(pathlib.Path(CfgBase.BASE_DIR, self.ico['Diameter']))
                    con.ico_alt_no = str(pathlib.Path(CfgBase.BASE_DIR, self.ico['Diameter_Driven']))

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
                con.ico_no = str(pathlib.Path(CfgBase.BASE_DIR, self.ico['PointOnObject']))

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
                con.ico_no = str(pathlib.Path(CfgBase.BASE_DIR, self.ico['Symmetric']))

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
                con.ico_no = str(pathlib.Path(CfgBase.BASE_DIR, self.ico['InternalAlignment']))

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
                con.ico_no = str(pathlib.Path(CfgBase.BASE_DIR, self.ico['SnellsLaw']))
                con.ico_alt_no = str(pathlib.Path(CfgBase.BASE_DIR, self.ico['SnellsLaw_Driven']))

            elif ct == ConType.BLOCK:
                # ConstraintType, GeoIndex
                cs: Cs = Cs.F
                kwargs = self.__get_kwargs(cs, item, "{0}")
                con = Constraint(idx, ct.value, **kwargs)
                con.sub_type = cs
                con.ico_no = str(pathlib.Path(CfgBase.BASE_DIR, self.ico['Block']))
            else:
                continue
            con.driving = item.Driving
            con.active = item.IsActive
            con.virtual = item.InVirtualSpace
            con.name = item.Name
            lo: Union[str, int] = con.name if con.name else con.cs_idx
            if lo in d_exp.keys():
                con.exp = d_exp[lo]
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
