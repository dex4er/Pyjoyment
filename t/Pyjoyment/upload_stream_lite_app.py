import Pyjo.Test.Pyjo

from Pyjo.Test import *
from Pyjoyment.Lite import get, hook, post

import re
import weakref


# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor of Pyjo.Reactor.detect()

# Stream multipart uploads into cache
cache = {}


@hook('after_build_tx')
def after_build_tx(tx, app):
    tx = weakref.proxy(tx)

    @tx.req.content.on('upgrade')
    def upgrade(single, multi):
        if not tx.req.url.path.contains('/upload'):
            return

        id = tx.req.url.query.param('id')

        @multi.on('part')
        def part(multi, single):
            @single.on('body')
            def body(single):
                if not re.search(r'my_file', single.headers.content_disposition or ''):
                    return
                single.unsubscribe('read')
                single.on('read', lambda single, chunk: cache.__setitem__(id, cache.get(id, b'') + chunk))


@post('/upload')
def upload(c):
    id = c.param('id')
    c.render(data=cache[id])


@get('/download')
def download(c):
    c.render(data=cache[c.param('id')])


t = Pyjo.Test.Pyjo.new()

with subtest('Small upload'):
    t.post_ok('/upload?id=23', form={'my_file': {'content': 'whatever'}}).status_is(200).content_is('whatever')

with subtest('Small download'):
    t.get_ok('/download?id=23').status_is(200).content_is('whatever')

with subtest('Big upload'):
    (
        t.post_ok('/upload?id=24', form={'my_file': {'content': '1234' * 131072}})
        .status_is(200)
        .content_is('1234' * 131072)
    )

with subtest('Big download'):
    t.get_ok('/download?id=24').status_is(200).content_is('1234' * 131072)

with subtest('Small download again'):
    t.get_ok('/download?id=23').status_is(200).content_is('whatever')

done_testing()
