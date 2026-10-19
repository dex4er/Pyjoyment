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
loop, which ``PYJO_REACTOR`` selects before :mod:`Pyjo.IOLoop` is loaded:

.. code-block:: sh

    uv add git+https://github.com/dex4er/Pyjo-Reactor-Twisted
    PYJO_REACTOR=Pyjo.Reactor.Twisted ./myapp.py daemon

`Pyjo-Reactor-Twisted <https://github.com/dex4er/Pyjo-Reactor-Twisted>`_
    ``Pyjo.Reactor.Twisted``, on the reactor of `Twisted <https://twisted.org>`_,
    so that an application shares the event loop with the code of Twisted.
