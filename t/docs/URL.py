from Pyjo.Test import *


with subtest('Synopsis'):
    from Pyjo.URL import URL

    # Parse
    url = URL('http://sri:foo@example.com:3000/foo?foo=bar#23')
    is_ok(url.scheme, 'http', 'url.scheme')
    is_ok(url.userinfo, 'sri:foo', 'url.userinfo')
    is_ok(url.host, 'example.com', 'url.host')
    is_ok(url.port, 3000, 'url.port')
    is_ok(str(url.path), '/foo', 'url.path')
    is_ok(str(url.query), 'foo=bar', 'url.query')
    is_ok(url.fragment, '23', 'url.fragment')

    import Pyjo.URL

    from urllib.parse import urlsplit

    # Parse
    url = Pyjo.URL.new('http://sri:foo@example.com:3000/foo?foo=bar#23')
    is_ok(url.scheme, 'http', 'url.scheme')
    is_ok(url.userinfo, 'sri:foo', 'url.userinfo')
    is_ok(url.host, 'example.com', 'url.host')
    is_ok(url.port, 3000, 'url.port')
    is_ok(str(url.path), '/foo', 'url.path')
    is_ok(str(url.query), 'foo=bar', 'url.query')
    is_ok(url.fragment, '23', 'url.fragment')

    # Build
    url = Pyjo.URL.new()
    url.scheme = 'http'
    url.host = 'example.com'
    url.port = 3000
    url.path = '/foo/bar'
    url.query = ('foo', 'bar')
    url.fragment = '23'
    is_ok(str(url), 'http://example.com:3000/foo/bar?foo=bar#23', 'url')

with subtest('new'):
    url = Pyjo.URL.new()
    is_ok(str(url), '', 'url')
    url = Pyjo.URL.new('http://127.0.0.1:3000/foo?f=b&baz=2#foo')
    is_ok(str(url), 'http://127.0.0.1:3000/foo?f=b&baz=2#foo', 'url')
    url = Pyjo.URL.new(urlsplit('http://127.0.0.1:3000/foo?f=b&baz=2#foo'))
    is_ok(str(url), 'http://127.0.0.1:3000/foo?f=b&baz=2#foo', 'urlsplit')

with subtest('fragment'):
    fragment = url.fragment
    is_ok(fragment, 'foo', 'fragment')
    url.fragment = '♥pyjoyment♥'
    is_ok(url.fragment, '♥pyjoyment♥', 'url.fragment')

    # "yada"
    is_ok(Pyjo.URL.new('http://example.com/foo?bar=baz#yada').fragment, 'yada', 'fragment')

with subtest('host'):
    host = url.host
    is_ok(host, '127.0.0.1', 'host')
    url.host = '127.0.0.1'
    is_ok(url.host, '127.0.0.1', 'url.host')

    # "example.com"
    is_ok(Pyjo.URL.new('http://sri:t3st@example.com:8080/foo').host, 'example.com', 'host')

with subtest('port'):
    port = url.port
    is_ok(port, 3000, 'port')
    url.port = 8080
    is_ok(url.port, 8080, 'url.port')

    # 8080
    is_ok(Pyjo.URL.new('http://sri:t3st@example.com:8080/foo').port, 8080, 'port')

with subtest('scheme'):
    scheme = url.scheme
    is_ok(scheme, 'http', 'scheme')
    url.scheme = 'http'
    is_ok(url.scheme, 'http', 'url.scheme')

    # "http"
    is_ok(Pyjo.URL.new('http://example.com/foo').scheme, 'http', 'scheme')

with subtest('userinfo'):
    info = url.userinfo
    is_ok(info, None, 'info')
    url.userinfo = 'root:♥'
    is_ok(url.userinfo, 'root:♥', 'url.userinfo')

    # "sri:t3st"
    is_ok(Pyjo.URL.new('https://sri:t3st@example.com/foo').userinfo, 'sri:t3st', 'userinfo')

