import Pyjo.Base

from Pyjo.Test import *

import dataclasses
import functools
import operator


@dataclasses.dataclass
class Cat(Pyjo.Base.object):
    name: str = 'Nyan'
    lives: list[int] = dataclasses.field(default_factory=lambda: [9])


with subtest('A dataclass'):
    cat = Cat.new(name='Longcat')
    is_ok(cat, Cat(name='Longcat'), 'equal to the one of the constructor')
    is_deeply_ok(dataclasses.asdict(cat.set(name='Garfield')), {'name': 'Garfield', 'lives': [9]}, 'asdict')
    is_ok(dataclasses.replace(cat, name='Tom').name, 'Tom', 'replace')
    ok(Cat.new().lives is not Cat.new().lives, 'default factory for each object')

with subtest('A frozen dataclass'):

    @dataclasses.dataclass(frozen=True)
    class Frozen(Pyjo.Base.object):
        name: str = 'Nyan'

    throws_ok(lambda: Frozen.new().set(name='x'), dataclasses.FrozenInstanceError, "cannot assign to field 'name'")

with subtest('Slots'):

    class Slotted(Pyjo.Base.object):
        __slots__ = ('name',)

        def __init__(self, name='Nyan'):
            self.name = name

    is_ok(Slotted.new().set(name='x').name, 'x', 'set')
    throws_ok(lambda: Slotted.new().set(other=1), AttributeError, "'Slotted' object has no attribute 'other'")

with subtest('Callables of functools and operator'):
    cat = Cat.new()
    cat.tap(operator.methodcaller('set', name='Tom'))
    is_ok(cat.name, 'Tom', 'methodcaller')
    cat.tap(functools.partial(Cat.set, name='Jerry'))
    is_ok(cat.name, 'Jerry', 'partial')
    is_ok(cat.tap(operator.attrgetter('lives')).name, 'Jerry', 'attrgetter, its result ignored')

done_testing()
