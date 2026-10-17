import Pyjoyment
import Pyjoyment.Command.get

from Pyjo.Test import *

import contextlib
import io
import re


# Not in Mojolicious: the output as bytes, which get writes as Mojo prints them
@contextlib.contextmanager
def stdout():
    buffer = io.BytesIO()
    wrapper = io.TextIOWrapper(buffer, write_through=True)
    try:
        with contextlib.redirect_stdout(wrapper):
            yield buffer
    finally:
        wrapper.detach()


# The local application of the examples, as a test does not ask remote hosts
app = Pyjoyment.new()
app.log.level = 'fatal'
routes = app.routes
routes.get('/', {'text': 'Hello!'})
routes.get(
    '/hello.html',
    {
        'inline': '<html><head><title>Hi</title></head><body><h1 id="a">One</h1>'
        '<h2>Two <b>bold</b></h2><a href="/x">X</a></body></html>'
    },
)
routes.get('/secrets.json', lambda c: c.render(json=[{'content': 'a'}, {'content': c.req.url.to_abs().userinfo}]))
routes.any('/echo', lambda c: c.render(text=f'{c.req.method} {c.param("q")} {c.req.body.decode()}'))
routes.get('/redirect', lambda c: c.redirect_to('/'))
get = Pyjoyment.Command.get.new(app=app)

with subtest('Synopsis'):
    like_ok(get.usage, r'^Usage: APPLICATION get \[OPTIONS\] URL \[SELECTOR\|JSON-POINTER\] \[COMMANDS\]\n', 'usage')
    with stdout() as buffer:
        get.run('/')
    is_ok(buffer.getvalue(), b'Hello!', 'request')
    with stdout() as buffer:
        get.run('-H', 'Accept: text/html', '/hello.html', 'head > title', 'text')
    is_ok(buffer.getvalue(), b'Hi\n', 'text')
    with stdout() as buffer:
        get.run('//sri:secr3t@/secrets.json', '/1/content')
    is_ok(buffer.getvalue(), b'sri:secr3t\n', 'JSON Pointer')
    with stdout() as buffer:
        get.run('-u', 'sri:s3cret', '/secrets.json', '/1/content')
    is_ok(buffer.getvalue(), b'sri:s3cret\n', 'user')
    with stdout() as buffer:
        get.run('-M', 'PUT', '-c', 'data', '/echo')
    is_ok(buffer.getvalue(), b'PUT None data', 'method and content')
    with stdout() as buffer:
        get.run('-f', 'q=Pyjoyment', '-M', 'POST', '/echo')
    is_ok(buffer.getvalue(), b'POST Pyjoyment q=Pyjoyment', 'form')
    with stdout() as buffer:
        get.run('/hello.html', 'h2', 'all')
    is_ok(buffer.getvalue(), b'Two bold\n', 'all text')
    with stdout() as buffer:
        get.run('/hello.html', 'a', 'attr', 'href')
    is_ok(buffer.getvalue(), b'/x\n', 'attribute')
    with stdout() as buffer:
        get.run('/hello.html', '*', 'attr', 'id')
    is_ok(buffer.getvalue(), b'a\n', 'attributes')
    with stdout() as buffer:
        get.run('/hello.html', 'h1, h2', '1', 'text')
    is_ok(buffer.getvalue(), b'Two \n', 'number')
    with stdout() as buffer:
        get.run('/hello.html', 'h1')
    is_ok(buffer.getvalue(), b'<h1 id="a">One</h1>\n', 'elements')
    with stdout() as buffer:
        get.run('-r', '/redirect')
    is_ok(buffer.getvalue(), b'Hello!', 'redirect')
    stderr = io.StringIO()
    with stdout() as buffer, contextlib.redirect_stderr(stderr):
        get.run('-v', '/')
    like_ok(stderr.getvalue(), r'(?s)^GET / HTTP/1\.1\r\n.*\n\nHTTP/1\.1 200 OK\r\n', 'verbose')
    throws_ok(lambda: get.run('/hello.html', 'h1', 'nothing'), re.compile(r'^Unknown command "nothing"'), 'command')

with subtest('Attributes'):
    is_ok(Pyjoyment.Command.get.new().description, 'Perform HTTP request', 'description')

done_testing()
