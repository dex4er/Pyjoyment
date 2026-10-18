import Pyjo.File
import Pyjo.Test.Pyjo
import Pyjoyment

from Pyjo.Test import *
from Pyjo.Util import b64_encode

import os
import re
import shutil
import subprocess
import sys
import tempfile


# The examples of docs/guides/testing.rst, which includes them: test scripts, which run against the applications that
# this test writes, as the guide does not show them
EXAMPLES = Pyjo.File.curfile().dirname().dirname().sibling('docs', 'guides', 'testing')

APPLICATIONS = {
    'Celestial.py': """
import Pyjoyment


class Celestial(Pyjoyment.object):
    def startup(self):
        r = self.routes
        r.post('/notifications').to(cb=lambda c: c.render(json={'message': 'notification created'}, status=201))
        r.get('/sunrise').to(cb=lambda c: c.render(text='6:00 am'))
        r.get('/sunset').to(cb=lambda c: c.render(text='8:00 pm'))
        r.post('/insurance').to(cb=lambda c: c.render(inline='<div id="thanks">thank you <%= param("name") %></div>'))


new = Celestial.new
object = Celestial
""",
    'EchoService.py': """
import Pyjoyment


class EchoService(Pyjoyment.object):
    def startup(self):
        r = self.routes

        @r.websocket('/echo')
        def echo(c):
            c.on('message', lambda c, msg: c.send(f'echo: {msg}'))

        @r.websocket('/echo.json')
        def echo_json(c):
            c.on('json', lambda c, document: c.send({'json': document}))


new = EchoService.new
object = EchoService
""",
    'MyApp.py': """
import Pyjoyment

import time


class MyApp(Pyjoyment.object):
    def startup(self):
        r = self.routes

        @r.get('/')
        def index(c):
            if (login := c.session('login')) is None:
                return c.render(text='Please log in', status=401)
            c.render(text=f'You logged in at {login}')

        @r.post('/login')
        def login(c):
            if c.param('password') != 'let me in':
                return c.render(text='Please log in', status=401)
            c.session(login=int(time.time()))
            c.render(text='You are logged in')

        r.post('/redirect/pyjo').to(cb=lambda c: c.redirect_to('https://pyjoyment.readthedocs.io'))


new = MyApp.new
object = MyApp
""",
}


def project():
    # A directory with the applications, and the scripts of the guide in its "t" directory
    home = tempfile.mkdtemp()
    for name, code in APPLICATIONS.items():
        Pyjo.File.path(home, name).spew(code.lstrip('\n').encode())
    return home


def run(home, *args, **environ):
    env = {**os.environ, 'PYTHONPATH': os.getcwd()}
    for name in ('PYJO_EXE', 'PYJO_HOME', 'PYJO_LOG_LEVEL', 'PYJO_HARNESS_IS_VERBOSE'):
        env.pop(name, None)
    env.update(environ)
    return subprocess.run([sys.executable, *args], cwd=home, capture_output=True, text=True, env=env, timeout=120)


def prove(home, name):
    t = Pyjo.File.path(home, 't').make_path()
    shutil.copy(EXAMPLES.child(f'{name}.py').to_str(), t.to_str())
    result = run(home, '-m', 'Pyjo.Prove', '-l', f't/{name}.py')
    if not like_ok(result.stdout, re.compile(r'^Result: PASS$', re.M), f'{name}.py passes'):
        diag(result.stdout, result.stderr)
    return result


with subtest('Overview'):
    home = project()
    prove(home, 'celestial')
    shutil.rmtree(home)

# An application with the resources of the snippets
app = Pyjoyment.new()
r = app.routes
r.get('/frogs').to(
    cb=lambda c: (
        c.render(json=[{'species': 'Lithobates catesbeianus'}])
        if c.param('q') == 'bullfrog'
        else c.render(text='Ptychadena interioris, bullfrog and hypnotoad')
    )
)
bees = {}


@r.put('/bees')
def put_bees(c):
    bees[id := str(len(bees) + 1)] = c.req.json()
    c.render(json={'id': id}, status=202)


