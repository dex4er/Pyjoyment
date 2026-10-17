"""
Pyjoyment.Lite - Micro real-time web framework
==============================================
::

    from Pyjoyment.Lite import *

    # Route with placeholder
    @get('/:foo')
    def foo(c):
        foo = c.param('foo')
        c.render(text=f'Hello from {foo}.')

    # Start the Pyjoyment command system
    app.start()

:mod:`Pyjoyment.Lite` is a tiny domain specific language built around
:mod:`Pyjoyment`, made up of only about a dozen Python functions.

The module that imports the functions gets an application of its own, as
``from Pyjoyment.Lite import *`` makes one for it, named after its file, with
its home in the directory of the file and its ``DATA`` templates in its
docstring after a line ``__DATA__``, which is there before ``app.start()``
runs. A route is a decorator of its callback too, which returns the route. ::

    from Pyjoyment.Lite import *

    get('/', {'text': 'Hello World!'})

    @get('/:foo')
    def foo(c):
        c.render(text=f'Hello from {c.param("foo")}.')

    app.start()

Growing
-------

Here we have collected a few snippets that illustrate very well just how
similar :mod:`Pyjoyment.Lite` and :mod:`Pyjoyment` applications are.

Routes
^^^^^^

The functions ``get``, ``post`` and friends all have equivalent methods. ::

    # Pyjoyment.Lite
    @get('/foo')
    def foo(c):
        c.render(text='Hello World!')

    # Pyjoyment
    class MyApp(Pyjoyment.object):
        def startup(self):
            routes = self.routes
            routes.get('/foo', lambda c: c.render(text='Hello World!'))

Application
^^^^^^^^^^^

The application object you can access with the name ``app`` is the object
passed as ``self`` to the ``startup`` method. ::

    # Pyjoyment.Lite
    app.max_request_size = 16777216

    # Pyjoyment
    class MyApp(Pyjoyment.object):
        def startup(self):
            self.max_request_size = 16777216

Plugins
^^^^^^^

Instead of the ``plugin`` function you just use the method
:meth:`Pyjoyment.Pyjoyment_App.plugin`. ::

    # Pyjoyment.Lite
    plugin('Config')

    # Pyjoyment
    class MyApp(Pyjoyment.object):
        def startup(self):
            self.plugin('Config')

Helpers
^^^^^^^

Similar to plugins, instead of the ``helper`` function you just use the
method :meth:`Pyjoyment.Pyjoyment_App.helper`. ::

    # Pyjoyment.Lite
    @helper('two')
    def two(c):
        return 1 + 1

    # Pyjoyment
    class MyApp(Pyjoyment.object):
        def startup(self):
            self.helper('two', lambda c: 1 + 1)

Templates
^^^^^^^^^

Instead of the ``template`` function you just use the method
:meth:`Pyjoyment.Pyjoyment_App.template`. ::

    # Pyjoyment.Lite
    @template('hello.html')
    def hello(c, name):
        return t('<p>Hello {name}!</p>')

    # Pyjoyment
    class MyApp(Pyjoyment.object):
        def startup(self):
            self.template('hello.html', lambda c, name: t('<p>Hello {name}!</p>', name=name))

Under
^^^^^

Instead of sequential function calls, we can use methods to build a tree with
nested routes, that much better illustrates how routes work internally. ::

    # Pyjoyment.Lite
    under('/foo')
    get('/bar', lambda c: ...)

    # Pyjoyment
    class MyApp(Pyjoyment.object):
        def startup(self):
            routes = self.routes
            foo = routes.under('/foo')
            foo.get('/bar', lambda c: ...)

Functions
---------

:mod:`Pyjoyment.Lite` implements the following functions, which are
automatically exported.

any ::

    route = any('/:foo', lambda c: ...)
    route = any('/:foo', lambda c: ..., 'name')
    route = any('/:foo', {'foo': 'bar'}, lambda c: ...)
    route = any('/:foo', lambda c: ..., foo=re.compile(r'\\w+'))
    route = any(['GET', 'POST'], '/:foo', lambda c: ...)
    route = any(['GET', 'POST'], '/:foo', lambda c: ..., foo=re.compile(r'\\w+'))
    route = any(['GET', 'POST'], '/:foo', lambda c: ...).requires(agent=re.compile(r'Firefox'))

Generate route with :meth:`Pyjoyment.Routes.Route.Pyjoyment_Routes_Route.any`,
matching any of the listed HTTP request methods or all.

app ::

    app = app

The :mod:`Pyjoyment.Lite` application object, which is a subclass of
:mod:`Pyjoyment`. ::

    # Use all the available attributes and methods
    app.log.level = 'error'
    app.defaults(foo='bar')

delete ::

    route = delete('/:foo', lambda c: ...)
    route = delete('/:foo', lambda c: ..., 'name')
    route = delete('/:foo', {'foo': 'bar'}, lambda c: ...)
    route = delete('/:foo', lambda c: ..., foo=re.compile(r'\\w+'))
    route = delete('/:foo', lambda c: ...).requires(agent=re.compile(r'Firefox'))

Generate route with
:meth:`Pyjoyment.Routes.Route.Pyjoyment_Routes_Route.delete`, matching only
``DELETE`` requests.

get ::

    route = get('/:foo', lambda c: ...)
    route = get('/:foo', lambda c: ..., 'name')
    route = get('/:foo', {'foo': 'bar'}, lambda c: ...)
    route = get('/:foo', lambda c: ..., foo=re.compile(r'\\w+'))
    route = get('/:foo', lambda c: ...).requires(agent=re.compile(r'Firefox'))

Generate route with :meth:`Pyjoyment.Routes.Route.Pyjoyment_Routes_Route.get`,
matching only ``GET`` requests.

group ::

    with group():
        ...

Start a new route group, which ends with the block. A function can be the
group too: ``group(lambda: ...)``.

helper ::

    helper('foo', lambda c, *args: ...)

Add a new helper with :meth:`Pyjoyment.Pyjoyment_App.helper`.

hook ::

    hook('after_dispatch', lambda c: ...)

Share code with :meth:`Pyjoyment.Pyjoyment_App.hook`.

options ::

    route = options('/:foo', lambda c: ...)
    route = options('/:foo', lambda c: ..., 'name')
    route = options('/:foo', {'foo': 'bar'}, lambda c: ...)
    route = options('/:foo', lambda c: ..., foo=re.compile(r'\\w+'))
    route = options('/:foo', lambda c: ...).requires(agent=re.compile(r'Firefox'))

Generate route with
:meth:`Pyjoyment.Routes.Route.Pyjoyment_Routes_Route.options`, matching only
``OPTIONS`` requests.

patch ::

    route = patch('/:foo', lambda c: ...)
    route = patch('/:foo', lambda c: ..., 'name')
    route = patch('/:foo', {'foo': 'bar'}, lambda c: ...)
    route = patch('/:foo', lambda c: ..., foo=re.compile(r'\\w+'))
    route = patch('/:foo', lambda c: ...).requires(agent=re.compile(r'Firefox'))

Generate route with
:meth:`Pyjoyment.Routes.Route.Pyjoyment_Routes_Route.patch`, matching only
``PATCH`` requests.

plugin ::

    plugin('SomePlugin', foo=23)

Load a plugin with :meth:`Pyjoyment.Pyjoyment_App.plugin`.

post ::

    route = post('/:foo', lambda c: ...)
    route = post('/:foo', lambda c: ..., 'name')
    route = post('/:foo', {'foo': 'bar'}, lambda c: ...)
    route = post('/:foo', lambda c: ..., foo=re.compile(r'\\w+'))
    route = post('/:foo', lambda c: ...).requires(agent=re.compile(r'Firefox'))

Generate route with
:meth:`Pyjoyment.Routes.Route.Pyjoyment_Routes_Route.post`, matching only
``POST`` requests.

put ::

    route = put('/:foo', lambda c: ...)
    route = put('/:foo', lambda c: ..., 'name')
    route = put('/:foo', {'foo': 'bar'}, lambda c: ...)
    route = put('/:foo', lambda c: ..., foo=re.compile(r'\\w+'))
    route = put('/:foo', lambda c: ...).requires(agent=re.compile(r'Firefox'))

Generate route with :meth:`Pyjoyment.Routes.Route.Pyjoyment_Routes_Route.put`,
matching only ``PUT`` requests.

query ::

    route = query('/:foo', lambda c: ...)
    route = query('/:foo', lambda c: ..., 'name')
    route = query('/:foo', {'foo': 'bar'}, lambda c: ...)
    route = query('/:foo', lambda c: ..., foo=re.compile(r'\\w+'))
    route = query('/:foo', lambda c: ...).requires(agent=re.compile(r'Firefox'))

Generate route with
:meth:`Pyjoyment.Routes.Route.Pyjoyment_Routes_Route.query`, matching only
``QUERY`` requests.

template ::

    template('index.html', lambda c: t('<p>Hello!</p>'))

    @template('index.html')
    def index(c): ...

Add a template of a function with :meth:`Pyjoyment.Pyjoyment_App.template`,
the counterpart of a template of the ``DATA`` section for template strings,
see :mod:`Pyjoyment.Plugin.PyRenderer`.

under ::

    route = under(lambda c: ...)
    route = under('/:foo', lambda c: ...)
    route = under('/:foo', {'foo': 'bar'})
    route = under('/:foo', foo=re.compile(r'\\w+'))
    route = under('/:foo').requires(agent=re.compile(r'Firefox'))
    route = under(format=['json', 'yaml'])

Generate nested route with
:meth:`Pyjoyment.Routes.Route.Pyjoyment_Routes_Route.under`, to which all
following routes are automatically appended.

websocket ::

    route = websocket('/:foo', lambda c: ...)
    route = websocket('/:foo', lambda c: ..., 'name')
    route = websocket('/:foo', {'foo': 'bar'}, lambda c: ...)
    route = websocket('/:foo', lambda c: ..., foo=re.compile(r'\\w+'))
    route = websocket('/:foo', lambda c: ...).requires(agent=re.compile(r'Firefox'))

Generate route with
:meth:`Pyjoyment.Routes.Route.Pyjoyment_Routes_Route.websocket`, matching
only WebSocket handshakes.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojolicious::Lite <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojolicious/Lite.pm>`_
of Mojolicious 9.49.

Classes
-------
"""

