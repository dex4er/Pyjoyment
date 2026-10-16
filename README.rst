.. image:: https://github.com/dex4er/Pyjoyment/actions/workflows/tests.yaml/badge.svg?branch=master
   :target: https://github.com/dex4er/Pyjoyment/actions/workflows/tests.yaml
.. image:: https://app.readthedocs.org/projects/pyjoyment/badge/?version=latest
   :target: https://pyjoyment.readthedocs.io/en/latest/

Pyjoyment
=========

.. begin-intro

A real-time web framework for the Python programming language, ported from
`Mojolicious <https://mojolicious.org>`_, the real-time web framework for Perl.
Pyjoyment keeps the API of Mojolicious with Python names, so its documentation
and experience carry over.

The ``Pyjo`` package is the web development toolkit, ported from the ``Mojo``
modules, which can be used for all kinds of applications independently of the
web framework:

* HTTP and WebSocket client and server.
* Non-blocking I/O web server, which also runs as an ASGI, WSGI or CGI
  application.
* HTML/XML parser with CSS selector support, and JSON with JSON Pointers.
* Python-ish templates and template strings, with automatic escaping.
* Containers for URLs, paths, query strings, headers, cookies and HTTP
  messages.
* Event emitter, event loop with TCP, UDP and UNIX domain sockets, logger
  and utility functions.
* Test scripts which print the `Test Anything Protocol <https://testanything.org/>`_
  (TAP), with ``Pyjo.Test``, inspired by Perl's ``Test::More``, and a test
  harness, ``Pyjo.Prove``, inspired by Perl's ``prove``.

The ``Pyjoyment`` package is reserved for the web framework itself: routes,
controllers, renderer and ``Pyjoyment.Lite``.

Pyjoyment requires Python 3.12 or newer and runs on PyPy on a best-effort
basis. It needs nothing besides the Python standard library.

.. end-intro

Status
======

.. begin-status

Pyjoyment was written against Mojolicious 6 and is being revived as a port of
Mojolicious 9 to Python 3.12 and newer, with ``asyncio`` as its event loop.
The toolkit, the ``Pyjo`` package, is ported: URLs, DOM and CSS selectors,
JSON, templates, HTTP messages and cookies, the event loop with promises, the
user agent, and the servers, on their own, preforking, with hot deployment or
reloading, and through ASGI, WSGI and CGI. A ported module names the
Mojolicious version it was ported from in its documentation. The web
framework, the ``Pyjoyment`` package with routes, controllers and plugins, is
not there yet.

The progress is tracked in `GitHub Issues <https://github.com/dex4er/Pyjoyment/issues>`_.

.. end-status

Installation
============

.. begin-installation

Pyjoyment is installed from its Git repository, as the release on PyPI
predates the revival: ::

    pip install git+https://github.com/dex4er/Pyjoyment

or, in a project managed with `uv <https://docs.astral.sh/uv/>`_: ::

    uv add git+https://github.com/dex4er/Pyjoyment

.. end-installation

Quick start
===========

``Pyjo.HelloWorld`` is the application that a server runs when it is given
none, and it answers every request with ``Your Pyjo is working!``. It runs
natively on the web server of Pyjoyment:

.. code-block:: python

   import Pyjo.HelloWorld
   import Pyjo.Server.Daemon


   Pyjo.Server.Daemon.new(app=Pyjo.HelloWorld.new(), listen=['http://*:3000']).run()

on `uvicorn <https://www.uvicorn.org/>`_, an ASGI server
(``pip install uvicorn``):

.. code-block:: python

   import Pyjo.HelloWorld
   import Pyjo.Server.ASGI

   import uvicorn


   app = Pyjo.Server.ASGI.new(app=Pyjo.HelloWorld.new()).to_asgi_app()

   uvicorn.run(app, port=3000)

or on `Werkzeug <https://werkzeug.palletsprojects.com/>`_, a WSGI server
(``pip install werkzeug``):

.. code-block:: python

   import Pyjo.HelloWorld
   import Pyjo.Server.WSGI

   from werkzeug.serving import run_simple


   app = Pyjo.Server.WSGI.new(app=Pyjo.HelloWorld.new()).to_wsgi_app()

   run_simple('localhost', 3000, app)

