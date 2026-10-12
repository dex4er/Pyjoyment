import Pyjo.Test


class NoseTest(Pyjo.Test.NoseTest):
    script = __file__
    srcdir = '../..'


class UnitTest(Pyjo.Test.UnitTest):
    script = __file__


if __name__ == '__main__':
    from Pyjo.Test import *  # noqa

    import Pyjo.Headers

    # Basic functionality
    headers = Pyjo.Headers.new()
    headers.add('Connection', 'close')
    headers.add('Connection', 'keep-alive')
    is_ok(headers.header('Connection'), 'close, keep-alive', 'right value')
    headers.remove('Connection')
    is_ok(headers.header('Connection'), None, 'no value')
    headers.content_type = 'text/html'
    headers.content_type = 'text/html'
    headers.expect = 'continue-100'
    headers.connection = 'close'
    is_ok(headers.content_type, 'text/html', 'right value')
    like_ok(headers.to_str(), r'.*\x0d\x0a.*\x0d\x0a.*', 'right format')
    d = headers.to_dict()
    is_ok(d['Connection'], 'close', 'right value')
    is_ok(d['Expect'], 'continue-100', 'right value')
    is_ok(d['Content-Type'], 'text/html', 'right value')
    d = headers.to_dict_list()
    is_deeply_ok(d['Connection'], ['close'], 'right structure')
    is_deeply_ok(d['Expect'], ['continue-100'], 'right structure')
    is_deeply_ok(d['Content-Type'], ['text/html'], 'right structure')
    is_deeply_ok(headers.names, ['Content-Type', 'Expect', 'Connection'], 'right structure')
    headers.expires = 'Thu, 01 Dec 1994 16:00:00 GMT'
    headers.cache_control = 'public'
    is_ok(headers.expires, 'Thu, 01 Dec 1994 16:00:00 GMT', 'right value')
    is_ok(headers.cache_control, 'public', 'right value')
    headers.etag = 'abc321'
    is_ok(headers.etag, 'abc321', 'right value')
    is_ok(headers.header('ETag'), headers.etag, 'values are equal')
    headers.status = '200 OK'
    is_ok(headers.status, '200 OK', 'right value')
    is_ok(headers.header('Status'), headers.status, 'values are equal')

    # Mixed case
    is_ok(headers.header('content-type', 'text/plain').content_type, 'text/plain', 'right value')
    is_ok(headers.header('Content-Type', 'text/html').content_type, 'text/html', 'right value')

    # Common headers
    headers = Pyjo.Headers.new()
    is_ok(headers.set(accept='foo').accept, 'foo', 'right value')
    is_ok(headers.set(accept_charset='foo').accept_charset, 'foo', 'right value')
    is_ok(headers.set(accept_encoding='foo').accept_encoding, 'foo', 'right value')
    is_ok(headers.set(accept_language='foo').accept_language, 'foo', 'right value')
    is_ok(headers.set(accept_ranges='foo').accept_ranges, 'foo', 'right value')
    is_ok(headers.set(access_control_allow_origin='foo').access_control_allow_origin, 'foo', 'right value')
    is_ok(headers.set(allow='foo').allow, 'foo', 'right value')
    is_ok(headers.set(authorization='foo').authorization, 'foo', 'right value')
    is_ok(headers.set(connection='foo').connection, 'foo', 'right value')
    is_ok(headers.set(cache_control='foo').cache_control, 'foo', 'right value')
    is_ok(headers.set(content_disposition='foo').content_disposition, 'foo', 'right value')
    is_ok(headers.set(content_encoding='foo').content_encoding, 'foo', 'right value')
    is_ok(headers.set(content_language='foo').content_language, 'foo', 'right value')
    is_ok(headers.set(content_length='foo').content_length, 'foo', 'right value')
    is_ok(headers.set(content_location='foo').content_location, 'foo', 'right value')
    is_ok(headers.set(content_range='foo').content_range, 'foo', 'right value')
    is_ok(headers.set(content_security_policy='foo').content_security_policy, 'foo', 'right value')
    is_ok(headers.set(content_type='foo').content_type, 'foo', 'right value')
    is_ok(headers.set(cookie='foo').cookie, 'foo', 'right value')
    is_ok(headers.set(dnt='foo').dnt, 'foo', 'right value')
    is_ok(headers.set(date='foo').date, 'foo', 'right value')
    is_ok(headers.set(etag='foo').etag, 'foo', 'right value')
    is_ok(headers.set(expect='foo').expect, 'foo', 'right value')
    is_ok(headers.set(expires='foo').expires, 'foo', 'right value')
    is_ok(headers.set(host='foo').host, 'foo', 'right value')
    is_ok(headers.set(if_modified_since='foo').if_modified_since, 'foo', 'right value')
    is_ok(headers.set(last_modified='foo').last_modified, 'foo', 'right value')
    is_ok(headers.set(link='foo').link, 'foo', 'right value')
    is_ok(headers.set(location='foo').location, 'foo', 'right value')
    is_ok(headers.set(origin='foo').origin, 'foo', 'right value')
    is_ok(headers.set(proxy_authenticate='foo').proxy_authenticate, 'foo', 'right value')
    is_ok(headers.set(proxy_authorization='foo').proxy_authorization, 'foo', 'right value')
    is_ok(headers.set(range='foo').range, 'foo', 'right value')
    is_ok(headers.set(sec_websocket_accept='foo').sec_websocket_accept, 'foo', 'right value')
    is_ok(headers.set(sec_websocket_extensions='foo').sec_websocket_extensions, 'foo', 'right value')
    is_ok(headers.set(sec_websocket_key='foo').sec_websocket_key, 'foo', 'right value')
    is_ok(headers.set(sec_websocket_protocol='foo').sec_websocket_protocol, 'foo', 'right value')
    is_ok(headers.set(sec_websocket_version='foo').sec_websocket_version, 'foo', 'right value')
    is_ok(headers.set(server='foo').server, 'foo', 'right value')
    is_ok(headers.set(set_cookie='foo').set_cookie, 'foo', 'right value')
    is_ok(headers.set(status='foo').status, 'foo', 'right value')
    is_ok(headers.set(strict_transport_security='foo').strict_transport_security, 'foo', 'right value')
    is_ok(headers.set(te='foo').te, 'foo', 'right value')
    is_ok(headers.set(trailer='foo').trailer, 'foo', 'right value')
    is_ok(headers.set(transfer_encoding='foo').transfer_encoding, 'foo', 'right value')
    is_ok(headers.set(upgrade='foo').upgrade, 'foo', 'right value')
    is_ok(headers.set(user_agent='foo').user_agent, 'foo', 'right value')
    is_ok(headers.set(vary='foo').vary, 'foo', 'right value')
    is_ok(headers.set(www_authenticate='foo').www_authenticate, 'foo', 'right value')

    # Clone
    headers = Pyjo.Headers.new()
    headers.add('Connection', 'close')
    headers.add('Connection', 'keep-alive')
    is_ok(headers.header('Connection'), 'close, keep-alive', 'right value')
    clone = headers.clone()
    headers.connection = 'nothing'
    is_ok(headers.header('Connection'), 'nothing', 'right value')
    is_ok(clone.header('Connection'), 'close, keep-alive', 'right value')
    headers = Pyjo.Headers.new()
    headers.expect = '100-continue'
    is_ok(headers.expect, '100-continue', 'right value')
    clone = headers.clone()
    clone.expect = 'nothing'
    is_ok(headers.expect, '100-continue', 'right value')
    is_ok(clone.expect, 'nothing', 'right value')
    clone = Pyjo.Headers.new().add('Foo', 'bar', 'baz').clone()
    is_deeply_ok(clone.to_dict_list()['Foo'], ['bar', 'baz'], 'right structure')

    # Parse headers
    headers = Pyjo.Headers.new()
    isa_ok(
        headers.parse("""Content-Type: text/plain
o: x
Expect: 100-continue
Cache-control: public
Expires: Thu, 01 Dec 1994 16:00:00 GMT

"""),
        Pyjo.Headers.object,
        'right return value',
    )
    ok(headers.is_finished, 'parser is_ok.finished')
    is_ok(headers.content_type, 'text/plain', 'right value')
    is_ok(headers.expect, '100-continue', 'right value')
    is_ok(headers.cache_control, 'public', 'right value')
    is_ok(headers.expires, 'Thu, 01 Dec 1994 16:00:00 GMT', 'right value')
    is_ok(headers.header('o'), 'x', 'right value')

    # Parse multiline headers
    headers = Pyjo.Headers.new()
    headers.parse("""Foo: first
 second
 third
Content-Type: text/plain
Foo Bar: baz
Foo: first again
  second ":again"

""")
    ok(headers.is_finished, 'parser is_ok(finished')
    d = {
        'Content-Type': ['text/plain'],
        'Foo': ['first second third', 'first again second ":again"'],
        'Foo Bar': ['baz'],
    }
    is_deeply_ok(headers.to_dict_list(), d, 'right structure')
    is_ok(headers.header('Foo'), 'first second third, first again second ":again"', 'right value')
    headers = Pyjo.Headers.new().parse(headers.to_str() + '\x0d\x0a\x0d\x0a')
    ok(headers.is_finished, 'parser is_ok(finished')
    is_deeply_ok(headers.to_dict_list(), d, 'successful roundtrip')
    d = {'Content-Type': 'text/plain', 'Foo': 'first second third, first again second ":again"', 'Foo Bar': 'baz'}
    is_deeply_ok(headers.to_dict(), d, 'right structure')

    # Set headers from hash
    headers = Pyjo.Headers.new()
    headers.from_dict({'Connection': 'close', 'Content-Type': 'text/html'})
    is_deeply_ok(headers.to_dict(), {'Connection': 'close', 'Content-Type': 'text/html'}, 'right structure')

    # Remove all headers
    headers.from_dict({})
    is_deeply_ok(headers.to_dict(), {}, 'right structure')

    # Append values
    headers = Pyjo.Headers.new()
    headers.vary = 'Accept'
    headers.append('Vary', 'Accept-Encoding')
    is_ok(headers.vary, 'Accept, Accept-Encoding', 'right value')
    headers = Pyjo.Headers.new()
    headers.append('Vary', 'Accept')
    is_ok(headers.vary, 'Accept', 'right value')
    headers.append('Vary', 'Accept-Encoding')
    is_ok(headers.vary, 'Accept, Accept-Encoding', 'right value')
    headers = Pyjo.Headers.new()
    headers.add('Vary', 'Accept', 'Accept-Encoding')
    is_deeply_ok(headers.to_dict_list(), {'Vary': ['Accept', 'Accept-Encoding']}, 'right structure')
    headers.append('Vary', 'Accept-Language')
    is_deeply_ok(headers.to_dict_list(), {'Vary': ['Accept, Accept-Encoding, Accept-Language']}, 'right structure')

    # Multiple headers with the same name
    headers = Pyjo.Headers.new()
    headers.from_dict({'X-Test': [23, 24], 'X-Test2': 'foo'})
    d = headers.to_dict()
    is_ok(d['X-Test'], '23, 24', 'right value')
    is_ok(d['X-Test2'], 'foo', 'right value')
    d = headers.to_dict_list()
    is_deeply_ok(d['X-Test'], ['23', '24'], 'right structure')
    is_deeply_ok(d['X-Test2'], ['foo'], 'right structure')
    headers = Pyjo.Headers.new().parse(headers.to_str() + '\x0d\x0a\x0d\x0a')
    is_deeply_ok(headers.to_dict_list(), {'X-Test': ['23', '24'], 'X-Test2': ['foo']}, 'right structure')

    # Headers in chunks
    headers = Pyjo.Headers.new()
    isa_ok(headers.parse('Content-Type: text/plain\n'), Pyjo.Headers.object, 'right return value')
    ok(not headers.is_finished, 'parser is_ok(not finished')
    ok(headers.content_type is None, 'no value')
    isa_ok(headers.parse('X-Bender: Bite my shiny\n'), Pyjo.Headers.object, 'right return value')
    ok(not headers.is_finished, 'parser is_ok(not finished')
    ok(headers.connection is None, 'no value')
    isa_ok(headers.parse('X-Bender: metal ass!\n\n'), Pyjo.Headers.object, 'right return value')
    ok(headers.is_finished, 'parser is_ok(finished')
    is_ok(headers.content_type, 'text/plain', 'right value')
    is_ok(headers.header('X-Bender'), 'Bite my shiny, metal ass!', 'right value')

    done_testing()