import Pyjo.File
import Pyjo.UserAgent.Server
import Pyjoyment
import Pyjoyment.Routes.Route

import contextlib
import os
import sys
import types

from collections.abc import Callable, Generator
from typing import TYPE_CHECKING, Any


# Renamed from Mojolicious: del is delete, as del is a keyword of Python, and del_ is its alias
__all__ = [
    'any',
    'app',
    'del_',
    'delete',
    'get',
    'group',
    'helper',
    'hook',
    'options',
    'patch',
    'plugin',
    'post',
    'put',
    'query',
    'template',
    'under',
    'websocket',
]


class Pyjoyment_Lite(Pyjoyment.object):
    """
    :mod:`Pyjoyment.Lite` inherits all attributes and methods from
    :mod:`Pyjoyment`.
    """


# Unlike Mojolicious: Mojo exports the functions into the package that uses it, and Python imports a module once, so
# the functions are attributes of this module that its __getattr__ makes for the module that imports them, which
# gets an application of its own, as a package of Perl does
def __getattr__(name: str) -> Any:
    if name not in __all__:
        raise AttributeError(f'module {__name__!r} has no attribute {name!r}', name=name)
    return _functions(sys._getframe(1))[name]  # pyright: ignore[reportPrivateUsage]


# The functions of the module of a frame, which import them, skipping the frames of the import system; they are kept in
# the module, as Mojo puts them in the package, so that a script that runs again, as load_app runs it, gets an
# application of its own
def _functions(frame: types.FrameType) -> dict[str, Any]:
    while frame.f_back is not None and frame.f_code.co_filename.startswith('<frozen importlib'):
        frame = frame.f_back
    namespace = frame.f_globals
    if (functions := namespace.get('__pyjoyment_lite__')) is None:
        caller: str = namespace.get('__name__', '__main__')
        functions = namespace['__pyjoyment_lite__'] = _import(caller, namespace.get('__file__'))
    return functions


