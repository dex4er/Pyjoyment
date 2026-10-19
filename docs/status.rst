Status
======

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
