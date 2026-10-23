Intro
=====

A real-time web framework for the Python programming language, ported from
`Mojolicious <https://mojolicious.org>`_, the real-time web framework for Perl.
Pyjoyment keeps the API of Mojolicious with Python names, so its documentation
and experience carry over.

The ``Pyjo`` package is the web development toolkit, ported from the ``Mojo``
modules, which can be used for all kinds of applications independently of the
web framework:

* HTTP and WebSocket client and server.
* Non-blocking I/O web server, which also speaks FastCGI, to a web server in
  front of it and to an application behind it, as PHP on php-fpm, and runs as
  an ASGI, WSGI or CGI application, or as an event function of AWS Lambda.
* HTML/XML parser with CSS selector support.
* JSON with JSON Pointers and JSON Schema, from type hints and validated,
  YAML and TOML, all loaded and dumped.
* Command line options with ``Pyjo.GetOpt``, in the way of Getopt::Long,
  argparse and Cobra, also from environment variables.
* Python-ish templates and template strings, with automatic escaping.
* Containers for URLs, paths, query strings, headers, cookies and HTTP
  messages.
* Event emitter, event loop with TCP, UDP and UNIX domain sockets and child
  processes, logger and utility functions.
* Test scripts which print the `Test Anything Protocol <https://testanything.org/>`_
  (TAP), with ``Pyjo.Test``, inspired by Perl's ``Test::More``, and a test
  harness, ``Pyjo.Prove``, inspired by Perl's ``prove``.

The ``Pyjoyment`` package is the web framework itself: routes, controllers,
renderer, plugins, ``Pyjoyment.Lite`` and the command line interface. It
renders JSON, YAML and TOML, and reads its configuration from Python, JSON,
YAML and TOML files.

It mounts the applications of other frameworks under a path or a host, next to
its own routes: WSGI applications, as those of Flask, and ASGI applications, as
those of Starlette and the servers of the MCP SDK, in the same process and on
the same server, whose responses stream at the pace of the client, with their
WebSockets, FastCGI applications, as PHP on php-fpm, which it connects to, CGI
programs, which it runs, as a web server does, with one script for every path
or the scripts of a directory, and event functions of AWS Lambda, which it runs
in a process of their own, as Lambda does.

Both are cloud native: ``generate dockerfile`` writes the image of an
application, whose server stops gracefully on the ``TERM`` of its container
and listens on the port of ``PORT``, as Knative, Cloud Run, Render, Koyeb and
Heroku set it, and an application runs as an event function of AWS Lambda
too.

Pyjoyment requires Python 3.12 or newer and runs on PyPy on a best-effort
basis. It needs nothing besides the Python standard library.
