import Pyjo.Test.Pyjo
import Pyjoyment

from Pyjo.Test import *

import importlib.util


# The applications of other frameworks, which Pyjoyment.Plugin.Mount mounts, of the dependency group "servers": uv run
# --only-group servers python -m Pyjo.Prove t/servers
if missing := [m for m in ('flask',) if not importlib.util.find_spec(m)]:
    plan(skip_all=f'needs the dependency group "servers", without {", ".join(missing)}')

import flask  # noqa: E402


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

done_testing()
