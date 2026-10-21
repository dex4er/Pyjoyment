import Pyjo.App.FastCGI
import Pyjo.Reactor
import Pyjo.Test.Pyjo
import Pyjoyment

from Pyjo.Test import *
from Pyjo.Util import url_escape

import glob
import importlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time


# The applications of other frameworks, which Pyjoyment.Plugin.Mount mounts, of the dependency group "servers": uv run
# --only-group servers python -m Pyjo.Prove t/servers
if missing := [m for m in ('flask', 'starlette', 'waitress') if not importlib.util.find_spec(m)]:
    plan(skip_all=f'needs the dependency group "servers", without {", ".join(missing)}')

import flask  # noqa: E402
import starlette.applications  # noqa: E402
import starlette.responses  # noqa: E402
import starlette.routing  # noqa: E402


# The servers in processes of their own
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
Server = importlib.import_module('ServerProcess').Server

# The examples of an application of Pyjoyment on WSGI and on ASGI, mounted in an application of Pyjoyment.Lite, on the
# WSGI and the ASGI servers
EXAMPLE = os.path.join(os.path.dirname(__file__), '..', '..', 'examples', 'pyjoyment', 'mount_wsgi_inception.py')
EXAMPLE_ASGI = os.path.join(os.path.dirname(__file__), '..', '..', 'examples', 'pyjoyment', 'mount_asgi_inception.py')

# The script of PHP of the example of php-fpm, which a FastCGI application runs, and php-fpm, as it is on PATH, as
# Debian names it with its version, or as Homebrew installs it
PHP = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'examples', 'pyjoyment', 'php', 'index.php'))
PHP_FPM = shutil.which('php-fpm') or next(
    (
        path
        for path in (*sorted(glob.glob('/usr/sbin/php-fpm*'), reverse=True), '/opt/homebrew/opt/php/sbin/php-fpm')
        if os.access(path, os.X_OK)
    ),
    None,
)
PYTHON = sys.executable
UWSGI = shutil.which('uwsgi', path=os.path.dirname(sys.executable))
GUNICORN = [PYTHON, '-m', 'gunicorn', 'served:application', '--bind', '127.0.0.1:{port}']
# The servers, and wsgi.multithread, wsgi.multiprocess and wsgi.run_once that they set
SERVERS = [
    ('Gunicorn', importlib.util.find_spec('gunicorn'), GUNICORN, [False, False, False]),
    (
        'Gunicorn with threads',
        importlib.util.find_spec('gunicorn'),
        [*GUNICORN, '--threads', '4'],
        [True, False, False],
    ),
    (
        'Gunicorn with workers',
        importlib.util.find_spec('gunicorn'),
        [*GUNICORN, '--workers', '2'],
        [False, True, False],
    ),
    (
        'uWSGI',
        UWSGI,
        [UWSGI, '--http-socket', '127.0.0.1:{port}', '--module', 'served:application'],
        [False, False, False],
    ),
    (
        'Waitress',
        True,
        [PYTHON, '-m', 'waitress', '--listen=127.0.0.1:{port}', 'served:application'],
        [True, False, False],
    ),
    (
        'Werkzeug',
        importlib.util.find_spec('werkzeug'),
        [
            PYTHON,
            '-c',
            'from werkzeug.serving import run_simple; from served import application; '
            "run_simple('127.0.0.1', {port}, application, threaded=True)",
        ],
        [True, False, False],
    ),
]
LOCAL = ['--host', '127.0.0.1', '--port', '{port}']
ASGI_SERVERS = [
    ('uvicorn', 'uvicorn', [PYTHON, '-m', 'uvicorn', 'served_asgi:application', '--log-level', 'warning', *LOCAL]),
    (
        'uvicorn on uvloop',
        'uvloop',
        [PYTHON, '-m', 'uvicorn', 'served_asgi:application', '--loop', 'uvloop', '--log-level', 'warning', *LOCAL],
    ),
    ('Hypercorn', 'hypercorn', [PYTHON, '-m', 'hypercorn', 'served_asgi:application', '--bind', '127.0.0.1:{port}']),
    ('Daphne', 'daphne', [PYTHON, '-m', 'daphne', '-b', '127.0.0.1', '-p', '{port}', 'served_asgi:application']),
    ('Granian', 'granian', [PYTHON, '-m', 'granian', '--interface', 'asgi', 'served_asgi:application', *LOCAL]),
]