with subtest('__bool__'):
    boolean = bool(url)
    is_ok(boolean, True, 'boolean')

with subtest('__str__'):
    string = str(url)
    is_ok(string, 'http://127.0.0.1:8080/foo?f=b&baz=2#%E2%99%A5pyjoyment%E2%99%A5', 'string')

with subtest('base'):
    base = url.base
    is_ok(str(base), '', 'base')
    url.base = Pyjo.URL.new()
    is_ok(str(url.base), '', 'url.base')

    # "http://example.com/a/b?c"
    is_ok(
        str(Pyjo.URL.new('/a/b?c').set(base=Pyjo.URL.new('http://example.com')).to_abs()),
        'http://example.com/a/b?c',
        'to_abs()',
    )

with subtest('clone'):
    url2 = url.clone()
    is_ok(url2.to_unsafe_str(), url.to_unsafe_str(), 'url2')
    isnt_ok(id(url2), id(url), 'another object')

with subtest('host_port'):
    host_port = url.host_port
    is_ok(host_port, '127.0.0.1:8080', 'host_port')
    url.host_port = 'example.com:8080'
    is_ok(url.host_port, 'example.com:8080', 'url.host_port')

    # "xn--n3h.net:8080"
    is_ok(Pyjo.URL.new('http://☃.net:8080/test').host_port, 'xn--n3h.net:8080', 'host_port')

    # "example.com"
    is_ok(Pyjo.URL.new('http://example.com/test').host_port, 'example.com', 'host_port')

with subtest('ihost'):
    ihost = url.ihost
    is_ok(ihost, 'example.com', 'ihost')
    url.ihost = 'xn--bcher-kva.ch'
    is_ok(url.host, 'bücher.ch', 'url.host')

    # "xn--n3h.net"
    is_ok(Pyjo.URL.new('http://☃.net').ihost, 'xn--n3h.net', 'ihost')

    # "example.com"
    is_ok(Pyjo.URL.new('http://example.com').ihost, 'example.com', 'ihost')

with subtest('is_abs'):
    boolean = url.is_abs
    is_ok(boolean, True, 'boolean')

    # True
    is_ok(Pyjo.URL.new('http://example.com').is_abs, True, 'http://example.com')
    is_ok(Pyjo.URL.new('http://example.com/test/index.html').is_abs, True, 'http://example.com/test/index.html')

    # False
    is_ok(Pyjo.URL.new('test/index.html').is_abs, False, 'test/index.html')
    is_ok(Pyjo.URL.new('/test/index.html').is_abs, False, '/test/index.html')
    is_ok(Pyjo.URL.new('//example.com/test/index.html').is_abs, False, '//example.com/test/index.html')

with subtest('parse'):
    url = Pyjo.URL.new()
    url = url.parse('http://127.0.0.1:3000/foo/bar?fo=o&baz=23#foo')
    is_ok(str(url), 'http://127.0.0.1:3000/foo/bar?fo=o&baz=23#foo', 'url')
    url = Pyjo.URL.new().parse(urlsplit('http://127.0.0.1:3000/foo/bar?fo=o&baz=23#foo'))
    is_ok(str(url), 'http://127.0.0.1:3000/foo/bar?fo=o&baz=23#foo', 'urlsplit')

    # "/test/123"
    is_ok(str(Pyjo.URL.new().parse('/test/123?foo=bar').path), '/test/123', 'path')

    # "example.com"
    is_ok(Pyjo.URL.new().parse('http://example.com/test/123?foo=bar').host, 'example.com', 'host')

    # "sri@example.com"
    is_ok(str(Pyjo.URL.new().parse('mailto:sri@example.com').path), 'sri@example.com', 'path')

with subtest('password'):
    url = Pyjo.URL.new('http://isabel:s3cret@pyjoyment.org')
    password = url.password
    is_ok(password, 's3cret', 'password')

    # "s3cret"
    is_ok(Pyjo.URL.new('http://isabel:s3cret@pyjoyment.org').password, 's3cret', 'password')

    # "s:3:c:r:e:t"
    is_ok(Pyjo.URL.new('http://isabel:s:3:c:r:e:t@pyjoyment.org').password, 's:3:c:r:e:t', 'password')