def _import(caller: str, file: str | None) -> dict[str, Any]:
    # Remember executable for later
    if not os.environ.get('PYJO_EXE') and file:
        os.environ['PYJO_EXE'] = file
    exe = os.environ.get('PYJO_EXE') or file or sys.argv[0]

    # Reuse home directory if possible
    home = os.environ.get('PYJO_HOME')
    try:
        if not home and exe:
            os.environ['PYJO_HOME'] = Pyjo.File.path(exe).to_abs().dirname().to_str()

        # Generate moniker based on filename
        moniker = Pyjo.File.path(exe).basename('.py') if exe else 'pyjoyment'
        app = Pyjoyment_Lite.new(moniker=moniker)
    finally:
        if not home:
            os.environ.pop('PYJO_HOME', None)

    # Initialize routes without namespaces
    routes = app.routes
    routes.namespaces = []
    app.static.classes[0] = app.renderer.classes[0] = caller

    # Unlike Mojolicious: Mojo makes the package that uses it a subclass of Mojolicious, with the functions new and app
    # that return the application, and a module is not a class, so the class is kept with the functions of the module,
    # where the routes find it by the name of the module
    cls = type(
        'Pyjoyment_Lite',
        (Pyjoyment_Lite,),
        {'__module__': caller, 'new': classmethod(lambda cls, *args, **kwargs: app)},
    )

    # The Pyjoyment.Lite DSL
    dsl = _DSL(app, routes)
    functions: dict[str, Any] = {
        name: dsl.route(name) for name in ('any', 'get', 'options', 'patch', 'post', 'put', 'query', 'websocket')
    }
    functions['delete'] = functions['del_'] = dsl.route('delete')
    functions.update(app=app, group=dsl.group, helper=app.helper, hook=app.hook, plugin=app.plugin, under=dsl.under)
    functions['class'] = cls

    # Not in Mojolicious: the templates of functions, for the handler "py"
    functions['template'] = app.template

    # Make sure there's a default application for testing
    if Pyjo.UserAgent.Server.app() is None:
        Pyjo.UserAgent.Server.app(app)

    # Left out from Mojolicious: strict mode of Mojo::Base, which Python does not need
    return functions


