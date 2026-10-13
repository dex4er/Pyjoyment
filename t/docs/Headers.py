from Pyjo.Test import *

import re


with subtest('Synopsis'):
    import Pyjo.Headers

    # Parse
    headers = Pyjo.Headers.new()
    headers.parse('Content-Length: 42\x0d\x0a')
    headers.parse('Content-Type: text/html\x0d\x0a\x0d\x0a')
    is_ok(headers.content_length, '42', 'headers.content_length')
    is_ok(headers.content_type, 'text/html', 'headers.content_type')

    # Build
    headers = Pyjo.Headers.new()
    headers.content_length = 42
    headers.content_type = 'text/plain'
    is_ok(headers.to_str(), 'Content-Length: 42\x0d\x0aContent-Type: text/plain', 'headers.to_str()')

with subtest('Description'):
    # "text/html"
    is_ok(Pyjo.Headers.new({'Content-Type': 'text/html'})['content-type'], 'text/html', 'mapping')

    # [('Vary', 'Accept'), ('Vary', 'Accept-Encoding')]
    is_ok(
        Pyjo.Headers.new([('Vary', 'Accept'), ('Vary', 'Accept-Encoding')]).to_list(),
        [('Vary', 'Accept'), ('Vary', 'Accept-Encoding')],
        'to_list()',
    )

with subtest('new'):
    import http.client
    import io

    headers = Pyjo.Headers.new()
    is_ok(len(headers), 0, 'new()')
    headers = Pyjo.Headers.new({'Content-Type': 'text/html'})
    is_ok(headers.content_type, 'text/html', 'dict')
    headers = Pyjo.Headers.new([('Vary', 'Accept'), ('Vary', 'Accept-Encoding')])
    is_ok(headers.vary, 'Accept, Accept-Encoding', 'list of pairs')

    class HTTPResponse:
        headers = http.client.parse_headers(io.BytesIO(b'Content-Type: text/plain\r\n\r\n'))

    http_response = HTTPResponse()
    headers = Pyjo.Headers.new(http_response.headers)
    is_ok(headers.content_type, 'text/plain', 'http.client.HTTPMessage')

with subtest('max_line_size'):
    size = headers.max_line_size
    is_ok(size, 8192, 'size')
    headers.max_line_size = 1024
    is_ok(headers.max_line_size, 1024, 'headers.max_line_size')

with subtest('max_lines'):
    num = headers.max_lines
    is_ok(num, 100, 'num')
    headers.max_lines = 200
    is_ok(headers.max_lines, 200, 'headers.max_lines')

with subtest('__bool__'):
    boolean = bool(Pyjo.Headers.new())
    is_ok(boolean, True, 'boolean')

with subtest('__contains__'):
    boolean = 'Content-Type' in headers
    is_ok(boolean, True, 'boolean')

with subtest('__getitem__'):
    value = headers['Content-Type']
    is_ok(value, 'text/plain', 'value')
    throws_ok(lambda: headers['X-Missing'], KeyError, 'KeyError')

with subtest('__iter__'):
    names = list(headers)
    is_ok(names, ['Content-Type'], 'names')

with subtest('__len__'):
    size = len(headers)
    is_ok(size, 1, 'size')

with subtest('__str__'):
    string = str(headers)
    is_ok(string, 'Content-Type: text/plain', 'string')

with subtest('Shortcuts'):
    headers = Pyjo.Headers.new()
    for attr, shortcut in vars(Pyjo.Headers.object).items():
        if isinstance(shortcut, Pyjo.Headers._Shortcut):
            example = re.search(rf'headers\.{attr} = (.+)', shortcut.__doc__ or '')
            value = eval(example[1]) if example else None
            setattr(headers, attr, value)
            is_ok(getattr(headers, attr), str(value), f'headers.{attr}')

with subtest('add'):
    headers = Pyjo.Headers.new()
    headers = headers.add('Foo', 'one value')
    headers = headers.add('Foo', 'first value', 'second value')
    is_ok(headers.every_header('Foo'), ['one value', 'first value', 'second value'], 'headers')

    # "Vary: Accept
    #  Vary: Accept-Encoding"
    is_ok(
        Pyjo.Headers.new().add('Vary', 'Accept').add('Vary', 'Accept-Encoding').to_str(),
        'Vary: Accept\x0d\x0aVary: Accept-Encoding',
        'to_str()',
    )

with subtest('append'):
    headers = Pyjo.Headers.new()
    headers = headers.append('Vary', 'Accept-Encoding')
    is_ok(headers.vary, 'Accept-Encoding', 'headers')

    # "Vary: Accept"
    is_ok(Pyjo.Headers.new().append('Vary', 'Accept').to_str(), 'Vary: Accept', 'one value')

    # "Vary: Accept, Accept-Encoding"
    is_ok(
        Pyjo.Headers.new().set(vary='Accept').append('Vary', 'Accept-Encoding').to_str(),
        'Vary: Accept, Accept-Encoding',
        'flattened',
    )

with subtest('clone'):
    clone = headers.clone()
    is_ok(str(clone), str(headers), 'clone')
    isnt_ok(id(clone), id(headers), 'another object')

