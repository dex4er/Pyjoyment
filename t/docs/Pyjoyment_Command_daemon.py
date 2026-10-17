import Pyjoyment
import Pyjoyment.Command.daemon

from Pyjo.Test import *

import contextlib
import io
import re


with subtest('Synopsis'):
    app = Pyjoyment.new()
    daemon = Pyjoyment.Command.daemon.new(app=app)
    like_ok(daemon.usage, r'^Usage: APPLICATION daemon \[OPTIONS\]\n\n  \./myapp\.py daemon\n', 'usage')
    server = daemon.build_server('-p', '-l', 'http://*:8080')
    is_deeply_ok(server.listen, ['http://*:8080'], 'listen')
    ok(server.reverse_proxy, 'proxy')
    server = daemon.build_server('-l', 'http://127.0.0.1:8080', '-p', '127.0.0.0/8', '-p', 'fc00::/7')
    is_deeply_ok(server.trusted_proxies, ['127.0.0.0/8', 'fc00::/7'], 'trusted proxies')
    server = daemon.build_server('-b', '5', '-c', '10', '-i', '20', '-k', '3', '-r', '50')
    is_deeply_ok(
        [server.backlog, server.max_clients, server.inactivity_timeout, server.keep_alive_timeout, server.max_requests],
        [5, 10, 20, 3, 50],
        'options',
    )

with subtest('Attributes'):
    daemon = Pyjoyment.Command.daemon.new()
    like_ok(daemon.description, r'Start application', 'description')
    daemon.usage = 'Foo'
    is_ok(daemon.usage, 'Foo', 'usage')

with subtest('build_server'):
    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr):
        throws_ok(
            lambda: Pyjoyment.Command.daemon.new().build_server('--unknown'),
            re.compile(r'^Usage: APPLICATION daemon'),
            'usage',
        )
    like_ok(stderr.getvalue(), r'^Unknown option: unknown', 'warning')

done_testing()
