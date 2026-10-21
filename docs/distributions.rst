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

- `Pyjo.Reactor.Twisted - Low-level event reactor with Twisted support
  <https://pyjoyment.readthedocs.io/projects/pyjo-reactor-twisted/en/latest/>`_
