"""
Pyjo.App - Duct tape for the HTML5 web
======================================
::

    import Pyjo.App

    class MyApp(Pyjo.App.object):

        # All the complexities of CGI, WSGI, ASGI, HTTP and WebSockets get
        # reduced to a single method call!
        def handler(self, tx):

            # Request
            method = tx.req.method
            path = tx.req.url.path

            # Response
            tx.res.code = 200
            tx.res.headers.content_type = 'text/plain'
            tx.res.body = f'{method} request for {path}!'.encode()

            # Resume transaction
            tx.resume()

:mod:`Pyjo.App` is the base class of applications of :mod:`Pyjo`, a flexible
runtime environment for real-time web frameworks, with all the basic tools and
helpers needed to write simple web applications and higher level web
frameworks, such as :mod:`Pyjoyment`.

See also
--------

:mod:`Pyjo.HelloWorld`, :mod:`Pyjoyment`, https://mojolicious.org.

Inspired by `Mojo <https://github.com/mojolicious/mojo/blob/v6.0/lib/Mojo.pm>`_ of Mojolicious 6.0, the base class of
Mojolicious until Mojolicious 7.
"""

import Pyjo.Base
import Pyjo.Home
import Pyjo.Log
import Pyjo.Server
import Pyjo.Transaction.HTTP
import Pyjo.UserAgent
import Pyjo.Util

import os
import sys

from typing import Any, Self, overload


class Pyjo_App(Pyjo.Base.object):
    """
    :mod:`Pyjo.App` inherits all methods from :mod:`Pyjo.Base` and implements
    the following new ones.
    """

    # The methods that keep a stash, whose values the arguments of the constructor are
    _stashes: tuple[str, ...] = ('config',)

    def __init__(self, attrs: dict[str, Any] | None = None, /, **kwargs: Any) -> None:
        """::

            app = MyApp.new()
            app = MyApp.new(moniker='foo_bar')
            app = MyApp.new({'moniker': 'foo_bar'})

        Construct a new application, with the attributes as keyword arguments
        or a dict, and the arguments of
        :meth:`Pyjo.Server.Pyjo_Server.load_app` for its script. The value of
        ``config`` is the dict of :meth:`config`.
        """
        self._home: Pyjo.Home.object | None = None
        self._log: Pyjo.Log.object | None = None
        self._moniker: str | None = None
        self._ua: Pyjo.UserAgent.object | None = None

        # Not in Mojolicious: the value of a method that keeps a stash, as config, is its dict, as Mojo keeps the stash in
        # the hash of the object, which the arguments of new fill
        for name, value in {**(attrs or {}), **kwargs, **Pyjo.Server.args_override}.items():
            setattr(self, f'_{name}' if name in self._stashes else name, value)

    @property
    def home(self) -> Pyjo.Home.object:
        """::

            home = app.home
            app.home = Pyjo.Home.new()

        The home directory of your application, defaults to a :mod:`Pyjo.Home`
        object which stringifies to the actual path. ::

            # Portably generate path relative to home directory
            path = app.home.child('data', 'important.txt')
        """
        if self._home is None:
            self._home = Pyjo.Home.new().detect(type(self))
        return self._home

    @home.setter
    def home(self, value: Pyjo.Home.object) -> None:
        self._home = value

    @property
    def log(self) -> Pyjo.Log.object:
        """::

            log = app.log
            app.log = Pyjo.Log.new()

        The logging layer of your application, defaults to a :mod:`Pyjo.Log`
        object. ::

            # Log debug message
            app.log.debug('It works')
        """
        if self._log is None:
            self._log = Pyjo.Log.new()
        return self._log

    @log.setter
    def log(self, value: Pyjo.Log.object) -> None:
        self._log = value

    @property
    def moniker(self) -> str:
        """::

            moniker = app.moniker
            app.moniker = 'foo_bar'

        Moniker of this application, often used as default filename for
        configuration files and the like, defaults to decamelizing the
        application class with :func:`Pyjo.Util.decamelize`: the module of a
        class that the module names ``object``, as ``pyjo-hello_world`` of
        :mod:`Pyjo.HelloWorld`, or the class in its module.
        """
        if self._moniker is None:
            self._moniker = Pyjo.Util.decamelize(_package(type(self)).replace('.', '::'))
        return self._moniker

    @moniker.setter
    def moniker(self, value: str) -> None:
        self._moniker = value

    @property
    def ua(self) -> Pyjo.UserAgent.object:
        """::

            ua = app.ua
            app.ua = Pyjo.UserAgent.new()

        A full featured HTTP user agent for use in your applications, defaults
        to a :mod:`Pyjo.UserAgent` object. ::

            # Perform blocking request
            print(app.ua.get('example.com').result.body)
        """
        if self._ua is None:
            self._ua = Pyjo.UserAgent.new()
        return self._ua

    @ua.setter
    def ua(self, value: Pyjo.UserAgent.object) -> None:
        self._ua = value

    def build_tx(self) -> Pyjo.Transaction.HTTP.object:
        """::

            tx = app.build_tx()

        Transaction builder, defaults to building a
        :mod:`Pyjo.Transaction.HTTP` object.
        """
        return Pyjo.Transaction.HTTP.new()

    # config(**values) with no values is config(), which the first overload types
    @overload
    def config(self) -> dict[str, Any]: ...  # pyright: ignore[reportOverlappingOverload]

    @overload
    def config(self, name: str, /) -> Any: ...

    @overload
    def config(self, values: dict[str, Any], /) -> Self: ...

    @overload
    def config(self, **values: Any) -> Self: ...

    def config(self, *args: Any, **values: Any) -> Any:
        """::

            hash = app.config()
            foo = app.config('foo')
            app = app.config({'foo': 'bar', 'baz': 23})
            app = app.config(foo='bar', baz=23)

        Application configuration. ::

            # Remove value
            foo = app.config().pop('foo')

            # Assign multiple values at once
            app.config(foo='test', bar=23)
        """
        return Pyjo.Util._stash('config', self, args, values)  # pyright: ignore[reportPrivateUsage]

    def handler(self, tx: Any) -> None:
        """::

            app.handler(Pyjo.Transaction.HTTP.new())

        The handler is the main entry point to your application or framework
        and will be called for each new transaction, which will usually be a
        :mod:`Pyjo.Transaction.HTTP` or :mod:`Pyjo.Transaction.WebSocket`
        object. Meant to be overloaded in a subclass. ::

            def handler(self, tx):
                ...
        """
        raise NotImplementedError('Method "handler" not implemented by subclass')

    def server(self, server: Pyjo.Server.object) -> None:
        """::

            app.server(Pyjo.Server.new())

        Called by the server before it starts. Meant to be overloaded in a
        subclass.
        """

    def start(self, *args: str) -> Self:
        """::

            app = app.start()

        Start the application. When the environment variable
        ``PYJO_APP_LOADER`` is set, as :meth:`Pyjo.Server.Pyjo_Server.load_app`
        does, it is kept in :data:`Pyjo.Server.loaded_app` for the server.
        """
        # Application loader
        if os.environ.get('PYJO_APP_LOADER') is not None:
            Pyjo.Server.loaded_app = self
        return self


# The name of a class as Mojo has the package: the module that names the class its object, or the class in the module,
# and the class only in a script
def _package(cls: type) -> str:
    module = cls.__module__
    if getattr(sys.modules.get(module), 'object', None) is cls:
        return module
    return cls.__qualname__ if module == '__main__' else f'{module}.{cls.__qualname__}'


new = Pyjo_App.new
object = Pyjo_App
