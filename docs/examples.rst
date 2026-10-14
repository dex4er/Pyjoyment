Examples
========

Quick start
-----------

``Pyjo.HelloWorld`` natively, on the web server of Pyjoyment:

    .. include:: ../examples/hello_world.py
       :code: python

On `uvicorn <https://www.uvicorn.org/>`_, an ASGI server:

    .. include:: ../examples/hello_world_uvicorn.py
       :code: python

On `Werkzeug <https://werkzeug.palletsprojects.com/>`_, a WSGI server:

    .. include:: ../examples/hello_world_werkzeug.py
       :code: python


Web scraping
------------

    .. include:: ../examples/entities.py
       :code: python


URL manipulation
----------------

    .. include:: ../examples/url.py
       :code: python


Non-blocking TCP client/server
------------------------------

    .. include:: ../examples/ioloop.py
       :code: python


Standalone HTTP server serving embedded template file
-----------------------------------------------------

    .. include:: ../examples/http_server.py
       :code: python
