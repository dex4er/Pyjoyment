import Pyjo.Test.Pyjo
import Pyjoyment

from Pyjo.Test import *

import importlib
import importlib.util
import os
import shutil
import sys
import tempfile


# The applications of other frameworks, which Pyjoyment.Plugin.Mount mounts, of the dependency group "servers": uv run
# --only-group servers python -m Pyjo.Prove t/servers
if missing := [m for m in ('flask', 'waitress') if not importlib.util.find_spec(m)]:
    plan(skip_all=f'needs the dependency group "servers", without {", ".join(missing)}')

import flask  # noqa: E402


# The servers in processes of their own
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
Server = importlib.import_module('ServerProcess').Server

# The example of an application of Pyjoyment on WSGI, mounted in an application of Pyjoyment.Lite, on the WSGI servers
EXAMPLE = os.path.join(os.path.dirname(__file__), '..', '..', 'examples', 'pyjoyment', 'mount_wsgi_inception.py')
PYTHON = sys.executable
UWSGI = shutil.which('uwsgi', path=os.path.dirname(sys.executable))
GUNICORN = [PYTHON, '-m', 'gunicorn', 'inception:application', '--bind', '127.0.0.1:{port}']
SERVERS = [
    ('Gunicorn', importlib.util.find_spec('gunicorn'), GUNICORN),
    ('Gunicorn with threads', importlib.util.find_spec('gunicorn'), [*GUNICORN, '--threads', '4']),
    ('uWSGI', UWSGI, [UWSGI, '--http-socket', '127.0.0.1:{port}', '--module', 'inception:application']),
    ('Waitress', True, [PYTHON, '-m', 'waitress', '--listen=127.0.0.1:{port}', 'inception:application']),
    (
        'Werkzeug',
        importlib.util.find_spec('werkzeug'),
        [
            PYTHON,
            '-c',
            'from werkzeug.serving import run_simple; from inception import application; '
            "run_simple('127.0.0.1', {port}, application, threaded=True)",
        ],
    ),
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

with tempfile.TemporaryDirectory() as dir:
    shutil.copy(EXAMPLE, os.path.join(dir, 'inception.py'))

    for name, available, command in SERVERS:
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
            except Exception:
                diag(server.output())
                raise
            finally:
                server.close()

done_testing()
