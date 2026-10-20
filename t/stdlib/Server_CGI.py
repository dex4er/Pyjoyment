import Pyjo.Message.Response

from Pyjo.File import tempdir
from Pyjo.Test import *

import os
import subprocess
import sys


# A CGI script in a process of its own, with the environment and the standard input of a CGI server
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SCRIPT = """
import Pyjo.IOLoop
import Pyjo.Server.CGI

cgi = Pyjo.Server.CGI.new()


@cgi.unsubscribe('request').on('request')
def request(cgi, tx):
    if tx.req.url.path.to_route() == '/later':
        tx.res.code = 200
        tx.res.content.write_chunk(b'Hello ')
        Pyjo.IOLoop.timer(0.1, lambda loop: tx.res.content.write_chunk(b'World!').write_chunk(b''))
        return tx.resume()
    tx.res.code = 201
    tx.res.headers.content_type = 'text/plain'
    tx.res.body = f'{tx.req.method} {tx.req.url.to_abs()} {tx.req.params.to_dict()} {tx.remote_address}'.encode()
    tx.resume()


cgi.run()
"""

script = tempdir().child('app.py').spew(SCRIPT)


def cgi(env, content=b''):
    env = {
        'PATH': os.environ.get('PATH', ''),
        # Windows, which a CGI server gives its programs, as Python cannot start its sockets without it
        **({'SYSTEMROOT': os.environ['SYSTEMROOT']} if sys.platform == 'win32' else {}),
        'PYTHONPATH': ROOT,
        'GATEWAY_INTERFACE': 'CGI/1.1',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '8080',
        'REMOTE_ADDR': '192.0.2.1',
        'SCRIPT_NAME': '/cgi-bin/app.py',
        'HTTP_HOST': 'localhost:8080',
        **env,
    }
    process = subprocess.run([sys.executable, script.to_str()], env=env, input=content, capture_output=True, timeout=30)
    return process.returncode, Pyjo.Message.Response.new().parse(b'HTTP/1.1 200 OK\r\n' + process.stdout)


with subtest('GET'):
    code, res = cgi({'REQUEST_METHOD': 'GET', 'PATH_INFO': '/foo', 'QUERY_STRING': 'a=1'})
    is_ok(code, 0, 'exit status')
    is_ok(res.headers.status, '201 Created', 'status of the response')
    is_ok(res.headers.content_type, 'text/plain', 'right "Content-Type" value')
    is_ok(res.body, b"GET http://localhost:8080/cgi-bin/app.py/foo?a=1 {'a': '1'} 192.0.2.1", 'right content')

with subtest('POST with a form'):
    content = b'x=1&y=2'
    code, res = cgi(
        {
            'REQUEST_METHOD': 'POST',
            'PATH_INFO': '/form',
            'CONTENT_TYPE': 'application/x-www-form-urlencoded',
            'CONTENT_LENGTH': str(len(content)),
        },
        content,
    )
    is_ok(code, 0, 'exit status')
    is_ok(res.body, b"POST http://localhost:8080/cgi-bin/app.py/form {'x': '1', 'y': '2'} 192.0.2.1", 'right content')

with subtest('Content given later'):
    code, res = cgi({'REQUEST_METHOD': 'GET', 'PATH_INFO': '/later'})
    is_ok(code, 0, 'exit status')
    is_ok(res.headers.status, '200 OK', 'status of the response')
    is_ok(res.body, b'Hello World!', 'right content')

done_testing()
