import Pyjo.File
import Pyjo.Test.Pyjo
import Pyjoyment

from Pyjo.Test import *
from Pyjo.Util import b64_encode

import importlib.metadata
import importlib.util
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


def generated_app():
    # A project of generate app, as the guide makes it in "An example"
    home = tempfile.mkdtemp()
    run(home, '-m', 'Pyjoyment', 'generate', 'app', 'MyApp')
    return home, Pyjo.File.path(home, 'my_app')


with subtest('Overview'):
    home = project()
    prove(home, 'celestial')
    shutil.rmtree(home)

with subtest('Test scripts'):
    home = tempfile.mkdtemp()
    Pyjo.File.path(home, 't').make_path().child('equal.py').spew(
        b"from Pyjo.Test import *\n\nis_ok(1 + 1, 3, 'addition')\n\n"
        b"with subtest('Strings'):\n    ok('Pyjo'.startswith('P'), 'starts with P')\n"
        b"    is_ok('Pyjo'.lower(), 'pyjo', 'lower case')\n\ndone_testing()\n"
    )
    result = run(home, 't/equal.py')
    is_ok(
        result.stdout,
        'not ok 1 - addition\n# Subtest: Strings\n    ok 1 - starts with P\n    ok 2 - lower case\n    1..2\n'
        'ok 2 - Strings\n1..2\n',
        'TAP',
    )
    like_ok(
        result.stderr,
        re.compile(
            r"^#   Failed test 'addition'\n#   at .*[/\\]t[/\\]equal\.py line 3\.\n#          got: 2\n#     expected: 3\n"
            r'# Looks like you failed 1 test of 2\.\n$'
        ),
        'diagnostics',
    )
    is_ok(result.returncode, 1, 'exit status of the failed tests')
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
    like_ok(result.stdout, re.compile(r'^  \[write\] .*[/\\]my_app[/\\]t[/\\]basic\.py$', re.M), 'test written')
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

with subtest('A single test script'):
    home, my_app = generated_app()
    result = run(my_app.to_str(), 't/basic.py', PYTHONPATH=os.pathsep.join(['.', os.getcwd()]))
    is_ok(
        result.stdout,
        'ok 1 - GET /\nok 2 - 200 OK\nok 3 - content is similar\n1..3\n',
        'PYTHONPATH=. python t/basic.py',
    )
    shutil.rmtree(home)

with subtest('pyjo-prove'):
    home, my_app = generated_app()
    result = run(my_app.to_str(), '-m', 'Pyjo.Prove', '-l', 't')
    like_ok(
        result.stdout,
        re.compile(
            r'^t/basic\.py \.+ ok\nAll tests successful\.\nFiles=1, Tests=3, \d+ wallclock secs\nResult: PASS\n$'
        ),
        'pyjo-prove -l t',
    )
    result = run(my_app.to_str(), '-m', 'Pyjo.Prove', '-l', '-r', '-j', '0', '--timeout', '60', 't')
    like_ok(result.stdout, re.compile(r'^Result: PASS$', re.M), 'pyjo-prove -l -r -j 0 --timeout 60 t')
    # A variable before the command is of a shell of POSIX, which the cmd.exe of Windows is not
    if sys.platform == 'win32' or not shutil.which('prove'):
        skip('Perl prove on a system of POSIX is required', 1)
    else:
        # A python on PATH which is the interpreter running this test
        bindir = Pyjo.File.path(home, 'bin').make_path()
        os.symlink(sys.executable, bindir.child('python').to_str())
        env = {**os.environ, 'PYTHONPATH': os.pathsep.join(['.', os.getcwd()])}
        env['PATH'] = os.pathsep.join([bindir.to_str(), env.get('PATH', '')])
        for name in ('PYJO_EXE', 'PYJO_HOME', 'PYJO_LOG_LEVEL', 'PYJO_HARNESS_IS_VERBOSE'):
            env.pop(name, None)
        p = subprocess.run(
            ['prove', '--ext=py', '--exec=python', '-r', 't'],
            cwd=my_app.to_str(),
            capture_output=True,
            text=True,
            env=env,
            timeout=120,
        )
        like_ok(p.stdout, re.compile(r'^Result: PASS$', re.M), 'PYTHONPATH=. prove --ext=py --exec=python -r t')
    shutil.rmtree(home)

