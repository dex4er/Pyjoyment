from Pyjo.Test import *

import contextlib
import io


with subtest('Synopsis'):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        from Pyjo.Base import Base

        from dataclasses import dataclass

        @dataclass
        class Cat(Base):
            name: str = 'Nyan'
            age: int = 4

        mew = Cat(name='Longcat')
        print(mew.age)

        # Or import the module, as in Google Python Style Guide

        import Pyjo.Base

        from dataclasses import dataclass, field

        @dataclass
        class Cat(Pyjo.Base.object):
            name: str = 'Nyan'
            age: int = 4
            weight: int = 4

        @dataclass
        class Tiger(Cat):
            friend: Cat = field(default_factory=Cat)
            stripes: int = 42

        mew = Cat.new(name='Longcat')
        print(mew.age)
        print(mew.set(age=3, weight=5).age)

        rawr = Tiger.new(stripes=38, weight=250)
        print(rawr.tap(lambda rawr: rawr.friend.set(name='Tacgnol')).weight)
    is_ok(output.getvalue(), '4\n4\n3\n250\n', 'output')
    is_ok(rawr.friend.name, 'Tacgnol', 'friend')

with subtest('Description'):

    class Lion(Cat):
        @property
        def pride(self):
            if not hasattr(self, '_pride'):
                self._pride = [Cat.new(), Cat.new()]
            return self._pride

    lion = Lion.new()
    is_ok(len(lion.pride), 2, 'built')
    ok(lion.pride is lion.pride, 'built once')

with subtest('Constructors'):
    import Pyjo.Path

    path = Pyjo.Path.new('/foo/bar')
    is_ok(str(path), '/foo/bar', 'new')

    # Or import the class

    from Pyjo.Path import Path

    path = Path('/foo/bar')
    is_ok(str(path), '/foo/bar', 'constructor')

with subtest('Fluent interfaces'):

    @dataclass
    class Duck(Pyjo.Base.object):
        name: str | None = None

        def quack(self):
            print(f'{self.name}: Quack!')

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        Duck.new().set(name='Donald').quack()
    is_ok(output.getvalue(), 'Donald: Quack!\n', 'output')

with subtest('new'):

    @dataclass
    class SubClass(Pyjo.Base.object):
        name: str | None = None
        other: str | None = None

        def some_method(self, *args):
            self.other = ' '.join(args) or 'called'

    obj = SubClass.new()
    is_ok(obj.name, None, 'no name')
    obj = SubClass.new(name='value')
    is_ok(obj.name, 'value', 'name')
    obj = SubClass.new(**{'name': 'value'})
    is_ok(obj.name, 'value', 'name from a dict')

with subtest('set'):
    obj = obj.set(name='value')
    is_ok(obj.name, 'value', 'name')
    obj = obj.set(name='value', other='value')
    is_ok(obj.other, 'value', 'other')

    # Longer version
    obj.name = 'value'
    is_ok(obj.name, 'value', 'name')

with subtest('tap'):
    obj = obj.tap(lambda obj: obj.set(name='tapped'))
    is_ok(obj.name, 'tapped', 'callback')
    obj = obj.tap('some_method')
    is_ok(obj.other, 'called', 'method')
    args = ('a', 'b')
    obj = obj.tap('some_method', *args)
    is_ok(obj.other, 'a b', 'method with arguments')

    # Longer version
    obj = obj.tap(lambda obj: obj.some_method(*args))
    is_ok(obj.other, 'a b', 'longer version')

    # Inject side effects into a method chain
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        obj.set(foo='A').tap(lambda obj: print(obj.foo)).set(foo='B')
    is_ok(output.getvalue(), 'A\n', 'side effect')
    is_ok(obj.foo, 'B', 'chain continues')

with subtest('tap function'):
    from Pyjo.Base import tap

    tap(obj, lambda obj: obj.set(name='function'))
    is_ok(obj.name, 'function', 'callback')
    tap(obj, 'some_method', *args)
    is_ok(obj.other, 'a b', 'method')

done_testing()
