import Pyjo.File
import Pyjo.Test.Pyjo
import Pyjoyment

from Pyjo.Test import *

import os
import re
import shutil
import subprocess
import sys
import tempfile
import time


# The examples of docs/guides/growing.rst, which includes them: a directory for each stage of the application, with the
# files that the stage adds or changes, and the final application in "login"
EXAMPLES = Pyjo.File.curfile().dirname().dirname().sibling('docs', 'guides', 'growing')


def stage(home, name):
    # The files of a stage over the ones of the stages before it
    shutil.copytree(
        EXAMPLES.child(name).to_str(), home, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__')
    )


def run(home, *args):
    env = {**os.environ, 'PYTHONPATH': os.getcwd()}
    env.pop('PYJO_EXE', None)
    env.pop('PYJO_HOME', None)
    return subprocess.run([sys.executable, *args], cwd=home, capture_output=True, text=True, env=env, timeout=60)


def prove(home, test):
    result = run(home, '-m', 'Pyjo.Prove', '-l', test)
    if not like_ok(result.stdout, re.compile(r'^Result: PASS$', re.M), f'{test} passes'):
        diag(result.stdout, result.stderr)


home = tempfile.mkdtemp()

with subtest('Foundation'):
    stage(home, 'foundation')
    t = Pyjo.Test.Pyjo.new(Pyjo.File.path(home, 'myapp.py'))
    t.get_ok('/').status_is(200).content_is('Hello World!')
    is_ok(os.stat(Pyjo.File.path(home, 'myapp.py').to_str()).st_mode & 0o700, 0o700, 'executable')

with subtest('Model'):
    stage(home, 'model')
    Pyjo.File.path(home, 'MyApp', 'Model').make_path()
    shutil.copy(EXAMPLES.child('login', 'MyApp', 'Model', 'Users.py').to_str(), Pyjo.File.path(home, 'MyApp', 'Model'))
    is_ok(run(home, 'myapp.py', 'get', '/').stdout, 'Wrong username or password.', 'wrong password')
    is_ok(run(home, 'myapp.py', 'get', '/?user=sebastian&pass=secr3t').stdout, 'Welcome sebastian.', 'right password')
    is_ok(run(home, 'myapp.py', 'get', '/?user=sebastian&pass=secret').stdout, 'Wrong username or password.', 'wrong')

with subtest('Testing'):
    # Your application won't pass these tests
    Pyjo.File.path(home, 't').make_path()
    shutil.copy(EXAMPLES.child('prototype', 't', 'login.py').to_str(), Pyjo.File.path(home, 't'))
    result = run(home, '-m', 'Pyjo.Prove', '-l', 't/login.py')
    like_ok(result.stdout, re.compile(r'^Result: FAIL$', re.M), 'test fails')

    result = run(home, 'myapp.py', 'get', '-v', '/?user=sebastian&pass=secr3t')
    like_ok(result.stderr, re.compile(r'^GET /\?user=sebastian&pass=secr3t HTTP/1\.1$', re.M), 'request')
    like_ok(result.stderr, re.compile(r'^User-Agent: Pyjoyment \(Python\)$', re.M), 'user agent')
    like_ok(result.stderr, re.compile(r'^HTTP/1\.1 200 OK$', re.M), 'response')
    like_ok(result.stderr, re.compile(r'^Content-Length: 18$', re.M), 'length')
    like_ok(result.stderr, re.compile(r'^Server: Pyjoyment \(Python\)$', re.M), 'server')
    is_ok(result.stdout, 'Welcome sebastian.', 'body')

with subtest('Final prototype'):
    stage(home, 'prototype')
    prove(home, 't/login.py')

with subtest('State keeping'):
    app = Pyjoyment.new()
    app.secrets = ['Pyjoyment rocks']
    is_deeply_ok(app.secrets, ['Pyjoyment rocks'], 'secrets')

    @app.routes.get('/login')
    def login(c):
        c.session(user='sebastian')
        c.render(text='ok')

    @app.routes.get('/user')
    def user(c):
        user = c.session('user')
        c.render(text=user or 'nobody')

    @app.routes.get('/expiration')
    def expiration(c):
        c.session(expiration=3600)
        c.render(text='ok')

    @app.routes.get('/expires')
    def expires(c):
        c.session(expires=1)
        c.render(text='ok')

    @app.routes.get('/flash')
    def flash(c):
        c.flash(message='Everything is fine.')
        c.redirect_to('goodbye')

    @app.routes.get('/goodbye')
    def goodbye(c):
        c.render(text=c.flash('message') or 'nothing')

    t = Pyjo.Test.Pyjo.new(app)
    t.get_ok('/user').status_is(200).content_is('nobody')
    t.get_ok('/login').status_is(200)
    t.get_ok('/user').status_is(200).content_is('sebastian')
    t.get_ok('/expiration').status_is(200)
    cookie = next(c for c in t.ua.cookie_jar.all() if c.name == 'pyjoyment')
    ok(3500 < cookie.expires - time.time() <= 3600, 'expires in an hour')
    t.get_ok('/expires').status_is(200)
    t.get_ok('/user').status_is(200).content_is('nobody')
    t.get_ok('/flash').status_is(302).header_like('Location', re.compile(r'/goodbye$'))
    t.get_ok('/goodbye').status_is(200).content_is('Everything is fine.')
    t.get_ok('/goodbye').status_is(200).content_is('nothing')

with subtest('Inflating templates'):
    result = run(home, 'myapp.py', 'inflate')
    is_ok(result.returncode, 0, 'inflate')
    for name in ('index.html.ep', 'protected.html.ep', 'layouts/default.html.ep'):
        ok(os.path.isfile(Pyjo.File.path(home, 'templates', name).to_str()), f'templates/{name}')
    prove(home, 't/login.py')

with subtest('Simplified application class and script'):
    stage(home, 'hybrid')
    prove(home, 't/login.py')

with subtest('Controller class, application class and templates'):
    # $ mkdir templates/login
    # $ mv templates/index.html.ep templates/login/index.html.ep
    # $ mv templates/protected.html.ep templates/login/protected.html.ep
    templates = Pyjo.File.path(home, 'templates')
    templates.child('login').make_path()
    for name in ('index.html.ep', 'protected.html.ep'):
        templates.child(name).move_to(templates.child('login', name))
    stage(home, 'login')
    prove(home, 't/login.py')

    # The templates of the final application are the inflated ones
    for name in ('layouts/default.html.ep', 'login/index.html.ep', 'login/protected.html.ep'):
        is_ok(templates.child(name).slurp(), EXAMPLES.child('login', 'templates', name).slurp(), name)

with subtest('Script'):
    # $ rm myapp.py
    Pyjo.File.path(home, 'myapp.py').remove()
    like_ok(run(home, '-m', 'MyApp', 'get', '/').stdout, re.compile(r'<form action="/"'), 'python -m MyApp')

with subtest('Simplified tests'):
    prove(home, 't/login.py')

    # The final application of the guide in a directory of its own
    final = tempfile.mkdtemp()
    stage(final, 'login')
    prove(final, 't/login.py')
    shutil.rmtree(final)

shutil.rmtree(home)

done_testing()
