import Pyjo.Test.Pyjo

from Pyjo.Test import *
from Pyjoyment.Lite import get, helper, websocket


# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor of Pyjo.Reactor.detect(); plan skip_all for a
# Perl older than 5.20 and -signatures, as the functions of Python have signatures


@helper('send_json')
def send_json(c, hash):
    c.send({'json': hash})


@get('/')
def root(c):
    c.render(text='works!')


@websocket('/json')
def json(c):
    @c.on('json')
    def message(c, hash):
        c.send_json(hash)


t = Pyjo.Test.Pyjo.new()

with subtest('Plain action'):
    t.get_ok('/').status_is(200).content_is('works!')

with subtest('WebSocket'):
    (
        t.websocket_ok('/json')
        .send_ok({'json': {'snowman': '☃'}})
        .message_ok()
        .json_message_is('', {'snowman': '☃'})
        .finish_ok()
    )

done_testing()
