
"""
Pyjo.HelloWorld - Hello world!
==============================
::

    import Pyjo.HelloWorld

    hello = Pyjo.HelloWorld.new()
    hello.start()

:mod:`Pyjo.HelloWorld` is the default :mod:`Pyjoyment` application, used mostly for
testing.

Classes
-------
"""

import Pyjo.Base
import Pyjo.Log
import Pyjo.Transaction.HTTP

from Pyjo.Util import notnone


class Pyjo_HelloWorld(Pyjo.Base.object):
    """
    :mod:`Pyjo.HelloWorld` inherits all attributes and methods from
    :mod:`Pyjo.Base` and implements the following new ones.
    """

    def __init__(self, **kwargs):
        self.log = notnone(kwargs.get('log'), lambda: Pyjo.Log.new())

    def app(self):
        return self

    def build_tx(self):
        return Pyjo.Transaction.HTTP.new()

    def handler(self, tx):
        tx.res.code = 200
        tx.res.headers.content_type = 'text/plain'
        tx.res.body = b"Hello, world!\n"
        tx.resume()
        return self

    def start(self):
        return


new = Pyjo_HelloWorld.new
object = Pyjo_HelloWorld