r.get('/bees/:id').to(cb=lambda c: c.render(json=bees[c.param('id')]))
r.post('/calls').to(cb=lambda c: c.render(text=c.req.body.decode()))
r.get('/internal/personnel').to(cb=lambda c: c.render(text=f'{c.req.headers.authorization} {c.req.url.query.to_str()}'))
r.post('/doorbell').to(cb=lambda c: c.render(text='ding', status=200 if c.param('action') == 'ring once' else 301))
r.get('/map-of-the-world.pdf').to(cb=lambda c: c.render(data=b'%PDF-1.7', format='pdf'))
r.get('/scary-things/spiders', format=['json', 'html']).to(
    cb=lambda c: c.respond_to(
        json={'json': {'arachnid': 'brown recluse'}},
        html={'inline': '<title>All The Spiders</title>'},
    )
)
r.get('/animals/friendly', format=['json']).to(
    cb=lambda c: c.render(json={'beings': {'jeremiah': {'age': 42, 'species': 'Bullfrog'}}})
)
r.get('/html').to(
    cb=lambda c: c.render(inline='<html><head><title>Hello!</title></head><div class="foo" x="y">Hello!</div></html>')
)
for i in range(1, 5):
    r.get(f'/{i}').to(cb=lambda c, i=i: c.redirect_to(f'/{i + 1}'))
r.get('/5').to(cb=lambda c: c.render(json={'message': 'this is five'}))
r.get('/cookie').to(cb=lambda c: c.cookie('smarty', 'pants') and c.render(text='cookie'))


@r.any(['RING'], '/doorbell')
def ring(c):
    if c.cookie('Secret') == "don't tell anybody":
        return c.render(json={'status': 'ding dong'})
    c.render(json={'status': 'silence'}, status=403)


with subtest('Test.Pyjo at a glance'):
    with Pyjo.Test.Pyjo.new(app) as t:
        t.get_ok('/frogs')
        t.status_is(200)
        t.content_like(re.compile(r'bullfrog'))
        t.content_like(re.compile(r'hypnotoad'))

        t.get_ok('/frogs').status_is(200).content_like(re.compile(r'bullfrog')).content_like(re.compile(r'hypnotoad'))

        t.put_ok('/bees', json={'type': 'worker', 'name': 'Karl'}).status_is(202).json_has('/id')

        # Pull out the id from the response
        newbee = t.tx.res.json('/id')

        # Make a new request with data from the previous response
        t.get_ok(f'/bees/{newbee}').status_is(200).json_is('/name', 'Karl')

        # First transaction
        (
            t.get_ok('/frogs?q=bullfrog', {'Content-Type': 'application/json'})
            .status_is(200)
            .json_like('/0/species', re.compile(r'(?i)catesbeianus'))
        )

        # Still first transaction
        t.content_type_is('application/json;charset=UTF-8')

        # Second transaction
        (
            t.get_ok('/frogs?q=banjo', {'Content-Type': 'text/html'})
            .status_is(200)
            .content_like(re.compile(r'(?i)interioris'))
        )

        # Still second transaction
        t.content_type_is('text/html;charset=UTF-8')

with subtest('The Test.Pyjo object'):
    with Pyjo.Test.Pyjo.new() as t:
        t.ua.server.app = app
        url = t.ua.server.url().to_str()
        t.get_ok(f'{url}frogs').status_is(200).content_like(re.compile(r'(?i)hypnotoad'))
        tx = t.ua.post(f'{url}calls', form={'q': 'hypnotoad'})
        is_ok(tx.result.text, 'q=hypnotoad', 'user agent')

