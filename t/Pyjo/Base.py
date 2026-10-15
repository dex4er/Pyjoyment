import Pyjo.Base

from Pyjo.Test import *

import importlib
import os
import re
import sys
import tempfile
import textwrap

from dataclasses import dataclass
from typing import Any


# The modules of t/mojo/lib/Mojo/BaseTest
lib = tempfile.TemporaryDirectory()
os.mkdir(os.path.join(lib.name, 'BaseTest'))
for name, code in {
    '__init__': '',
    'Base1': """
        import Pyjo.Base

        from dataclasses import dataclass
        from typing import Any


        @dataclass
        class Base1(Pyjo.Base.object):
            foo: Any = None
    """,
    'Base2': """
        from BaseTest.Base1 import Base1

        from dataclasses import dataclass


        @dataclass
        class Base2(Base1):
            bar: int = 2
            baz: int = 2
            yada: int = 0
    """,
    'Base3': """
        from BaseTest.Base1 import Base1

        from dataclasses import dataclass
        from typing import Any


        @dataclass
        class Base3(Base1):
            test: Any = None
    """,
}.items():
    with open(os.path.join(lib.name, 'BaseTest', f'{name}.py'), 'w') as f:
        f.write(textwrap.dedent(code))
sys.path.insert(0, lib.name)

Base2 = importlib.import_module('BaseTest.Base2').Base2
Base3 = importlib.import_module('BaseTest.Base3').Base3


@dataclass
class BaseTest(Base2):
    tests: Any = 1
    name: Any = None

    def more_tests(self, count=1):
        self.tests += count
        return self.tests


class BaseTestTest(BaseTest):
    pass


class BaseTestTestTest(BaseTestTest):
    pass


# Left out from Mojolicious: the classes with weak attributes, as weakref.proxy takes the place of weak

with subtest('Basic functionality'):
    object = BaseTest.new().set(foo=23)
    object2 = BaseTestTest.new(foo=24)
    is_ok(object2.foo, 24, 'right attribute value')
    is_ok(object.foo, 23, 'right attribute value')

# Left out from Mojolicious: the subtest "Instance method", as attr is left out

with subtest('Default value defined but false'):
    object = BaseTestTestTest.new()
    ok(object.yada is not None)
    is_ok(object.yada, 0, 'right attribute value')
    is_ok(object.set(yada=5).yada, 5, 'right attribute value')

with subtest('Default value support'):
    object = BaseTest.new()
    isa_ok(object.set(name='foobarbaz'), BaseTest, 'attribute value has right class')
    object2 = BaseTest.new().set(tests=3)
    is_ok(object2.tests, 3, 'right attribute value')
    is_ok(object.tests, 1, 'right attribute default value')

with subtest('Chained attributes and callback default value support'):
    object = BaseTest.new()
    is_ok(object.bar, 2, 'right attribute value')
    is_ok(object.set(bar=6).bar, 6, 'right chained attribute value')
    is_ok(object.baz, 2, 'right attribute value')
    is_ok(object.set(baz=6).baz, 6, 'right chained attribute value')

with subtest('Tap into chain'):
    object = BaseTest.new()
    is_ok(object.tap(lambda o: o.set(name='foo')).name, 'foo', 'right attribute value')
    is_ok(object.tap(lambda o: o.set(name='bar').name).name, 'bar', 'right attribute value')
    is_ok(object.tap('tests').tests, 1, 'right attribute value')
    is_ok(object.more_tests(), 2, 'right attribute value')
    is_ok(object.tap('more_tests').tests, 3, 'right attribute value')
    is_ok(object.tap('more_tests', 3).tests, 6, 'right attribute value')

with subtest('Inherit -base flag'):
    object = Base3.new(test=1)
    is_ok(object.test, 1, 'right attribute value')
    is_ok(object.foo, None, 'no attribute value')
    is_ok(object.set(foo=3).foo, 3, 'right attribute value')

# Left out from Mojolicious: the subtests "Exceptions" and "Weaken", as attr is left out

# Not in Mojolicious: the keyword arguments of the constructor, and a dict of them
with subtest('Constructor'):
    object = BaseTest.new(foo=1, name='test')
    is_ok((object.foo, object.name), (1, 'test'), 'keyword arguments')
    object = BaseTest.new(**{'foo': 2})
    is_ok(object.foo, 2, 'dict of keyword arguments')
    throws_ok(lambda: BaseTest.new(unknown=1), TypeError, re.compile('unknown'))
    is_ok(type(Pyjo.Base.new()), Pyjo.Base.object, 'new of the module')

# Not in Mojolicious: set, the expression form of an assignment
with subtest('Set'):
    object = BaseTest.new()
    ok(object.set(foo=1, name='x') is object, 'same object')
    is_ok((object.foo, object.name), (1, 'x'), 'attributes')
    ok(object.set() is object, 'nothing to set')

# Not in Mojolicious: the errors of tap
with subtest('Tap errors'):
    object = BaseTest.new()
    throws_ok(lambda: object.tap('tests', 1), TypeError, "'tests' of BaseTest is not callable")
    throws_ok(lambda: object.tap('missing'), AttributeError, re.compile('missing'))
    is_ok(object.tap(lambda o, n, m=0: o.more_tests(n + m), 2, m=1).tests, 4, 'arguments of the callback')

# Not in Mojolicious: the tap of the module, for an object that is not Pyjo.Base
with subtest('Tap function'):
    items = [1]
    is_ok(Pyjo.Base.tap(items, 'append', 2), None, 'nothing returned')
    is_ok(items, [1, 2], 'method called')
    Pyjo.Base.tap(items, lambda i: i.append(3))
    is_ok(items, [1, 2, 3], 'callback called')

lib.cleanup()

done_testing()
