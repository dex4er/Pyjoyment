import Pyjo.Log
import Pyjo.Test.Pyjo

from Pyjo.Test import *
from Pyjoyment.Lite import get, hook

import io
import json


# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor of Pyjo.Reactor.detect()


@hook('before_dispatch')
def before_dispatch(c):
    c.req.request_id = '17a60115'


@get('/simple')
def simple(c):
    c.log().debug('First!')
    c.log().info('Second!', 'Third!')
    c.app.log.debug('No context!')
    c.log().warn(lambda: ('Fourth!', 'Fifth!'))
    c.render(text='Simple!')


t = Pyjo.Test.Pyjo.new()

with subtest('Simple log messages with and without context'):
    handle = io.StringIO()
    t.app.log = Pyjo.Log.new(handle=handle)
    t.get_ok('/simple').status_is(200).content_is('Simple!')
    buffer = handle.getvalue()
    like_ok(buffer, (r'First.*Second.*Third.*No context!.*Fourth.*Fifth', 's'), 'right order')
    like_ok(buffer, r'\[.+\] \[\d+\] \[debug\] \[17a60115\] First!', 'message with request id')
    like_ok(buffer, (r'\[.+\] \[\d+\] \[info\] \[17a60115\] Second! Third!', 's'), 'message with request id')
    like_ok(buffer, r'\[.+\] \[\d+\] \[debug\] No context!', 'message without request id')
    like_ok(buffer, (r'\[.+\] \[\d+\] \[warn\] \[17a60115\] Fourth! Fifth!', 's'), 'message with request id')

with subtest('Concurrent requests'):
    handle = io.StringIO()
    t.app.log = Pyjo.Log.new(handle=handle)
    first = t.app.build_controller()
    first.req.request_id = '123-first'
    second = t.app.build_controller()
    second.req.request_id = '123-second'
    first.log().debug('First!')
    second.log().debug('Second!')
    first.log().debug('Third!')
    second.log().debug('Fourth!')
    t.app.log.debug('Fifth!')
    buffer = handle.getvalue()
    like_ok(buffer, (r'First.*Second.*Third.*Fourth.*Fifth', 's'), 'right order')
    like_ok(buffer, r'\[.+\] \[\d+\] \[debug\] \[123-first\] First!', 'message with request id')
    like_ok(buffer, r'\[.+\] \[\d+\] \[debug\] \[123-second\] Second!', 'message with request id')
    like_ok(buffer, r'\[.+\] \[\d+\] \[debug\] \[123-first\] Third!', 'message with request id')
    like_ok(buffer, r'\[.+\] \[\d+\] \[debug\] \[123-second\] Fourth!', 'message with request id')
    like_ok(buffer, r'\[.+\] \[\d+\] \[debug\] Fifth!', 'message without request id')

# Not in Mojolicious: the request id as a field of its own of a message of JSON
with subtest('JSON log messages'):
    handle = io.StringIO()
    t.app.log = Pyjo.Log.new(handle=handle, json=True)
    t.get_ok('/simple').status_is(200).content_is('Simple!')
    records = [json.loads(line) for line in handle.getvalue().splitlines()]
    first = next(record for record in records if record['message'] == 'First!')
    is_ok(first['request_id'], '17a60115', 'request id')
    is_ok(first['level'], 'debug', 'level')
    second = next(record for record in records if record['message'] == 'Second! Third!')
    is_ok(second['request_id'], '17a60115', 'request id')
    no_context = next(record for record in records if record['message'] == 'No context!')
    ok('request_id' not in no_context, 'message without request id')

done_testing()