class _DSL:
    def __init__(self, app: Pyjoyment_Lite, routes: Pyjoyment.Routes.Route.object) -> None:
        self.app = app
        self.routes: Pyjoyment.Routes.Route.object = routes
        self.root: Pyjoyment.Routes.Route.object = routes

    def group(self, cb: Callable[[], Any] | None = None) -> Any:
        if cb is None:
            return self._group()
        with self._group():
            cb()
        return None

    def route(self, name: str) -> Callable[..., Pyjoyment.Routes.Route.object]:
        def route(*args: Any, **constraints: Any) -> Pyjoyment.Routes.Route.object:
            return getattr(self.routes, name)(*args, **constraints)

        return route

    def under(self, *args: Any, **constraints: Any) -> Pyjoyment.Routes.Route.object:
        self.routes = self.root.under(*args, **constraints)
        return self.routes

    @contextlib.contextmanager
    def _group(self) -> Generator[None]:
        old, self.root = self.root, self.routes
        try:
            yield
        finally:
            self.routes, self.root = self.root, old


if TYPE_CHECKING:
    app: Pyjoyment_Lite

    def any(*args: Any, **constraints: Any) -> Pyjoyment.Routes.Route.object: ...
    def del_(*args: Any, **constraints: Any) -> Pyjoyment.Routes.Route.object: ...
    def delete(*args: Any, **constraints: Any) -> Pyjoyment.Routes.Route.object: ...
    def get(*args: Any, **constraints: Any) -> Pyjoyment.Routes.Route.object: ...
    def group(cb: Callable[[], Any] | None = None) -> Any: ...
    def helper(name: str, cb: Callable[..., Any] | None = None) -> Any: ...
    def hook(name: str, cb: Callable[..., Any] | None = None) -> Any: ...
    def options(*args: Any, **constraints: Any) -> Pyjoyment.Routes.Route.object: ...
    def patch(*args: Any, **constraints: Any) -> Pyjoyment.Routes.Route.object: ...
    def plugin(name: str, conf: dict[str, Any] | None = None, /, **values: Any) -> Any: ...
    def post(*args: Any, **constraints: Any) -> Pyjoyment.Routes.Route.object: ...
    def put(*args: Any, **constraints: Any) -> Pyjoyment.Routes.Route.object: ...
    def query(*args: Any, **constraints: Any) -> Pyjoyment.Routes.Route.object: ...
    def template(name: str, cb: Callable[..., Any] | None = None) -> Any: ...
    def under(*args: Any, **constraints: Any) -> Pyjoyment.Routes.Route.object: ...
    def websocket(*args: Any, **constraints: Any) -> Pyjoyment.Routes.Route.object: ...


new = Pyjoyment_Lite.new
object = Pyjoyment_Lite
