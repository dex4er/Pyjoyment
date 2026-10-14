from Pyjo.Test import *

import io
import os
import sys

from unittest.mock import patch


env = {'PATH_INFO': '/foo', 'REQUEST_METHOD': 'GET', 'SCRIPT_NAME': '/', 'HTTP_HOST': 'localhost'}

with subtest('Synopsis'):
    stdout = io.BytesIO()
    with patch.dict(os.environ, env), patch.object(sys, 'stdout', io.TextIOWrapper(stdout, write_through=True)):
        import Pyjo.Server.CGI

        cgi = Pyjo.Server.CGI.new()

        @cgi.unsubscribe('request').on('request')
        def request(cgi, tx):
            # Request
            method = tx.req.method
            path = tx.req.url.path

            # Response
            tx.res.code = 200
            tx.res.headers.content_type = 'text/plain'
            tx.res.body = f'{method} request for {path}!'.encode()

            # Resume transaction
            tx.resume()

        cgi.run()
        output = stdout.getvalue()
    like_ok(output, rb'^Content-Length: 20\r\nContent-Type: text/plain\r\n', 'headers')
    like_ok(output, rb'\r\n\r\nGET request for foo!$', 'content')

with subtest('new'):
    cgi = Pyjo.Server.CGI.new()
    is_ok(cgi.nph, None, 'cgi')
    cgi = Pyjo.Server.CGI.new(nph=True)
    is_ok(cgi.nph, True, 'cgi.nph')

with subtest('nph'):
    boolean = cgi.nph
    is_ok(boolean, True, 'boolean')
    cgi.nph = boolean
    is_ok(cgi.nph, True, 'cgi.nph')

with subtest('run'):
    stdout = io.BytesIO()
    with patch.dict(os.environ, env), patch.object(sys, 'stdout', io.TextIOWrapper(stdout, write_through=True)):
        status = Pyjo.Server.CGI.new().run()
    is_ok(status, 200, 'status')

done_testing()
