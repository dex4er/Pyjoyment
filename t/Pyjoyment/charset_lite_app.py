"""
__DATA__
@@ index.html.ep
<p>やった</p>
"""

import Pyjo.Test.Pyjo

from Pyjo.String.Unicode import u
from Pyjo.Test import *
from Pyjoyment.Lite import app, get, post


# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor of Pyjo.Reactor.detect()

# Not in Mojolicious: the templates of the DATA section are in the docstring, as the requests come before the end of the
# script

yatta = 'やった'
yatta_sjis = yatta.encode('shift_jis')

app.types.type('html', 'text/html;charset=Shift_JIS')
app.renderer.encoding = 'Shift_JIS'


@app.hook('before_dispatch')
def before_dispatch(c):
    c.req.default_charset = 'Shift_JIS'
    c.req.url.query.charset = 'Shift_JIS'


# UTF-8 text renderer
def test(renderer, c, output, options):
    options.pop('encoding', None)
    output.write(u(c.stash('test')).encode('UTF-8'))


app.renderer.add_handler('test', test)

get('/', {'format': None}, 'index', format=[yatta])


@post('/')
def root(c):
    c.render(text='foo: ' + c.param('foo'))


@post('/data')
def data(c):
    c.render(data=c.req.body, format='bin')


@get('/unicode')
def unicode(c):
    c.render(test=yatta, handler='test', format='txt')


get('/json', lambda c: c.render(json={'test': yatta}))

get('/привет/мир', lambda c: c.render(json={'foo': yatta}))


@get('/params')
def params(c):
    c.render(json={'params': c.req.url.query.to_dict(), 'yatta': c.param('yatta')})


t = Pyjo.Test.Pyjo.new()

with subtest('Plain old ASCII'):
    t.post_ok('/', form={'foo': 'yatta'}).status_is(200).content_is('foo: yatta')

with subtest('Send raw Shift_JIS octets (like browsers do)'):
    (
        t.post_ok('/', form={'foo': yatta_sjis}, charset=None)
        .status_is(200)
        .content_type_unlike(r'application')
        .content_type_like(r'Shift_JIS')
        .content_like(yatta)
    )

with subtest('Send raw Shift_JIS octets (like browsers do, multipart message)'):
    (
        t.post_ok('/', {'Content-Type': 'multipart/form-data'}, form={'foo': yatta_sjis}, charset=None)
        .status_is(200)
        .content_type_like(r'Shift_JIS')
        .content_like(yatta)
    )

with subtest('Send as string'):
    (
        t.post_ok('/', form={'foo': yatta}, charset='shift_jis')
        .status_is(200)
        .content_type_like(r'Shift_JIS')
        .content_like(yatta)
    )

with subtest('Send as string (multipart message)'):
    (
        t.post_ok('/', {'Content-Type': 'multipart/form-data'}, form={'foo': yatta}, charset='shift_jis')
        .status_is(200)
        .content_type_like(r'Shift_JIS')
        .content_like(yatta)
    )

with subtest('Unicode renderer'):
    t.get_ok('/unicode').status_is(200).content_type_is('text/plain;charset=UTF-8').content_is(yatta)

with subtest(
    'Templates in the DATA section should be written in UTF-8, and those in separate files in Shift_JIS '
    '(Pyjoyment will do the decoding)'
):
    t.get_ok('/').status_is(200).content_type_like(r'Shift_JIS').content_like(yatta)

with subtest('Unicode format'):
    t.get_ok(f'/.{yatta}').status_is(500).content_like(r'Route without action and nothing to render')

with subtest('Send and receive raw Shift_JIS octets (like browsers do)'):
    t.post_ok('/data', yatta_sjis).status_is(200).content_is(yatta_sjis.decode('latin-1'))

with subtest('JSON data'):
    t.get_ok('/json').status_is(200).content_type_is('application/json;charset=UTF-8').json_is({'test': yatta})

with subtest('IRI'):
    t.get_ok('/привет/мир').status_is(200).content_type_is('application/json;charset=UTF-8').json_is({'foo': yatta})

with subtest('Shift_JIS parameters'):
    url = t.ua.server.url().set(path='/params', query=('foo', 3, 'yatta', yatta))
    url.query.charset = 'shift_jis'
    t.get_ok(url).status_is(200).json_is({'params': {'foo': '3', 'yatta': yatta}, 'yatta': yatta})

done_testing()
