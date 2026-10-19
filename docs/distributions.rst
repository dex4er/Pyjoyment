Distributions
=============

Pyjoyment needs nothing besides the Python standard library, so what needs
another library is a distribution of its own, which adds a module to a
namespace of Pyjoyment, as ``Pyjo.Reactor`` for a reactor or
``Pyjoyment.Plugin`` for a plugin. They are installed from their Git
repositories until they are on PyPI.

Reactors
--------

A reactor runs the I/O and the timers of :mod:`Pyjo.IOLoop` on another event
loop, which ``PYJO_REACTOR`` selects before :mod:`Pyjo.IOLoop` is loaded. Its
API is the one of :mod:`Pyjo.Reactor`, which :mod:`Pyjo.IOLoop` calls, so an
application uses it through :mod:`Pyjo.IOLoop`, as it uses
:mod:`Pyjo.Reactor.Asyncio` and :mod:`Pyjo.Reactor.Poll`, and needs nothing
of its own for it. A reactor passes the whole test suite of Pyjoyment.

Pyjo.Reactor.Twisted
~~~~~~~~~~~~~~~~~~~~

`Pyjo-Reactor-Twisted <https://github.com/dex4er/Pyjo-Reactor-Twisted>`_ runs
the event loop on the reactor of `Twisted <https://twisted.org>`_, so that an
application shares it with the code of Twisted.

.. code-block:: sh

    uv add git+https://github.com/dex4er/Pyjo-Reactor-Twisted
    PYJO_REACTOR=Pyjo.Reactor.Twisted ./myapp.py daemon

Its API is the one of :mod:`Pyjo.Reactor.Poll`, which it is a subclass of,
with these differences:

- It uses the reactor of Twisted that the application installed, or else the
  reactor of poll of Twisted, or of select on macOS and where there is no
  poll, not the reactor of epoll, the default of Twisted on Linux: epoll keeps
  its state in the kernel, which loses a socket that is closed before it is
  removed and is shared with the child of a fork, as a worker of
  :mod:`Pyjo.Server.Prefork`.
- The reactor of Twisted is unique in a process, so ``new()`` returns a
  :mod:`Pyjo.Reactor.Poll` object while another object uses it, and the
  threads of :mod:`Pyjo.Server.Prethread` get :mod:`Pyjo.Reactor.Poll` objects.
- While the reactor of Twisted runs, started by something else, as ``twistd``
  or Scrapy, ``start()`` and ``one_tick()`` return right away, and the reactor
  of Twisted that runs handles the events.