and answers on port 3000: ::

    curl http://localhost:3000/

Documentation
=============

The documentation is on `Read the Docs <https://pyjoyment.readthedocs.io/>`_.

Examples
========

Web scraping
------------

.. code-block:: python

   import Pyjo.UserAgent

   from Pyjo.String.Unicode import u


   # Extract named character references from HTML spec
   tx = Pyjo.UserAgent.new().get('https://html.spec.whatwg.org')
   for n in tx.res.dom('#named-character-references-table tbody > tr').each():
       u(n.at('td > code').text + ' ' + n.children('td')[1].text).trim().say()

URL manipulation
----------------

.. code-block:: python

   import Pyjo.URL


   # 'ssh+git://git@github.com/dex4er/Pyjoyment.git'
   url = Pyjo.URL.new('https://github.com/dex4er/Pyjoyment')
   print(url.set(scheme='ssh+git', userinfo='git', path=f'{url.path}.git').to_unsafe_str())

   # 'https://pypi.org/search/?q=Pyjoyment&o=&c=Programming+Language+%3A%3A+Python'
   url = Pyjo.URL.new('https://pypi.org/search/')
   print(url.set(query=[('q', 'Pyjoyment'), ('o', ''), ('c', 'Programming Language :: Python')]))

Non-blocking TCP client/server
------------------------------

.. code-block:: python

   import Pyjo.IOLoop


   # Listen on port 3000
   @Pyjo.IOLoop.server(port=3000)
   def server(loop, stream, cid):

       @stream.on
       def read(stream, chunk):
           # Process input chunk
           print(f'Server: {chunk.decode("utf-8")}')

           # Write response
           stream.write(b'HTTP/1.1 200 OK\x0d\x0a\x0d\x0a')

           # Disconnect client
           stream.close_gracefully()


   # Connect to port 3000
   @Pyjo.IOLoop.client(port=3000)
   def client(loop, err, stream):

       @stream.on
       def read(stream, chunk):
           # Process input
           print(f'Client: {chunk.decode("utf-8")}')

       # Write request
       stream.write(b'GET / HTTP/1.1\x0d\x0a\x0d\x0a')


   # Add a timer
   @Pyjo.IOLoop.timer(3)
   def timeouter(loop):
       print('Timeout')
       # Shutdown server
       loop.remove(server)


   # Start event loop
   Pyjo.IOLoop.start()

Standalone HTTP server serving embedded template file
------------------------------------------------------

.. code-block:: python

   import Pyjo.Server.Daemon
   import Pyjo.Template
   import Pyjo.URL

   from Pyjo.Loader import data_section

   import sys


   opts = {'address': '0.0.0.0', 'port': '3000'} | dict(a.split('=', 1) for a in sys.argv[1:])

   listen = str(Pyjo.URL.new().set(scheme='http', host=opts['address'], port=opts['port']))

   daemon = Pyjo.Server.Daemon.new(listen=[listen])
   daemon.unsubscribe('request')


   # Embedded template file
   __DATA__ = r"""
   @@ index.html.ep
   <!DOCTYPE html>
   <html>
   <head>
   <meta charset="UTF-8">
   <title>Pyjoyment</title>
   </head>
   <body>
   <h1>♥ Pyjoyment ♥</h1>
   <h2>This page is served by Pyjoyment framework.</h2>
   <p><%= method %> request for <%= path %></p>
   </body>
   </html>
   """

   template = Pyjo.Template.new(auto_escape=True, vars=True).parse(data_section(__name__, 'index.html.ep'))


   @daemon.on
   def request(daemon, tx):
       # Request
       method = tx.req.method
       path = tx.req.url.path

       # Response
       tx.res.code = 200
       tx.res.headers.content_type = 'text/html; charset=utf-8'
       tx.res.body = template.process({'method': method, 'path': path}).encode()

       # Resume transaction
       tx.resume()


   daemon.run()

Copyright and license
=====================

.. begin-license

Copyright (C) 2014-2026, Piotr Roszatycki.

Based on Mojolicious: Copyright (C) 2008-2025, Sebastian Riedel and others.

This program is free software, you can redistribute it and/or modify it under
the terms of the Artistic License version 2.0.

.. end-license
