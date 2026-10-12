
"""
Pyjo.Server.Base - HTTP/WebSocket server base class
===================================================
::

    import Pyjo.Server.Base

    class MyServer(Pyjo.Server.Base.object):

        def run(self):
            # Get a transaction
            tx = self.build_tx()

            # Emit "request" event
            self.emit('request', tx)

:mod:`Pyjo.Server.Base` is an abstract base class for HTTP/WebSocket servers and server
interfaces, like :mod:`Pyjo.Server.CGI`, :mod:`Pyjo.Server.Daemon`
and :mod:`Pyjo.Server.WSGI`.

Events
------

:mod:`Pyjo.Server.Base` inherits all events from :mod:`Pyjo.EventEmitter` and can emit the
following new ones.

request
~~~~~~~
::

    @server.on
    def request(server, tx):
        ...

Emitted when a request is ready and needs to be handled. ::

    server.unsubscribe('request')

    @server.on
    def request(server, tx):
        tx.res.code = 200
        tx.res.headers.content_type = 'text/plain'
        tx.res.body = b'Hello World!'
        tx.resume()

Classes
-------
"""

import Pyjo.EventEmitter

import os
import sys

from Pyjo.Loader import load_module
from Pyjo.Util import getenv, not_implemented, notnone


class Pyjo_Server_Base(Pyjo.EventEmitter.object):
    """
    :mod:`Pyjo.Server.Base` inherits all attributes and methods from
    :mod:`Pyjo.EventEmitter` and implements the following new ones.
    """

    def __init__(self, **kwargs):
        """::

            server = Pyjo.Server.Base.new()
            server = Pyjo.Server.Base.new(reverse_proxy=True)

        Construct a new ``Pyjo.Server`` object and subscribe to ``request`` event
        with default request handling.
        """
        super().__init__(**kwargs)

        self.app = notnone(kwargs.get('app'), lambda: self.build_app('Pyjo.HelloWorld'))
        """::

            app = server.app
            server.app = MyApp.new()

        Application this server handles, defaults to a :mod:`Pyjo.HelloWorld` object.
        """

        self.reverse_proxy = notnone(kwargs.get('reverse_proxy'), lambda: getenv('PYJO_REVERSE_PROXY'))
        """::

            boolean = server.reverse_proxy
            server.reverse_proxy = boolean

        This server operates behind a reverse proxy, defaults to the value of the
        ``PYJO_REVERSE_PROXY`` environment variable.
        """

        def request_cb(server, tx):
            server.app.handler(tx)

        self.on(request_cb, 'request')

    def build_app(self, app):
        """::

            app = server.build_app('MyApp')

        Build application from class.
        """
        module = load_module(app)
        if module:
            return module.new()
        else:
            raise ImportError("No application module named '{0}'".format(app))

    def build_tx(self):
        """::

            tx = server.build_tx()

        Let application build a transaction.
        """
        tx = self.app.build_tx()
        if self.reverse_proxy:
            tx.req.reverse_proxy = True
        return tx

    def daemonize(self):
        """::

            server->daemonize;

        Daemonize server process.
        """
        # Fork and kill parent
        pid = os.fork()
        if pid > 0:
            os._exit(0)
        os.setsid()

        # Close filehandles
        null = os.open(os.devnull, os.O_RDWR)
        os.dup2(null, sys.stdin.fileno())
        os.dup2(null, sys.stdout.fileno())
        os.dup2(null, sys.stderr.fileno())

    @not_implemented
    def run(self):
        """::

            server.run()

        Run server. Meant to be overloaded in a subclass.
        """


new = Pyjo_Server_Base.new
object = Pyjo_Server_Base
