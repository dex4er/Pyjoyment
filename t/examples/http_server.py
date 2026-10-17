from Pyjo.File import curfile
from Pyjo.Test import *

import importlib
import sys
import tempfile


# The script of examples/http_server.py, in a process of its own, as it runs its server, on a free port
sys.path.insert(0, curfile().dirname().sibling('lib').to_str())
ServerProcess = importlib.import_module('ServerProcess')

script = curfile().dirname().dirname().sibling('examples', 'http_server.py').to_str()

with tempfile.TemporaryDirectory() as dir:
    server = ServerProcess.Server(dir, [sys.executable, script, 'address=127.0.0.1', 'port={port}'])
    try:
        with subtest('Embedded template file'):
            status, headers, body = server.request('GET', '/foo')
            is_ok(status, 200, 'right status')
            is_ok(headers['Content-Type'], 'text/html; charset=utf-8', 'right type')
            like_ok(body.decode(), r'<h1>♥ Pyjoyment ♥</h1>', 'right heading')
            like_ok(body.decode(), r'<p>GET request for /foo</p>', 'right request')
    except Exception:
        diag(server.output())
        raise
    finally:
        server.close()

done_testing()