with subtest('path'):
    url = Pyjo.URL.new('http://example.com/test/Pyjo')
    path = url.path
    is_ok(str(path), '/test/Pyjo', 'path')
    url.path = 'foo/bar'
    is_ok(str(url.path), '/test/foo/bar', 'relative')
    url.path = '/foo/bar'
    is_ok(str(url.path), '/foo/bar', 'absolute')
    url.path = Pyjo.Path.new()
    is_ok(str(url.path), '', 'Pyjo.Path')

    # "test"
    is_ok(Pyjo.URL.new('http://example.com/test/Pyjo').path.parts[0], 'test', 'parts[0]')

    # "/test/DOM/HTML"
    is_ok(str(Pyjo.URL.new('http://example.com/test/Pyjo').path.merge('DOM/HTML')), '/test/DOM/HTML', 'merge')

    # "http://example.com/DOM/HTML"
    is_ok(
        str(Pyjo.URL.new('http://example.com/test/Pyjo').set(path='/DOM/HTML')),
        'http://example.com/DOM/HTML',
        'set(path=...) absolute',
    )

    # "http://example.com/test/DOM/HTML"
    is_ok(
        str(Pyjo.URL.new('http://example.com/test/Pyjo').set(path='DOM/HTML')),
        'http://example.com/test/DOM/HTML',
        'set(path=...) relative',
    )

    # "http://example.com/test/Pyjo/DOM/HTML"
    is_ok(
        str(Pyjo.URL.new('http://example.com/test/Pyjo/').set(path='DOM/HTML')),
        'http://example.com/test/Pyjo/DOM/HTML',
        'set(path=...) relative with trailing slash',
    )

with subtest('path_query'):
    url = Pyjo.URL.new('http://example.com/test?a=1&b=2')
    path_query = url.path_query
    is_ok(path_query, '/test?a=1&b=2', 'path_query')
    url.path_query = '/foo/bar?a=1&b=2'
    is_ok(str(url), 'http://example.com/foo/bar?a=1&b=2', 'url')

    # "/test?a=1&b=2"
    is_ok(Pyjo.URL.new('http://example.com/test?a=1&b=2').path_query, '/test?a=1&b=2', 'path_query')

    # "/"
    is_ok(Pyjo.URL.new('http://example.com/').path_query, '/', 'path_query')

with subtest('protocol'):
    proto = url.protocol
    is_ok(proto, 'http', 'proto')

    # "http"
    is_ok(Pyjo.URL.new('HtTp://example.com').protocol, 'http', 'protocol')

with subtest('query'):
    url = Pyjo.URL.new('http://example.com')
    query = url.query
    is_ok(str(query), '', 'query')
    url.query = {'merge': 'to'}
    url.query = ['append', 'with']
    is_ok(str(url.query), 'merge=to&append=with', 'merged and appended')
    url.query = ('replace', 'with')
    is_ok(str(url.query), 'replace=with', 'replaced')
    url.query = 'a=1&b=2'
    is_ok(str(url.query), 'a=1&b=2', 'parsed')
    url.query = Pyjo.Parameters.new()
    is_ok(str(url.query), '', 'Pyjo.Parameters')

    # "2"
    is_ok(Pyjo.URL.new('http://example.com?a=1&b=2').query.param('b'), '2', 'param')

    # "b=2&a=2&c=3"
    is_ok(str(Pyjo.URL.new('http://example.com?a=1&b=2').query.merge('a', 2, 'c', 3)), 'b=2&a=2&c=3', 'merge')

    # "http://example.com?a=2&c=3"
    is_ok(
        str(Pyjo.URL.new('http://example.com?a=1&b=2').set(query=('a', 2, 'c', 3))),
        'http://example.com?a=2&c=3',
        'tuple',
    )

    # "http://example.com?a=2&a=3"
    is_ok(
        str(Pyjo.URL.new('http://example.com?a=1&b=2').set(query=('a', [2, 3]))),
        'http://example.com?a=2&a=3',
        'tuple with list',
    )

    # "http://example.com?b=2&a=2&c=3"
    is_ok(
        str(Pyjo.URL.new('http://example.com?a=1&b=2').set(query={'a': 2, 'c': 3})),
        'http://example.com?b=2&a=2&c=3',
        'dict',
    )

    # "http://example.com?b=2"
    is_ok(
        str(Pyjo.URL.new('http://example.com?a=1&b=2').set(query={'a': None})),
        'http://example.com?b=2',
        'dict with None',
    )

    # "http://example.com?a=1&b=2&a=2&c=3"
    is_ok(
        str(Pyjo.URL.new('http://example.com?a=1&b=2').set(query=['a', 2, 'c', 3])),
        'http://example.com?a=1&b=2&a=2&c=3',
        'list',
    )

