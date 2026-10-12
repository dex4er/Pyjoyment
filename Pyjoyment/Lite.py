"""
Pyjoyment.Lite - Micro real-time web framework
==============================================
::

    from Pyjoyment.Lite import get, path

    # Route with placeholder
    @path('/:foo')
    def get(c):
        foo = c.param('foo')
        c.render(text="Hello from {0}".format(foo))

    # Start the Mojolicious command system
    app.start
"""

import Pyjoyment.Base


class Pyjoyment_Lite(Pyjoyment.Base.object):
    pass


app = Pyjoyment_Lite()


def get(path, **kwargs):
    pass


def path(path):
    def wrap(cb):
        return cb

    return wrap


def post(path, **kwargs):
    pass


def websocket(path, **kwargs):
    pass