with subtest('An example'):
    home = tempfile.mkdtemp()
    result = run(home, '-m', 'Pyjoyment', 'generate', 'app', 'MyApp')
    like_ok(result.stdout, re.compile(r'^  \[write\] .*/my_app/t/basic\.py$', re.M), 'test written')
    basic = Pyjo.File.path(home, 'my_app', 't', 'basic.py').slurp().decode()
    is_ok(
        basic,
        'from Pyjo.Test import *\n\nimport Pyjo.Test.Pyjo\n\n\n'
        "t = Pyjo.Test.Pyjo.new('MyApp')\nt.get_ok('/').status_is(200).content_like(r'(?i)Pyjoyment')\n\n"
        'done_testing()\n',
        'boilerplate',
    )
    my_app = Pyjo.File.path(home, 'my_app').to_str()
    result = run(my_app, '-m', 'Pyjo.Prove', '-lv', 't')
    like_ok(result.stdout, re.compile(r'^ok 3 - content is similar$', re.M), 'verbose')
    like_ok(result.stdout, re.compile(r'^Result: PASS$', re.M), 'passes')
    like_ok(result.stdout + result.stderr, re.compile(r'\[trace\]'), 'log of the application')
    result = run(my_app, '-m', 'Pyjo.Prove', '-lv', 't', PYJO_LOG_LEVEL='fatal')
    like_ok(result.stdout, re.compile(r'^ok 3 - content is similar$', re.M), 'verbose and quiet')
    unlike_ok(result.stdout + result.stderr, re.compile(r'\[trace\]'), 'no log of the application')

    # Testing with configuration data
    shutil.copy(EXAMPLES.child('weather', 'MyApp', '__init__.py').to_str(), Pyjo.File.path(my_app, 'MyApp').to_str())
    Pyjo.File.path(my_app, 't', 'weather.py').spew(
        b'from Pyjo.Test import *\n\nimport Pyjo.Test.Pyjo\n\nimport re\n\n\n'
        b"t = Pyjo.Test.Pyjo.new('MyApp', {'enable_weather': 1})\n"
        b"t.get_ok('/').status_is(200).content_like(re.compile(r'(?i)Pyjoyment'))\n"
        b"t.get_ok('/weather').status_is(200).content_like(re.compile(r'\xf0\x9f\x94\xa5'))\n\n"
        b"t = Pyjo.Test.Pyjo.new('MyApp')\nt.get_ok('/weather').status_is(404)\n\ndone_testing()\n"
    )
    result = run(my_app, '-m', 'Pyjo.Prove', '-l', 't/weather.py')
    if not like_ok(result.stdout, re.compile(r'^Result: PASS$', re.M), 'feature flag'):
        diag(result.stdout, result.stderr)
    shutil.rmtree(home)

with subtest('Testing application helpers'):
    helpers = Pyjoyment.new()

    @helpers.helper('basic_auth')
    def basic_auth(c, *values):
        return {'Authorization': 'Basic ' + b64_encode(':'.join(values).encode(), '')}

    with Pyjo.Test.Pyjo.new(helpers) as t:
        is_deeply_ok(
            t.app.basic_auth('bif', "Bif's Passwerdd"),
            {'Authorization': 'Basic YmlmOkJpZidzIFBhc3N3ZXJkZA=='},
            'correct header value',
        )

with subtest('Using HTTP request assertions'):
    with Pyjo.Test.Pyjo.new(app) as t:
        t.post_ok('/calls', form={'to': '+43.55.555.5555'}).content_is('to=%2B43.55.555.5555')
        is_ok(t.tx.req.headers.content_type, 'application/x-www-form-urlencoded', 'Content-Type')
        is_ok(t.tx.req.headers.content_length, '20', 'Content-Length')
        t.get_ok('/internal/personnel', {'Authorization': 'Token secret-password'}, form={'q': 'Professor Plum'})
        t.content_is('Token secret-password q=Professor+Plum')
        is_ok(t.tx.req.url.path_query, '/internal/personnel?q=Professor+Plum', 'query')

with subtest('HTTP response status code'):
    with Pyjo.Test.Pyjo.new(app) as t:
        t.post_ok('/doorbell', form={'action': 'ring once'}).status_is(200)
        t.post_ok('/doorbell', form={'action': 'ring twice'})
        is_ok(t.tx.res.message, 'Moved Permanently', 'try next door')
        t.status_isnt(200)

