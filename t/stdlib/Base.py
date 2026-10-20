import Pyjo.Base
import Pyjo.Collection
import Pyjo.Date
import Pyjo.Path
import Pyjo.String.Unicode
import Pyjo.URL

from Pyjo.Collection import Collection
from Pyjo.Date import Date
from Pyjo.File import curfile
from Pyjo.Path import Path
from Pyjo.String.Unicode import Unicode
from Pyjo.Test import *
from Pyjo.URL import URL

import dataclasses
import functools
import importlib
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

with subtest('The class of a module under its name'):
    # A module without the name, which would hide a builtin, the package, a name that the module has, or which is the
    # name of a command, not of a class
    WITHOUT = {'Pyjo.Exception', 'Pyjo.IOLoop.TLS', 'Pyjo.String.Template', 'Pyjo.Test.Pyjo', 'Pyjoyment'}
    root = curfile().dirname().dirname().dirname()
    for file in root.child('Pyjo').list_tree().to_list() + root.child('Pyjoyment').list_tree().to_list():
        if file.basename() == '__main__.py' or not file.to_str().endswith('.py'):
            continue
        if not any(line.startswith('object = ') for line in file.slurp('UTF-8').splitlines()):
            continue
        parts = file.to_rel(root).to_list()
        parts[-1] = parts[-1].removesuffix('.py')
        if parts[-1] == '__init__':
            parts.pop()
        name = '.'.join(parts)
        module = importlib.import_module(name)
        if name in WITHOUT or name.startswith('Pyjoyment.Command.'):
            ok(getattr(module, parts[-1], None) is not module.object, f'{name} without {parts[-1]}')
        else:
            ok(getattr(module, parts[-1], None) is module.object, f'{name}.{parts[-1]}')

with subtest('The constructor and new'):
    is_ok(str(URL('https://example.com/foo')), str(Pyjo.URL.new('https://example.com/foo')), 'URL')
    is_ok(str(Path('/foo%2Fbar%3B/baz.html')), str(Pyjo.Path.new('/foo%2Fbar%3B/baz.html')), 'Path')
    is_ok(Date('Sun, 06 Nov 1994 08:49:37 GMT').epoch, Pyjo.Date.new('Sun, 06 Nov 1994 08:49:37 GMT').epoch, 'Date')
    is_ok(Unicode('foo', 'bar'), Pyjo.String.Unicode.new('foo', 'bar'), 'Unicode joins its parts')

    # Collection keeps the constructor of list, which takes an iterable
    is_deeply_ok(Collection([1, 2, 3]), Pyjo.Collection.new(1, 2, 3), 'Collection')
    is_deeply_ok(Collection(n for n in range(3)), [0, 1, 2], 'Collection of a generator')

done_testing()
