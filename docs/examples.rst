Examples
========

Quick start
-----------

A whole web application of ``Pyjoyment.Lite``:

    .. include:: ../examples/pyjoyment/hello.py
       :code: python


Duct tape for the HTML5 web
---------------------------

A WebSocket service used by the template to extract the title from a website:

    .. include:: ../examples/pyjoyment/title.py
       :code: python


Applications of other frameworks
--------------------------------

A WSGI application, in a file of its own, under a path of an application of
``Pyjoyment.Lite``:

    .. include:: ../examples/pyjoyment/mount_wsgi.py
       :code: python

The WSGI application, which also runs on its own, on the WSGI server of the
standard library:

    .. include:: ../examples/pyjoyment/hello_wsgi.py
       :code: python

An application of Pyjoyment as the WSGI application, in the same file:

    .. include:: ../examples/pyjoyment/mount_wsgi_inception.py
       :code: python

An ASGI application, in a file of its own, under a path of an application of
``Pyjoyment.Lite``, whose events stream at the pace of the client:

    .. include:: ../examples/pyjoyment/mount_asgi.py
       :code: python

The ASGI application, which also runs on its own, on an ASGI server:

    .. include:: ../examples/pyjoyment/hello_asgi.py
       :code: python

An application of Pyjoyment as the ASGI application, in the same file:

    .. include:: ../examples/pyjoyment/mount_asgi_inception.py
       :code: python

PHP on php-fpm, a FastCGI application, under a path of an application of
``Pyjoyment.Lite``, with the scripts of its directory and the pool of
php-fpm:

    .. include:: ../examples/pyjoyment/mount_fastcgi_php.py
       :code: python

    .. include:: ../examples/pyjoyment/php/index.php
       :code: php

    .. include:: ../examples/pyjoyment/php/phpinfo.php
       :code: php

    .. include:: ../examples/pyjoyment/php/php-fpm.conf
       :code: ini

A CGI program of Python in the directory ``cgi-bin``, under a path of an
application of ``Pyjoyment.Lite``, a process for each request:

    .. include:: ../examples/pyjoyment/mount_cgi.py
       :code: python

    .. include:: ../examples/pyjoyment/cgi-bin/hello.py
       :code: python

PHP on php-cgi, with the scripts of the same directory as for php-fpm, a
process of php-cgi for each request:

    .. include:: ../examples/pyjoyment/mount_cgi_php.py
       :code: python


Servers
-------

``Pyjo.HelloWorld`` natively, on the web server of Pyjoyment:

    .. include:: ../examples/servers/hello_world.py
       :code: python

On `uvicorn <https://www.uvicorn.org/>`_, an ASGI server:

    .. include:: ../examples/servers/hello_world_uvicorn.py
       :code: python

On `Werkzeug <https://werkzeug.palletsprojects.com/>`_, a WSGI server:

    .. include:: ../examples/servers/hello_world_werkzeug.py
       :code: python

As an event function of `AWS Lambda <https://aws.amazon.com/lambda/>`_:

    .. include:: ../examples/servers/hello_world_lambda.py
       :code: python


Requests on a timer
-------------------

The user agent requests the server every second, in the same event loop, without
blocking it:

    .. include:: ../examples/ua/user_agent.py
       :code: python

A request on a loopback
-----------------------

A blocking request of the user agent to the server, in the same event loop:

    .. include:: ../examples/ua/loopback.py
       :code: python

Web scraping
------------

    .. include:: ../examples/ua/entities.py
       :code: python


URL manipulation
----------------

    .. include:: ../examples/pyjo/url.py
       :code: python


Non-blocking TCP client/server
------------------------------

    .. include:: ../examples/pyjo/ioloop.py
       :code: python


Standalone HTTP server serving embedded template file
-----------------------------------------------------

    .. include:: ../examples/servers/http_server.py
       :code: python
