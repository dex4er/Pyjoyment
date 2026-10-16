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
import Pyjo.Exception
import Pyjo.Loader
import Pyjoyment.Routes.Pattern
import Pyjoyment.Routes.Route

from Pyjo.Util import camelize
from Pyjoyment.Routes.Route import Pyjoyment_Routes_Route

import re

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Self, cast


if TYPE_CHECKING:
    import Pyjoyment
    import Pyjoyment.Controller


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

        self._loaded: dict[str, type] = {}
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

    # Renamed from Mojolicious: continue, which is a keyword of Python
    def proceed(self, c: 'Pyjoyment.Controller.object') -> None:
        """::

            r.proceed(Pyjoyment.Controller.new())

        Continue dispatch chain and emit the hook ``around_action`` of
        :mod:`Pyjoyment` for every action.
        """
        match = c.match
        stack = match.stack
        position = match.position
        if position >= len(stack):
            return _render(c)
        field = stack[position]

        # Merge captures into stash
        stash = c.stash()
        stash.setdefault('mojo.captures', {}).update(field)
        stash.update(field)

        position += 1
        last = position >= len(stack)
        if cb := field.get('cb'):
            proceed = self._callback(c, cb, last)
        else:
            proceed = self._controller(c, field, last)
        match.position = position
        if last or proceed:
            self.proceed(c)

    # The name of Mojolicious, with an underscore as continue is a keyword of Python
    continue_ = proceed

    def dispatch(self, c: 'Pyjoyment.Controller.object') -> bool:
        """::

            boolean = r.dispatch(Pyjoyment.Controller.new())

        Match routes with :meth:`match` and dispatch with :meth:`proceed`.
        """
        self.match(c)
        if not c.match.stack:
            return False
        self.proceed(c)
        return True

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

    def match(self, c: 'Pyjoyment.Controller.object') -> None:
        """::

            r.match(Pyjoyment.Controller.new())

        Match routes with :mod:`Pyjoyment.Routes.Match`.
        """
        # Path (partial path gets priority)
        req = c.req
        path = c.stash().get('path')
        if path is not None:
            if not path.startswith('/'):
                path = f'/{path}'
        else:
            path = req.url.path.to_route()

        # Method (HEAD will be treated as GET)
        method = req.method.upper()
        override = req.url.query.clone().param('_method')
        if override and method == 'POST':
            method = override.upper()
        if method == 'HEAD':
            method = 'GET'

        # Check cache
        tx: Any = c.tx
        ws = 1 if tx.is_websocket else 0
        match = c.match
        match.root = self
        cache = self.cache
        if result := cache.get(f'{method}:{path}:{ws}'):
            match.endpoint, match.stack = result['endpoint'], result['stack']
            return

        # Check routes
        match.find(c, method=method, path=path, websocket=bool(ws))
        if (route := match.endpoint) is None:
            return
        cache.set(f'{method}:{path}:{ws}', {'endpoint': route, 'stack': match.stack})

    def _callback(self, c: 'Pyjoyment.Controller.object', cb: Callable[..., Any], last: bool) -> Any:
        if last:
            c.stash()['mojo.routed'] = True
        c.helpers.log().trace('Routing to a callback')
        return _action(c.app, c, cb, last)

    def _class(self, c: 'Pyjoyment.Controller.object', field: dict[str, Any]) -> Any:
        # Application instance
        if field.get('app') is not None and not isinstance(field['app'], str):
            return field['app']

        # Application class
        classes: list[str] = []
        cls = camelize(field['controller']).replace('::', '.') if field.get('controller') else ''
        if field.get('app'):
            classes.append(field['app'])

        # Specific namespace
        elif (namespace := field.get('namespace')) is not None:
            if not cls:
                raise Pyjo.Exception.new(f'Namespace "{namespace}" requires a controller')
            classes.append(f'{namespace}.{cls}' if namespace else cls)

        # All namespaces
        elif cls:
            classes.extend(f'{namespace}.{cls}' for namespace in self.namespaces)

        # Try to load all classes
        for name in classes:
            # Failed
            if (found := self._load(name)) is None:
                continue
            if not found:
                raise Pyjo.Exception.new(f'Class "{name}" is not a controller')

            # Success
            return cast(type[Any], found).new(app=c.app, match=c.match, stash=c.stash(), tx=c.tx)

        # Nothing found
        if classes:
            raise Pyjo.Exception.new(f'Controller "{classes[-1]}" does not exist')
        return False

    def _controller(self, old: 'Pyjoyment.Controller.object', field: dict[str, Any], last: bool) -> bool:
        import Pyjoyment

        # Load and instantiate controller/application
        new: Any = self._class(old, field)
        if not new:
            return new is not None

        # Application
        controller = cast(type[Any], type(new))
        cls = f'{controller.__module__}.{controller.__qualname__}'
        log = old.helpers.log()
        if isinstance(new, Pyjoyment.object):
            log.trace(f'Routing to application "{cls}"')

            # Try to connect routes
            if (r := getattr(new, 'routes', None)) is not None and r.parent is None:
                r.parent = old.match.endpoint
            new.handler(old)
            old.stash()['mojo.routed'] = True

        # Action
        elif method := field.get('action'):
            log.trace(f'Routing to controller "{cls}" and action "{method}"')

            if callable(sub := getattr(controller, method, None)):
                if last:
                    old.stash()['mojo.routed'] = True
                if _action(old.app, new, sub, last):
                    return True

            else:
                log.trace('Action not found in controller')

        else:
            raise Pyjo.Exception.new(f'Controller "{cls}" requires an action')

        return False

    def _load(self, name: str) -> type | bool | None:
        # Load unless already loaded
        if (loaded := self._loaded.get(name)) is not None:
            return loaded
        if isinstance(e := Pyjo.Loader.load_class(name), Exception):
            raise e
        if (cls := Pyjo.Loader._class(name)) is None:  # pyright: ignore[reportPrivateUsage]
            return None

        # Check base classes
        bases = [Pyjo.Loader._class(base) for base in self.base_classes]  # pyright: ignore[reportPrivateUsage]
        if not any(base is not None and issubclass(cls, base) for base in bases):
            return False
        self._loaded[name] = cls
        return cls


def _action(app: Any, *args: Any) -> Any:
    return app.plugins.emit_chain('around_action', *args)


def _render(c: 'Pyjoyment.Controller.object') -> None:
    stash = c.stash()
    if stash.get('mojo.rendered'):
        return
    if not c.render_maybe() and not stash.get('mojo.routed'):
        raise Pyjo.Exception.new('Route without action and nothing to render')


new = Pyjoyment_Routes.new
object = Pyjoyment_Routes
