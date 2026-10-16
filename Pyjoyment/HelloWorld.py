"""
Pyjoyment.HelloWorld - Hello World!
===================================
::

    import Pyjoyment.HelloWorld

    hello = Pyjoyment.HelloWorld.new()
    hello.start()

:mod:`Pyjoyment.HelloWorld` is the default :mod:`Pyjoyment` application, used
mostly for testing. :mod:`Pyjo.Server` defaults to :mod:`Pyjo.HelloWorld`, its
counterpart without :mod:`Pyjoyment`.

See also
--------

:mod:`Pyjoyment`, :mod:`Pyjo.HelloWorld`, https://mojolicious.org.

Ported from `Mojo::HelloWorld <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/HelloWorld.pm>`_ of
Mojolicious 9.49.
"""

import Pyjoyment


class Pyjoyment_HelloWorld(Pyjoyment.object):
    """
    :mod:`Pyjoyment.HelloWorld` inherits all attributes and methods from
    :mod:`Pyjoyment` and implements the following new ones.
    """

    def startup(self) -> None:
        """::

            hello.startup()

        Creates a catch-all route that renders a text message.
        """
        self.preload_namespaces = []
        self.log.level = 'error'
        self.log.path = None
        # Unlike Mojolicious: it answers "Your Pyjoyment is working!", as the moniker names it
        self.routes.any('/*whatever', {'whatever': '', 'text': 'Your Pyjoyment is working!'})


new = Pyjoyment_HelloWorld.new
object = Pyjoyment_HelloWorld
