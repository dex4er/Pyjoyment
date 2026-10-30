import Pyjo.IOLoop
import Pyjo.Test.Pyjo

from Pyjo.Test import *
from Pyjoyment.Lite import get, post

import time


# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor of Pyjo.Reactor.detect()


@get('/events')
def events(c):
    c.write_sse({'text': 'One', 'id': 24})
    c.write_sse({'text': 'Two'})
    c.finish()


@post('/delayed')
def delayed(c):
    c.write_sse({'type': 'test', 'text': 'One'})

    @Pyjo.IOLoop.timer(1)
    def timer(loop):
        c.write_sse({'type': 'test', 'text': 'Two'}, lambda c: c.finish())


@get('/infinite')
def infinite(c):
    c.write_sse()
    id = Pyjo.IOLoop.recurring(0.1, lambda loop: c.write_sse({'type': 'time', 'text': int(time.time())}))
    c.tx.on('finish', lambda tx: Pyjo.IOLoop.remove(id))


@get('/redirect')
def redirect(c):
    c.redirect_to('/infinite')


# Not in Mojolicious: a stream of one event, which stays open without another one, as sse_finish_ok of Mojo waits for
# the next event
@get('/quiet')
def quiet(c):
    c.helpers.inactivity_timeout(0)
    c.write_sse({'text': 'One'})


t = Pyjo.Test.Pyjo.new()
t.ua.max_redirects = 10

with subtest('Basic SSE connection'):
    (
        t.get_sse_ok('/events')
        .status_is(200)
        .content_type_is('text/event-stream')
        .sse_ok()
        .sse_type_is('message')
        .sse_text_is('One')
        .sse_text_isnt('Two')
        .sse_id_is('24')
        .sse_id_isnt('25')
        .sse_ok()
        .sse_type_is('message')
        .sse_type_isnt('foo')
        .sse_text_is('Two')
        .sse_finished_ok()
    )
    (
        t.get_sse_ok('/events')
        .status_is(200)
        .sse_ok()
        .sse_type_is('message')
        .sse_text_is('One')
        .sse_ok()
        .sse_type_is('message')
        .sse_text_is('Two')
        .sse_finished_ok()
    )

with subtest('Delayed events'):
    (
        t.post_sse_ok('/delayed')
        .status_is(200)
        .sse_ok()
        .sse_type_is('test')
        .sse_text_is('One')
        .sse_ok()
        .sse_type_is('test')
        .sse_text_is('Two')
        .sse_finished_ok()
    )

with subtest('Infinite stream of events'):
    (
        t.get_sse_ok('/infinite')
        .status_is(200)
        .sse_ok()
        .sse_type_is('time')
        .sse_text_like(r'\d+')
        .sse_text_unlike(r'test')
        .sse_ok()
        .sse_type_is('time')
        .sse_text_like(r'\d+')
        .sse_ok()
        .sse_type_is('time')
        .sse_text_like(r'\d+')
        .sse_finish_ok()
    )

with subtest('Early finish'):
    t.get_sse_ok('/events').status_is(200).sse_ok().sse_type_is('message').sse_text_is('One').sse_finish_ok()

with subtest('Follow redirect'):
    (
        t.get_sse_ok('/redirect')
        .status_is(200)
        .sse_ok()
        .sse_type_is('time')
        .sse_text_like(r'\d+')
        .sse_ok()
        .sse_type_is('time')
        .sse_text_like(r'\d+')
        .sse_finish_ok()
    )

# Not in Mojolicious: sse_finish_ok of a stream without events closes it at once
with subtest('Finish without events'):
    t.ua.inactivity_timeout = 30
    started = time.monotonic()
    t.get_sse_ok('/quiet').status_is(200).sse_ok().sse_text_is('One').sse_finish_ok()
    ok(time.monotonic() - started < 5, 'closed at once')

done_testing()
