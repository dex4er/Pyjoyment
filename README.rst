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
* Non-blocking I/O web server, which also speaks FastCGI and runs as an ASGI,
  WSGI or CGI application, or as an event function of AWS Lambda.
* HTML/XML parser with CSS selector support.
* JSON with JSON Pointers, YAML and TOML, all loaded and dumped.
* Command line options with ``Pyjo.GetOpt``, in the way of Getopt::Long,
  argparse and Cobra, also from environment variables.
* Python-ish templates and template strings, with automatic escaping.
* Containers for URLs, paths, query strings, headers, cookies and HTTP
  messages.
* Event emitter, event loop with TCP, UDP and UNIX domain sockets, logger
  and utility functions.
* Test scripts which print the `Test Anything Protocol <https://testanything.org/>`_
  (TAP), with ``Pyjo.Test``, inspired by Perl's ``Test::More``, and a test
  harness, ``Pyjo.Prove``, inspired by Perl's ``prove``.

The ``Pyjoyment`` package is the web framework itself: routes, controllers,
renderer, plugins, ``Pyjoyment.Lite`` and the command line interface. It
renders JSON, YAML and TOML, and reads its configuration from Python, JSON,
YAML and TOML files.

Both are cloud native: ``generate dockerfile`` writes the image of an
application, whose server stops gracefully on the ``TERM`` of its container
and listens on the port of ``PORT``, as Knative, Cloud Run, Render, Koyeb and
Heroku set it, and an application runs as an event function of AWS Lambda
too.

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
user agent, and the servers, on their own, preforking, prethreading, with hot
deployment or reloading, and through FastCGI, ASGI, WSGI, CGI and AWS Lambda. So is the web framework, the
``Pyjoyment`` package: routes, controllers, the renderer with templates and
template strings, plugins, ``Pyjoyment.Lite`` and the commands. The tests of
Mojolicious are ported with them, and a ported module names the Mojolicious
version it was ported from in its documentation.

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

These three lines are a whole web application.

.. code-block:: python

   from Pyjoyment.Lite import *


   get('/', {'text': 'I ♥ Pyjoyment!'})

   app.start()

To run the example with the built-in development web server, just put the
code into a file and start it with ``pyjo-reload``. ::

    $ pyjo-reload hello.py
    Web application available at http://127.0.0.1:3000

Test it with any HTTP client you prefer. ::

    $ curl http://127.0.0.1:3000/
    I ♥ Pyjoyment!

Duct tape for the HTML5 web
===========================

Use all the latest Python and HTML features in beautiful single file
prototypes like this one, and grow them easily into well-structured
Model-View-Controller web applications with ``pyjo generate app``.

.. code-block:: python

   """
   __DATA__

   @@ index.html.ep
   % url = url_for('title')
   <script>
     const ws = new WebSocket('<%= url.to_abs() %>');
     ws.onmessage = function (event) { document.body.innerHTML += event.data };
     ws.onopen    = function (event) { ws.send('https://mojolicious.org') };
   </script>
   """

   from Pyjoyment.Lite import *


   # Render template "index.html.ep" from the DATA section
   @get('/')
   def index(c):
       c.render(template='index')


   # WebSocket service used by the template to extract the title from a website
   @websocket('/title')
   def title(c):
       @c.on('message')
       def message(c, msg):
           c.ua().get_p(msg).then(lambda tx: c.send(tx.result.dom().at('title').text))


   app.start()

The templates of a script of ``Pyjoyment.Lite`` are in its docstring, after a
line ``__DATA__``, and the website is requested without blocking, as the
WebSocket service runs in the event loop.

Servers
========

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

On a platform that tells the server the port to listen on with the ``PORT``
environment variable, as `Knative <https://knative.dev/>`_,
`Cloud Run <https://cloud.google.com/run>`_, `Render <https://render.com/>`_,
`Koyeb <https://www.koyeb.com/>`_ or `Heroku <https://www.heroku.com/>`_, the
web server of Pyjoyment listens on that port, and ``generate dockerfile``
writes the ``Dockerfile`` of the image of an application, with the port that
the image exposes: ::

    ./myapp.py generate dockerfile --port 8080

On `AWS Lambda <https://aws.amazon.com/lambda/>`_, it is an event function,
whose handler ``hello_world_lambda.handler`` answers the events of API
Gateway, Function URLs and Application Load Balancers:

.. code-block:: python

   import Pyjo.HelloWorld
   import Pyjo.Server.Lambda


   # The handler "hello_world_lambda.handler" of an event function of AWS Lambda
   handler = Pyjo.Server.Lambda.new(app=Pyjo.HelloWorld.new()).to_lambda_app()

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

   """
   __DATA__

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

   import Pyjo.App
   import Pyjo.GetOpt
   import Pyjo.Server.Daemon
   import Pyjo.Template
   import Pyjo.URL

   from Pyjo.Loader import data_section
   from Pyjo.Util import die


   class MyApp(Pyjo.App.object):
       # Embedded template file
       template = Pyjo.Template.new(auto_escape=True, vars=True).parse(data_section(__name__, 'index.html.ep'))

       # All the complexities of CGI, WSGI, ASGI, HTTP and WebSockets get reduced to a single method call!
       def handler(self, tx):
           # Resume transaction at the end of the block
           with tx:
               # Request
               method = tx.req.method
               path = tx.req.url.path

               # Response
               tx.res.code = 200
               tx.res.headers.content_type = 'text/html; charset=utf-8'
               tx.res.body = self.template.process({'method': method, 'path': path}).encode()


   # Options --address and --port
   getopt = Pyjo.GetOpt.new().option('a|address=s', default='0.0.0.0').option('p|port=i', default=3000)
   opts = getopt.parse() or die('Usage: http_server.py [--address ADDRESS] [--port PORT]')

   url = Pyjo.URL.new().set(scheme='http', host=opts.address, port=opts.port)

   Pyjo.Server.Daemon.new(app=MyApp.new(), listen=[url]).run()

Copyright and license
=====================

.. begin-license

Copyright (C) 2014-2026, Piotr Roszatycki.

Based on Mojolicious: Copyright (C) 2008-2025, Sebastian Riedel and others.

This program is free software, you can redistribute it and/or modify it under
the terms of the Artistic License version 2.0.

The pages of errors bundle `Bootstrap <https://getbootstrap.com>`_, with
Popper, under the MIT License, and `highlight.js <https://highlightjs.org>`_
under the BSD 3-Clause License, whose texts are next to them in
``Pyjoyment/resources/public/pyjo``.

.. end-license
