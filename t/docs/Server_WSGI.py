from Pyjo.Test import *

import http.client
import io
import threading
import wsgiref.util


def environ(path='/foo'):
    env = {'PATH_INFO': path, 'REQUEST_METHOD': 'GET', 'SCRIPT_NAME': '', 'wsgi.input': io.BytesIO()}
    wsgiref.util.setup_testing_defaults(env)
    return env


with subtest('Synopsis'):
    from Pyjo.Server.WSGI import WSGI

    wsgi = WSGI()

    @wsgi.unsubscribe('request').on('request')
    def request(wsgi, tx):
        # Request
        method = tx.req.method
        path = tx.req.url.path

        # Response
        tx.res.code = 200
        tx.res.headers.content_type = 'text/plain'
        tx.res.body = f'{method} request for {path}!'.encode()

        # Resume transaction
        tx.resume()

    app = wsgi.to_wsgi_app()

    got = []
    body = app(environ(), lambda status, headers, exc_info=None: got.extend([status, headers]))
    is_ok(got[0], '200 OK', 'status')
    is_ok(dict(got[1])['Content-Type'], 'text/plain', 'header')
    is_ok(b''.join(body), b'GET request for /foo!', 'content')
    body.close()

    import Pyjo.Server.WSGI

    wsgi = Pyjo.Server.WSGI.new()

    # F811 "Redefinition of unused `request`": the synopsis defines it in both forms
    @wsgi.unsubscribe('request').on('request')
    def request(wsgi, tx):  # noqa: F811
        # Request
        method = tx.req.method
        path = tx.req.url.path

        # Response
        tx.res.code = 200
        tx.res.headers.content_type = 'text/plain'
        tx.res.body = f'{method} request for {path}!'.encode()

        # Resume transaction
        tx.resume()

    app = wsgi.to_wsgi_app()

    got = []
    body = app(environ(), lambda status, headers, exc_info=None: got.extend([status, headers]))
    is_ok(got[0], '200 OK', 'status')
    is_ok(dict(got[1])['Content-Type'], 'text/plain', 'header')
    is_ok(b''.join(body), b'GET request for /foo!', 'content')
    body.close()

with subtest('Description'):
    import wsgiref.simple_server

    # Serve with the server of wsgiref, on a free port and in a thread here
    class QuietHandler(wsgiref.simple_server.WSGIRequestHandler):
        def log_message(self, *args):
            pass

    httpd = wsgiref.simple_server.make_server('127.0.0.1', 0, app, handler_class=QuietHandler)
    thread = threading.Thread(target=httpd.serve_forever)
    thread.start()
    conn = http.client.HTTPConnection('127.0.0.1', httpd.server_address[1], timeout=10)
    conn.request('GET', '/bar')
    is_ok(conn.getresponse().read(), b'GET request for /bar!', 'served')
    conn.close()
    httpd.shutdown()
    httpd.server_close()
    thread.join()

with subtest('run'):
    status, headers, body = wsgi.run(environ('/baz'))
    is_ok(status, '200 OK', 'status')
    ok(len(headers), 'headers')
    is_ok(b''.join(body), b'GET request for /baz!', 'body')
    body.close()

with subtest('to_wsgi_app'):
    app = wsgi.to_wsgi_app()
    ok(callable(app), 'application')

done_testing()
