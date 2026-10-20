r"""
Pyjo.Base - Minimal base class for Pyjo projects
================================================
::

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

:mod:`Pyjo.Base` is a simple base class for :mod:`Pyjo` projects with fluent
interfaces.

The attributes of an object are the attributes of Python. A dataclass, as
above, or ``__init__`` gives them their default values, and a property builds
a default value the first time it is read, as a callback of ``has`` does in
Mojolicious. ::

    class Lion(Cat):
        @property
        def pride(self):
            if not hasattr(self, '_pride'):
                self._pride = [Cat.new(), Cat.new()]
            return self._pride

Constructors
------------

The constructor of a class and :meth:`~Pyjo_Base.new` make the same object, and
both are correct. :meth:`~Pyjo_Base.new` is the constructor of Mojolicious,
which the documentation uses, after ``import`` of the module. Each module has
its class under the name of the module too, as ``Path`` of :mod:`Pyjo.Path`,
for the constructor of Python, after ``from ... import`` of the class. ::

    import Pyjo.Path

    path = Pyjo.Path.new('/foo/bar')

    # Or import the class

    from Pyjo.Path import Path

    path = Path('/foo/bar')

The synopsis of each module shows its first example in both forms.

Fluent interfaces
-----------------

Fluent interfaces are a way to design object-oriented APIs around method
chaining to create domain-specific languages, with the goal of making the
readability of the source code close to written prose. ::

    @dataclass
    class Duck(Pyjo.Base.object):
        name: str | None = None

        def quack(self):
            print(f'{self.name}: Quack!')

:mod:`Pyjo.Base` will help you with this by having :meth:`~Pyjo_Base.set`
return its invocant (``self``) when it is used to assign new attribute values. ::

    Duck.new().set(name='Donald').quack()

In this case :meth:`~Pyjo_Base.set` is called on the object created by
``Duck.new()``. It assigns a new attribute value and then returns the ``Duck``
object, so the ``quack`` method can be called on it afterwards. These method
chains can continue until one of the methods called does not return the
``Duck`` object.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::Base <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/Base.pm>`_
of Mojolicious 9.49.

Classes
-------
"""

from collections.abc import Callable
from typing import Any, Self


# Left out from Mojolicious: the flags of import, -strict, -base, -role, -signatures and -async_await, as Python has
# them on its own, and has, as the attributes of Python take its place


class Pyjo_Base:
    """
    :mod:`Pyjo.Base` implements the following methods.
    """

    # Not in Mojolicious: no __dict__ of its own, so that a subclass with __slots__ has none either
    __slots__ = ()

    # Left out from Mojolicious: attr, as the attributes of Python, the properties and weakref.proxy take its place

    @classmethod
    def new(cls, *args: Any, **kwargs: Any) -> Self:
        """::

            obj = SubClass.new()
            obj = SubClass.new(name='value')
            obj = SubClass.new(**{'name': 'value'})

        This base class provides a basic constructor, which passes its
        arguments to the constructor of the class: the attribute values are
        keyword arguments.
        """
        return cls(*args, **kwargs)

    # Not in Mojolicious: the expression form of an assignment, as the accessors of Mojo chain when they set a value
    def set(self, **kwargs: Any) -> Self:
        """::

            obj = obj.set(name='value')
            obj = obj.set(name='value', other='value')

        Assign attribute values and return the object, so that a chain of
        method calls can continue. ::

            # Longer version
            obj.name = 'value'
        """
        for k, v in sorted(kwargs.items()):
            setattr(self, k, v)
        return self

    def tap(self, cb: Callable[..., Any] | str, *args: Any, **kwargs: Any) -> Self:
        """::

            obj = obj.tap(lambda obj: ...)
            obj = obj.tap('some_method')
            obj = obj.tap('some_method', *args, **kwargs)

        Tap into a method chain to perform operations on an object within the
        chain (also known as a K combinator or Kestrel). The object will be
        the first argument passed to the callback. The callback's return value
        will be ignored; instead, the object (the callback's first argument)
        will be the return value. In this way, arbitrary code can be used
        within (i.e., spliced or tapped into) a chained set of object method
        calls. A name of an attribute that is not a method is read, which
        builds the default value of a property. ::

            # Longer version
            obj = obj.tap(lambda obj: obj.some_method(*args))

            # Inject side effects into a method chain
            obj.set(foo='A').tap(lambda obj: print(obj.foo)).set(foo='B')
        """
        tap(self, cb, *args, **kwargs)
        return self

    # Left out from Mojolicious: with_roles, as Pyjoyment has no roles


# Not in Mojolicious: a function of its own, for the classes that are not Pyjo.Base, as a list and a string
def tap(obj: Any, cb: Callable[..., Any] | str, *args: Any, **kwargs: Any) -> None:
    """::

        tap(obj, lambda obj: ...)
        tap(obj, 'some_method', *args, **kwargs)

    Call the callback with the object, or its method of the name with the
    arguments, or read its attribute of the name, as :meth:`Pyjo_Base.tap` and
    the ``tap`` of the classes that are not :mod:`Pyjo.Base` do.
    """
    if callable(cb):
        cb(obj, *args, **kwargs)
        return
    value = getattr(obj, cb)
    if callable(value):
        value(*args, **kwargs)
    elif args or kwargs:
        raise TypeError(f'{cb!r} of {type(obj).__name__} is not callable')


new = Pyjo_Base.new
object = Pyjo_Base
Base = Pyjo_Base
