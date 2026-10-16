import Pyjo.Test.Pyjo
import Pyjoyment

from Pyjo.Test import *
from Pyjoyment.Lite import *

import re


any('/', {'text': 'Hello Test!'})


@websocket('/websocket')
def ws(c):
    c.send({'text': b'testing message'})


@any('/sse')
def sse(c):
    c.write_sse({'text': 'One', 'id': 23})
    c.write_sse({'text': 'Two'})
    c.write_sse({'text': 'Three'})
    c.write_sse({'text': 'Four'})
    c.finish()


t = Pyjo.Test.Pyjo.new()

with subtest('Basics'):
    isa_ok(t.app, Pyjoyment.object, 'right class')
    t.get_ok('/').status_is(200).content_is('Hello Test!')
    ok(t.success, 'success')
    t.handler = lambda *args: 1
    t.status_is(404)
    ok(t.success, 'success')
    t.handler = lambda *args: 0
    t.status_is(404)
    ok(not t.success, 'no success')

with subtest('or'):
    or_ = ''

    def false(t):
        global or_
        or_ += 'false'

    def true(t):
        global or_
        or_ += 'true'

    t.success = False
    t.or_(false)
    t.success = True
    t.or_(true)
    is_ok(or_, 'false', 'right result')

args = []


def handler(*values):
    args[:] = values
    return len(values)


t.handler = handler

with subtest('get_ok'):
    t.get_ok('/')
    is_deeply_ok(args, ['ok', 1, 'GET /'], 'right result')
    is_ok(t.tx.req.method, 'GET', 'right method')

with subtest('head_ok'):
    t.head_ok('/')
    is_deeply_ok(args, ['ok', 1, 'HEAD /'], 'right result')
    is_ok(t.tx.req.method, 'HEAD', 'right method')

with subtest('post_ok'):
    t.post_ok('/')
    is_deeply_ok(args, ['ok', 1, 'POST /'], 'right result')
    is_ok(t.tx.req.method, 'POST', 'right method')

with subtest('put_ok'):
    t.put_ok('/')
    is_deeply_ok(args, ['ok', 1, 'PUT /'], 'right result')
    is_ok(t.tx.req.method, 'PUT', 'right method')

with subtest('patch_ok'):
    t.patch_ok('/')
    is_deeply_ok(args, ['ok', 1, 'PATCH /'], 'right result')
    is_ok(t.tx.req.method, 'PATCH', 'right method')

with subtest('delete_ok'):
    t.delete_ok('/')
    is_deeply_ok(args, ['ok', 1, 'DELETE /'], 'right result')
    is_ok(t.tx.req.method, 'DELETE', 'right method')

with subtest('options_ok'):
    t.options_ok('/')
    is_deeply_ok(args, ['ok', 1, 'OPTIONS /'], 'right result')
    is_ok(t.tx.req.method, 'OPTIONS', 'right method')

with subtest('query_ok'):
    t.query_ok('/')
    is_deeply_ok(args, ['ok', 1, 'QUERY /'], 'right result')
    is_ok(t.tx.req.method, 'QUERY', 'right method')

with subtest('status_is'):
    t.status_is(200)
    is_deeply_ok(args, ['is', 200, 200, '200 OK'], 'right result')
    t.status_is(404, 'some description')
    is_deeply_ok(args, ['is', 200, 404, 'some description'], 'right result')

with subtest('content_is'):
    t.content_is('Hello Test!')
    is_deeply_ok(args, ['is', 'Hello Test!', 'Hello Test!', 'exact match for content'], 'right result')
    t.content_is('Hello Test!', 'some description')
    is_deeply_ok(args, ['is', 'Hello Test!', 'Hello Test!', 'some description'], 'right result')

with subtest('content_isnt'):
    t.content_isnt('Goodbye Test!')
    is_deeply_ok(args, ['isnt', 'Hello Test!', 'Goodbye Test!', 'no match for content'], 'right result')
    t.content_isnt('Goodbye Test!', 'some description')
    is_deeply_ok(args, ['isnt', 'Hello Test!', 'Goodbye Test!', 'some description'], 'right result')

with subtest('content_like'):
    t.content_like(re.compile(r'Hello Test!'))
    is_deeply_ok(args, ['like', 'Hello Test!', re.compile(r'Hello Test!'), 'content is similar'], 'right result')
    t.content_like(re.compile(r'Hello Test!'), 'some description')
    is_deeply_ok(args, ['like', 'Hello Test!', re.compile(r'Hello Test!'), 'some description'], 'right result')

