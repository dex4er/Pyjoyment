import Pyjo.Server.Prethread
import Pyjoyment
import Pyjoyment.Command.prethread

from Pyjo.Test import *

import contextlib
import io
import os
import re

from unittest.mock import patch


with subtest('Synopsis'):
    app = Pyjoyment.new()
    prethread = Pyjoyment.Command.prethread.new(app=app)
    like_ok(prethread.usage, r'^Usage: APPLICATION prethread \[OPTIONS\]\n\n  \./myapp\.py prethread\n', 'usage')
    server = prethread.build_server('-p', '-l', 'http://*:8080')
    is_deeply_ok(server.listen, ['http://*:8080'], 'listen')
    ok(server.reverse_proxy, 'proxy')
    server = prethread.build_server('-l', 'http://127.0.0.1:8080', '-p', '127.0.0.0/8', '-p', 'fc00::/7')
    is_deeply_ok(server.trusted_proxies, ['127.0.0.0/8', 'fc00::/7'], 'trusted proxies')
    server = prethread.build_server('-b', '5', '-c', '10', '-i', '20', '-k', '3', '-r', '50')
    is_deeply_ok(
        [server.backlog, server.max_clients, server.inactivity_timeout, server.keep_alive_timeout, server.max_requests],
        [5, 10, 20, 3, 50],
        'options',
    )
    server = prethread.build_server(
        '-a', '7', '-G', '9', '-I', '2', '-H', '8', '-P', '/tmp/p.pid', '-s', '1', '-w', '12'
    )
    is_deeply_ok(
        [server.accepts, server.graceful_timeout, server.heartbeat_interval, server.heartbeat_timeout, server.spare],
        [7, 9, 2, 8, 1],
        'options of prethread',
    )
    is_ok(server.pid_file, '/tmp/p.pid', 'pid file')
    is_ok(server.workers, 12, 'workers')
    isa_ok(server, Pyjo.Server.Prethread.object, 'server')

with subtest('Description'):
    # PYJO_GRACEFUL_TIMEOUT=8 PYJO_WORKERS=2 ./myapp.py prethread
    with patch.dict(os.environ, {'PYJO_GRACEFUL_TIMEOUT': '8', 'PYJO_WORKERS': '2'}):
        server = prethread.build_server()
        is_deeply_ok([server.graceful_timeout, server.workers], [8, 2], 'options of the environment')
        is_ok(prethread.build_server('-w', '3').workers, 3, 'command line first')

with subtest('Attributes'):
    prethread = Pyjoyment.Command.prethread.new()
    like_ok(prethread.description, r'Start application', 'description')
    prethread.usage = 'Foo'
    is_ok(prethread.usage, 'Foo', 'usage')

with subtest('build_server'):
    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr):
        throws_ok(
            lambda: Pyjoyment.Command.prethread.new().build_server('--unknown'),
            re.compile(r'^Usage: APPLICATION prethread'),
            'usage',
        )
    like_ok(stderr.getvalue(), r'^Unknown option: unknown', 'warning')

done_testing()
