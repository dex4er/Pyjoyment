import Pyjoyment
import Pyjoyment.Command.prefork

from Pyjo.Test import *

import contextlib
import io
import re


with subtest('Synopsis'):
    app = Pyjoyment.new()
    prefork = Pyjoyment.Command.prefork.new(app=app)
    like_ok(prefork.usage, r'^Usage: APPLICATION prefork \[OPTIONS\]\n\n  \./myapp\.py prefork\n', 'usage')
    server = prefork.build_server('-p', '-l', 'http://*:8080')
    is_deeply_ok(server.listen, ['http://*:8080'], 'listen')
    ok(server.reverse_proxy, 'proxy')
    server = prefork.build_server('-l', 'http://127.0.0.1:8080', '-p', '127.0.0.0/8', '-p', 'fc00::/7')
    is_deeply_ok(server.trusted_proxies, ['127.0.0.0/8', 'fc00::/7'], 'trusted proxies')
    server = prefork.build_server('-b', '5', '-c', '10', '-i', '20', '-k', '3', '-r', '50')
    is_deeply_ok(
        [server.backlog, server.max_clients, server.inactivity_timeout, server.keep_alive_timeout, server.max_requests],
        [5, 10, 20, 3, 50],
        'options',
    )
    server = prefork.build_server('-a', '7', '-G', '9', '-I', '2', '-H', '8', '-P', '/tmp/p.pid', '-s', '1', '-w', '12')
    is_deeply_ok(
        [server.accepts, server.graceful_timeout, server.heartbeat_interval, server.heartbeat_timeout, server.spare],
        [7, 9, 2, 8, 1],
        'options of prefork',
    )
    is_ok(server.pid_file, '/tmp/p.pid', 'pid file')
    is_ok(server.workers, 12, 'workers')

with subtest('Attributes'):
    prefork = Pyjoyment.Command.prefork.new()
    like_ok(prefork.description, r'Start application', 'description')
    prefork.usage = 'Foo'
    is_ok(prefork.usage, 'Foo', 'usage')

with subtest('build_server'):
    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr):
        throws_ok(
            lambda: Pyjoyment.Command.prefork.new().build_server('--unknown'),
            re.compile(r'^Usage: APPLICATION prefork'),
            'usage',
        )
    like_ok(stderr.getvalue(), r'^Unknown option: unknown', 'warning')

done_testing()
