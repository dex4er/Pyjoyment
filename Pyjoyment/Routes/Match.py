"""
Pyjoyment.Routes.Match - Find routes
====================================
::

    import Pyjoyment.Controller
    import Pyjoyment.Routes

    from Pyjoyment.Routes.Match import Match

    # Routes
    r = Pyjoyment.Routes.new()
    r.get('/user/:id')
    r.put('/user/:id')

    # Match
    c = Pyjoyment.Controller.new()
    match = Match(root=r)
    match.find(c, method='PUT', path='/user/23')
    print(match.stack[0]['id'])

    # Or import the module, as in Google Python Style Guide

    import Pyjoyment.Controller
    import Pyjoyment.Routes
    import Pyjoyment.Routes.Match

    # Routes
    r = Pyjoyment.Routes.new()
    r.get('/user/:id')
    r.put('/user/:id')

    # Match
    c = Pyjoyment.Controller.new()
    match = Pyjoyment.Routes.Match.new(root=r)
    match.find(c, method='PUT', path='/user/23')
    print(match.stack[0]['id'])

    # Render
    print(match.path_for()['path'])
    print(match.path_for(id=24)['path'])

:mod:`Pyjoyment.Routes.Match` finds routes in :mod:`Pyjoyment.Routes`
structures.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojolicious::Routes::Match
<https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojolicious/Routes/Match.pm>`_ of Mojolicious 9.49.
"""

import Pyjo.Base
import Pyjo.Util
import Pyjoyment.Routes.Route

from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    import Pyjoyment.Controller


_MISSING = object()


class Pyjoyment_Routes_Match(Pyjo.Base.object):
    """
    :mod:`Pyjoyment.Routes.Match` inherits all methods from :mod:`Pyjo.Base`
    and implements the following new ones.
    """

    def __init__(
        self,
        endpoint: Pyjoyment.Routes.Route.object | None = None,
        position: int = 0,
        root: Any = None,
        stack: list[dict[str, Any]] | None = None,
    ) -> None:
        """::

            match = Pyjoyment.Routes.Match.new(root=r)

        Construct a new :mod:`Pyjoyment.Routes.Match` object.
        """
        self.endpoint = endpoint
        """::

            route = match.endpoint
            match.endpoint = Pyjoyment.Routes.Route.new()

        The route endpoint that matched, usually a :mod:`Pyjoyment.Routes.Route`
        object.
        """

        self.position = position
        """::

            position = match.position
            match.position = 2

        Current position on the :attr:`stack`, defaults to ``0``.
        """

        # The root has the attributes of Pyjoyment.Routes, which imports this module
        self.root = root
        """::

            root = match.root
            match.root = Pyjoyment.Routes.new()

        The root of the route structure, usually a :mod:`Pyjoyment.Routes`
        object.
        """

        self.stack: list[dict[str, Any]] = stack if stack is not None else []
        """::

            stack = match.stack
            match.stack = [{'action': 'foo'}, {'action': 'bar'}]

        Captured parameters with nesting history.
        """

        self._captures: dict[str, Any] = {}
        self._conditions: dict[str, Any] | None = None

    def find(self, c: 'Pyjoyment.Controller.object', *, method: str, path: str, websocket: bool = False) -> bool:
        """::

            match.find(Pyjoyment.Controller.new(), method='GET', path='/')

        Match controller and options against :attr:`root` to find an
        appropriate :attr:`endpoint`.
        """
        return self._match(self.root, c, method, path, websocket)

    def path_for(self, *args: Any, **values: Any) -> dict[str, Any]:
        """::

            info = match.path_for()
            info = match.path_for(foo='bar')
            info = match.path_for({'foo': 'bar'})
            info = match.path_for('named')
            info = match.path_for('named', foo='bar')
            info = match.path_for('named', {'foo': 'bar'})

        Render matching route with parameters into path.
        """
        name, values = Pyjo.Util._options(args, values)  # pyright: ignore[reportPrivateUsage]

        # Current route
        current = not name or name == 'current'
        if current:
            if (route := self.endpoint) is None:
                return {}

        # Find endpoint
        elif (route := self.root.lookup(name)) is None:
            return {'path': name}

        # Merge values (clear format)
        captures = self.stack[-1] if self.stack else {}
        merged = {**captures, 'format': None, **values}
        pattern = route.pattern
        constraints = pattern.constraints
        if 'format' not in values and (format := constraints.get('format')) and format is not True:
            value = captures.get('format') if current else None
            merged['format'] = value if value is not None else pattern.defaults.get('format')

        return {'path': route.render(merged), 'websocket': route.has_websocket}

    def _match(
        self,
        r: Pyjoyment.Routes.Route.object,
        c: 'Pyjoyment.Controller.object',
        method: str,
        path: str,
        websocket: bool,
    ) -> bool:
        # Pattern
        partial = r.partial
        detect = (endpoint := r.is_endpoint) and not partial
        if (result := r.pattern.match_partial(path, detect)) is None:
            return False
        found, path = result

        # The captures of this route are set until it returns, as Mojo does with local
        captures = self._captures
        saved = [(key, captures.get(key, _MISSING)) for key in found]
        captures.update(found)
        try:
            # Method
            if (methods := r.methods()) and method not in methods:
                return False

            # Conditions
            if over := r.requires():
                if (conditions := self._conditions) is None:
                    conditions = self._conditions = self.root.conditions
                for name, value in over:
                    if not (condition := conditions.get(name)):
                        return False
                    if not condition(r, c, captures, value):
                        return False

            # WebSocket
            if r.is_websocket and not websocket:
                return False

            # Partial
            empty = not path or path == '/'
            if partial:
                captures['path'] = path
                self.endpoint = r
                empty = True

            # Endpoint (or intermediate destination)
            if (endpoint and empty) or r.inline:
                self.stack.append({**captures})
                if endpoint and empty:
                    if format := captures.get('format'):
                        for frame in self.stack:
                            frame['format'] = format
                    self.endpoint = r
                    return True
                captures.pop('app', None)
                captures.pop('cb', None)

            # Match children
            snapshot = list(self.stack) if r.parent is not None else []
            for child in r.children:
                if self._match(child, c, method, path, websocket):
                    return True
                self.stack = list(snapshot)

            return False

        finally:
            for key, value in saved:
                if value is _MISSING:
                    captures.pop(key, None)
                else:
                    captures[key] = value


new = Pyjoyment_Routes_Match.new
object = Pyjoyment_Routes_Match
Match = Pyjoyment_Routes_Match
