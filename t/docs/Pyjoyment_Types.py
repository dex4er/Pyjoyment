import Pyjo.Message.Response

from Pyjo.Test import *

from types import SimpleNamespace


with subtest('Synopsis'):
    import Pyjoyment.Types

    types = Pyjoyment.Types.new()
    types.type('foo', 'text/foo')
    is_ok(types.type('foo'), 'text/foo', 'type of foo')

with subtest('mapping'):
    types = Pyjoyment.Types.new()
    mapping = types.mapping
    is_ok(mapping['png'], ['image/png'], 'default')
    types.mapping = {'png': ['image/png']}
    is_deeply_ok(types.mapping, {'png': ['image/png']}, 'set')

with subtest('new'):
    types = Pyjoyment.Types.new()
    is_ok(types.type('html'), 'text/html;charset=UTF-8', 'default mapping')
    types = Pyjoyment.Types.new(mapping={'png': ['image/png']})
    is_deeply_ok(types.mapping, {'png': ['image/png']}, 'mapping')

with subtest('content_type'):
    types = Pyjoyment.Types.new()
    # TODO: Pyjoyment.Controller.new(), when it is ported; until then a controller with a response
    c = SimpleNamespace(res=Pyjo.Message.Response.new())
    types.content_type(c, ext='json')
    is_ok(c.res.headers.content_type, 'application/json;charset=UTF-8', 'ext')
    c.res.headers.remove('Content-Type')
    types.content_type(c, file='foo/bar.png')
    is_ok(c.res.headers.content_type, 'image/png', 'file')

with subtest('detect'):
    types = Pyjoyment.Types.new()
    exts = types.detect('text/html, application/json;q=9')
    is_deeply_ok(exts, ['json', 'htm', 'html'], 'extensions')

    # List detected extensions prioritized
    is_deeply_ok(types.detect('application/json, text/xml;q=0.1'), ['json', 'xml'], 'prioritized')

with subtest('file_type'):
    types = Pyjoyment.Types.new()
    type = types.file_type('foo/bar.png')
    is_ok(type, 'image/png', 'type of the file')

with subtest('type'):
    types = Pyjoyment.Types.new()
    type = types.type('png')
    is_ok(type, 'image/png', 'type')
    is_ok(types.type('png', 'image/png'), types, 'returns the types')
    is_ok(types.type('json', ['application/json', 'text/x-json']), types, 'returns the types')
    is_ok(types.type('json'), 'application/json', 'first type')
    is_deeply_ok(types.detect('text/x-json'), ['json'], 'alternative')

done_testing()
