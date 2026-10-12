"""
Pyjo.Server.WSGI - WSGI server
==============================
::

    import Pyjo.Server.WSGI
    from Pyjo.Util import b

    from wsgiref.simple_server import make_server

    wsgi = Pyjo.Server.WSGI.new()
    wsgi.unsubscribe('request')

    @wsgi.on
    def request(wsgi, tx):
        # Request
        method = tx.req.method
        path = tx.req.url.path

        # Response
        tx.res.code = 200
        tx.res.headers.content_type = 'text/plain'
        tx.res.body = b("{0} request for {1}!".format(method, path))

        # Resume transaction
        tx.resume()

    app = wsgi.to_wsgi_app()

    httpd = make_server('', 3000, app)
    httpd.serve_forever()

:mod:`Pyjo.Server.WSGI` allows :mod:`Pyjoyment` applications to run on all ``WSGI``
compatible servers.

Events
------

:mod:`Pyjo.Server.WSGI` inherits all events from :mod:`Pyjo.Server.Base`.

Classes
-------
"""

import Pyjo.Server.Base

from Pyjo.Util import convert


class Pyjo_Server_WSGI(Pyjo.Server.Base.object):
    """
    :mod:`Pyjo.Server.WSGI` inherits all attributes and methods from
    :mod:`Pyjo.Server.Base` and implements the following new ones.
    """

    def run(self, environ):
        """::

            res = psgi.run(environ)

        Run ``WSGI``.
        """
        tx = self.build_tx()
        req = tx.req.parse(environ)
        tx.local_port = environ.get('SERVER_PORT', None)
        tx.remote_address = environ.get('REMOTE_ADDR', None)

        # Request body (may block if we try to read too much)
        length = convert(environ.get('CONTENT_LENGTH', 0), int, 0)
        while not req.is_finished:
            buf_size = length if length and length < 131072 else 131072
            buf = bytearray(buf_size)
            wsgi_input = environ.get('wsgi.input', None)
            if not wsgi_input:
                break
            read = wsgi_input.readinto(buf)
            if not read:
                break
            req.parse(buf[:read])
            length -= read
            if length <= 0:
                break

        self.emit('request', tx)

        # Response headers
        res = tx.res.fix_headers()
        status = f'{res.code or 404} {res.message or res.default_message()}'
        headers_dict = res.headers.to_dict_list()
        headers = []
        for name, value_list in headers_dict.items():
            for value in value_list:
                headers.append(
                    (name, value),
                )

        # WSGI response
        return status, headers, self._body(tx, tx.is_empty)

    def to_wsgi_app(self):
        # Preload application and wrap it
        self.app

        def application(environ, start_response):
            status, headers, body = self.run(environ)
            start_response(status, headers)
            return body

        return application

    def _body(self, tx, empty):
        # Empty
        if empty:
            return

        # No content yet, try again later
        offset = 0
        while True:
            chunk = tx.res.get_body_chunk(offset)
            if chunk is None:
                yield b''
                return

            # End of content
            if not len(chunk):
                return

            offset += len(chunk)
            yield bytes(chunk)


new = Pyjo_Server_WSGI.new
object = Pyjo_Server_WSGI