with subtest('content_type_is'):
    t.content_type_is('text/html;charset=UTF-8')
    is_deeply_ok(
        args,
        ['is', 'text/html;charset=UTF-8', 'text/html;charset=UTF-8', 'Content-Type: text/html;charset=UTF-8'],
        'right result',
    )
    t.content_type_is('text/html;charset=UTF-8', 'some description')
    is_deeply_ok(args, ['is', 'text/html;charset=UTF-8', 'text/html;charset=UTF-8', 'some description'], 'right result')

with subtest('content_type_isnt'):
    t.content_type_isnt('image/png')
    is_deeply_ok(args, ['isnt', 'text/html;charset=UTF-8', 'image/png', 'not Content-Type: image/png'], 'right result')
    t.content_type_isnt('image/png', 'some description')
    is_deeply_ok(args, ['isnt', 'text/html;charset=UTF-8', 'image/png', 'some description'], 'right result')

with subtest('content_type_like'):
    t.content_type_like(re.compile(r'text/html;charset=UTF-8'))
    is_deeply_ok(
        args,
        ['like', 'text/html;charset=UTF-8', re.compile(r'text/html;charset=UTF-8'), 'Content-Type is similar'],
        'right result',
    )
    t.content_type_like(re.compile(r'text/html;charset=UTF-8'), 'some description')
    is_deeply_ok(
        args,
        ['like', 'text/html;charset=UTF-8', re.compile(r'text/html;charset=UTF-8'), 'some description'],
        'right result',
    )

with subtest('content_type_unlike'):
    t.content_type_unlike(re.compile(r'image/png'))
    is_deeply_ok(
        args,
        ['unlike', 'text/html;charset=UTF-8', re.compile(r'image/png'), 'Content-Type is not similar'],
        'right result',
    )
    t.content_type_unlike(re.compile(r'image/png'), 'some description')
    is_deeply_ok(
        args, ['unlike', 'text/html;charset=UTF-8', re.compile(r'image/png'), 'some description'], 'right result'
    )

with subtest('content_unlike'):
    t.content_unlike(re.compile(r'Goodbye Test!'))
    is_deeply_ok(
        args, ['unlike', 'Hello Test!', re.compile(r'Goodbye Test!'), 'content is not similar'], 'right result'
    )
    t.content_unlike(re.compile(r'Goodbye Test!'), 'some description')
    is_deeply_ok(args, ['unlike', 'Hello Test!', re.compile(r'Goodbye Test!'), 'some description'], 'right result')

with subtest('attr_is'):
    t.tx.res.body = b'<p id="test">Test</p>'
    t.attr_is('p', 'id', 'wrong')
    is_deeply_ok(args, ['is', 'test', 'wrong', 'exact match for attribute "id" at selector "p"'], 'right result')
    t.attr_is('p', 'id', 'wrong', 'some description')
    is_deeply_ok(args, ['is', 'test', 'wrong', 'some description'], 'right result')

with subtest('attr_isnt'):
    t.tx.res.body = b'<p id="test">Test</p>'
    t.attr_isnt('p', 'id', 'wrong')
    is_deeply_ok(args, ['isnt', 'test', 'wrong', 'no match for attribute "id" at selector "p"'], 'right result')
    t.attr_isnt('p', 'id', 'wrong', 'some description')
    is_deeply_ok(args, ['isnt', 'test', 'wrong', 'some description'], 'right result')

with subtest('attr_like'):
    t.tx.res.body = b'<p id="test">Test</p>'
    t.attr_like('p', 'id', re.compile(r'test'))
    is_deeply_ok(
        args, ['like', 'test', re.compile(r'test'), 'similar match for attribute "id" at selector "p"'], 'right result'
    )
    t.attr_like('p', 'id', re.compile(r'test'), 'some description')
    is_deeply_ok(args, ['like', 'test', re.compile(r'test'), 'some description'], 'right result')

with subtest('attr_unlike'):
    t.tx.res.body = b'<p id="test">Test</p>'
    t.attr_unlike('p', 'id', re.compile(r'wrong'))
    is_deeply_ok(
        args,
        ['unlike', 'test', re.compile(r'wrong'), 'no similar match for attribute "id" at selector "p"'],
        'right result',
    )
    t.attr_unlike('p', 'id', re.compile(r'wrong'), 'some description')
    is_deeply_ok(args, ['unlike', 'test', re.compile(r'wrong'), 'some description'], 'right result')

with subtest('header_exists'):
    t.header_exists('Content-Type')
    is_deeply_ok(args, ['ok', 1, 'header "Content-Type" exists'], 'right result')
    t.header_exists('Content-Type', 'some description')
    is_deeply_ok(args, ['ok', 1, 'some description'], 'right result')

