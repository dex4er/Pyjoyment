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
* Non-blocking I/O web server, which also runs as a WSGI or CGI application.
* HTML/XML parser with CSS selector support, and JSON with JSON Pointers.
* Containers for URLs, paths, query strings, headers, cookies and HTTP
  messages.
* Event emitter, event loop, logger and utility functions.
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
Mojolicious 9.49, with ``asyncio`` as its event loop. The modules are ported
anew one by one, and a ported module names the Mojolicious version it was
ported from in its documentation. The other modules still follow Mojolicious
6, with an event loop of their own based on ``select(2)`` and ``poll(2)``, and
the web framework is not there yet.

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

   tx = Pyjo.UserAgent.new().get('https://html.spec.whatwg.org')
   for n in tx.res.dom('#named-character-references-table tbody > tr').each():
       u(n.at('td > code').text + ' ' + n.children('td')[1].text).trim().say()



URL manipulation
----------------

.. code-block:: python

   import Pyjo.URL
   from Pyjo.String.Unicode import u

   # 'ssh+git://git@github.com/dex4er/Pyjoyment.git'
   url = Pyjo.URL.new('https://github.com/dex4er/Pyjoyment')
   print(url.set(scheme='ssh+git', userinfo='git', path=u(url.path) + '.git'))

   # 'http://metacpan.org/search?q=Mojo::URL&size=20'
   print(Pyjo.URL.new('http://metacpan.org/search')
         .set(query={'q': 'Mojo::URL', 'size': 20}))


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
           print("Server: {0}".format(chunk.decode('utf-8')))

           # Write response
           stream.write(b"HTTP/1.1 200 OK\x0d\x0a\x0d\x0a")

           # Disconnect client
           stream.close_gracefully()


   # Connect to port 3000
   @Pyjo.IOLoop.client(port=3000)
   def client(loop, err, stream):

       @stream.on
       def read(stream, chunk):
           # Process input
           print("Client: {0}".format(chunk.decode('utf-8')))

       # Write request
       stream.write(b"GET / HTTP/1.1\x0d\x0a\x0d\x0a")


   # Add a timer
   @Pyjo.IOLoop.timer(3)
   def timeouter(loop):
       print("Timeout")
       # Shutdown server
       loop.remove(server)


   # Start event loop
   Pyjo.IOLoop.start()


Standalone HTTP server serving embedded template file
------------------------------------------------------

.. code-block:: python

   # -*- coding: utf-8 -*-

   import Pyjo.Server.Daemon
   import Pyjo.URL

   from Pyjo.Loader import embedded_file
   from Pyjo.Util import b, u

   import sys


   opts = dict([['address', '0.0.0.0'], ['port', 3000]] + list(map(lambda a: a.split('='), sys.argv[1:])))
   listen = str(Pyjo.URL.new(scheme='http', host=opts['address'], port=opts['port']))

   daemon = Pyjo.Server.Daemon.new(listen=[listen])
   daemon.unsubscribe('request')


   # Embedded template file
   DATA = u(r'''
   @@ index.html.tpl
   <!DOCTYPE html>
   <html>
   <head>
   <meta charset="UTF-8">
   <title>Pyjoyment</title>
   </head>
   <body>
   <h1>♥ Pyjoyment ♥</h1>
   <h2>This page is served by Pyjoyment framework.</h2>
   <p>{method} request for {path}</p>
   </body>
   </html>
   ''')


   @daemon.on
   def request(daemon, tx):
       # Request
       method = tx.req.method
       path = tx.req.url.path

       # Template
       template = embedded_file(sys.modules[__name__], 'index.html.tpl')

       # Response
       tx.res.code = 200
       tx.res.headers.content_type = 'text/html; charset=utf-8'
       tx.res.body = b(template.format(**locals()))

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
