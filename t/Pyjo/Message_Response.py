if __name__ == '__main__':
    from Pyjo.Test import *  # noqa

    import Pyjo.Asset.Memory
    import Pyjo.Content.Single

    from Pyjo.JSON import encode_json
    from Pyjo.Util import b, die, setenv

    import platform
    import zlib

    import Pyjo.Message.Response

    from t.lib.Value import Value

    # Common status codes
    res = Pyjo.Message.Response.new()
    is_ok(res.set(code=100).default_message(), 'Continue', 'right message')
    is_ok(res.set(code=101).default_message(), 'Switching Protocols', 'right message')
    is_ok(res.set(code=102).default_message(), 'Processing', 'right message')
    is_ok(res.set(code=200).default_message(), 'OK', 'right message')
    is_ok(res.set(code=201).default_message(), 'Created', 'right message')
    is_ok(res.set(code=202).default_message(), 'Accepted', 'right message')
    is_ok(res.set(code=203).default_message(), 'Non-Authoritative Information', 'right message')
    is_ok(res.set(code=204).default_message(), 'No Content', 'right message')
    is_ok(res.set(code=205).default_message(), 'Reset Content', 'right message')
    is_ok(res.set(code=206).default_message(), 'Partial Content', 'right message')
    is_ok(res.set(code=207).default_message(), 'Multi-Status', 'right message')
    is_ok(res.set(code=208).default_message(), 'Already Reported', 'right message')
    is_ok(res.set(code=226).default_message(), 'IM Used', 'right message')
    is_ok(res.set(code=300).default_message(), 'Multiple Choices', 'right message')
    is_ok(res.set(code=301).default_message(), 'Moved Permanently', 'right message')
    is_ok(res.set(code=302).default_message(), 'Found', 'right message')
    is_ok(res.set(code=303).default_message(), 'See Other', 'right message')
    is_ok(res.set(code=304).default_message(), 'Not Modified', 'right message')
    is_ok(res.set(code=305).default_message(), 'Use Proxy', 'right message')
    is_ok(res.set(code=307).default_message(), 'Temporary Redirect', 'right message')
    is_ok(res.set(code=308).default_message(), 'Permanent Redirect', 'right message')
    is_ok(res.set(code=400).default_message(), 'Bad Request', 'right message')
    is_ok(res.set(code=401).default_message(), 'Unauthorized', 'right message')
    is_ok(res.set(code=402).default_message(), 'Payment Required', 'right message')
    is_ok(res.set(code=403).default_message(), 'Forbidden', 'right message')
    is_ok(res.set(code=404).default_message(), 'Not Found', 'right message')
    is_ok(res.set(code=405).default_message(), 'Method Not Allowed', 'right message')
    is_ok(res.set(code=406).default_message(), 'Not Acceptable', 'right message')
    is_ok(res.set(code=407).default_message(), 'Proxy Authentication Required', 'right message')
    is_ok(res.set(code=408).default_message(), 'Request Timeout', 'right message')
    is_ok(res.set(code=409).default_message(), 'Conflict', 'right message')
    is_ok(res.set(code=410).default_message(), 'Gone', 'right message')
    is_ok(res.set(code=411).default_message(), 'Length Required', 'right message')
    is_ok(res.set(code=412).default_message(), 'Precondition Failed', 'right message')
    is_ok(res.set(code=413).default_message(), 'Request Entity Too Large', 'right message')
    is_ok(res.set(code=414).default_message(), 'Request-URI Too Long', 'right message')
    is_ok(res.set(code=415).default_message(), 'Unsupported Media Type', 'right message')
    is_ok(res.set(code=416).default_message(), 'Request Range Not Satisfiable', 'right message')
    is_ok(res.set(code=417).default_message(), 'Expectation Failed', 'right message')
    is_ok(res.set(code=418).default_message(), "I'm a teapot", 'right message')
    is_ok(res.set(code=422).default_message(), 'Unprocessable Entity', 'right message')
    is_ok(res.set(code=423).default_message(), 'Locked', 'right message')
    is_ok(res.set(code=424).default_message(), 'Failed Dependency', 'right message')
    is_ok(res.set(code=425).default_message(), 'Unordered Colection', 'right message')
    is_ok(res.set(code=426).default_message(), 'Upgrade Required', 'right message')
    is_ok(res.set(code=428).default_message(), 'Precondition Required', 'right message')
    is_ok(res.set(code=429).default_message(), 'Too Many Requests', 'right message')
    is_ok(res.set(code=431).default_message(), 'Request Header Fields Too Large', 'right message')
    is_ok(res.set(code=500).default_message(), 'Internal Server Error', 'right message')
    is_ok(res.set(code=501).default_message(), 'Not Implemented', 'right message')
    is_ok(res.set(code=502).default_message(), 'Bad Gateway', 'right message')
    is_ok(res.set(code=503).default_message(), 'Service Unavailable', 'right message')
    is_ok(res.set(code=504).default_message(), 'Gateway Timeout', 'right message')
    is_ok(res.set(code=505).default_message(), 'HTTP Version Not Supported', 'right message')
    is_ok(res.set(code=506).default_message(), 'Variant Also Negotiates', 'right message')
    is_ok(res.set(code=507).default_message(), 'Insufficient Storage', 'right message')
    is_ok(res.set(code=508).default_message(), 'Loop Detected', 'right message')
    is_ok(res.set(code=509).default_message(), 'Bandwidth Limit Exceeded', 'right message')
    is_ok(res.set(code=510).default_message(), 'Not Extended', 'right message')
    is_ok(res.set(code=511).default_message(), 'Network Authentication Required', 'right message')
    is_ok(res.default_message(100), 'Continue', 'right message')

    # Status code ranges
    ok(res.set(code=200).is_status_class(200), 'is in range')
    ok(res.set(code=201).is_status_class(200), 'is in range')
    ok(res.set(code=299).is_status_class(200), 'is in range')
    ok(res.set(code=302).is_status_class(300), 'is in range')
    ok(not res.set(code=199).is_status_class(200), 'not in range')
    ok(not res.set(code=300).is_status_class(200), 'not in range')
    ok(not res.set(code=200).is_status_class(100), 'not in range')
    ok(not res.set(code=200).is_status_class(300), 'not in range')
    ok(not res.set(code=None).is_status_class(200), 'no range')

    # Status code and message
    res = Pyjo.Message.Response.new()
    is_ok(res.code, None, 'no status')
    is_ok(res.default_message(), 'Not Found', 'right default message')
    is_ok(res.message, None, 'no message')
    res.message = 'Test'
    is_ok(res.message, 'Test', 'right message')
    res.code = 500
    is_ok(res.code, 500, 'right status')
    is_ok(res.message, 'Test', 'right message')
    is_ok(res.default_message(), 'Internal Server Error', 'right default message')
    res = Pyjo.Message.Response.new()
    is_ok(res.set(code=400).default_message(), 'Bad Request', 'right default message')
    res = Pyjo.Message.Response.new()
    is_ok(res.set(code=1).default_message(), '', 'empty default message')

    # Parse HTTP 1.1 response start-line, no headers and body
    res = Pyjo.Message.Response.new()
    res.parse(b'HTTP/1.1 200 OK\x0d\x0a\x0d\x0a')
    ok(res.is_finished, 'response is finished')
    is_ok(res.code, 200, 'right status')
    is_ok(res.message, 'OK', 'right message')
    is_ok(res.version, '1.1', 'right version')

    # Parse HTTP 1.1 response start-line, no headers and body (small chunks)
    res = Pyjo.Message.Response.new()
    res.parse(b'H')
    ok(not res.is_finished, 'response is not finished')
    res.parse(b'T')
    ok(not res.is_finished, 'response is not finished')
    res.parse(b'T')
    ok(not res.is_finished, 'response is not finished')
    res.parse(b'P')
    ok(not res.is_finished, 'response is not finished')
    res.parse(b'/')
    ok(not res.is_finished, 'response is not finished')
    res.parse(b'1')
    ok(not res.is_finished, 'response is not finished')
    res.parse(b'.')
    ok(not res.is_finished, 'response is not finished')
    res.parse(b'1')
    ok(not res.is_finished, 'response is not finished')
    res.parse(b' ')
    ok(not res.is_finished, 'response is not finished')
    res.parse(b'2')
    ok(not res.is_finished, 'response is not finished')
    res.parse(b'0')
    ok(not res.is_finished, 'response is not finished')
    res.parse(b'0')
    ok(not res.is_finished, 'response is not finished')
    res.parse(b' ')
    ok(not res.is_finished, 'response is not finished')
    res.parse(b'O')
    ok(not res.is_finished, 'response is not finished')
    res.parse(b'K')
    ok(not res.is_finished, 'response is not finished')
    res.parse(b'\x0d')
    ok(not res.is_finished, 'response is not finished')
    res.parse(b'\x0a')
    ok(not res.is_finished, 'response is not finished')
    res.parse(b'\x0d')
    ok(not res.is_finished, 'response is not finished')
    res.parse(b'\x0a')
    ok(res.is_finished, 'response is finished')
    is_ok(res.code, 200, 'right status')
    is_ok(res.message, 'OK', 'right message')
    is_ok(res.version, '1.1', 'right version')

    # Parse HTTP 1.1 response start-line, no headers and body (no message)
    res = Pyjo.Message.Response.new()
    res.parse(b'HTTP/1.1 200\x0d\x0a\x0d\x0a')
    ok(res.is_finished, 'response is finished')
    is_ok(res.code, 200, 'right status')
    is_ok(res.message, None, 'no message')
    is_ok(res.version, '1.1', 'right version')

    # Parse HTTP 1.0 response start-line and headers but no body
    res = Pyjo.Message.Response.new()
    res.parse(b'HTTP/1.0 404 Damn it\x0d\x0a')
    res.parse(b'Content-Type: text/plain\x0d\x0a')
    res.parse(b'Content-Length: 0\x0d\x0a\x0d\x0a')
    ok(res.is_finished, 'response is finished')
    is_ok(res.code, 404, 'right status')
    is_ok(res.message, 'Damn it', 'right message')
    is_ok(res.version, '1.0', 'right version')
    is_ok(res.headers.content_type, 'text/plain', 'right "Content-Type" value')
    is_ok(res.headers.content_length, '0', 'right "Content-Length" value')

    # Parse full HTTP 1.0 response
    res = Pyjo.Message.Response.new()
    res.parse(b'HTTP/1.0 500 Internal Server Error\x0d\x0a')
    res.parse(b'Content-Type: text/plain\x0d\x0a')
    res.parse(b'Content-Length: 27\x0d\x0a\x0d\x0a')
    res.parse(b'Hello World!\n1234\nlalalala\n')
    ok(res.is_finished, 'response is finished')
    is_ok(res.code, 500, 'right status')
    is_ok(res.message, 'Internal Server Error', 'right message')
    is_ok(res.version, '1.0', 'right version')
    is_ok(res.headers.content_type, 'text/plain', 'right "Content-Type" value')
    is_ok(res.headers.content_length, '27', 'right "Content-Length" value')
    is_ok(res.body, b'Hello World!\n1234\nlalalala\n', 'right content')

    # Parse full HTTP 1.0 response (keep-alive)
    res = Pyjo.Message.Response.new()
    res.parse(b'HTTP/1.0 500 Internal Server Error\x0d\x0a')
    res.parse(b'Connection: keep-alive\x0d\x0a\x0d\x0a')
    res.parse(b'HTTP/1.0 200 OK\x0d\x0a\x0d\x0a')
    ok(res.is_finished, 'response is finished')
    is_ok(res.code, 500, 'right status')
    is_ok(res.message, 'Internal Server Error', 'right message')
    is_ok(res.version, '1.0', 'right version')
    is_ok(res.body, b'', 'no content')
    is_ok(res.content.leftovers, b'HTTP/1.0 200 OK\x0d\x0a\x0d\x0a', 'next response in leftovers')

    # Parse full HTTP 1.0 response (no limit)
    setenv('PYJO_MAX_MESSAGE_SIZE', '0')
    res = Pyjo.Message.Response.new()
    is_ok(res.max_message_size, 0, 'right size')
    res.parse(b'HTTP/1.0 500 Internal Server Error\x0d\x0a')
    res.parse(b'Content-Type: text/plain\x0d\x0a')
    res.parse(b'Content-Length: 27\x0d\x0a\x0d\x0a')
    res.parse(b'Hello World!\n1234\nlalalala\n')
    ok(res.is_finished, 'response is finished')
    ok(not res.error, 'no error')
    is_ok(res.code, 500, 'right status')
    is_ok(res.message, 'Internal Server Error', 'right message')
    is_ok(res.version, '1.0', 'right version')
    is_ok(res.headers.content_type, 'text/plain', 'right "Content-Type" value')
    is_ok(res.headers.content_length, '27', 'right "Content-Length" value')
    is_ok(res.body, b'Hello World!\n1234\nlalalala\n', 'right content')
    setenv('PYJO_MAX_MESSAGE_SIZE', None)

    # Parse broken start-line
    res = Pyjo.Message.Response.new()
    res.parse(b'12345\x0d\x0a')
    ok(res.is_finished, 'response is finished')
    is_deeply_ok(res.error, {'message': 'Bad response start-line', 'code': None}, 'right error')

    # Parse full HTTP 1.0 response (missing Content-Length)
    res = Pyjo.Message.Response.new()
    res.parse(b'HTTP/1.0 500 Internal Server Error\x0d\x0a')
    res.parse(b'Content-Type: text/plain\x0d\x0a')
    res.parse(b'Connection: close\x0d\x0a\x0d\x0a')
    res.parse(b'Hello World!\n1234\nlalalala\n')
    ok(not res.is_finished, 'response is not finished')
    is_ok(res.code, 500, 'right status')
    is_ok(res.message, 'Internal Server Error', 'right message')
    is_ok(res.version, '1.0', 'right version')
    is_ok(res.headers.content_type, 'text/plain', 'right "Content-Type" value')
    is_ok(res.headers.content_length, None, 'no "Content-Length" value')
    is_ok(res.body, b'Hello World!\n1234\nlalalala\n', 'right content')

    # Parse full HTTP 1.0 response (missing Content-Length and Connection)
    res = Pyjo.Message.Response.new()
    res.parse(b'HTTP/1.0 500 Internal Server Error\x0d\x0a')
    res.parse(b'Content-Type: text/plain\x0d\x0a\x0d\x0a')
    res.parse(b'Hello World!\n1')
    res.parse(b'234\nlala')
    res.parse(b'lala\n')
    ok(not res.is_finished, 'response is not finished')
    is_ok(res.code, 500, 'right status')
    is_ok(res.message, 'Internal Server Error', 'right message')
    is_ok(res.version, '1.0', 'right version')
    is_ok(res.headers.content_type, 'text/plain', 'right "Content-Type" value')
    is_ok(res.headers.content_length, None, 'no "Content-Length" value')
    is_ok(res.body, b'Hello World!\n1234\nlalalala\n', 'right content')

    # Parse full HTTP 1.1 response (missing Content-Length)
    res = Pyjo.Message.Response.new()
    res.parse(b'HTTP/1.1 500 Internal Server Error\x0d\x0a')
    res.parse(b'Content-Type: text/plain\x0d\x0a')
    res.parse(b'Connection: close\x0d\x0a\x0d\x0a')
    res.parse(b'Hello World!\n1234\nlalalala\n')
    ok(not res.is_finished, 'response is not finished')
    ok(not res.is_empty, 'response is not empty')
    ok(not res.content.skip_body, 'body has not been skipped')
    ok(res.content.relaxed, 'relaxed response')
    is_ok(res.code, 500, 'right status')
    is_ok(res.message, 'Internal Server Error', 'right message')
    is_ok(res.version, '1.1', 'right version')
    is_ok(res.headers.content_type, 'text/plain', 'right "Content-Type" value')
    is_ok(res.headers.content_length, None, 'no "Content-Length" value')
    is_ok(res.body, b'Hello World!\n1234\nlalalala\n', 'right content')

    # Parse full HTTP 1.1 response (broken Content-Length)
    res = Pyjo.Message.Response.new()
    res.parse(b'HTTP/1.1 200 OK\x0d\x0a')
    res.parse(b'Content-Length: 123test\x0d\x0a\x0d\x0a')
    res.parse(b'Hello World!')
    ok(res.is_finished, 'response is finished')
    is_ok(res.code, 200, 'right status')
    is_ok(res.message, 'OK', 'right message')
    is_ok(res.version, '1.1', 'right version')
    is_ok(res.headers.content_length, '123test', 'right "Content-Length" value')
    is_ok(res.body, b'', 'no content')
    is_ok(res.content.leftovers, b'Hello World!', 'content in leftovers')

    # Parse full HTTP 1.1 response (100 Continue)
    res = Pyjo.Message.Response.new()
    res.content.on('body', lambda content: content.headers.header('X-Body', 'one'))
    res.on('progress', lambda res, state, offset: res.headers.header('X-Progress', 'two'))
    res.on('finish', lambda res: res.headers.header('X-Finish', 'three'))
    res.parse(b'HTTP/1.1 100 Continue\x0d\x0a\x0d\x0a')
    ok(res.is_finished, 'response is finished')
    ok(res.is_empty, 'response is empty')
    ok(res.content.skip_body, 'body has been skipped')
    is_ok(res.code, 100, 'right status')
    is_ok(res.message, 'Continue', 'right message')
    is_ok(res.version, '1.1', 'right version')
    is_ok(res.headers.content_length, None, 'no "Content-Length" value')
    is_ok(res.headers.header('X-Body'), 'one', 'right "X-Body" value')
    is_ok(res.headers.header('X-Progress'), 'two', 'right "X-Progress" value')
    is_ok(res.headers.header('X-Finish'), 'three', 'right "X-Finish" value')
    is_ok(res.body, b'', 'no content')

    # Parse full HTTP 1.1 response (304 Not Modified)
    res = Pyjo.Message.Response.new()
    res.parse(b'HTTP/1.1 304 Not Modified\x0d\x0a')
    res.parse(b'Content-Type: text/html\x0d\x0a')
    res.parse(b'Content-Length: 9000\x0d\x0a')
    res.parse(b'Connection: keep-alive\x0d\x0a\x0d\x0a')
    ok(res.is_finished, 'response is finished')
    ok(res.is_empty, 'response is empty')
    ok(res.content.skip_body, 'body has been skipped')
    is_ok(res.code, 304, 'right status')
    is_ok(res.message, 'Not Modified', 'right message')
    is_ok(res.version, '1.1', 'right version')
    is_ok(res.headers.content_type, 'text/html', 'right "Content-Type" value')
    is_ok(res.headers.content_length, '9000', 'right "Content-Length" value')
    is_ok(res.headers.connection, 'keep-alive', 'right "Connection" value')
    is_ok(res.body, b'', 'no content')

    # Parse full HTTP 1.1 response (204 No Content)
    res = Pyjo.Message.Response.new()
    res.content.on('body', lambda content: content.headers.header('X-Body', 'one'))
    res.on('finish', lambda req: req.headers.header('X-Finish', 'two'))
    res.parse(b'HTTP/1.1 204 No Content\x0d\x0a')
    res.parse(b'Content-Type: text/html\x0d\x0a')
    res.parse(b'Content-Length: 9001\x0d\x0a')
    res.parse(b'Connection: keep-alive\x0d\x0a\x0d\x0a')
    ok(res.is_finished, 'response is finished')
    ok(res.is_empty, 'response is empty')
    ok(res.content.skip_body, 'body has been skipped')
    is_ok(res.code, 204, 'right status')
    is_ok(res.message, 'No Content', 'right message')
    is_ok(res.version, '1.1', 'right version')
    is_ok(res.headers.content_type, 'text/html', 'right "Content-Type" value')
    is_ok(res.headers.content_length, '9001', 'right "Content-Length" value')
    is_ok(res.headers.connection, 'keep-alive', 'right "Connection" value')
    is_ok(res.headers.header('X-Body'), 'one', 'right "X-Body" value')
    is_ok(res.headers.header('X-Finish'), 'two', 'right "X-Finish" value')
    is_ok(res.body, b'', 'no content')

    # Parse HTTP 1.1 response (413 error in one big chunk)
    res = Pyjo.Message.Response.new()
    res.parse(
        b'HTTP/1.1 413 Request Entity Too Large\x0d\x0a'
        b'Connection: Close\x0d\x0a'
        b'Date: Tue, 09 Feb 2010 16:34:51 GMT\x0d\x0a'
        b'Server: Mojolicious (Perl)\x0d\x0a\x0d\x0a'
    )
    ok(not res.is_finished, 'response is not finished')
    is_ok(res.code, 413, 'right status')
    is_ok(res.message, 'Request Entity Too Large', 'right message')
    is_ok(res.version, '1.1', 'right version')
    is_ok(res.headers.content_length, None, 'right "Content-Length" value')

    # Parse HTTP 1.1 chunked response (exceeding limit)
    setenv('PYJO_MAX_BUFFER_SIZE', '12')
    res = Pyjo.Message.Response.new()
    is_ok(res.content.max_buffer_size, 12, 'right size')
    res.parse(b'HTTP/1.1 200 OK\x0d\x0a')
    res.parse(b'Content-Type: text/plain\x0d\x0a')
    res.parse(b'Transfer-Encoding: chunked\x0d\x0a\x0d\x0a')
    ok(not res.is_limit_exceeded, 'limit is not exceeded')
    res.parse(b'a' * 1000)
    ok(res.is_finished, 'response is finished')
    ok(res.content.is_finished, 'content is finished')
    is_deeply_ok(res.error, {'message': 'Maximum buffer size exceeded', 'code': None}, 'right error')
    ok(res.is_limit_exceeded, 'limit is not exceeded')
    is_ok(res.code, 200, 'right status')
    is_ok(res.message, 'OK', 'right message')
    is_ok(res.version, '1.1', 'right version')
    is_ok(res.headers.content_type, 'text/plain', 'right "Content-Type" value')
    setenv('PYJO_MAX_BUFFER_SIZE', None)

    # Parse HTTP 1.1 multipart response (exceeding limit)
    setenv('PYJO_MAX_BUFFER_SIZE', '12')
    res = Pyjo.Message.Response.new()
    is_ok(res.content.max_buffer_size, 12, 'right size')
    res.parse(b'HTTP/1.1 200 OK\x0d\x0a')
    res.parse(b'Content-Length: 420\x0d\x0a')
    res.parse(b'Content-Type: multipart/form-data; bo')
    res.parse(b'undary=----------0xKhTmLbOuNdArY\x0d\x0a\x0d\x0a')
    ok(not res.content.is_limit_exceeded, 'limit is not exceeded')
    res.parse(b'a' * 200)
    ok(res.content.is_limit_exceeded, 'limit is exceeded')
    ok(res.is_finished, 'response is finished')
    ok(res.content.is_finished, 'content is finished')
    is_deeply_ok(res.error, {'message': 'Maximum buffer size exceeded', 'code': None}, 'right error')
    is_ok(res.code, 200, 'right status')
    is_ok(res.message, 'OK', 'right message')
    is_ok(res.version, '1.1', 'right version')
    is_ok(
        res.headers.content_type,
        'multipart/form-data; boundary=----------0xKhTmLbOuNdArY',
        'right "Content-Type" value',
    )
    setenv('PYJO_MAX_BUFFER_SIZE', None)

    if platform.python_implementation() == 'PyPy':
        skip('PyPy error', 10)
    else:
        # Parse HTTP 1.1 gzip compressed response (garbage bytes exceeding limit)
        setenv('PYJO_MAX_BUFFER_SIZE', '12')
        res = Pyjo.Message.Response.new()
        is_ok(res.content.max_buffer_size, 12, 'right size')
        res.parse(b'HTTP/1.1 200 OK\x0d\x0a')
        res.parse(b'Content-Length: 1000\x0d\x0a')
        res.parse(b'Content-Encoding: gzip\x0d\x0a\x0d\x0a')
        res.parse(b'a' * 5)
        ok(not res.content.is_limit_exceeded, 'limit is not exceeded')
        res.parse(b'a' * 995)
        ok(res.content.is_limit_exceeded, 'limit is exceeded')
        ok(res.is_finished, 'response is finished')
        ok(res.content.is_finished, 'content is finished')
        is_deeply_ok(res.error, {'message': 'Maximum buffer size exceeded', 'code': None}, 'right error')
        is_ok(res.code, 200, 'right status')
        is_ok(res.message, 'OK', 'right message')
        is_ok(res.version, '1.1', 'right version')
        is_ok(res.body, b'', 'no content')
        setenv('PYJO_MAX_BUFFER_SIZE', None)

    # Parse HTTP 1.1 chunked response
    res = Pyjo.Message.Response.new()
    res.parse(b'HTTP/1.1 500 Internal Server Error\x0d\x0a')
    res.parse(b'Content-Type: text/plain\x0d\x0a')
    res.parse(b'Transfer-Encoding: chunked\x0d\x0a\x0d\x0a')
    res.parse(b'4\x0d\x0a')
    res.parse(b'abcd\x0d\x0a')
    res.parse(b'9\x0d\x0a')
    res.parse(b'abcdefghi\x0d\x0a')
    res.parse(b'0\x0d\x0a\x0d\x0a')
    ok(res.is_finished, 'response is finished')
    is_ok(res.code, 500, 'right status')
    is_ok(res.message, 'Internal Server Error', 'right message')
    is_ok(res.version, '1.1', 'right version')
    is_ok(res.headers.content_type, 'text/plain', 'right "Content-Type" value')
    is_ok(res.headers.content_length, '13', 'right "Content-Length" value')
    is_ok(res.headers.transfer_encoding, None, 'no "Transfer-Encoding" value')
    is_ok(res.body_size, 13, 'right size')

    # Parse HTTP 1.1 multipart response
    res = Pyjo.Message.Response.new()
    res.parse(b'HTTP/1.1 200 OK\x0d\x0a')
    res.parse(b'Content-Length: 420\x0d\x0a')
    res.parse(b'Content-Type: multipart/form-data; bo')
    res.parse(b'undary=----------0xKhTmLbOuNdArY\x0d\x0a\x0d\x0a')
    res.parse(b'\x0d\x0a------------0xKhTmLbOuNdArY\x0d\x0a')
    res.parse(b'Content-Disposition: form-data; name="text1"\x0d\x0a')
    res.parse(b'\x0d\x0ahallo welt test123\n')
    res.parse(b'\x0d\x0a------------0xKhTmLbOuNdArY\x0d\x0a')
    res.parse(b'Content-Disposition: form-data; name="text2"\x0d\x0a')
    res.parse(b'\x0d\x0a\x0d\x0a------------0xKhTmLbOuNdArY\x0d\x0a')
    res.parse(b'Content-Disposition: form-data; name="upload"; file')
    res.parse(b'name="hello.pl"\x0d\x0a\x0d\x0a')
    res.parse(b'Content-Type: application/octet-stream\x0d\x0a\x0d\x0a')
    res.parse(b'#!/usr/bin/perl\n\n')
    res.parse(b'use strict;\n')
    res.parse(b'use warnings;\n\n')
    res.parse(b'print "Hello World :)\\n"\n')
    res.parse(b'\x0d\x0a------------0xKhTmLbOuNdArY--')
    ok(res.is_finished, 'response is finished')
    is_ok(res.code, 200, 'right status')
    is_ok(res.message, 'OK', 'right message')
    is_ok(res.version, '1.1', 'right version')
    is_ok(
        res.headers.content_type,
        'multipart/form-data; boundary=----------0xKhTmLbOuNdArY',
        'right "Content-Type" value',
    )
    isa_ok(res.content.parts[0], Pyjo.Content.Single.object, 'right part')
    isa_ok(res.content.parts[1], Pyjo.Content.Single.object, 'right part')
    isa_ok(res.content.parts[2], Pyjo.Content.Single.object, 'right part')
    is_ok(res.content.parts[0].asset.slurp(), b'hallo welt test123\n', 'right content')

    # Parse HTTP 1.1 chunked multipart response with leftovers (at once)
    res = Pyjo.Message.Response.new()
    multipart = (
        b'HTTP/1.1 200 OK\x0d\x0a'
        b'Transfer-Encoding: chunked\x0d\x0a'
        b'Content-Type: multipart/form-data; bo'
        b'undary=----------0xKhTmLbOuNdArY\x0d\x0a\x0d\x0a'
        b'19f\x0d\x0a------------0xKhTmLbOuNdArY\x0d\x0a'
        b'Content-Disposition: form-data; name="text1"\x0d\x0a'
        b'\x0d\x0ahallo welt test123\n'
        b'\x0d\x0a------------0xKhTmLbOuNdArY\x0d\x0a'
        b'Content-Disposition: form-data; name="text2"\x0d\x0a'
        b'\x0d\x0a\x0d\x0a------------0xKhTmLbOuNdArY\x0d\x0a'
        b'Content-Disposition: form-data; name="upload"; file'
        b'name="hello.pl"\x0d\x0a'
        b'Content-Type: application/octet-stream\x0d\x0a\x0d\x0a'
        b'#!/usr/bin/perl\n\n'
        b'use strict;\n'
        b'use warnings;\n\n'
        b'print "Hello World :)\\n"\n'
        b'\x0d\x0a------------0xKhTmLbOuNdA'
        b'r\x0d\x0a3\x0d\x0aY--\x0d\x0a'
        b'0\x0d\x0a\x0d\x0a'
        b'HTTP/1.0 200 OK\x0d\x0a\x0d\x0a'
    )
    res.parse(multipart)
    ok(res.is_finished, 'response is finished')
    is_ok(res.code, 200, 'right status')
    is_ok(res.message, 'OK', 'right message')
    is_ok(res.version, '1.1', 'right version')
    is_ok(
        res.headers.content_type,
        'multipart/form-data; boundary=----------0xKhTmLbOuNdArY',
        'right "Content-Type" value',
    )
    is_ok(res.headers.content_length, '418', 'right "Content-Length" value')
    is_ok(res.headers.transfer_encoding, None, 'no "Transfer-Encoding" value')
    is_ok(res.body_size, 418, 'right size')
    isa_ok(res.content.parts[0], Pyjo.Content.Single.object, 'right part')
    isa_ok(res.content.parts[1], Pyjo.Content.Single.object, 'right part')
    isa_ok(res.content.parts[2], Pyjo.Content.Single.object, 'right part')
    is_ok(res.content.parts[0].asset.slurp(), b'hallo welt test123\n', 'right content')
    is_ok(res.upload('upload').filename, 'hello.pl', 'right filename')
    isa_ok(res.upload('upload').asset, Pyjo.Asset.Memory.object, 'right file')
    is_ok(res.upload('upload').asset.size, 69, 'right size')
    is_ok(res.content.parts[2].headers.content_type, 'application/octet-stream', 'right "Content-Type" value')
    is_ok(res.content.leftovers, b'HTTP/1.0 200 OK\x0d\x0a\x0d\x0a', 'next response in leftovers')

    # Parse HTTP 1.1 chunked multipart response (in multiple small chunks)
    res = Pyjo.Message.Response.new()
    res.parse(b'HTTP/1.1 200 OK\x0d\x0a')
    res.parse(b'Transfer-Encoding: chunked\x0d\x0a')
    res.parse(b'Content-Type: multipart/parallel; boundary=AAA; charset=utf-8')
    res.parse(b'\x0d\x0a\x0d\x0a')
    res.parse(b'7\x0d\x0a')
    res.parse(b'--AAA\x0d\x0a')
    res.parse(b'\x0d\x0a1a\x0d\x0a')
    res.parse(b'Content-Type: image/jpeg\x0d\x0a')
    res.parse(b'\x0d\x0a16\x0d\x0a')
    res.parse(b'Content-ID: 600050\x0d\x0a\x0d\x0a')
    res.parse(b'\x0d')
    res.parse(b'\x0a6')
    res.parse(b'\x0d\x0aabcd\x0d\x0a')
    res.parse(b'\x0d\x0a7\x0d\x0a')
    res.parse(b'--AAA\x0d\x0a')
    res.parse(b'\x0d\x0a1a\x0d\x0a')
    res.parse(b'Content-Type: image/jpeg\x0d\x0a')
    res.parse(b'\x0d\x0a16\x0d\x0a')
    res.parse(b'Content-ID: 600051\x0d\x0a\x0d\x0a')
    res.parse(b'\x0d\x0a6\x0d\x0a')
    res.parse(b'efgh\x0d\x0a')
    res.parse(b'\x0d\x0a7\x0d\x0a')
    res.parse(b'--AAA--')
    ok(not res.is_finished, 'response is not finished')
    res.parse(b'\x0d\x0a0\x0d\x0a\x0d\x0a')
    ok(res.is_finished, 'response is finished')
    is_ok(res.code, 200, 'right status')
    is_ok(res.message, 'OK', 'right message')
    is_ok(res.version, '1.1', 'right version')
    is_ok(res.headers.content_type, 'multipart/parallel; boundary=AAA; charset=utf-8', 'right "Content-Type" value')
    is_ok(res.headers.content_length, '129', 'right "Content-Length" value')
    is_ok(res.headers.transfer_encoding, None, 'no "Transfer-Encoding" value')
    is_ok(res.body_size, 129, 'right size')
    isa_ok(res.content.parts[0], Pyjo.Content.Single.object, 'right part')
    isa_ok(res.content.parts[1], Pyjo.Content.Single.object, 'right part')
    is_ok(res.content.parts[0].asset.slurp(), b'abcd', 'right content')
    is_ok(res.content.parts[0].headers.content_type, 'image/jpeg', 'right "Content-Type" value')
    is_ok(res.content.parts[0].headers.header('Content-ID'), '600050', 'right "Content-ID" value')
    is_ok(res.content.parts[1].asset.slurp(), b'efgh', 'right content')
    is_ok(res.content.parts[1].headers.content_type, 'image/jpeg', 'right "Content-Type" value')
    is_ok(res.content.parts[1].headers.header('Content-ID'), '600051', 'right "Content-ID" value')

    # Parse HTTP 1.1 multipart response with missing boundary
    res = Pyjo.Message.Response.new()
    res.parse(b'HTTP/1.1 200 OK\x0d\x0a')
    res.parse(b'Content-Length: 420\x0d\x0a')
    res.parse(b'Content-Type: multipart/form-data; bo\x0d\x0a\x0d\x0a')
    res.parse(b'\x0d\x0a------------0xKhTmLbOuNdArY\x0d\x0a')
    res.parse(b'Content-Disposition: form-data; name="text1"\x0d\x0a')
    res.parse(b'\x0d\x0ahallo welt test123\n')
    res.parse(b'\x0d\x0a------------0xKhTmLbOuNdArY\x0d\x0a')
    res.parse(b'Content-Disposition: form-data; name="text2"\x0d\x0a')
    res.parse(b'\x0d\x0a\x0d\x0a------------0xKhTmLbOuNdArY\x0d\x0a')
    res.parse(b'Content-Disposition: form-data; name="upload"; file')
    res.parse(b'name="hello.pl"\x0d\x0a\x0d\x0a')
    res.parse(b'Content-Type: application/octet-stream\x0d\x0a\x0d\x0a')
    res.parse(b'#!/usr/bin/perl\n\n')
    res.parse(b'use strict;\n')
    res.parse(b'use warnings;\n\n')
    res.parse(b'print "Hello World :)\\n"\n')
    res.parse(b'\x0d\x0a------------0xKhTmLbOuNdArY--')
    ok(res.is_finished, 'response is finished')
    is_ok(res.code, 200, 'right status')
    is_ok(res.message, 'OK', 'right message')
    is_ok(res.version, '1.1', 'right version')
    is_ok(res.headers.content_type, 'multipart/form-data; bo', 'right "Content-Type" value')
    isa_ok(res.content, Pyjo.Content.Single.object, 'right content')
    ok(res.content.asset.slurp().find(b'hallo welt') >= 0, 'right content')

    # Parse HTTP 1.1 gzip compressed response
    gzip = zlib.compressobj(-1, zlib.DEFLATED, zlib.MAX_WBITS | 16)
    uncompressed = b'abc' * 1000
    compressed = gzip.compress(uncompressed)
    compressed += gzip.flush()
    res = Pyjo.Message.Response.new()
    res.parse(b'HTTP/1.1 200 OK\x0d\x0a')
    res.parse(b'Content-Type: text/plain\x0d\x0a')
    res.parse(b'Content-Length: ' + b(str(len(compressed))) + b'\x0d\x0a')
    res.parse(b'Content-Encoding: GZip\x0d\x0a\x0d\x0a')
    ok(res.content.is_compressed, 'content is compressed')
    is_ok(res.content.progress, 0, 'right progress')
    res.parse(compressed[:1])
    is_ok(res.content.progress, 1, 'right progress')
    res.parse(compressed[1:])
    is_ok(res.content.progress, len(compressed), 'right progress')
    ok(not res.content.is_compressed, 'content is not compressed anymore')
    ok(res.is_finished, 'response is finished')
    ok(not res.error, 'no error')
    is_ok(res.code, 200, 'right status')
    is_ok(res.message, 'OK', 'right message')
    is_ok(res.version, '1.1', 'right version')
    is_ok(res.headers.content_type, 'text/plain', 'right "Content-Type" value')
    is_ok(res.headers.content_length, str(len(uncompressed)), 'right "Content-Length" value')
    is_ok(res.headers.content_encoding, None, 'no "Content-Encoding" value')
    is_ok(res.body, uncompressed, 'right content')

    # Parse HTTP 1.1 chunked gzip compressed response
    gzip = zlib.compressobj(-1, zlib.DEFLATED, zlib.MAX_WBITS | 16)
    uncompressed = b'abc' * 1000
    compressed = gzip.compress(uncompressed)
    compressed += gzip.flush()
    res = Pyjo.Message.Response.new()
    res.parse(b'HTTP/1.1 200 OK\x0d\x0a')
    res.parse(b'Content-Type: text/plain\x0d\x0a')
    res.parse(b'Content-Encoding: gzip\x0d\x0a')
    res.parse(b'Transfer-Encoding: chunked\x0d\x0a\x0d\x0a')
    ok(res.content.is_chunked, 'content is chunked')
    ok(res.content.is_compressed, 'content is compressed')
    res.parse(b'1\x0d\x0a')
    res.parse(compressed[:1])
    res.parse(b'\x0d\x0a')
    res.parse(b(f'{len(compressed) - 1:x}'))
    res.parse(b'\x0d\x0a')
    res.parse(compressed[1:])
    res.parse(b'\x0d\x0a')
    res.parse(b'0\x0d\x0a\x0d\x0a')
    ok(not res.content.is_chunked, 'content is not chunked anymore')
    ok(not res.content.is_compressed, 'content is not compressed anymore')
    ok(res.is_finished, 'response is finished')
    ok(not res.error, 'no error')
    is_ok(res.code, 200, 'right status')
    is_ok(res.message, 'OK', 'right message')
    is_ok(res.version, '1.1', 'right version')
    is_ok(res.headers.content_type, 'text/plain', 'right "Content-Type" value')
    is_ok(res.headers.content_length, str(len(uncompressed)), 'right "Content-Length" value')
    is_ok(res.headers.transfer_encoding, None, 'no "Transfer-Encoding" value')
    is_ok(res.headers.content_encoding, None, 'no "Content-Encoding" value')
    is_ok(res.body, uncompressed, 'right content')

    # Build HTTP 1.1 response start-line with minimal headers
    res = Pyjo.Message.Response.new()
    res.code = 404
    res.headers.date = 'Sun, 17 Aug 2008 16:27:35 GMT'
    res = Pyjo.Message.Response.new().parse(res.to_bytes())
    ok(res.is_finished, 'response is finished')
    is_ok(res.code, 404, 'right status')
    is_ok(res.message, 'Not Found', 'right message')
    is_ok(res.version, '1.1', 'right version')
    is_ok(res.headers.date, 'Sun, 17 Aug 2008 16:27:35 GMT', 'right "Date" value')
    is_ok(res.headers.content_length, '0', 'right "Content-Length" value')

    # Build HTTP 1.1 response start-line with minimal headers (strange message)
    res = Pyjo.Message.Response.new()
    res.code = 404
    res.message = 'Looks-0k!@ ;\':" #$%^<>,.\\o/ &*()'
    res.headers.date = 'Sun, 17 Aug 2008 16:27:35 GMT'
    res = Pyjo.Message.Response.new().parse(res.to_bytes())
    ok(res.is_finished, 'response is finished')
    is_ok(res.code, 404, 'right status')
    is_ok(res.message, 'Looks-0k!@ ;\':" #$%^<>,.\\o/ &*()', 'right message')
    is_ok(res.version, '1.1', 'right version')
    is_ok(res.headers.date, 'Sun, 17 Aug 2008 16:27:35 GMT', 'right "Date" value')
    is_ok(res.headers.content_length, '0', 'right "Content-Length" value')

    # Build HTTP 1.1 response start-line and header
    res = Pyjo.Message.Response.new()
    res.code = 200
    res.headers.connection = 'keep-alive'
    res.headers.date = 'Sun, 17 Aug 2008 16:27:35 GMT'
    res = Pyjo.Message.Response.new().parse(res.to_bytes())
    ok(res.is_finished, 'response is finished')
    is_ok(res.code, 200, 'right status')
    is_ok(res.message, 'OK', 'right message')
    is_ok(res.version, '1.1', 'right version')
    is_ok(res.headers.connection, 'keep-alive', 'right "Connection" value')
    is_ok(res.headers.date, 'Sun, 17 Aug 2008 16:27:35 GMT', 'right "Date" value')
    is_ok(res.headers.content_length, '0', 'right "Content-Length" value')

    # Build full HTTP 1.1 response
    res = Pyjo.Message.Response.new()
    res.code = 200
    res.headers.connection = 'keep-alive'
    res.headers.date = 'Sun, 17 Aug 2008 16:27:35 GMT'
    res.body = b'Hello World!\n'
    res = Pyjo.Message.Response.new().parse(res.to_bytes())
    ok(res.is_finished, 'response is finished')
    is_ok(res.code, 200, 'right status')
    is_ok(res.message, 'OK', 'right message')
    is_ok(res.version, '1.1', 'right version')
    is_ok(res.headers.connection, 'keep-alive', 'right "Connection" value')
    is_ok(res.headers.date, 'Sun, 17 Aug 2008 16:27:35 GMT', 'right "Date" value')
    is_ok(res.headers.content_length, '13', 'right "Content-Length" value')
    is_ok(res.body, b'Hello World!\n', 'right content')

    # Build HTTP 1.1 response parts with progress
    res = Pyjo.Message.Response.new()
    finished = Value(None)
    state = Value(None)
    progressed = Value(0)
    res.on('finish', lambda res: finished.set(res.is_finished))

    @res.on
    def progress(res, part, offset):
        state.set(part)
        progressed.set(progressed.get() + offset)

    res.code = 200
    res.headers.connection = 'keep-alive'
    res.headers.date = 'Sun, 17 Aug 2008 16:27:35 GMT'
    res.body = b'Hello World!\n'
    ok(not state.get(), 'no state')
    ok(not progressed.get(), 'no progress')
    ok(not finished.get(), 'not finished')
    ok(res.build_start_line(), 'built start-line')
    is_ok(state.get(), 'start_line', 'made progress on start_line')
    ok(progressed.get(), 'made progress')
    progressed.set(0)
    ok(not finished.get(), 'not finished')
    ok(res.build_headers(), 'built headers')
    is_ok(state.get(), 'headers', 'made progress on headers')
    ok(progressed.get(), 'made progress')
    progressed.set(0)
    ok(not finished.get(), 'not finished')
    ok(res.build_body(), 'built body')
    is_ok(state.get(), 'body', 'made progress on headers')
    ok(progressed.get(), 'made progress')
    ok(finished.get(), 'finished')
    is_ok(res.build_headers(), res.content.build_headers(), 'headers are equal')
    is_ok(res.build_body(), res.content.build_body(), 'body is equal')

    # Build HTTP 1.1 multipart response
    res = Pyjo.Message.Response.new()
    res.content = Pyjo.Content.MultiPart.new()
    res.code = 200
    res.headers.content_type = 'multipart/mixed; boundary=7am1X'
    res.headers.date = 'Sun, 17 Aug 2008 16:27:35 GMT'
    res.content.parts.append(Pyjo.Content.Single.new(asset=Pyjo.Asset.File.new()))
    res.content.parts[-1].asset.add_chunk(b'Hallo Welt lalalalalala!')
    content = Pyjo.Content.Single.new()
    content.asset.add_chunk(b'lala\nfoobar\nperl rocks\n')
    content.headers.content_type = 'text/plain'
    res.content.parts.append(content)
    res = Pyjo.Message.Response.new().parse(res.to_bytes())
    ok(res.is_finished, 'response is finished')
    is_ok(res.code, 200, 'right status')
    is_ok(res.message, 'OK', 'right message')
    is_ok(res.version, '1.1', 'right version')
    is_ok(res.headers.date, 'Sun, 17 Aug 2008 16:27:35 GMT', 'right "Date" value')
    is_ok(res.headers.content_length, '110', 'right "Content-Length" value')
    is_ok(res.headers.content_type, 'multipart/mixed; boundary=7am1X', 'right "Content-Type" value')
    is_ok(res.content.parts[0].asset.slurp(), b'Hallo Welt lalalalalala!', 'right content')
    is_ok(res.content.parts[1].headers.content_type, 'text/plain', 'right "Content-Type" value')
    is_ok(res.content.parts[1].asset.slurp(), b'lala\nfoobar\nperl rocks\n', 'right content')

    # Parse response with cookie
    res = Pyjo.Message.Response.new()
    res.parse(b'HTTP/1.0 200 OK\x0d\x0a')
    res.parse(b'Content-Type: text/plain\x0d\x0a')
    res.parse(b'Content-Length: 27\x0d\x0a')
    res.parse(b'Set-Cookie: foo=bar; path=/test\x0d\x0a\x0d\x0a')
    res.parse(b'Hello World!\n1234\nlalalala\n')
    ok(res.is_finished, 'response is finished')
    is_ok(res.code, 200, 'right status')
    is_ok(res.message, 'OK', 'right message')
    is_ok(res.version, '1.0', 'right version')
    is_ok(res.headers.content_type, 'text/plain', 'right "Content-Type" value')
    is_ok(res.headers.content_length, '27', 'right "Content-Length" value')
    is_ok(res.headers.set_cookie, 'foo=bar; path=/test', 'right "Set-Cookie" value')
    cookies = res.cookies
    is_ok(cookies[0].name, 'foo', 'right name')
    is_ok(cookies[0].value, 'bar', 'right value')
    is_ok(cookies[0].path, '/test', 'right path')
    is_ok(res.cookie('foo').value, 'bar', 'right value')
    is_ok(res.cookie('foo').path, '/test', 'right path')

    # Parse WebSocket handshake response
    res = Pyjo.Message.Response.new()
    res.parse(b'HTTP/1.1 101 Switching Protocols\x0d\x0a')
    res.parse(b'Upgrade: websocket\x0d\x0a')
    res.parse(b'Connection: Upgrade\x0d\x0a')
    res.parse(b'Sec-WebSocket-Accept: abcdef=\x0d\x0a')
    res.parse(b'Sec-WebSocket-Protocol: sample\x0d\x0a\x0d\x0a')
    ok(res.is_finished, 'response is finished')
    ok(res.is_empty, 'response is empty')
    ok(res.content.skip_body, 'body has been skipped')
    is_ok(res.code, 101, 'right status')
    is_ok(res.message, 'Switching Protocols', 'right message')
    is_ok(res.version, '1.1', 'right version')
    is_ok(res.headers.upgrade, 'websocket', 'right "Upgrade" value')
    is_ok(res.headers.connection, 'Upgrade', 'right "Connection" value')
    is_ok(res.headers.sec_websocket_accept, 'abcdef=', 'right "Sec-WebSocket-Accept" value')
    is_ok(res.headers.sec_websocket_protocol, 'sample', 'right "Sec-WebSocket-Protocol" value')
    is_ok(res.body, b'', 'no content')

    # Parse WebSocket handshake response (with frame)
    res = Pyjo.Message.Response.new()
    res.parse(b'HTTP/1.1 101 Switching Protocols\x0d\x0a')
    res.parse(b'Upgrade: websocket\x0d\x0a')
    res.parse(b'Connection: Upgrade\x0d\x0a')
    res.parse(b'Sec-WebSocket-Accept: abcdef=\x0d\x0a')
    res.parse(b'Sec-WebSocket-Protocol: sample\x0d\x0a')
    res.parse(b'\x0d\x0a\x81\x08\x77\x68\x61\x74\x65\x76\x65\x72')
    ok(res.is_finished, 'response is finished')
    ok(res.is_empty, 'response is empty')
    ok(res.content.skip_body, 'body has been skipped')
    is_ok(res.code, 101, 'right status')
    is_ok(res.message, 'Switching Protocols', 'right message')
    is_ok(res.version, '1.1', 'right version')
    is_ok(res.headers.upgrade, 'websocket', 'right "Upgrade" value')
    is_ok(res.headers.connection, 'Upgrade', 'right "Connection" value')
    is_ok(res.headers.sec_websocket_accept, 'abcdef=', 'right "Sec-WebSocket-Accept" value')
    is_ok(res.headers.sec_websocket_protocol, 'sample', 'right "Sec-WebSocket-Protocol" value')
    is_ok(res.body, b'', 'no content')
    is_ok(res.content.leftovers, b'\x81\x08\x77\x68\x61\x74\x65\x76\x65\x72', 'frame in leftovers')

    # Build WebSocket handshake response
    res = Pyjo.Message.Response.new()
    res.code = 101
    res.headers.date = 'Sun, 17 Aug 2008 16:27:35 GMT'
    res.headers.upgrade = 'websocket'
    res.headers.connection = 'Upgrade'
    res.headers.sec_websocket_accept = 'abcdef='
    res.headers.sec_websocket_protocol = 'sample'
    res = Pyjo.Message.Response.new().parse(res.to_bytes())
    ok(res.is_finished, 'response is finished')
    is_ok(res.code, 101, 'right status')
    is_ok(res.message, 'Switching Protocols', 'right message')
    is_ok(res.version, '1.1', 'right version')
    is_ok(res.headers.connection, 'Upgrade', 'right "Connection" value')
    is_ok(res.headers.date, 'Sun, 17 Aug 2008 16:27:35 GMT', 'right "Date" value')
    is_ok(res.headers.upgrade, 'websocket', 'right "Upgrade" value')
    is_ok(res.headers.content_length, '0', 'right "Content-Length" value')
    is_ok(res.headers.sec_websocket_accept, 'abcdef=', 'right "Sec-WebSocket-Accept" value')
    is_ok(res.headers.sec_websocket_protocol, 'sample', 'right "Sec-WebSocket-Protocol" value')
    is_ok(res.body, b'', 'no content')

    # Build and parse HTTP 1.1 response with 3 cookies
    res = Pyjo.Message.Response.new()
    res.code = 404
    res.headers.date = 'Sun, 17 Aug 2008 16:27:35 GMT'
    res.cookies = [
        {'name': 'foo', 'value': 'bar', 'path': '/foobar'},
        {'name': 'bar', 'value': 'baz', 'path': '/test/23'},
    ]
    res.set_cookie({'name': 'baz', 'value': 'yada', 'path': '/foobar'})
    ok(res.to_bytes(), 'message built')
    res2 = Pyjo.Message.Response.new()
    res2.parse(res.to_bytes())
    ok(res2.is_finished, 'response is finished')
    is_ok(res2.code, 404, 'right status')
    is_ok(res2.version, '1.1', 'right version')
    is_ok(res2.headers.content_length, '0', 'right "Content-Length" value')
    ok(res2.cookie('foo') is not None, 'cookie "foo" exists')
    ok(res2.cookie('bar') is not None, 'cookie "bar" exists')
    ok(res2.cookie('baz') is not None, 'cookie "baz" exists')
    none_ok(res2.cookie('yada'), 'cookie "yada" does not exist')
    is_ok(res2.cookie('foo').path, '/foobar', 'right path')
    is_ok(res2.cookie('foo').value, 'bar', 'right value')
    is_ok(res2.cookie('bar').path, '/test/23', 'right path')
    is_ok(res2.cookie('bar').value, 'baz', 'right value')
    is_ok(res2.cookie('baz').path, '/foobar', 'right path')
    is_ok(res2.cookie('baz').value, 'yada', 'right value')

    # Build chunked response body
    res = Pyjo.Message.Response.new()
    res.code = 200
    invocant = Value(None)
    res.content.write_chunk(b'hello!', lambda content, offset: invocant.set(content))
    res.content.write_chunk(b'hello world!').write_chunk(b'')
    ok(res.content.is_chunked, 'chunked content')
    ok(res.content.is_dynamic, 'dynamic content')
    is_ok(res.build_body(), b'6\x0d\x0ahello!\x0d\x0ac\x0d\x0ahello world!\x0d\x0a0\x0d\x0a\x0d\x0a', 'right format')
    isa_ok(invocant.get(), Pyjo.Content.Single.object, 'right invocant')

    # Build dynamic response body
    res = Pyjo.Message.Response.new()
    res.code = 200
    invocant = Value(None)
    res.content.write(b'hello!', lambda content, offset: invocant.set(content))
    res.content.write(b'hello world!').write(b'')
    ok(not res.content.is_chunked, 'no chunked content')
    ok(res.content.is_dynamic, 'dynamic content')
    is_ok(res.build_body(), b'hello!hello world!', 'right format')
    isa_ok(invocant.get(), Pyjo.Content.Single.object, 'right invocant')

    # Build response with callback (make sure it's called)
    res = Pyjo.Message.Response.new()
    res.code = 200
    res.headers.content_length = '10'
    res.content.write(b'lala', lambda content, offset: die(Exception('Body callback was called properly')))
    res.get_body_chunk(0)
    throws_ok(lambda: res.get_body_chunk(3), 'Body callback was called properly', 'right error')

    # Build response with callback (consistency calls)
    res = Pyjo.Message.Response.new()
    body = b'I is here'
    res.headers.content_length = str(len(body))

    def cb(content, offset):
        content.write(body[offset : offset + 1], cb)

    res.content.write(b'', cb)
    full = b''
    count = 0
    offset = 0

    while True:
        chunk = res.get_body_chunk(offset)
        if not chunk:
            break
        full += chunk
        offset = len(full)
        count += 1

    res.fix_headers()
    is_ok(res.headers.connection, None, 'no "Connection" value')
    ok(not res.content.is_dynamic, 'no dynamic content')
    is_ok(count, len(body), 'right length')
    is_ok(full, body, 'right content')

    # Build response with callback (no Content-Length header)
    res = Pyjo.Message.Response.new()
    body = b'I is here'

    def cb(content, offset):
        content.write(body[offset : offset + 1], cb)

    res.content.write(b'', cb)
    res.fix_headers()
    full = b''
    count = 0
    offset = 0

    while True:
        chunk = res.get_body_chunk(offset)
        if not chunk:
            break
        full += chunk
        offset = len(full)
        count += 1

    is_ok(res.headers.connection, 'close', 'right "Connection" value')
    ok(res.content.is_dynamic, 'dynamic content')
    is_ok(count, len(body), 'right length')
    is_ok(full, body, 'right content')

    # Body
    res = Pyjo.Message.Response.new()
    res.body = b'hi there!'
    ok(not res.content.asset.is_file, 'stored in memory')
    ok(not res.content.asset.auto_upgrade, 'no upgrade')
    is_ok(res.body, b'hi there!', 'right content')
    res.body = b''
    is_ok(res.body, b'', 'no content')
    res.body = b'hi there!'
    is_ok(res.body, b'hi there!', 'right content')
    res.body = b'0'
    is_ok(res.body, b'0', 'right content')
    is_ok(res.set(body=b'hello!').body, b'hello!', 'right content')
    res.content = Pyjo.Content.MultiPart.new()
    res.body = b'hi!'
    is_ok(res.body, b'hi!', 'right content')

    # Text
    res = Pyjo.Message.Response.new()
    snowman = b('☃')
    is_ok(res.set(body=snowman).text, '☃', 'right content')
    is_ok(res.set(body=snowman).dom().text, '☃', 'right text')
    res = Pyjo.Message.Response.new()
    yatta = b('やった', 'shift_jis')
    res.headers.content_type = 'text/plain;charset=shift_jis'
    is_ok(res.set(body=yatta).text, 'やった', 'right content')
    is_ok(res.set(body=yatta).dom().text, 'やった', 'right text')

    # Body exceeding memory limit (no upgrade)
    setenv('PYJO_MAX_MEMORY_SIZE', '8')
    res = Pyjo.Message.Response.new()
    res.body = b'hi there!'
    is_ok(res.body, b'hi there!', 'right content')
    is_ok(res.content.asset.max_memory_size, 8, 'right size')
    is_ok(res.content.asset.size, 9, 'right size')
    ok(not res.content.asset.is_file, 'stored in memory')
    setenv('PYJO_MAX_MEMORY_SIZE', None)

    # Parse response and extract JSON data
    res = Pyjo.Message.Response.new()
    res.parse(b'HTTP/1.1 200 OK\x0a')
    res.parse(b'Content-Type: application/json\x0a')
    res.parse(b'Content-Length: 27\x0a\x0a')
    res.parse(encode_json({'foo': 'bar', 'baz': [1, 2, 3]}))
    ok(res.is_finished, 'response is finished')
    is_ok(res.code, 200, 'right status')
    is_ok(res.message, 'OK', 'right message')
    is_ok(res.version, '1.1', 'right version')
    is_deeply_ok(res.json(), {'foo': 'bar', 'baz': [1, 2, 3]}, 'right JSON data')
    is_ok(res.json('/foo'), 'bar', 'right result')
    is_ok(res.json('/baz/1'), 2, 'right result')
    is_deeply_ok(res.json('/baz'), [1, 2, 3], 'right result')
    res.json()['baz'][1] = 4
    is_deeply_ok(res.json('/baz'), [1, 4, 3], 'right result')

    # Parse response and extract HTML
    res = Pyjo.Message.Response.new()
    res.parse(b'HTTP/1.1 200 OK\x0a')
    res.parse(b'Content-Type: text/html\x0a')
    res.parse(b'Content-Length: 51\x0a\x0a')
    res.parse(b'<p>foo<a href="/">bar</a><a href="/baz">baz</a></p>')
    ok(res.is_finished, 'response is finished')
    is_ok(res.code, 200, 'right status')
    is_ok(res.message, 'OK', 'right message')
    is_ok(res.version, '1.1', 'right version')
    is_ok(res.dom().at('p').text, 'foo', 'right value')
    is_ok(res.dom().at('p > a').text, 'bar', 'right value')
    is_ok(res.dom('p').first().text, 'foo', 'right value')
    is_deeply_ok(res.dom('p > a').map('text').to_list(), ['bar', 'baz'], 'right values')
    text = res.dom('a').map('set', content='yada').first().root.find('p > a').map('text').to_list()
    is_deeply_ok(text, ['yada', 'yada'], 'right values')
    is_deeply_ok(res.dom('p > a').map('text').to_list(), ['yada', 'yada'], 'right values')
    text = res.dom().find('a').map('set', content='test').first().root.find('p > a').map('text').to_list()
    is_deeply_ok(text, ['test', 'test'], 'right values')
    is_deeply_ok(res.dom().find('p > a').map('text').to_list(), ['test', 'test'], 'right values')

    # Build DOM from response with charset
    res = Pyjo.Message.Response.new()
    res.parse(b'HTTP/1.0 200 OK\x0a')
    res.parse(b'Content-Type: application/atom+xml; charset=UTF-8; type=feed\x0a')
    res.parse(b'\x0a')
    res.body = b'<p>foo <a href="/">bar</a><a href="/baz">baz</a></p>'
    ok(not res.is_finished, 'response is not finished')
    is_ok(res.headers.content_type, 'application/atom+xml; charset=UTF-8; type=feed', 'right "Content-Type" value')
    ok(res.dom(), 'dom built')
    count = Value(0)
    res.dom('a').each(lambda i, n: count.inc())
    is_ok(count.get(), 2, 'all anchors found')

    done_testing()
