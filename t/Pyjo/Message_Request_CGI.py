if __name__ == '__main__':
    from Pyjo.Test import *  # noqa

    from Pyjo.Util import setenv

    import Pyjo.Message.Request

    from t.lib.Value import Value

    # Parse Lighttpd CGI environment variables and body
    req = Pyjo.Message.Request.new()
    body = Value(0)
    req.content.on('body', lambda content: body.inc())
    req.parse(
        {
            'HTTP_CONTENT_LENGTH': '11',
            'HTTP_DNT': '1',
            'PATH_INFO': '/te+st/index.cgi/foo/bar',
            'QUERY_STRING': 'lalala=23&bar=baz',
            'REQUEST_METHOD': 'POST',
            'SCRIPT_NAME': '/te+st/index.cgi',
            'HTTP_HOST': 'localhost:8080',
            'SERVER_PROTOCOL': 'HTTP/1.0',
        }
    )
    is_ok(body.get(), 1, 'body event has been emitted once')
    req.parse(b'Hello ')
    is_ok(body.get(), 1, 'body event has been emitted once')
    req.parse(b'World')
    is_ok(body.get(), 1, 'body event has been emitted once')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'POST', 'right method')
    is_ok(req.url.path, 'foo/bar', 'right path')
    is_ok(req.url.base.path, '/te+st/index.cgi/', 'right base path')
    is_ok(req.url.base.host, 'localhost', 'right base host')
    is_ok(req.url.base.port, 8080, 'right base port')
    is_ok(req.url.query, 'lalala=23&bar=baz', 'right query')
    is_ok(req.version, '1.0', 'right version')
    is_ok(req.headers.dnt, '1', 'right "DNT" value')
    is_ok(req.body, b'Hello World', 'right content')
    is_ok(
        req.url.to_abs().to_str(),
        'http://localhost:8080/te+st/index.cgi/foo/bar?lalala=23&bar=baz',
        'right absolute URL',
    )

    # Parse Lighttpd CGI environment variables and body (behind reverse proxy)
    req = Pyjo.Message.Request.new()
    req.parse(
        {
            'HTTP_CONTENT_LENGTH': '11',
            'HTTP_DNT': '1',
            'HTTP_X_FORWARDED_FOR': '127.0.0.1',
            'PATH_INFO': '/test/index.cgi/foo/bar',
            'QUERY_STRING': 'lalala=23&bar=baz',
            'REQUEST_METHOD': 'POST',
            'SCRIPT_NAME': '/test/index.cgi',
            'HTTP_HOST': 'mojolicio.us',
            'SERVER_PROTOCOL': 'HTTP/1.0',
        }
    )
    req.parse(b'Hello World')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'POST', 'right method')
    is_ok(req.url.path, 'foo/bar', 'right path')
    is_ok(req.url.base.path, '/test/index.cgi/', 'right base path')
    is_ok(req.url.base.host, 'mojolicio.us', 'right base host')
    is_ok(req.url.base.port, None, 'no base port')
    is_ok(req.url.query, 'lalala=23&bar=baz', 'right query')
    is_ok(req.version, '1.0', 'right version')
    is_ok(req.headers.dnt, '1', 'right "DNT" value')
    is_ok(req.body, b'Hello World', 'right content')
    is_ok(
        req.url.to_abs().to_str(), 'http://mojolicio.us/test/index.cgi/foo/bar?lalala=23&bar=baz', 'right absolute URL'
    )

    # Parse Apache CGI environment variables and body
    req = Pyjo.Message.Request.new()
    req.parse(
        {
            'CONTENT_LENGTH': '11',
            'CONTENT_TYPE': 'application/x-www-form-urlencoded',
            'HTTP_DNT': '1',
            'PATH_INFO': '/test/index.cgi/foo/bar',
            'QUERY_STRING': 'lalala=23&bar=baz',
            'REQUEST_METHOD': 'POST',
            'SCRIPT_NAME': '/test/index.cgi',
            'HTTP_HOST': 'localhost:8080',
            'SERVER_PROTOCOL': 'HTTP/1.0',
        }
    )
    req.parse(b'hello=world')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'POST', 'right method')
    is_ok(req.url.path, 'foo/bar', 'right path')
    is_ok(req.url.base.path, '/test/index.cgi/', 'right base path')
    is_ok(req.url.base.host, 'localhost', 'right base host')
    is_ok(req.url.base.port, 8080, 'right base port')
    is_ok(req.url.query, 'lalala=23&bar=baz', 'right query')
    is_ok(req.version, '1.0', 'right version')
    is_ok(req.headers.dnt, '1', 'right "DNT" value')
    is_ok(req.body, b'hello=world', 'right content')
    is_deeply_ok(req.param('hello'), 'world', 'right value')
    is_ok(
        req.url.to_abs().to_str(),
        'http://localhost:8080/test/index.cgi/foo/bar?lalala=23&bar=baz',
        'right absolute URL',
    )

    # Parse Apache CGI environment variables and body (file storage)
    setenv('PYJO_MAX_MEMORY_SIZE', '10')
    req = Pyjo.Message.Request.new()
    is_ok(req.content.asset.max_memory_size, 10, 'right size')
    ok(not req.content.is_parsing_body, 'is not parsing body')
    req.parse(
        {
            'CONTENT_LENGTH': '12',
            'CONTENT_TYPE': 'text/plain',
            'HTTP_DNT': '1',
            'PATH_INFO': '/test/index.cgi/foo/bar',
            'QUERY_STRING': 'lalala=23&bar=baz',
            'REQUEST_METHOD': 'POST',
            'SCRIPT_NAME': '/test/index.cgi',
            'HTTP_HOST': 'localhost:8080',
            'SERVER_PROTOCOL': 'HTTP/1.1',
        }
    )
    ok(req.content.is_parsing_body, 'is parsing body')
    is_ok(req.content.progress, 0, 'right progress')
    req.parse(b'Hello ')
    ok(req.content.is_parsing_body, 'is parsing body')
    ok(not req.content.asset.is_file, 'stored in memory')
    is_ok(req.content.progress, 6, 'right progress')
    req.parse(b'World!')
    ok(not req.content.is_parsing_body, 'is not parsing body')
    ok(req.content.asset.is_file, 'stored in file')
    is_ok(req.content.progress, 12, 'right progress')
    ok(req.is_finished, 'request is finished')
    ok(not req.content.is_multipart, 'no multipart content')
    is_ok(req.method, 'POST', 'right method')
    is_ok(req.url.path, 'foo/bar', 'right path')
    is_ok(req.url.base.path, '/test/index.cgi/', 'right base path')
    is_ok(req.url.base.host, 'localhost', 'right base host')
    is_ok(req.url.base.port, 8080, 'right base port')
    is_ok(req.url.query, 'lalala=23&bar=baz', 'right query')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.headers.dnt, '1', 'right "DNT" value')
    is_ok(req.headers.content_type, 'text/plain', 'right "Content-Type" value')
    is_ok(req.headers.content_length, '12', 'right "Content-Length" value')
    is_ok(req.body, b'Hello World!', 'right content')
    is_ok(
        req.url.to_abs().to_str(),
        'http://localhost:8080/test/index.cgi/foo/bar?lalala=23&bar=baz',
        'right absolute URL',
    )
    setenv('PYJO_MAX_MEMORY_SIZE', None)

    # Parse Apache CGI environment variables with basic authentication
    req = Pyjo.Message.Request.new()
    req.parse(
        {
            'CONTENT_LENGTH': '11',
            'HTTP_Authorization': 'Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ==',
            'HTTP_Proxy_Authorization': 'Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ==',
            'CONTENT_TYPE': 'application/x-www-form-urlencoded',
            'HTTP_DNT': '1',
            'PATH_INFO': '/test/index.cgi/foo/bar',
            'QUERY_STRING': 'lalala=23&bar=baz',
            'REQUEST_METHOD': 'POST',
            'SCRIPT_NAME': '/test/index.cgi',
            'HTTP_HOST': 'localhost:8080',
            'SERVER_PROTOCOL': 'HTTP/1.0',
        }
    )
    req.parse(b'hello=world')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'POST', 'right method')
    is_ok(req.url.path, 'foo/bar', 'right path')
    is_ok(req.url.base.path, '/test/index.cgi/', 'right base path')
    is_ok(req.url.base.host, 'localhost', 'right base host')
    is_ok(req.url.base.port, 8080, 'right base port')
    is_ok(req.url.query, 'lalala=23&bar=baz', 'right query')
    is_ok(req.version, '1.0', 'right version')
    is_ok(req.headers.dnt, '1', 'right "DNT" value')
    is_ok(req.body, b'hello=world', 'right content')
    is_deeply_ok(req.param('hello'), 'world', 'right value')
    is_ok(
        req.url.to_abs().to_str(),
        'http://localhost:8080/test/index.cgi/foo/bar?lalala=23&bar=baz',
        'right absolute URL',
    )
    is_ok(req.url.base, 'http://localhost:8080/test/index.cgi/', 'right base URL')
    is_ok(req.url.base.userinfo, 'Aladdin:open sesame', 'right userinfo')
    is_ok(req.url, 'foo/bar?lalala=23&bar=baz', 'right URL')
    is_ok(req.proxy.userinfo, 'Aladdin:open sesame', 'right proxy userinfo')

    # Parse Apache 2.2 (win32) CGI environment variables and body
    req = Pyjo.Message.Request.new()
    finished = Value(None)
    progress = Value(0)
    req.on('finish', lambda req: finished.set(req.is_finished))
    req.on('progress', lambda req, state, offset: progress.inc())
    ok(not finished.get(), 'not finished')
    ok(not progress.get(), 'no progress')
    is_ok(req.content.progress, 0, 'right progress')
    req.parse(
        {
            'CONTENT_LENGTH': '87',
            'CONTENT_TYPE': 'application/x-www-form-urlencoded; charset=UTF-8',
            'PATH_INFO': '',
            'QUERY_STRING': '',
            'REQUEST_METHOD': 'POST',
            'SCRIPT_NAME': '/index.pl',
            'HTTP_HOST': 'test1',
            'SERVER_PROTOCOL': 'HTTP/1.1',
        }
    )
    ok(not finished.get(), 'not finished')
    ok(progress.get(), 'made progress')
    progress.set(0)
    is_ok(req.content.progress, 0, 'right progress')
    req.parse(b'request=&ajax=true&login=test&password=111&')
    ok(not finished.get(), 'not finished')
    ok(progress.get(), 'made progress')
    progress.set(0)
    is_ok(req.content.progress, 43, 'right progress')
    req.parse(b'edition=db6d8b30-16df-4ecd-be2f-c8194f94e1f4')
    ok(finished.get(), 'finished')
    ok(progress.get(), 'made progress')
    is_ok(req.content.progress, 87, 'right progress')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'POST', 'right method')
    is_ok(req.url.path, '', 'no path')
    is_ok(req.url.base.path, '/index.pl/', 'right base path')
    is_ok(req.url.base.host, 'test1', 'right base host')
    is_ok(req.url.base.port, None, 'no base port')
    ok(not req.url.query.to_str(), 'no query')
    is_ok(req.version, '1.1', 'right version')
    is_ok(
        req.body,
        b'request=&ajax=true&login=test&password=111&edition=db6d8b30-16df-4ecd-be2f-c8194f94e1f4',
        'right content',
    )
    is_ok(req.param('ajax'), 'true', 'right value')
    is_ok(req.param('login'), 'test', 'right value')
    is_ok(req.param('password'), '111', 'right value')
    is_ok(req.param('edition'), 'db6d8b30-16df-4ecd-be2f-c8194f94e1f4', 'right value')
    is_ok(req.url.to_abs().to_str(), 'http://test1/index.pl/', 'right absolute URL')

    # Parse Apache 2.2 (win32) CGI environment variables and body
    req = Pyjo.Message.Request.new()
    req.parse(
        {
            'CONTENT_LENGTH': '87',
            'CONTENT_TYPE': 'application/x-www-form-urlencoded; charset=UTF-8',
            'PATH_INFO': '',
            'QUERY_STRING': '',
            'REQUEST_METHOD': 'POST',
            'SCRIPT_NAME': '/index.pl',
            'HTTP_HOST': 'test1',
            'SERVER_PROTOCOL': 'HTTP/1.1',
        }
    )
    req.parse(b'request=&ajax=true&login=test&password=111&')
    req.parse(b'edition=db6d8b30-16df-4ecd-be2f-c8194f94e1f4')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'POST', 'right method')
    is_ok(req.url.path, '', 'no path')
    is_ok(req.url.base.path, '/index.pl/', 'right base path')
    is_ok(req.url.base.host, 'test1', 'right base host')
    is_ok(req.url.base.port, None, 'no base port')
    ok(not req.url.query.to_str(), 'no query')
    is_ok(req.version, '1.1', 'right version')
    is_ok(
        req.body,
        b'request=&ajax=true&login=test&password=111&edition=db6d8b30-16df-4ecd-be2f-c8194f94e1f4',
        'right content',
    )
    is_ok(req.param('ajax'), 'true', 'right value')
    is_ok(req.param('login'), 'test', 'right value')
    is_ok(req.param('password'), '111', 'right value')
    is_ok(req.param('edition'), 'db6d8b30-16df-4ecd-be2f-c8194f94e1f4', 'right value')
    is_ok(req.url.to_abs().to_str(), 'http://test1/index.pl/', 'right absolute URL')

    # Parse Apache 2.2.14 CGI environment variables and body (root)
    req = Pyjo.Message.Request.new()
    req.parse(
        {
            'SCRIPT_NAME': '/upload',
            'SERVER_NAME': '127.0.0.1',
            'SERVER_ADMIN': '[no address given]',
            'PATH_INFO': '/upload',
            'HTTP_CONNECTION': 'Keep-Alive',
            'REQUEST_METHOD': 'POST',
            'CONTENT_LENGTH': '11',
            'SCRIPT_FILENAME': '/tmp/SnLu1cQ3t2/test.fcgi',
            'SERVER_SOFTWARE': 'Apache/2.2.14 (Unix) mod_fastcgi/2.4.2',
            'QUERY_STRING': '',
            'REMOTE_PORT': '58232',
            'HTTP_USER_AGENT': 'Mojolicious (Perl)',
            'SERVER_PORT': '13028',
            'SERVER_SIGNATURE': '',
            'REMOTE_ADDR': '127.0.0.1',
            'CONTENT_TYPE': 'application/x-www-form-urlencoded; charset=UTF-8',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'REQUEST_URI': '/upload',
            'GATEWAY_INTERFACE': 'CGI/1.1',
            'SERVER_ADDR': '127.0.0.1',
            'DOCUMENT_ROOT': '/tmp/SnLu1cQ3t2',
            'PATH_TRANSLATED': '/tmp/test.fcgi/upload',
            'HTTP_HOST': '127.0.0.1:13028',
        }
    )
    req.parse(b'hello=world')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'POST', 'right method')
    is_ok(req.url.base.host, '127.0.0.1', 'right base host')
    is_ok(req.url.base.port, 13028, 'right base port')
    is_ok(req.url.path, '', 'no path')
    is_ok(req.url.base.path, '/upload/', 'right base path')
    is_ok(req.version, '1.1', 'right version')
    ok(not req.is_secure, 'not secure')
    is_ok(req.body, b'hello=world', 'right content')
    is_deeply_ok(req.param('hello'), 'world', 'right parameters')
    is_ok(req.url.to_abs().to_str(), 'http://127.0.0.1:13028/upload/', 'right absolute URL')

    # Parse Apache 2.2.11 CGI environment variables and body (HTTPS=ON)
    req = Pyjo.Message.Request.new()
    req.parse(
        {
            'CONTENT_LENGTH': 11,
            'CONTENT_TYPE': 'application/x-www-form-urlencoded',
            'PATH_INFO': '/foo/bar',
            'QUERY_STRING': '',
            'REQUEST_METHOD': 'GET',
            'SCRIPT_NAME': '/test/index.cgi',
            'HTTP_HOST': 'localhost',
            'HTTPS': 'ON',
            'SERVER_PROTOCOL': 'HTTP/1.0',
        }
    )
    req.parse(b'hello=world')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.url.base.host, 'localhost', 'right base host')
    is_ok(req.url.path, 'foo/bar', 'right path')
    is_ok(req.url.base.path, '/test/index.cgi/', 'right base path')
    is_ok(req.version, '1.0', 'right version')
    ok(req.is_secure, 'is secure')
    is_ok(req.body, b'hello=world', 'right content')
    is_deeply_ok(req.param('hello'), 'world', 'right parameters')
    is_ok(req.url.to_abs().to_str(), 'https://localhost/test/index.cgi/foo/bar', 'right absolute URL')

    # Parse Apache 2.2.11 CGI environment variables and body (trailing slash)
    req = Pyjo.Message.Request.new()
    req.parse(
        {
            'CONTENT_LENGTH': 11,
            'CONTENT_TYPE': 'application/x-www-form-urlencoded',
            'PATH_INFO': '/foo/bar/',
            'QUERY_STRING': '',
            'REQUEST_METHOD': 'GET',
            'SCRIPT_NAME': '/test/index.cgi',
            'HTTP_HOST': 'localhost',
            'SERVER_PROTOCOL': 'HTTP/1.0',
        }
    )
    req.parse(b'hello=world')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.url.base.host, 'localhost', 'right base host')
    is_ok(req.url.path, 'foo/bar/', 'right path')
    is_ok(req.url.base.path, '/test/index.cgi/', 'right base path')
    is_ok(req.version, '1.0', 'right version')
    is_ok(req.body, b'hello=world', 'right content')
    is_deeply_ok(req.param('hello'), 'world', 'right parameters')
    is_ok(req.url.to_abs().to_str(), 'http://localhost/test/index.cgi/foo/bar/', 'right absolute URL')

    # Parse Apache 2.2.11 CGI environment variables and body (no SCRIPT_NAME)
    req = Pyjo.Message.Request.new()
    req.parse(
        {
            'CONTENT_LENGTH': 11,
            'CONTENT_TYPE': 'application/x-www-form-urlencoded',
            'PATH_INFO': '/foo/bar',
            'QUERY_STRING': '',
            'REQUEST_METHOD': 'GET',
            'HTTP_HOST': 'localhost',
            'SERVER_PROTOCOL': 'HTTP/1.0',
        }
    )
    req.parse(b'hello=world')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.url.base.host, 'localhost', 'right base host')
    is_ok(req.url.path, '/foo/bar', 'right path')
    is_ok(req.url.base.path, '', 'no base path')
    is_ok(req.version, '1.0', 'right version')
    is_ok(req.body, b'hello=world', 'right content')
    is_deeply_ok(req.param('hello'), 'world', 'right parameters')
    is_ok(req.url.to_abs().to_str(), 'http://localhost/foo/bar', 'right absolute URL')

    # Parse Apache 2.2.11 CGI environment variables and body (no PATH_INFO)
    req = Pyjo.Message.Request.new()
    req.parse(
        {
            'CONTENT_LENGTH': 11,
            'CONTENT_TYPE': 'application/x-www-form-urlencoded',
            'QUERY_STRING': '',
            'REQUEST_METHOD': 'GET',
            'SCRIPT_NAME': '/test/index.cgi',
            'HTTP_HOST': 'localhost',
            'SERVER_PROTOCOL': 'HTTP/1.0',
        }
    )
    req.parse(b'hello=world')
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.url.base.host, 'localhost', 'right base host')
    is_ok(req.url.path, '', 'no path')
    is_ok(req.url.base.path, '/test/index.cgi/', 'right base path')
    is_ok(req.version, '1.0', 'right version')
    is_ok(req.body, b'hello=world', 'right content')
    is_deeply_ok(req.param('hello'), 'world', 'right parameters')
    is_ok(req.url.to_abs().to_str(), 'http://localhost/test/index.cgi/', 'right absolute URL')

    # Parse Apache 2.2.9 CGI environment variables (root without PATH_INFO)
    req = Pyjo.Message.Request.new()
    req.parse(
        {
            'SCRIPT_NAME': '/cgi-bin/myapp/myapp.pl',
            'HTTP_CONNECTION': 'keep-alive',
            'HTTP_HOST': 'getmyapp.org',
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': '',
            'REQUEST_URI': '/cgi-bin/myapp/myapp.pl',
            'SERVER_PROTOCOL': 'HTTP/1.1',
        }
    )
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.url.base.host, 'getmyapp.org', 'right base host')
    is_ok(req.url.path, '', 'no path')
    is_ok(req.url.base.path, '/cgi-bin/myapp/myapp.pl/', 'right base path')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url.to_abs().to_str(), 'http://getmyapp.org/cgi-bin/myapp/myapp.pl/', 'right absolute URL')

    # Parse Apache mod_fastcgi CGI environment variables (multipart file upload)
    req = Pyjo.Message.Request.new()
    is_ok(req.content.progress, 0, 'right progress')
    req.parse(
        {
            'SCRIPT_NAME': '',
            'SERVER_NAME': '127.0.0.1',
            'SERVER_ADMIN': '[no address given]',
            'PATH_INFO': '/upload',
            'HTTP_CONNECTION': 'Keep-Alive',
            'REQUEST_METHOD': 'POST',
            'CONTENT_LENGTH': '139',
            'SCRIPT_FILENAME': '/tmp/SnLu1cQ3t2/test.fcgi',
            'SERVER_SOFTWARE': 'Apache/2.2.14 (Unix) mod_fastcgi/2.4.2',
            'QUERY_STRING': '',
            'REMOTE_PORT': '58232',
            'HTTP_USER_AGENT': 'Mojolicious (Perl)',
            'SERVER_PORT': '13028',
            'SERVER_SIGNATURE': '',
            'REMOTE_ADDR': '127.0.0.1',
            'CONTENT_TYPE': 'multipart/form-data; boundary=8jXGX',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'PATH': '/usr/local/bin:/usr/local/sbin:/usr/bin:/bin:/usr/sbin:/sbin',
            'REQUEST_URI': '/upload',
            'GATEWAY_INTERFACE': 'CGI/1.1',
            'SERVER_ADDR': '127.0.0.1',
            'DOCUMENT_ROOT': '/tmp/SnLu1cQ3t2',
            'PATH_TRANSLATED': '/tmp/test.fcgi/upload',
            'HTTP_HOST': '127.0.0.1:13028',
        }
    )
    is_ok(req.content.progress, 0, 'right progress')
    req.parse(b'--8jXGX\x0d\x0a')
    is_ok(req.content.progress, 9, 'right progress')
    req.parse(
        b'Content-Disposition: form-data; name="file"; filename="file.txt"'
        b'\x0d\x0aContent-Type: application/octet-stream\x0d\x0a\x0d\x0a'
    )
    is_ok(req.content.progress, 117, 'right progress')
    req.parse(b'11023456789')
    is_ok(req.content.progress, 128, 'right progress')
    req.parse(b'\x0d\x0a--8jXGX--')
    is_ok(req.content.progress, 139, 'right progress')
    ok(req.is_finished, 'request is finished')
    ok(req.content.is_multipart, 'multipart content')
    is_ok(req.method, 'POST', 'right method')
    is_ok(req.url.base.host, '127.0.0.1', 'right base host')
    is_ok(req.url.path, '/upload', 'right path')
    is_ok(req.url.base.path, '', 'no base path')
    is_ok(req.version, '1.1', 'right version')
    is_ok(req.url.to_abs().to_str(), 'http://127.0.0.1:13028/upload', 'right absolute URL')
    upload = req.upload('file')
    is_ok(upload.filename, 'file.txt', 'right filename')
    is_ok(upload.slurp(), b'11023456789', 'right uploaded content')

    # Parse IIS 7.5 like CGI environment (HTTPS=off)
    req = Pyjo.Message.Request.new()
    req.parse(
        {
            'CONTENT_LENGTH': 0,
            'PATH_INFO': '/index.pl/',
            'SERVER_SOFTWARE': 'Microsoft-IIS/7.5',
            'QUERY_STRING': '',
            'REQUEST_METHOD': 'GET',
            'SCRIPT_NAME': '/index.pl',
            'HTTP_HOST': 'test',
            'HTTPS': 'off',
            'SERVER_PROTOCOL': 'HTTP/1.1',
        }
    )
    ok(req.is_finished, 'request is finished')
    is_ok(req.method, 'GET', 'right method')
    is_ok(req.url.path, '', 'right URL')
    is_ok(req.url.base.protocol, 'http', 'right base protocol')
    is_ok(req.url.base.path, '/index.pl/', 'right base path')
    is_ok(req.url.base.host, 'test', 'right base host')
    ok(not req.url.query.to_str(), 'no query')
    is_ok(req.version, '1.1', 'right version')
    ok(not req.is_secure, 'not secure')

    done_testing()
