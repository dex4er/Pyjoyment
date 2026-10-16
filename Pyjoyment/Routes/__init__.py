"""
Pyjoyment.Routes - Always find your destination with routes
===========================================================
::

    import Pyjoyment.Routes

    # Simple route
    r = Pyjoyment.Routes.new()
    r.any('/').to(controller='blog', action='welcome')

    # More advanced routes
    blog = r.under('/blog')
    blog.get('/list').to('blog#list')
    blog.get('/:id', id=re.compile(r'\\d+')).to('blog#show', id=23)
    blog.patch(lambda c: c.render(text='Go away!', status=405))

:mod:`Pyjoyment.Routes` is the core of the :mod:`Pyjoyment` web framework.

Types
-----

These placeholder types are available by default.

num ::

    r.get('/article/<id:num>')

Placeholder value needs to be a non-fractional number, similar to the regular
expression ``([0-9]+)``.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojolicious::Routes <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojolicious/Routes.pm>`_
of Mojolicious 9.49.
"""

import Pyjo.Cache
import Pyjoyment.Routes.Pattern
import Pyjoyment.Routes.Route

from Pyjoyment.Routes.Route import Pyjoyment_Routes_Route

import re

from collections.abc import Callable
from typing import Any, Self


# A condition gets the route, the controller, the captures and the value that the route requires
type Condition = Callable[[Pyjoyment.Routes.Route.object, Any, dict[str, Any], Any], Any]


# Pyjoyment.Routes is not an attribute of Pyjoyment until this package is loaded
class Pyjoyment_Routes(Pyjoyment_Routes_Route):
    """
    :mod:`Pyjoyment.Routes` inherits all attributes and methods from
    :mod:`Pyjoyment.Routes.Route` and implements the following new ones.
    """

    def __init__(self) -> None:
        """::

            r = Pyjoyment.Routes.new()

        Construct a new :mod:`Pyjoyment.Routes` object.
        """
        super().__init__()

        self.base_classes = ['Pyjoyment.Controller', 'Pyjoyment']
        """::

            classes = r.base_classes
            r.base_classes = ['MyApp.Controller']

        Base classes used to identify controllers, defaults to
        :mod:`Pyjoyment.Controller` and :mod:`Pyjoyment`.
        """

        self.cache: Pyjo.Cache.object[str, Any] = Pyjo.Cache.new()
        """::

            cache = r.cache
            r.cache = Pyjo.Cache.new()

        Routing cache, defaults to a :mod:`Pyjo.Cache` object.
        """

        self.conditions: dict[str, Condition] = {}
        """::

            conditions = r.conditions
            r.conditions = {'foo': lambda route, c, captures, arg: ...}

        Contains all available conditions.
        """

        self.namespaces: list[str] = []
        """::

            namespaces = r.namespaces
            r.namespaces = ['MyApp.Controller', 'MyApp']

        Namespaces to load controllers from. ::

            # Add another namespace to load controllers from
            r.namespaces.append('MyApp.MyController')
        """

        self.shortcuts: dict[str, Callable[..., Any]] = {}
        """::

            shortcuts = r.shortcuts
            r.shortcuts = {'foo': lambda route, *args: ...}

        Contains all available shortcuts.
        """

        self.types: dict[str, Pyjoyment.Routes.Pattern.Constraint] = {'num': re.compile(r'[0-9]+')}
        """::

            types = r.types
            r.types = {'lower': re.compile(r'[a-z]+')}

        Registered placeholder types, by default only ``num`` is already
        defined.
        """

        self._reverse: dict[str, Pyjoyment.Routes.Route.object] | None = None

    def add_condition(self, name: str, cb: Condition) -> Self:
        """::

            r = r.add_condition('foo', lambda route, c, captures, arg: ...)

        Register a condition. ::

            def foo(route, c, captures, arg):
                ...
                return True

            r.add_condition('foo', foo)
        """
        self.conditions[name] = cb
        return self

    def add_shortcut(self, name: str, cb: Callable[..., Any]) -> Self:
        """::

            r = r.add_shortcut('foo', lambda route, *args: ...)

        Register a shortcut. ::

            r.add_shortcut('foo', lambda route, *args: ...)
        """
        self.shortcuts[name] = cb
        return self

    def add_type(self, name: str, type: 'Pyjoyment.Routes.Pattern.Constraint') -> Self:
        """::

            r = r.add_type('foo', re.compile(r'\\w+'))
            r = r.add_type('foo', ['bar', 'baz'])

        Register a placeholder type. ::

            r.add_type('lower', re.compile(r'[a-z]+'))
        """
        self.types[name] = type
        return self

    # TODO: continue, with dispatch.t, when Pyjoyment.Controller and Pyjoyment are ported

    # TODO: dispatch, with dispatch.t, when Pyjoyment.Controller and Pyjoyment are ported

    def lookup(self, name: str) -> 'Pyjoyment.Routes.Route.object | None':
        """::

            route = r.lookup('foo')

        Find route by name with
        :meth:`~Pyjoyment.Routes.Route.Pyjoyment_Routes_Route.find` and cache
        all results for future lookups.
        """
        if self._reverse is None:
            self._reverse = self._index()
        return self._reverse.get(name)

    # TODO: match, with dispatch.t, when Pyjoyment.Controller and Pyjoyment are ported


new = Pyjoyment_Routes.new
object = Pyjoyment_Routes
