Intro
=====

An asynchronous, event driver web framework for the Python programming language.

Pyjoyment provides own reactor which handles I/O and timer events in its own
main event loop but it supports other loops, ie. *libev*, *asyncio*.

Pyjoyment uses intensively own event emmiter which should be familiar for
Node.JS programmers.

It provides tool set for parsing and creating HTTP messages and HTML documents.
It also supports WSGI interface.

Pyjoyment requires Python 3.12 or newer and runs on PyPy. It doesn't
require any external libraries or compilers.

Pyjoyment is based on `Mojolicious <http://mojolicio.us>`_: a next generation
web framework for the Perl programming language.
