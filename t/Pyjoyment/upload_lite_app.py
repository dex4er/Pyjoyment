import Pyjo.Asset.File
import Pyjo.Test.Pyjo

from Pyjo.Test import *
from Pyjoyment.Lite import get, post


# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor of Pyjo.Reactor.detect()


@get('/request_size')
def request_size(c):
    c.render(text=c.req.max_message_size)


@post('/upload')
def upload(c):
    file = c.param('file')
    headers = file.headers
    c.render(
        text=file.filename
        + file.asset.slurp().decode('latin-1')
        + c.param('test')
        + (headers.content_type or '')
        + (headers.header('X-X') or '')
    )


@post('/multi')
def multi(c):
    uploads = [upload for name in c.every_param('name') for upload in c.every_param(name)]
    c.render(text=''.join(upload.filename + upload.asset.slurp().decode('latin-1') for upload in uploads))


t = Pyjo.Test.Pyjo.new()

with subtest('Request size limit'):
    t.get_ok('/request_size').status_is(200).content_is('16777216')
    t.app.max_request_size = 0
    t.get_ok('/request_size').status_is(200).content_is('0')

with subtest('Asset and filename'):
    file = Pyjo.Asset.File.new().add_chunk(b'lalala')
    (
        t.post_ok('/upload', form={'file': {'file': file, 'filename': 'x'}, 'test': 'tset'})
        .status_is(200)
        .content_is('xlalalatset')
    )

with subtest('Path'):
    file = Pyjo.Asset.File.new().add_chunk(b'lalala')
    t.post_ok('/upload', form={'file': {'file': file.path}, 'test': 'foo'}).status_is(200).content_like(r'lalalafoo$')

with subtest('Memory'):
    (
        t.post_ok('/upload', form={'file': {'content': 'alalal'}, 'test': 'tset'})
        .status_is(200)
        .content_is('filealalaltset')
    )

with subtest('Memory with headers'):
    hash = {'content': 'alalal', 'Content-Type': 'foo/bar', 'X-X': 'Y'}
    t.post_ok('/upload', form={'file': hash, 'test': 'tset'}).status_is(200).content_is('filealalaltsetfoo/barY')

with subtest('Multiple file uploads'):
    (
        t.post_ok('/multi?name=file1&name=file2', form={'file1': {'content': '1111'}, 'file2': {'content': '11112222'}})
        .status_is(200)
        .content_is('file11111file211112222')
    )

with subtest('Multiple file uploads reverse'):
    (
        t.post_ok('/multi?name=file2&name=file1', form={'file1': {'content': '1111'}, 'file2': {'content': '11112222'}})
        .status_is(200)
        .content_is('file211112222file11111')
    )

with subtest('Multiple file uploads with same name'):
    (
        t.post_ok(
            '/multi?name=file',
            form={'file': [{'content': 'just', 'filename': 'one.txt'}, {'content': 'works', 'filename': 'two.txt'}]},
        )
        .status_is(200)
        .content_is('one.txtjusttwo.txtworks')
    )

done_testing()