with subtest('pytest'):
    if importlib.util.find_spec('pytest') is None:
        plan(skip_all='pytest is required, as of the dependency group "pytest"')
    # The plugin of the entry point where Pyjoyment is installed, or of the checkout otherwise
    pytest_plugin = importlib.metadata.entry_points(group='pytest11').select(value='Pyjo.Test.pytest_plugin')
    pytest = ['-m', 'pytest', '-p', 'no:cacheprovider', *([] if pytest_plugin else ['-p', 'Pyjo.Test.pytest_plugin'])]
    home, my_app = generated_app()
    result = run(my_app.to_str(), *pytest)
    # The paths of the progress of pytest have the separator of the system, \ on Windows
    like_ok(result.stdout.replace('\\', '/'), re.compile(r'^t/basic\.py \.\s+\[100%\]$', re.M), 'pytest')
    if importlib.util.find_spec('xdist') is None:
        skip('pytest-xdist is required, as of the dependency group "pytest"', 1)
    else:
        result = run(my_app.to_str(), *pytest, '-n', 'auto')
        like_ok(result.stdout, re.compile(r'^=+ 1 passed in ', re.M), 'pytest -n auto')
    my_app.child('tests').make_path().child('conftest.py').spew(
        b"import pytest\n\n\n@pytest.fixture\ndef app():\n    return 'MyApp'\n"
    )
    my_app.child('tests', 'test_basic.py').spew(
        b"def test_index(t):\n    t.get_ok('/').status_is(200).content_like(r'(?i)Pyjoyment')\n"
    )
    result = run(my_app.to_str(), *pytest, 'tests')
    like_ok(result.stdout.replace('\\', '/'), re.compile(r'^tests/test_basic\.py \.\s+\[100%\]$', re.M), 'pytest tests')
    shutil.rmtree(home)

with subtest('Basic assertions'):
    home = tempfile.mkdtemp()
    Pyjo.File.path(home, 't').make_path().child('basic.py').spew(
        b"""from Pyjo.Test import *

import re

ok(1 + 1 == 2, 'a true value')
is_ok(int('42'), 42, 'equal, with ==')
isnt_ok('pyjo', 'mojo', 'not equal, with !=')
like_ok('Hello Pyjo', r'Pyjo$', 'matches a regular expression')
unlike_ok('Hello Pyjo', re.compile(r'(?i)mojo'), "doesn't match a regular expression")
cmp_ok(3, '<', 4, 'compared with an operator')
is_deeply_ok({'a': [1, 2]}, {'a': [1, 2]}, 'the same data structure')
isa_ok([], list, 'an instance of a class')
in_ok(['foo', 'bar'], 'foo', 'contains an element')
not_in_ok({'a': 1}, 'b', "doesn't contain an element")
none_ok({}.get('missing'), 'None')
throws_ok(lambda: int('x'), ValueError, 'raises an exception')
pass_ok('passes always')

done_testing()
"""
    )
    result = run(home, 't/basic.py')
    like_ok(result.stdout, re.compile(r'^ok 13 - passes always\n1\.\.13\n\Z', re.M), 'all assertions pass')
    unlike_ok(result.stdout, re.compile(r'^not ok', re.M), 'no failed assertion')
    is_ok(result.stderr, '', 'no diagnostics')
    is_ok(result.returncode, 0, 'right exit status')

    with Pyjo.Test.Pyjo.new(app) as t:
        t.get_ok('/frogs')
        if not is_ok(t.tx.res.code, 200, 'right status'):
            diag(t.tx.res.text)

    Pyjo.File.path(home, 't', 'online.py').spew(
        b'from Pyjo.Test import *\n\nimport os\n\n'
        b"if not os.getenv('TEST_ONLINE'):\n    plan(skip_all='set TEST_ONLINE to enable this test')\n\n"
        b'ok(True)\n\ndone_testing()\n'
    )
    result = run(home, 't/online.py', TEST_ONLINE='')
    is_ok(result.stdout, '1..0 # SKIP set TEST_ONLINE to enable this test\n', 'skipped without TEST_ONLINE')
    shutil.rmtree(home)

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
