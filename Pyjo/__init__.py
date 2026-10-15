"""
Pyjo - Web development toolkit
==============================
::

    # HTTP/WebSocket user agent
    import Pyjo.UserAgent
    ua = Pyjo.UserAgent.new()
    print(ua.get('www.mojolicious.org').result.headers.server)

    # HTML/XML DOM parser with CSS selectors
    import Pyjo.DOM
    dom = Pyjo.DOM.new('<div><b>Hello Pyjo!</b></div>')
    print(dom.at('div > b').text)

    # Python-ish templates
    import Pyjo.Template
    mt = Pyjo.Template.new(vars=True)
    print(mt.render('Hello <%= what %>!', {'what': 'Pyjo'}))

    # HTTP/WebSocket server
    import Pyjo.Server.Daemon
    daemon = Pyjo.Server.Daemon.new(listen=['http://*:8080'])

    @daemon.unsubscribe('request').on('request')
    def request(daemon, tx):
        tx.res.code = 200
        tx.res.body = b'Hello Pyjo!'
        tx.resume()

    daemon.run()

    # Event loop
    import Pyjo.IOLoop
    for seconds in range(1, 6):
        Pyjo.IOLoop.timer(seconds, lambda loop, seconds=seconds: print(seconds))
    Pyjo.IOLoop.start()

A powerful web development toolkit, with all the basic tools and helpers
needed to write simple web applications and higher level web frameworks, such
as :mod:`Pyjoyment`. Some of the most commonly used tools are
:mod:`Pyjo.UserAgent`, :mod:`Pyjo.DOM`, :mod:`Pyjo.JSON`,
:mod:`Pyjo.Server.Daemon`, :mod:`Pyjo.Server.Prefork`, :mod:`Pyjo.IOLoop` and
:mod:`Pyjo.Template`.

:mod:`Pyjo` is a namespace package that may be split across multiple
distributions, as another reactor in :mod:`Pyjo.Reactor` comes from one of its
own.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo.pm>`_
of Mojolicious 9.49.
"""

from pkgutil import extend_path


# Not in Mojolicious: a namespace package, as Python does not merge a regular package from every directory of sys.path
__path__ = extend_path(__path__, __name__)
