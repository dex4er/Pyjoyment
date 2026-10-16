"""
Pyjo.HelloWorld - Hello World!
==============================
::

    import Pyjo.HelloWorld

    hello = Pyjo.HelloWorld.new()
    hello.start()

:mod:`Pyjo.HelloWorld` is the default application of :mod:`Pyjo.Server`, used
mostly for testing. It answers every request with ``Your Pyjo is working!``,
and is a :mod:`Pyjo.App` without :mod:`Pyjoyment`, whose counterpart is
:mod:`Pyjoyment.HelloWorld`.

See also
--------

:mod:`Pyjo.App`, :mod:`Pyjoyment.HelloWorld`, https://mojolicious.org.

Inspired by `Mojo::HelloWorld <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/HelloWorld.pm>`_ of
Mojolicious 9.49, an application of Mojolicious, which :mod:`Pyjoyment.HelloWorld` ports.

Classes
-------
"""

import Pyjo.App
import Pyjo.Log

from typing import Any


class Pyjo_HelloWorld(Pyjo.App.object):
    """
    :mod:`Pyjo.HelloWorld` inherits all attributes and methods from
    :mod:`Pyjo.App` and implements the following new ones.
    """

    def __init__(self, attrs: dict[str, Any] | None = None, /, **kwargs: Any) -> None:
        """::

            hello = Pyjo.HelloWorld.new()
            hello = Pyjo.HelloWorld.new(log=Pyjo.Log.new())

        Construct a new :mod:`Pyjo.HelloWorld` object, which logs errors only
        unless it gets a :attr:`~Pyjo.App.Pyjo_App.log`.
        """
        super().__init__(attrs, **kwargs)
        if self._log is None:
            self._log = Pyjo.Log.new(level='error')

    def handler(self, tx: Any) -> None:
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


new = Pyjo_HelloWorld.new
object = Pyjo_HelloWorld