with subtest('header_exists_not'):
    t.header_exists_not('X-Exists-Not')
    is_deeply_ok(args, ['ok', 1, 'no "X-Exists-Not" header'], 'right result')
    t.header_exists_not('X-Exists-Not', 'some description')
    is_deeply_ok(args, ['ok', 1, 'some description'], 'right result')

with subtest('header_is'):
    t.header_is('Content-Type', 'text/html;charset=UTF-8')
    is_deeply_ok(
        args,
        ['is', 'text/html;charset=UTF-8', 'text/html;charset=UTF-8', 'Content-Type: text/html;charset=UTF-8'],
        'right result',
    )
    t.header_is('Content-Type', 'text/html;charset=UTF-8', 'some description')
    is_deeply_ok(args, ['is', 'text/html;charset=UTF-8', 'text/html;charset=UTF-8', 'some description'], 'right result')

with subtest('header_isnt'):
    t.header_isnt('Content-Type', 'image/png')
    is_deeply_ok(args, ['isnt', 'text/html;charset=UTF-8', 'image/png', 'not Content-Type: image/png'], 'right result')
    t.header_isnt('Content-Type', 'image/png', 'some description')
    is_deeply_ok(args, ['isnt', 'text/html;charset=UTF-8', 'image/png', 'some description'], 'right result')

with subtest('header_like'):
    t.header_like('Content-Type', re.compile(r'text/html;charset=UTF-8'))
    is_deeply_ok(
        args,
        ['like', 'text/html;charset=UTF-8', re.compile(r'text/html;charset=UTF-8'), 'Content-Type is similar'],
        'right result',
    )
    t.header_like('Content-Type', re.compile(r'text/html;charset=UTF-8'), 'some description')
    is_deeply_ok(
        args,
        ['like', 'text/html;charset=UTF-8', re.compile(r'text/html;charset=UTF-8'), 'some description'],
        'right result',
    )

with subtest('header_unlike'):
    t.header_unlike('Content-Type', re.compile(r'image/png'))
    is_deeply_ok(
        args,
        ['unlike', 'text/html;charset=UTF-8', re.compile(r'image/png'), 'Content-Type is not similar'],
        'right result',
    )
    t.header_unlike('Content-Type', re.compile(r'image/png'), 'some description')
    is_deeply_ok(
        args, ['unlike', 'text/html;charset=UTF-8', re.compile(r'image/png'), 'some description'], 'right result'
    )

with subtest('message_is'):
    t.websocket_ok('/websocket').message_ok().message_is('testing message')
    is_deeply_ok(args, ['is', 'testing message', 'testing message', 'exact match for message'], 'right result')
    t.websocket_ok('/websocket').message_ok().message_is('testing message', 'some description')
    is_deeply_ok(args, ['is', 'testing message', 'testing message', 'some description'], 'right result')
    t.websocket_ok('/websocket').message_ok().message_is('incorrect testing message')
    is_deeply_ok(
        args, ['is', 'testing message', 'incorrect testing message', 'exact match for message'], 'right result'
    )

with subtest('message_isnt'):
    t.websocket_ok('/websocket').message_ok().message_isnt('testing message')
    is_deeply_ok(args, ['isnt', 'testing message', 'testing message', 'no match for message'], 'right result.')
    t.websocket_ok('/websocket').message_ok().message_isnt('testing message', 'some description')
    is_deeply_ok(args, ['isnt', 'testing message', 'testing message', 'some description'], 'right result')
    t.websocket_ok('/websocket').message_ok().message_isnt('incorrect testing message')
    is_deeply_ok(args, ['isnt', 'testing message', 'incorrect testing message', 'no match for message'], 'right result')

with subtest('message_like'):
    t.websocket_ok('/websocket').message_ok().message_like(re.compile(r'^test'))
    is_deeply_ok(args, ['like', 'testing message', re.compile(r'^test'), 'message is similar'], 'right result')
    t.websocket_ok('/websocket').message_ok().message_like(re.compile(r'^test'), 'some description')
    is_deeply_ok(args, ['like', 'testing message', re.compile(r'^test'), 'some description'], 'right result')

with subtest('message_ok'):
    t.websocket_ok('/websocket').message_ok()
    is_deeply_ok(args, ['ok', True, 'message received'], 'right result')
    t.websocket_ok('/websocket').message_ok('some description')
    is_deeply_ok(args, ['ok', True, 'some description'], 'right result')
    t.websocket_ok('/').message_ok()
    is_deeply_ok(args, ['ok', False, 'message received'], 'right result')

