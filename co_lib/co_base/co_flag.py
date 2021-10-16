import functools
from enum import Flag, auto
from typing import NamedTuple

from .co_logger import _fl, xp, xps


def dirty(_func=None, *, flag=None):
    def decorator_dirty(func):
        @functools.wraps(func)
        def wrapper_dirty(*args, **kwargs):
            nam = func.__name__.ljust(8)
            arg = [str(a) for a in args]
            obj = func(*args, **kwargs)
            res = args[0]
            if nam == 'has':
                xp(f"{nam}: {arg} -> [ {obj} ]", **_fl)
            else:
                xp(f"{nam}: {arg} -> [ {res} ]", **_fl)
            return obj
        return wrapper_dirty
    if _func is None:
        return decorator_dirty
    else:
        return decorator_dirty(_func)


class FlagOps(Flag):

    @classmethod
    def all(cls):
        return ~cls(0)

    @classmethod
    def none(cls):
        return cls(0)

    def set(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.__class__(self.value | other.value)

    def reset(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.__class__(self.value & ~other.value)

    def has(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return bool(self.value & other.value) == other.value

    def toggle(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.__class__(self.value ^ other.value)

    def invert(self):
        return self.__class__(~self.value)


class Dirty(Flag):
    NONE = 0
    HV_EDGES = auto()
    PA_EDGES = auto()
    XY_EDGES = auto()
    COIN_POINTS = auto()
    CONSTRAINTS = auto()
    EQ_EDGES = auto()
    RD_CIRCLES = auto()


class Cs(Flag):
    F = auto()
    FP = auto()
    S = auto()
    SP = auto()
    T = auto()
    TP = auto()
    V = auto()


class ConsTrans(NamedTuple):
    co_idx: int
    type_id: str
    sub_type: Cs
    fmt: str


class Flags:

    def __init__(self, cls):
        self.__cls = cls
        self.__flags: cls = cls(0)

    def __str__(self):
        return str(self.__flags)

    @dirty
    def all(self):
        self.__flags = ~self.__cls(0)

    @dirty
    def all_but(self, flag):
        if not isinstance(flag, self.__cls):
            return NotImplemented
        self.__flags = ~self.__cls(flag)

    @dirty
    def none(self):
        self.__flags = self.__cls(0)

    @dirty
    def none_but(self, flag):
        if not isinstance(flag, self.__cls):
            return NotImplemented
        self.__flags = self.__cls(flag)

    @dirty
    def set(self, flag):
        if not isinstance(flag, self.__cls):
            return NotImplemented
        self.__flags |= flag

    @dirty
    def reset(self, flag):
        if not isinstance(flag, self.__cls):
            return NotImplemented
        self.__flags &= ~flag

    @dirty
    def has(self, flag):
        if not isinstance(flag, self.__cls):
            return NotImplemented
        return (self.__flags & flag) == flag

    @dirty
    def toggle(self, flag):
        if not isinstance(flag, self.__cls):
            return NotImplemented
        self.__flags ^= flag

    @dirty
    def invert(self):
        self.__flags = ~self.__flags


xps(__name__)
if __name__ == '__main__':

    for x, y in Cs.__members__.items():
        print(x, y)
    print('-------------------------')
    cs = Flags(Cs)
    cs.set(Cs.F | Cs.S)
    print(cs)
    print('-------------------------')
    c1 = Cs.F | Cs.S
    c2 = Cs.F | Cs.S
    c3 = Cs.F | Cs.FP
    print(c1)
    print(Cs.F in c1)
    print('-------------------------')
    print(c1)
    print(Cs.F in c1)
    print(Cs.FP in c1)
    print(Cs.S in c1)
    print('-------------------------')
    print((Cs.F in c1) & (Cs.S in c1))
    print((Cs.F in c1) | (Cs.S in c1))
    print((Cs.F in c1) & (Cs.FP in c1))
    print((Cs.F in c1) | (Cs.FP in c1))
    print('-------------------------')
    print(c1 in c2)
    print(c1 == c2)
    print(c1 in c3)
    print(c1 == c3)
    print((Cs.F | Cs.S) in c2)
    print((Cs.F | Cs.FP) in c2)

