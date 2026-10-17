import Pyjoyment
import Pyjoyment.Command.cgi

from Pyjo.Test import *

import io
import os
import sys

from unittest.mock import patch


with subtest('Synopsis'):
    cgi = Pyjoyment.Command.cgi.new()
    like_ok(cgi.usage, r'^Usage: APPLICATION cgi \[OPTIONS\]\n\n  \./myapp\.py cgi\n', 'usage')
    like_ok(cgi.usage, r'--nph', 'option')

with subtest('Attributes'):
    cgi = Pyjoyment.Command.cgi.new()
    is_ok(cgi.description, 'Start application with CGI', 'description')

with subtest('run'):
    app = Pyjoyment.new()
    app.log.level = 'fatal'
    app.routes.get('/', {'text': 'Hello CGI!'})
    environ = {'PATH_INFO': '/', 'REQUEST_METHOD': 'GET', 'SERVER_PROTOCOL': 'HTTP/1.1'}
    buffer = io.BytesIO()
    with (
        patch.dict(os.environ, environ),
        patch.object(sys, 'stdin', io.TextIOWrapper(io.BytesIO())),
        patch.object(sys, 'stdout', io.TextIOWrapper(buffer, write_through=True)),
    ):
        status = Pyjoyment.Command.cgi.new(app=app).run()
        output = buffer.getvalue()
    is_ok(status, 200, 'status')
    like_ok(output.decode(), r'Hello CGI!', 'output')

done_testing()