def application(prefix, wsgi):
    app = Pyjoyment.new()
    app.log.level = 'fatal'
    app.routes.get('/').to(cb=lambda c: c.render(text='Hello from Pyjoyment!'))
    app.plugin('Mount', {prefix: wsgi})
    return app


with subtest('Flask'):
    hello = flask.Flask('hello')
    hello.logger.disabled = True

    @hello.get('/')
    def index():
        return f'Hello from Flask at {flask.url_for("index")}!'

    @hello.get('/hello/<name>')
    def name(name):
        return {'name': name, 'url': flask.url_for('name', name=name, _external=True)}

    @hello.post('/form')
    def form():
        return f'{flask.request.form["foo"]} and {flask.request.files["file"].read().decode()}'

    @hello.get('/redirect')
    def redirect():
        return flask.redirect(flask.url_for('index'))

    @hello.get('/stream')
    def stream():
        def body():
            yield 'one'
            yield 'two'

        return flask.Response(flask.stream_with_context(body()), mimetype='text/plain')

    @hello.get('/fail')
    def fail():
        raise RuntimeError('Something went wrong')

    t = Pyjo.Test.Pyjo.new(application('/flask', hello))
    t.get_ok('/').status_is(200).content_is('Hello from Pyjoyment!')
    t.get_ok('/flask/').status_is(200).content_is('Hello from Flask at /flask/!')
    t.get_ok('/flask/hello/%E2%99%A5').status_is(200).json_is('/name', '♥')
    t.json_like('/url', r'^http://127\.0\.0\.1:\d+/flask/hello/%E2%99%A5$')
    t.post_ok('/flask/form', form={'foo': 'bar', 'file': {'content': 'Hello!', 'filename': 'hello.txt'}})
    t.status_is(200).content_is('bar and Hello!')
    t.get_ok('/flask/redirect').status_is(302).header_is('Location', '/flask/')
    t.get_ok('/flask/stream').status_is(200).content_type_like(r'^text/plain').content_is('onetwo')
    t.get_ok('/flask/missing').status_is(404).content_like(r'Not Found')
    t.get_ok('/flask/fail').status_is(500).content_like(r'Internal Server Error')

with subtest('Starlette'):

    async def index(request):
        return starlette.responses.PlainTextResponse(f'Hello from Starlette at {request.url_for("index").path}!')

    async def name(request):
        name = request.path_params['name']
        return starlette.responses.JSONResponse({'name': name, 'url': str(request.url_for('name', name=name))})

    async def echo(request):
        return starlette.responses.PlainTextResponse(
            f'{(await request.body()).decode()} and {request.query_params["x"]}'
        )

    async def redirect(request):
        return starlette.responses.RedirectResponse(request.url_for('index').path)

    async def stream(request):
        async def body():
            yield 'one'
            yield 'two'

        return starlette.responses.StreamingResponse(body(), media_type='text/plain')

    async def fail(request):
        raise RuntimeError('Something went wrong')

    hello = starlette.applications.Starlette(
        routes=[
            starlette.routing.Route('/', index, name='index'),
            starlette.routing.Route('/hello/{name}', name, name='name'),
            starlette.routing.Route('/echo', echo, methods=['POST']),
            starlette.routing.Route('/redirect', redirect),
            starlette.routing.Route('/stream', stream),
            starlette.routing.Route('/fail', fail),
        ]
    )

    t = Pyjo.Test.Pyjo.new(application('/starlette', hello))
    t.app.log.level = 'fatal'
    t.get_ok('/').status_is(200).content_is('Hello from Pyjoyment!')
    t.get_ok('/starlette/').status_is(200).content_is('Hello from Starlette at /starlette/!')
    t.get_ok('/starlette/hello/%E2%99%A5').status_is(200).json_is('/name', '♥')
    # Starlette does not escape a parameter of the path in url_for
    t.json_like('/url', r'^http://127\.0\.0\.1:\d+/starlette/hello/♥$')
    t.post_ok('/starlette/echo?x=1', b'Hello!').status_is(200).content_is('Hello! and 1')
    t.get_ok('/starlette/redirect').status_is(307).header_is('Location', '/starlette/')
    t.get_ok('/starlette/stream').status_is(200).content_type_like(r'^text/plain').content_is('onetwo')
    t.get_ok('/starlette/missing').status_is(404).content_like(r'Not Found')
    t.get_ok('/starlette/fail').status_is(500).content_like(r'Internal Server Error')