with subtest('dehop'):
    headers = Pyjo.Headers.new({'Connection': 'close', 'Server': 'Pyjoyment'})
    headers = headers.dehop()
    is_ok(headers.names(), ['Server'], 'headers')

with subtest('every_header'):
    headers = Pyjo.Headers.new([('Location', '/foo'), ('Location', '/bar')])
    all = headers.every_header('Location')
    is_ok(all, ['/foo', '/bar'], 'all')

    # Get first header value
    is_ok(headers.every_header('Location')[0], '/foo', 'first value')

with subtest('from_dict'):
    headers = headers.from_dict({'Cookie': 'a=b'})
    is_ok(headers.cookie, 'a=b', 'one value')
    headers = headers.from_dict({'Cookie': ['a=b', 'c=d']})
    is_ok(headers.every_header('Cookie'), ['a=b', 'a=b', 'c=d'], 'values')
    headers = headers.from_dict({})
    is_ok(len(headers), 0, 'removed')

with subtest('get'):
    headers = Pyjo.Headers.new({'Content-Type': 'text/html'})
    value = headers.get('Content-Type')
    is_ok(value, 'text/html', 'value')
    value = headers.get('X-Missing', 'text/plain')
    is_ok(value, 'text/plain', 'default')

with subtest('header'):
    value = headers.header('Foo')
    is_ok(value, None, 'value')
    headers = headers.header('Foo', 'one value')
    is_ok(headers.header('Foo'), 'one value', 'one value')
    headers = headers.header('Foo', 'first value', 'second value')
    is_ok(headers.header('Foo'), 'first value, second value', 'values')

with subtest('is_finished'):
    boolean = headers.is_finished
    is_ok(boolean, False, 'boolean')

with subtest('is_limit_exceeded'):
    boolean = headers.is_limit_exceeded
    is_ok(boolean, False, 'boolean')

with subtest('items'):
    items = headers.items()
    is_ok(items, [('Content-Type', 'text/html'), ('Foo', 'first value, second value')], 'items')

with subtest('keys'):
    names = headers.keys()
    is_ok(names, ['Content-Type', 'Foo'], 'names')

with subtest('leftovers'):
    headers = Pyjo.Headers.new().parse('Foo: bar\x0d\x0a\x0d\x0aHello')
    data = headers.leftovers()
    is_ok(data, b'Hello', 'data')

with subtest('links'):
    headers = Pyjo.Headers.new()
    links = headers.links
    is_ok(links, {}, 'links')
    headers.links = {'next': 'http://example.com/foo', 'prev': 'http://example.com/bar'}
    is_ok(headers.link, '<http://example.com/foo>; rel="next", <http://example.com/bar>; rel="prev"', 'set')

    # Extract information about next page
    headers.link = '<http://example.com/foo>; rel="next"; title="Next"'
    is_ok(headers.links['next']['link'], 'http://example.com/foo', 'link')
    is_ok(headers.links['next']['title'], 'Next', 'title')

with subtest('names'):
    names = headers.names()
    is_ok(names, ['Link'], 'names')

    # Names of all headers
    is_ok([name for name in headers.names()], ['Link'], 'for name in headers.names()')

with subtest('parse'):
    headers = Pyjo.Headers.new()
    headers = headers.parse('Content-Type: text/plain\x0d\x0a\x0d\x0a')
    is_ok(headers.content_type, 'text/plain', 'headers')

with subtest('referer'):
    referrer = headers.referer
    is_ok(referrer, None, 'referrer')
    headers.referer = 'http://example.com'
    is_ok(headers.referrer, 'http://example.com', 'headers.referer')

with subtest('referrer'):
    referrer = headers.referrer
    is_ok(referrer, 'http://example.com', 'referrer')
    headers.referrer = 'http://example.com'
    is_ok(headers.header('Referer'), 'http://example.com', 'headers.referrer')

with subtest('remove'):
    headers = headers.remove('Content-Type')
    is_ok(headers.content_type, None, 'headers')

with subtest('to_bytes'):
    data = headers.to_bytes()
    is_ok(data, b'Referer: http://example.com', 'data')

with subtest('to_dict'):
    headers = Pyjo.Headers.new({'DNT': 1, 'Vary': ['Accept', 'Accept-Encoding']})
    single = headers.to_dict()
    is_ok(single, {'DNT': '1', 'Vary': 'Accept, Accept-Encoding'}, 'single')
    multi = headers.to_dict(True)
    is_ok(multi, {'DNT': ['1'], 'Vary': ['Accept', 'Accept-Encoding']}, 'multi')
    is_ok(headers.to_dict()['DNT'], '1', "headers.to_dict()['DNT']")

with subtest('to_list'):
    pairs = headers.to_list()
    is_ok(pairs, [('DNT', '1'), ('Vary', 'Accept'), ('Vary', 'Accept-Encoding')], 'pairs')

with subtest('to_message'):
    message = headers.to_message()
    is_ok(message.get_all('Vary'), ['Accept', 'Accept-Encoding'], 'message')

with subtest('to_str'):
    string = headers.to_str()
    is_ok(string, 'DNT: 1\x0d\x0aVary: Accept\x0d\x0aVary: Accept-Encoding', 'string')

with subtest('values'):
    values = headers.values()
    is_ok(values, ['1', 'Accept, Accept-Encoding'], 'values')

done_testing()