with subtest('to_abs'):
    url = Pyjo.URL.new('baz.xml?test=123')
    abs = url.to_abs()
    is_ok(str(abs), 'baz.xml?test=123', 'abs')
    abs = url.to_abs(Pyjo.URL.new('http://example.com/foo'))
    is_ok(str(abs), 'http://example.com/baz.xml?test=123', 'abs')

    # "http://example.com/foo/baz.xml?test=123"
    is_ok(
        str(Pyjo.URL.new('baz.xml?test=123').to_abs(Pyjo.URL.new('http://example.com/foo/bar.html'))),
        'http://example.com/foo/baz.xml?test=123',
        'relative',
    )

    # "http://example.com/baz.xml?test=123"
    is_ok(
        str(Pyjo.URL.new('/baz.xml?test=123').to_abs(Pyjo.URL.new('http://example.com/foo/bar.html'))),
        'http://example.com/baz.xml?test=123',
        'absolute path',
    )

    # "http://example.com/foo/baz.xml?test=123"
    is_ok(
        str(Pyjo.URL.new('//example.com/foo/baz.xml?test=123').to_abs(Pyjo.URL.new('http://example.com/foo/bar.html'))),
        'http://example.com/foo/baz.xml?test=123',
        'without scheme',
    )

with subtest('to_str'):
    string = url.to_str()
    is_ok(string, 'baz.xml?test=123', 'string')

    # "http://pyjoyment.org"
    is_ok(Pyjo.URL.new().set(scheme='http', host='pyjoyment.org').to_str(), 'http://pyjoyment.org', 'built')

    # "http://pyjoyment.org"
    is_ok(Pyjo.URL.new('http://daniel:s3cret@pyjoyment.org').to_str(), 'http://pyjoyment.org', 'without userinfo')

with subtest('to_unsafe_str'):
    string = url.to_unsafe_str()
    is_ok(string, 'baz.xml?test=123', 'string')

    # "http://daniel:s3cret@pyjoyment.org"
    is_ok(
        Pyjo.URL.new('http://daniel:s3cret@pyjoyment.org').to_unsafe_str(),
        'http://daniel:s3cret@pyjoyment.org',
        'with userinfo',
    )

with subtest('to_urllib'):
    url = Pyjo.URL.new('http://example.com/foo')
    split = url.to_urllib()
    is_ok(split, urlsplit('http://example.com/foo'), 'split')

    # "isabel"
    is_ok(Pyjo.URL.new('http://isabel:s3cret@pyjoyment.org/foo').to_urllib().username, 'isabel', 'username')

with subtest('username'):
    url = Pyjo.URL.new('http://isabel:s3cret@pyjoyment.org')
    username = url.username
    is_ok(username, 'isabel', 'username')

    # "isabel"
    is_ok(Pyjo.URL.new('http://isabel:s3cret@pyjoyment.org').username, 'isabel', 'username')

done_testing()