with subtest('PHP on php-fpm'):
    if PHP_FPM is None or sys.platform == 'win32':
        skip('needs php-fpm', 1)
    else:
        with tempfile.TemporaryDirectory() as dir:
            # A pool on a UNIX domain socket of the temporary directory, which takes no port
            sock = os.path.join(dir, 'fpm.sock')
            conf = os.path.join(dir, 'php-fpm.conf')
            with open(conf, 'w') as file:
                file.write(
                    f'[global]\nerror_log = /dev/stderr\ndaemonize = no\n\n'
                    f'[www]\nlisten = {sock}\npm = static\npm.max_children = 2\n'
                )
            with open(os.path.join(dir, 'php-fpm.log'), 'w+') as log:
                fpm = subprocess.Popen([PHP_FPM, '-n', '-y', conf, '-F'], stdout=log, stderr=subprocess.STDOUT)
                try:
                    deadline = time.monotonic() + 10
                    while not os.path.exists(sock) and fpm.poll() is None and time.monotonic() < deadline:
                        time.sleep(0.05)

                    location = f'fcgi+unix://{url_escape(sock, rb"^A-Za-z0-9\-._~")}'
                    php = Pyjo.App.FastCGI.new(
                        url=location, env={'SCRIPT_FILENAME': PHP, 'DOCUMENT_ROOT': os.path.dirname(PHP)}
                    )
                    t = Pyjo.Test.Pyjo.new(application('/php', php))
                    t.get_ok('/php/foo/bar?x=1').status_is(200).content_type_like(r'^text/plain')
                    t.content_is('Hello PHP at /php for /foo/bar (GET /php/foo/bar?x=1)!\n')
                    t.header_like('X-Powered-By', r'^PHP/')
                    t.get_ok('/php').status_is(200).content_is('Hello PHP at /php for / (GET /php)!\n')
                    t.post_ok('/php/form', form={'a': '1'}).status_is(200)
                    t.content_is('Hello PHP at /php for /form (POST /php/form)!\n')
                    t.get_ok('/php/events').status_is(200).content_type_like(r'^text/event-stream')
                    t.content_is('data: 0\n\ndata: 1\n\ndata: 2\n\n')

                    # The scripts of the directory of the example
                    php = Pyjo.App.FastCGI.new(url=location, document_root=os.path.dirname(PHP))
                    t = Pyjo.Test.Pyjo.new(application('/php', php))
                    t.get_ok('/php/').status_is(200).content_is('Hello PHP at /php/index.php for  (GET /php/)!\n')
                    t.get_ok('/php/index.php/events').status_is(200).content_type_like(r'^text/event-stream')
                    t.content_is('data: 0\n\ndata: 1\n\ndata: 2\n\n')
                    t.get_ok('/php/phpinfo.php').status_is(200).content_like(r'<title>PHP [\d.]+ - phpinfo\(\)</title>')
                    t.get_ok('/php/missing.php').status_is(404)
                except Exception:
                    log.seek(0)
                    diag(log.read())
                    raise
                finally:
                    fpm.terminate()
                    fpm.wait(10)

