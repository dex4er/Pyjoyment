import Pyjo.Content.Single
import Pyjo.File
import Pyjo.Headers
import Pyjo.IOLoop
import Pyjo.Message.Request
import Pyjo.Message.Response
import Pyjo.Server.Daemon
import Pyjo.Server.Prefork
import Pyjo.Test.Pyjo
import Pyjo.UserAgent
import Pyjoyment

from Pyjo.Test import *

import os
import subprocess
import sys

from unittest.mock import patch


# The snippets of docs/guides/faq.rst, copied, with print and the comments that show a result turned into assertions
ROOT = Pyjo.File.curfile().dirname().dirname().dirname().to_str()

# The remote service of the examples, which an application of the test answers in its place, as the tests do not use
# the network
remote = Pyjoyment.new()
remote.log.level = 'fatal'


@remote.routes.get('/')
def index(c):
    c.render(inline='<html><head><title>Pyjoyment documentation</title></head></html>')


def local(ua, port):
    # The requests of the user agent go to the application of the test
    @ua.on('start')
    def start(ua, tx):
        url = tx.req.url
        url.scheme, url.host, url.port = 'http', '127.0.0.1', port


with subtest('Where did my file extension go?'):
    app = Pyjoyment.new()
    app.log.level = 'fatal'
    r = app.routes
    r.get('/foo').to(cb=lambda c: c.render(text='foo'))
    r.get('/bar', format=['html']).to(cb=lambda c: c.render(text=f'bar {c.stash("format")}'))
    r.get('/baz/#name').to(cb=lambda c: c.render(text=f'baz {c.param("name")}'))
    t = Pyjo.Test.Pyjo.new(app)
    t.get_ok('/foo.html').status_is(404)
    t.get_ok('/bar.html').status_is(200).content_is('bar html')
    t.get_ok('/baz/index.html').status_is(200).content_is('baz index.html')

with subtest('Can I configure Hot from the command line?'):
    tmp = Pyjo.File.tempdir()
    conf = tmp.child('myapp.conf').spew(
        """{
    'hot': {
        'listen': ['http://*:8080'],
        'workers': 10,
    }
}
"""
    )
    app = Pyjoyment.new()
    config = app.plugin('Config', {'file': conf.to_str()})
    is_deeply_ok(config['hot'], {'listen': ['http://*:8080'], 'workers': 10}, 'settings')

    # The command builds its server, which the hook of the script shows instead of running it
    script = tmp.child('myapp.py').spew(
        """from Pyjoyment.Lite import *

import sys


@app.hook('before_command')
def before_command(command, args):
    server = command.build_server(*args)
    print(app.mode, server.listen, server.workers)
    sys.exit()


app.start()
"""
    )
    env = {**os.environ, 'PYTHONPATH': ROOT}
    for name in ('PYJO_HOME', 'PYJO_LISTEN', 'PYJO_MODE', 'PYJO_WORKERS', 'PORT'):
        env.pop(name, None)
    result = subprocess.run(
        [sys.executable, script.to_str(), 'prefork', '-m', 'production', '-l', 'http://*:8080', '-w', '10'],
        capture_output=True,
        env=env,
        text=True,
        timeout=60,
    )
    is_ok(result.stdout, "production ['http://*:8080'] 10\n", 'production mode, listen location and workers')
    is_ok(result.returncode, 0, 'exit status')

with subtest('What does the error "...certificate verify failed" mean?'):
    app = Pyjoyment.new()
    app.log.level = 'fatal'
    app.routes.get('/').to(cb=lambda c: c.render(text='secure'))
    with Pyjo.Server.Daemon.new(app=app, listen=['https://127.0.0.1'], silent=True) as daemon:
        port = daemon.start().ports()[0]
        results = []

        def done(ua, tx):
            results.append(tx.error['message'] if tx.error else tx.res.text)
            Pyjo.IOLoop.stop()

        with Pyjo.UserAgent.new() as ua:
            ua.get(f'https://127.0.0.1:{port}', done)
            Pyjo.IOLoop.start()
        with Pyjo.UserAgent.new(insecure=True) as ua:
            ua.get(f'https://127.0.0.1:{port}', done)
            Pyjo.IOLoop.start()
        with patch.dict(os.environ, PYJO_INSECURE='1'), Pyjo.UserAgent.new() as ua:
            ok(ua.insecure, 'insecure from the environment variable')
    like_ok(results[0], r'certificate verify failed', 'invalid certificate')
    is_ok(results[1], 'secure', 'verification disabled')

with subtest('What does the error "Maximum message size exceeded" mean?'):
    app = Pyjoyment.new()
    is_ok(app.max_request_size, None, 'defaults to the limit of the message')
    is_ok(Pyjo.Message.Request.new().max_message_size, 16777216, '16MiB for requests')
    is_ok(Pyjo.UserAgent.new().max_response_size, None, 'defaults to the limit of the message')
    is_ok(Pyjo.Message.Response.new().max_message_size, 2147483648, '2GiB for responses')
    app.log.level = 'fatal'
    app.max_request_size = 1024
    app.routes.post('/').to(cb=lambda c: c.render(text=c.req.error['message'] if c.req.error else 'ok'))
    t = Pyjo.Test.Pyjo.new(app)
    t.post_ok('/', '1234' * 1024).status_is(200).header_is('Connection', 'close')
    t.content_is('Maximum message size exceeded')

