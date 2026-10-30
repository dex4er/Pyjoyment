import Pyjo.File

from Pyjo.Test import *

import importlib
import os
import re
import subprocess
import sys


# The scripts of plugins/pyjoyment/skills/scraping/SKILL.md, each in the file that its first line names, as a coding
# agent writes them, run against a mock of the sites in a process of its own, as the tests do not use the network
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
Skills = importlib.import_module('Skills')
Server = importlib.import_module('ServerProcess').Server

root = Pyjo.File.curfile().dirname().dirname().dirname()
env = dict(os.environ)
env['PYTHONPATH'] = os.pathsep.join([root.to_str(), *filter(None, [env.get('PYTHONPATH')])])
env['PYJO_LOG_LEVEL'] = 'fatal'

tmp = Pyjo.File.tempdir()
for code in Skills.blocks('scraping'):
    tmp.child(re.match(r'# (\S+)\n', code)[1]).spew(code)

MOCK = """
from Pyjoyment.Lite import *


@get('/')
def index(c):
    c.redirect_to('/home')


@get('/home')
def home(c):
    c.render(
        inline='<html><head><title>Home</title></head><body>'
        '<a href="/one">One</a><a href="two">Two</a><a href="https://example.com/three">Three</a>'
        '<a href="/four">Four</a><ul class="items"><li>Bread</li><li>Milk <b>fresh</b></li></ul></body></html>'
    )


@get('/api/items')
def items(c):
    c.render(json={'items': [{'name': 'Bread'}, {'name': 'Milk'}]})


@get('/page/<n:num>')
def page(c):
    c.render(inline='<title>Page <%= n %></title>', n=c.param('n'))


@get('/missing')
def missing(c):
    c.render(text='Not here', status=404)


app.start()
"""
tmp.child('mock.py').spew(MOCK)


def run(*args):
    p = subprocess.run([sys.executable, *args], cwd=tmp.to_str(), env=env, capture_output=True, text=True, timeout=60)
    return p.stdout, p.stderr, p.returncode


server = Server(tmp.to_str(), [sys.executable, 'mock.py', 'daemon', '-l', 'http://127.0.0.1:{port}'])
try:
    base = f'http://127.0.0.1:{server.port}'

    with subtest('A page and an API'):
        stdout, stderr, status = run('scrape.py', f'{base}/')
        is_ok(status, 0, 'success')
        is_deeply_ok(
            stdout.splitlines(),
            ['Home', f'{base}/one', f'{base}/two', 'https://example.com/three', 'Bread, Milk fresh', 'Bread'],
            'title, links, items and JSON',
        )
        stdout, stderr, status = run('scrape.py', f'{base}/missing')
        is_ok(status, 1, 'error')
        is_ok(stderr.strip(), '404 Not Found', 'response of an error')
        stdout, stderr, status = run('scrape.py', 'http://127.0.0.1:1/')
        isnt_ok(status, 0, 'error of the connection')
        like_ok(stderr, r'(?i)refused', 'exception')

    with subtest('Many pages at the same time'):
        stdout, stderr, status = run('titles.py', *(f'{base}/page/{n}' for n in range(1, 6)))
        is_ok(status, 0, 'success')
        is_deeply_ok(sorted(stdout.splitlines()), [f'{base}/page/{n}: Page {n}' for n in range(1, 6)], 'titles')

    with subtest('HTML without a request'):
        stdout, stderr, status = run('dom.py')
        is_ok(status, 0, 'success')
        is_deeply_ok(
            stdout.splitlines(), ['Apple', 'Apple, Banana', '<ul id="fruits"><li>Banana</li><li>Cherry</li></ul>']
        )

    with subtest('One-liners'):
        stdout, stderr, status = run('-m', 'Pyjo', f'g("{base}/home").dom().at("title").text')
        is_ok(stdout, 'Home\n', 'g')
        stdout, stderr, status = run('-m', 'Pyjo', f'g("{base}/api/items").json("/items/1/name")')
        is_ok(stdout, 'Milk\n', 'JSON')
        stdout, stderr, status = run('-m', 'Pyjo', 'x("<p>Hello <b>World</b></p>").at("b").text')
        is_ok(stdout, 'World\n', 'x')
        stdout, stderr, status = run('-m', 'Pyjo', f'g("{base}/").code')
        is_ok(stdout, '200\n', 'ten redirects')
finally:
    server.close()

done_testing()