with tempfile.TemporaryDirectory() as dir:
    shutil.copy(EXAMPLE, os.path.join(dir, 'inception.py'))

    # The example, with a WSGI application that gives the flags of the WSGI server, which the servers run
    with open(os.path.join(dir, 'served.py'), 'w') as file:
        file.write("""\
import json

from inception import app, application


def flags(environ, start_response):
    start_response('200 OK', [('Content-Type', 'application/json')])
    keys = ('wsgi.multithread', 'wsgi.multiprocess', 'wsgi.run_once')
    return [json.dumps([bool(environ[key]) for key in keys]).encode()]


app.plugin('Mount', {'/flags': flags})
""")

    for name, available, command, model in SERVERS:
        if not available:
            continue

        with subtest(f'Pyjoyment on WSGI mounted in Pyjoyment.Lite on {name}'):
            os.environ['PYJO_WSGI'] = '1'
            try:
                server = Server(dir, command)
            finally:
                del os.environ['PYJO_WSGI']
            try:
                status, headers, body = server.request('GET', '/')
                is_ok(status, 200, 'right status')
                is_ok(body, 'I ♥ Pyjoyment!'.encode(), 'right content')

                status, headers, body = server.request('GET', '/wsgi')
                is_ok(status, 200, 'right status')
                is_ok(body, b'Hello Pyjoyment at /wsgi on WSGI!', 'right content')

                status, headers, body = server.request('GET', '/wsgi/pyjo/pyjo.css')
                is_ok(status, 200, 'right status')
                is_ok(headers['Content-Type'], 'text/css', 'static file')

                status, headers, body = server.request('GET', '/wsgi/foo')
                is_ok(status, 404, 'not found')

                # The flags of the WSGI server for the WSGI application mounted in the application of Pyjoyment
                status, headers, body = server.request('GET', '/flags')
                is_ok(status, 200, 'right status')
                is_deeply_ok(json.loads(body), model, 'flags of the WSGI server')
            except Exception:
                diag(server.output())
                raise
            finally:
                server.close()

    shutil.copy(EXAMPLE_ASGI, os.path.join(dir, 'inception_asgi.py'))

    # The example, with routes of the inner application whose response and chunks come from timers of the event loop of
    # the ASGI server
    with open(os.path.join(dir, 'served_asgi.py'), 'w') as file:
        file.write("""\
import Pyjo.IOLoop

from inception_asgi import application, hello


@hello.routes.get('/later')
def later(c):
    c.render_later()
    Pyjo.IOLoop.timer(0.01, lambda loop: c.render(text='Hello later!'))


@hello.routes.get('/chunks')
def chunks(c):
    def write(n):
        if n < 3:
            Pyjo.IOLoop.timer(0.01, lambda loop: c.write_chunk(f'{n}'.encode(), lambda c: write(n + 1)))
        else:
            c.finish()

    write(0)
""")

    for name, module, command in ASGI_SERVERS:
        if not importlib.util.find_spec(module):
            continue

        with subtest(f'Pyjoyment on ASGI mounted in Pyjoyment.Lite on {name}'):
            # Pyjo.Server.ASGI needs a reactor that runs in the loop of the ASGI server, which Pyjo.Reactor.Poll, with a
            # loop of its own, does not
            if Pyjo.Reactor.object.detect() != 'Pyjo.Reactor.Asyncio':
                skip('needs Pyjo.Reactor.Asyncio, which runs in the loop of the ASGI server', 1)
                continue
            os.environ['PYJO_ASGI'] = '1'
            try:
                server = Server(dir, command)
            finally:
                del os.environ['PYJO_ASGI']
            try:
                status, headers, body = server.request('GET', '/')
                is_ok(status, 200, 'right status')
                is_ok(body, 'I ♥ Pyjoyment!'.encode(), 'right content')

                status, headers, body = server.request('GET', '/asgi')
                is_ok(status, 200, 'right status')
                is_ok(body, b'Hello Pyjoyment at /asgi on ASGI!', 'right content')

                status, headers, body = server.request('GET', '/asgi/pyjo/pyjo.css')
                is_ok(status, 200, 'right status')
                is_ok(headers['Content-Type'], 'text/css', 'static file')

                status, headers, body = server.request('GET', '/asgi/foo')
                is_ok(status, 404, 'not found')

                status, headers, body = server.request('GET', '/asgi/later')
                is_ok(body, b'Hello later!', 'response given later')

                status, headers, body = server.request('GET', '/asgi/chunks')
                is_ok(body, b'012', 'chunks given later')
            except Exception:
                diag(server.output())
                raise
            finally:
                server.close()

done_testing()
