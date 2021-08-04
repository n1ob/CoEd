from enum import Flag, auto

from PySide2.QtCore import QObject, Signal


class Event(QObject):
    # create a new signal on the fly and name it 'speak'
    cons_chg = Signal(str)

# so = Event()
# so.cons_chg.connect(say_some_words)
# so.cons_chg.emit("test")


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

    def clear(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.__class__(self.value & ~other.value)

    def has(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return (self.value & other.value) == other.value

    def toggle(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.__class__(self.value ^ other.value)


class Dirty(FlagOps):

    HV_EDGES = auto()
    XY_EDGES = auto()
    COIN_POINTS = auto()
    CONSTRAINTS = auto()


if __name__ == '__main__':

    f1: Dirty = Dirty.none()
    f1 = f1.set(Dirty.HV_EDGES)
    print(f1)
    print(f1.has(Dirty.HV_EDGES))
    f1 = f1.toggle(Dirty.HV_EDGES)
    print(f1)
    f1 = f1.all()
    print(f1)
    f1 = Dirty.all()
    print(f1)
    f1 = f1.clear(Dirty.CONSTRAINTS)
    print(f1)
    f1 = Dirty.none()
    print(f1)
    print('----------')

    print(Dirty.__members__)

    ff = Dirty.none()
    print(ff)
    # ff |= Dirty.CONSTRAINTS
    # print(ff)
    ff = ~ff
    print(ff)

    print('----------')

    for x in Dirty.__members__.values():
        print(x)
        print(x.__class__)
        print(isinstance(x, Dirty))