with subtest('message_unlike'):
    t.websocket_ok('/websocket').message_ok().message_unlike(re.compile(r'^test'))
    is_deeply_ok(args, ['unlike', 'testing message', re.compile(r'^test'), 'message is not similar'], 'right result')
    t.websocket_ok('/websocket').message_ok().message_unlike(re.compile(r'^test'), 'some description')
    is_deeply_ok(args, ['unlike', 'testing message', re.compile(r'^test'), 'some description'], 'right result')

with subtest('SSE'):
    with subtest('get_sse_ok'):
        t.get_sse_ok('/sse')
        is_deeply_ok(args, ['ok', 1, 'SSE connection established: GET /sse'], 'right result')
        t.sse_finish_ok()
        is_deeply_ok(args, ['ok', 1, 'closed SSE connection'], 'right result')

    with subtest('post_sse_ok'):
        t.post_sse_ok('/sse')
        is_deeply_ok(args, ['ok', 1, 'SSE connection established: POST /sse'], 'right result')
        t.sse_ok().sse_ok().sse_ok().sse_ok().sse_finished_ok()
        is_deeply_ok(args, ['ok', 1, 'SSE connection has been closed'], 'right result')

    # The id of an event is a string, as it comes from the wire, which Perl compares with a number
    with subtest('sse_id_is'):
        t.get_sse_ok('/sse').sse_ok().sse_id_is('Two')
        is_deeply_ok(args, ['is', '23', 'Two', 'exact match for SSE event id'], 'right result')
        t.sse_id_is('Two', 'some description')
        is_deeply_ok(args, ['is', '23', 'Two', 'some description'], 'right result')
        t.sse_finish_ok()

    with subtest('sse_id_isnt'):
        t.get_sse_ok('/sse').sse_ok().sse_id_isnt('Two')
        is_deeply_ok(args, ['isnt', '23', 'Two', 'no match for SSE event id'], 'right result')
        t.sse_id_isnt('Two', 'some description')
        is_deeply_ok(args, ['isnt', '23', 'Two', 'some description'], 'right result')
        t.sse_finish_ok()

    with subtest('sse_type_is'):
        t.get_sse_ok('/sse').sse_ok().sse_type_is('Two')
        is_deeply_ok(args, ['is', 'message', 'Two', 'exact match for SSE event type'], 'right result')
        t.sse_type_is('Two', 'some description')
        is_deeply_ok(args, ['is', 'message', 'Two', 'some description'], 'right result')
        t.sse_finish_ok()

    with subtest('sse_type_isnt'):
        t.get_sse_ok('/sse').sse_ok().sse_type_isnt('Two')
        is_deeply_ok(args, ['isnt', 'message', 'Two', 'no match for SSE event type'], 'right result')
        t.sse_type_isnt('Two', 'some description')
        is_deeply_ok(args, ['isnt', 'message', 'Two', 'some description'], 'right result')
        t.sse_finish_ok()

    with subtest('sse_text_is'):
        t.get_sse_ok('/sse').sse_ok().sse_text_is('Two')
        is_deeply_ok(args, ['is', 'One', 'Two', 'exact match for SSE event text'], 'right result')
        t.sse_text_is('Two', 'some description')
        is_deeply_ok(args, ['is', 'One', 'Two', 'some description'], 'right result')
        t.sse_finish_ok()

    with subtest('sse_text_isnt'):
        t.get_sse_ok('/sse').sse_ok().sse_text_isnt('Two')
        is_deeply_ok(args, ['isnt', 'One', 'Two', 'no match for SSE event text'], 'right result')
        t.sse_text_isnt('Two', 'some description')
        is_deeply_ok(args, ['isnt', 'One', 'Two', 'some description'], 'right result')
        t.sse_finish_ok()

    with subtest('sse_text_like'):
        t.get_sse_ok('/sse').sse_ok().sse_text_like(re.compile(r'Two'))
        is_deeply_ok(args, ['like', 'One', re.compile(r'Two'), 'similar match for SSE event text'], 'right result')
        t.sse_text_like(re.compile(r'Two'), 'some description')
        is_deeply_ok(args, ['like', 'One', re.compile(r'Two'), 'some description'], 'right result')
        t.sse_finish_ok()

    with subtest('sse_text_unlike'):
        t.get_sse_ok('/sse').sse_ok().sse_text_unlike(re.compile(r'Two'))
        is_deeply_ok(args, ['unlike', 'One', re.compile(r'Two'), 'no similar match for SSE event text'], 'right result')
        t.sse_text_unlike(re.compile(r'Two'), 'some description')
        is_deeply_ok(args, ['unlike', 'One', re.compile(r'Two'), 'some description'], 'right result')
        t.sse_finish_ok()

done_testing()