with subtest('HTTP response headers'):
    with Pyjo.Test.Pyjo.new(app) as t:
        t.get_ok('/map-of-the-world.pdf').content_type_is('application/pdf')
        t.get_ok('/map-of-the-world.pdf').header_is('Content-Type', 'application/pdf')
        (
            t.get_ok('/map-of-the-world.pdf')
            .content_type_is('application/pdf')
            .header_isnt('Compression', 'gzip')
            .header_unlike('Server', re.compile(r'(?i)IIS'))
        )

with subtest('HTTP response content assertions'):
    with Pyjo.Test.Pyjo.new(app) as t:
        t.get_ok('/scary-things/spiders.json').content_is('{"arachnid":"brown recluse"}')
        t.get_ok('/scary-things/spiders.html').content_like(re.compile(r'<title>All The Spiders</title>'))

        t.get_ok('/animals/friendly.json').json_has('/beings/jeremiah/age')
        (
            t.get_ok('/animals/friendly.json')
            .json_has('/beings/jeremiah/age')
            .json_is('/beings/jeremiah/age', 42)
            .json_like('/beings/jeremiah/species', re.compile(r'(?i)bullfrog'))
        )

        t.get_ok('/html')
        t.text_is('div.foo[x=y]', 'Hello!')
        t.text_is('html head title', 'Hello!', 'right title')

with subtest('Redirects'):
    with Pyjo.Test.Pyjo.new(app) as t:
        t.get_ok('/1').header_is('location', '/2')

        t.ua.max_redirects = 1
        t.get_ok('/1').header_is('location', '/3')

        t.ua.max_redirects = 2
        t.get_ok('/1').header_is('location', '/4')

        # Look at the previous hop
        is_ok(t.tx.previous.res.headers.location, '/3', 'previous redirect')

        t.ua.max_redirects = 3
        t.get_ok('/1').header_is('location', '/5')

        t.ua.max_redirects = 4
        t.get_ok('/1').json_is('/message', 'this is five')

with subtest('Cookies and session management'):
    home = project()
    prove(home, 'login')
    shutil.rmtree(home)

    with Pyjo.Test.Pyjo.new(app) as t:
        t.get_ok('/cookie')
        like_ok(str(t.tx.res.cookie('smarty')), re.compile(r'smarty=pants'), 'cookie found')

with subtest('Custom transactions'):
    with Pyjo.Test.Pyjo.new(app) as t:
        # Use custom "RING" verb
        tx = t.ua.build_tx('RING', '/doorbell')

        # Set a special cookie
        tx.req.cookies({'name': 'Secret', 'value': "don't tell anybody"})

        # Make the request
        t.request_ok(tx).status_is(200).json_is('/status', 'ding dong')

        t.request_ok(t.ua.build_tx('RING', '/doorbell')).status_is(403)

with subtest('Testing WebSocket web services'):
    home = project()
    prove(home, 'echo')
    shutil.rmtree(home)

with subtest('Extending Test.Pyjo'):
    home = project()
    shutil.copy(EXAMPLES.child('TestLocation.py').to_str(), home)
    Pyjo.File.path(home, 't').make_path().child('location.py').spew(
        b'from Pyjo.Test import *\n\nimport TestLocation\n\n\n'
        b"t = TestLocation.new('MyApp')\n\n"
        b'(\n'
        b"    t.post_ok('/redirect/pyjo', json={'message': 'Pyjo, here I come!'})\n"
        b'    .status_is(302)\n'
        b"    .location_is('https://pyjoyment.readthedocs.io')\n"
        b"    .otherwise(lambda t: diag('I miss tempire.'))\n"
        b')\n'
        b"t.location_is('https://mojolicious.org').otherwise(lambda t: diag('I miss tempire.'))\n\n"
        b'done_testing()\n'
    )
    result = run(home, '-m', 'Pyjo.Prove', '-lv', 't/location.py')
    like_ok(result.stdout, re.compile(r'^ok 3 - Location: https://pyjoyment\.readthedocs\.io$', re.M), 'location_is')
    like_ok(result.stdout, re.compile(r'^not ok 4 - Location: https://mojolicious\.org$', re.M), 'fails')
    like_ok(result.stdout + result.stderr, re.compile(r'# I miss tempire\.'), 'otherwise')
    shutil.rmtree(home)

done_testing()
