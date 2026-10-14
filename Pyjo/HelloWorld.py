"""
Pyjo.HelloWorld - Hello World!
==============================
::

    import Pyjo.HelloWorld

    hello = Pyjo.HelloWorld.new()
    hello.start()

:mod:`Pyjo.HelloWorld` is the default application of :mod:`Pyjo.Server`, used
mostly for testing. It answers every request with ``Your Pyjo is working!``,
and has only what a server needs from an application, without
:mod:`Pyjoyment`.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

The counterpart of `Mojo::HelloWorld <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/HelloWorld.pm>`_
of Mojolicious 9.49, an application of Mojolicious.

Classes
-------
"""

import Pyjo.Base
import Pyjo.Log
import Pyjo.Server
import Pyjo.Transaction.HTTP

import builtins
import os

from typing import Any, Self, overload


type Anything = builtins.object


class Pyjo_HelloWorld(Pyjo.Base.object):
    """
    :mod:`Pyjo.HelloWorld` inherits all methods from :mod:`Pyjo.Base` and
    implements the following new ones.
    """

    # TODO: a subclass of Pyjoyment with startup, as Mojo::HelloWorld is of Mojolicious, when Pyjoyment is ported; until
    # then an application of its own, with what a server needs from it
    # Unlike Mojolicious: it answers "Your Pyjo is working!", as the moniker names it

    def __init__(self, **kwargs: Any) -> None:
        """::

            hello = Pyjo.HelloWorld.new()
            hello = Pyjo.HelloWorld.new(log=Pyjo.Log.new())

        Construct a new :mod:`Pyjo.HelloWorld` object, with the arguments of
        :meth:`Pyjo.Server.Pyjo_Server.load_app` for its script.
        """
        kwargs |= Pyjo.Server.args_override

        self.log: Pyjo.Log.object = kwargs.get('log') or Pyjo.Log.new(level='error')
        """::

            log = hello.log
            hello.log = Pyjo.Log.new()

        The logging layer of the application, defaults to a :mod:`Pyjo.Log`
        object with the level ``error``.
        """

        self.moniker: str = kwargs.get('moniker', 'pyjo-hello_world')
        """::

            moniker = hello.moniker
            hello.moniker = 'foo_bar'

        Moniker of this application, defaults to ``pyjo-hello_world``.
        """

        self._config: dict[str, Any] = {}

    def build_tx(self) -> Pyjo.Transaction.HTTP.object:
        """::

            tx = hello.build_tx()

        Build :mod:`Pyjo.Transaction.HTTP` object.
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

            config = hello.config()
            foo = hello.config('foo')
            hello = hello.config({'foo': 'bar', 'baz': 23})
            hello = hello.config(foo='bar', baz=23)

        Application configuration, as servers like :mod:`Pyjo.Server.Hot` read
        their settings from it. ::

            # Remove value
            foo = hello.config().pop('foo')

            # Assign multiple values at once
            hello.config(foo='test', bar=23)
        """
        # Dict
        if not len(args) and not len(values):
            return self._config

        # Get
        if len(args) == 1 and isinstance(args[0], str):
            return self._config.get(args[0])

        # Set
        self._config.update(*args, **values)
        return self

    def handler(self, tx: Pyjo.Transaction.HTTP.object) -> None:
        """::

            hello.handler(Pyjo.Transaction.HTTP.new())

        Handle the request of the transaction with the response
        ``Your Pyjo is working!``.
        """
        res = tx.res
        res.code = 200
        res.headers.content_type = 'text/html;charset=UTF-8'
        res.body = b'Your Pyjo is working!'
        tx.resume()

    def server(self, server: Pyjo.Server.object) -> None:
        """::

            hello.server(Pyjo.Server.new())

        Called by the server before it starts.
        """

    def start(self, *args: str) -> Self:
        """::

            hello = hello.start()

        Start the application. When the environment variable
        ``PYJO_APP_LOADER`` is set, as :meth:`Pyjo.Server.Pyjo_Server.load_app`
        does, it is kept in :data:`Pyjo.Server.loaded_app` for the server.
        """
        # Application loader
        if os.environ.get('PYJO_APP_LOADER') is not None:
            Pyjo.Server.loaded_app = self
        # TODO: the commands, when Mojolicious::Commands is ported
        return self


new = Pyjo_HelloWorld.new
object = Pyjo_HelloWorld