with subtest('What does the error "Maximum start-line size exceeded" mean?'):
    is_ok(Pyjo.Message.Request.new().max_line_size, 8192, '8KiB')
    with patch.dict(os.environ, PYJO_MAX_LINE_SIZE='16'):
        req = Pyjo.Message.Request.new().parse(f'GET /{"a" * 16} HTTP/1.1\x0d\x0a'.encode())
    is_ok(req.error['message'], 'Maximum start-line size exceeded', 'right error')

with subtest('What does the error "Maximum header size exceeded" mean?'):
    is_ok(Pyjo.Headers.new().max_lines, 100, '100 headers')
    is_ok(Pyjo.Headers.new().max_line_size, 8192, '8KiB each')
    with patch.dict(os.environ, PYJO_MAX_LINES='1'):
        req = Pyjo.Message.Request.new().parse(b'GET / HTTP/1.1\x0d\x0aA: 1\x0d\x0aB: 2\x0d\x0a')
    is_ok(req.error['message'], 'Maximum header size exceeded', 'right error')

with subtest('What does the error "Maximum buffer size exceeded" mean?'):
    is_ok(Pyjo.Content.Single.new().max_buffer_size, 262144, 'around 256KiB')
    with patch.dict(os.environ, PYJO_MAX_BUFFER_SIZE='12'):
        req = Pyjo.Message.Request.new().parse(b'POST / HTTP/1.1\x0d\x0aTransfer-Encoding: chunked\x0d\x0a\x0d\x0a')
        req.parse(b'a' * 1000)
    is_ok(req.error['message'], 'Maximum buffer size exceeded', 'right error')

with subtest('What does "Your secret passphrase needs to be changed" mean?'):
    app = Pyjoyment.new()
    is_deeply_ok(app.secrets, [app.moniker], 'moniker')
    app.secrets = ['My very secret passphrase.']
    is_deeply_ok(app.secrets, ['My very secret passphrase.'], 'changed')

with subtest('What does "Inactivity timeout" mean?'):
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop('PYJO_INACTIVITY_TIMEOUT', None)
        is_ok(Pyjo.UserAgent.new().inactivity_timeout, 40, 'user agent')
        is_ok(Pyjo.Server.Daemon.new().inactivity_timeout, 30, 'web server')

with subtest('What does "Premature connection close" mean?'):
    with Pyjo.Server.Daemon.new(app=remote, listen=['http://127.0.0.1'], silent=True) as daemon:
        port = daemon.start().ports()[0]
        errors = []
        new = Pyjo.UserAgent.new

        def ua_new(*args, **kwargs):
            ua = new(*args, **kwargs)
            local(ua, port)
            return ua

        # The user agent of the example, whose requests go to the application of the test, and whose callback records
        # the error, where the example prints the title, which a destroyed user agent never gets
        with patch.object(Pyjo.UserAgent, 'new', ua_new):
            # The variable ua goes out of scope and gets destroyed too early
            # The timer of the example without its delay
            @Pyjo.IOLoop.timer(0)
            def visit(loop):
                ua = Pyjo.UserAgent.new()
                ua.get('https://pyjoyment.readthedocs.io', lambda ua, tx: errors.append(tx.error))

            Pyjo.IOLoop.timer(0.5, lambda loop: loop.stop())
            Pyjo.IOLoop.start()
    if sys.implementation.name == 'pypy':
        skip('PyPy frees the user agent only when its garbage collector runs', 1)
    else:
        is_deeply_ok(errors, [{'message': 'Premature connection close'}], 'right error')

with subtest('What does "Worker 31842 has no heartbeat (50 seconds), restarting" mean?'):
    is_ok(Pyjo.Server.Prefork.new().heartbeat_timeout, 50, '50 seconds')

with subtest('What does "Transaction already destroyed" mean?'):
    app = Pyjoyment.new()
    app.log.level = 'fatal'

    @app.routes.get('/visit')
    def visit(c):
        # Keep a strong reference to the transaction object
        tx = c.render_later().tx

        def visited(res):
            c.render(text='Visited pyjoyment.readthedocs.io')

        def failed(err):
            tx
            c.reply.exception(err)

        c.ua().get_p('https://pyjoyment.readthedocs.io').then(visited).catch(failed)

    with Pyjo.Server.Daemon.new(app=remote, listen=['http://127.0.0.1'], silent=True) as daemon:
        local(app.ua, daemon.start().ports()[0])
        t = Pyjo.Test.Pyjo.new(app)
        t.get_ok('/visit').status_is(200).content_is('Visited pyjoyment.readthedocs.io')

done_testing()
