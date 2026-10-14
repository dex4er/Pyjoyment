# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor that Pyjo.Reactor.detect gives

import Pyjo.UserAgent

from Pyjo.File import tempdir
from Pyjo.Test import *

import importlib
import os
import re
import sys


# The minimal Mojolicious::Lite of the tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
Lite = importlib.import_module('Lite')
app, get = Lite.app, Lite.get

# Silence
app.log.level = 'trace'
app.log.unsubscribe('message')


@get('/simple')
def simple(c):
    c.res.headers.accept_ranges = 'bytes'
    return c.render(data=b'CHUNK1CHUNK2CHUNK3')


@get('/redirect')
def redirect(c):
    return c.redirect_to('/simple')


@get('/resume')
def resume(c):
    c.res.headers.accept_ranges = 'bytes'
    if c.req.method == 'HEAD':
        return c.render(data=b'CHUNK1CHUNK2CHUNK3')
    range = c.req.headers.range
    if not range:
        return c.write(b'CHUNK1').finish()
    if range == 'bytes=6-18':
        return c.write(b'CHUNK2').finish()
    return c.write(b'CHUNK3').finish()


@get('/stream')
def stream(c):
    chunks = [b'CHUNK1', b'CHUNK2', b'CHUNK3', b'CHUNK4']
    c.res.code = 200
    c.res.headers.content_type = 'text/plain'

    def cb(content, *args):
        chunk = chunks.pop(0) if chunks else b''
        content.write_chunk(chunk, cb if chunk else None)

    cb(c.res.content)
    c.rendered()


@get('/header')
def header(c):
    custom = c.req.headers.header('X-Custom-Header') or 'MISSINGHEADER'
    c.res.headers.accept_ranges = 'bytes'
    return c.render(data=custom.encode())


dir = tempdir()
ua = Pyjo.UserAgent.new()

with subtest('Basic file download'):
    file = dir.child('simple1.txt')
    ok(file.download('/simple'), 'file downloaded')
    ok(os.path.exists(file), 'file exists')
    is_ok(file.slurp(), b'CHUNK1CHUNK2CHUNK3', 'right content')

with subtest('File already downloaded'):
    file = dir.child('simple1.txt')
    is_ok(file.slurp(), b'CHUNK1CHUNK2CHUNK3', 'right content')
    ok(file.download('/simple'), 'file downloaded')
    is_ok(file.slurp(), b'CHUNK1CHUNK2CHUNK3', 'right content')

with subtest('Basic file download (custom header)'):
    file = dir.child('header1.txt')
    ok(file.download('/header', headers={'X-Custom-Header': 'CORRECTFILECONTENT'}), 'file downloaded')
    ok(os.path.exists(file), 'file exists')
    is_ok(file.slurp(), b'CORRECTFILECONTENT', 'right content')

    file2 = dir.child('header2.txt')
    ok(file2.download('/header'), 'file downloaded')
    ok(os.path.exists(file2), 'file exists')
    is_ok(file2.slurp(), b'MISSINGHEADER', 'right content')

with subtest('Basic file download (redirect)'):
    file = dir.child('redirect1.txt')
    ok(file.download('/redirect'), 'file downloaded')
    ok(os.path.exists(file), 'file exists')
    is_ok(file.slurp(), b'CHUNK1CHUNK2CHUNK3', 'right content')

    ua2 = Pyjo.UserAgent.new(max_redirects=0)
    file2 = dir.child('redirect2.txt')
    ok(file2.download('/redirect', ua=ua2), 'file downloaded')
    ok(os.path.exists(file2), 'file exists')
    is_ok(file2.slurp(), b'', 'right content')

with subtest('Existing file is larger'):
    file = dir.child('simple2.txt').spew(b'CHUNK1CHUNK2CHUNK3CHUNK4')
    throws_ok(lambda: file.download('/simple'), re.compile(r'Download error: File size mismatch'), 'right error')

with subtest('Resumed file download'):
    file = dir.child('resume1.txt')
    ok(not file.download('/resume'), 'file partially downloaded')
    ok(not file.download('/resume'), 'file continued')
    ok(file.download('/resume'), 'file downloaded')
    ok(os.path.exists(file), 'file exists')
    is_ok(file.slurp(), b'CHUNK1CHUNK2CHUNK3', 'right content')

with subtest('Missing file'):
    file = dir.child('missing1.txt')
    throws_ok(lambda: file.download('/missing'), re.compile(r'404 response: Not Found'), 'file not found')

with subtest('File of unknown size'):
    file = dir.child('stream1.txt').spew(b'C')
    throws_ok(lambda: file.download('/stream'), re.compile(r'Download error: Unknown file size'), 'right error')

with subtest('File of unknown size downloaded'):
    file = dir.child('stream2.txt')
    ok(file.download('/stream'), 'file downloaded')
    ok(os.path.exists(file), 'file exists')
    is_ok(file.slurp(), b'CHUNK1CHUNK2CHUNK3CHUNK4', 'right content')

done_testing()
