r"""
Pyjo.Message.Request - HTTP request
===================================
::

    import Pyjo.Message.Request

    # Parse
    req = Pyjo.Message.Request.new()
    req.parse(b"GET /foo HTTP/1.0\x0d\x0a")
    req.parse(b"Content-Length: 12\x0d\x0a")
    req.parse(b"Content-Type: text/plain\x0d\x0a\x0d\x0a")
    req.parse(b'Hello World!')
    print(req.method)
    print(req.headers.content_type)
    print(req.body)

    # Build
    req = Pyjo.Message.Request.new()
    req.url.parse('http://127.0.0.1/foo/bar')
    req.method = 'GET'
    print(req)

:mod:`Pyjo.Message.Request` is a container for HTTP requests based on
:rfc:`7230`,
:rfc:`7231`,
:rfc:`7235` and
:rfc:`2817`.

Events
------

:mod:`Pyjo.Message.Request` inherits all events from :mod:`Pyjo.Message`.

Classes
-------
"""

import Pyjo.Cookie.Request
import Pyjo.Message
import Pyjo.URL

from Pyjo.Regexp import r
from Pyjo.Util import b, b64_decode, b64_encode, convert, notnone, u

import os


re_start_line = r(rb'^\s*(.*?)\x0d?\x0a')
re_request = r(rb'^(\S+)\s+(\S+)\s+HTTP\/(\d\.\d)$')
re_hostport = r(r'^([^:]*):?(.*)$')
re_server_protocol = r(r'^([^/]+)/([^/]+)$')


class Pyjo_Message_Request(Pyjo.Message.object):
    """
    :mod:`Pyjo.Message.Request` inherits all attributes and methods from
    :mod:`Pyjo.Message` and implements the following new ones.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.environ = kwargs.get('environ', {})
        """::

            environ = req.environ
            req.environ = {}

        Direct access to the ``CGI`` or ``WSGI`` environment hash if available. ::

            # Check CGI version
            version = req.environ['GATEWAY_INTERFACE']

            # Check WSGI version
            version = req.environ['wsgi.version']
        """

        self.method = kwargs.get('method', 'GET')
        """::

            method = req.method
            req.method = 'POST'

        HTTP request method, defaults to ``GET``.
        """

        self.url = notnone(kwargs.get('url'), lambda: Pyjo.URL.new())
        """::

            url = req.url
            req.url = Pyjo.URL.new()

        HTTP request URL, defaults to a `Pyjo.URL` object. ::

            # Get request information
            info = req.url.to_abs().userinfo
            host = req.url.to_abs().host
            path = req.url.to_abs().path
        """

        self.reverse_proxy = kwargs.get('reverse_proxy')
        """::

            boolean = req.reverse_proxy
            req.reverse_proxy = boleean

        Request has been performed through a reverse proxy.
        """

        self._params = None
        self._proxy = None
        self._start_buffer = None

    def __repr__(self):
        """::

            string = repr(req)

        String representation of an object shown in console.
        """
        return f'<{self.__class__.__module__}.{self.__class__.__name__} method={repr(self.method)} url={repr(self.url)} version={repr(self.version)}>'

    def clone(self):
        """::

            clone = req.clone

        Clone request if possible, otherwise return ``None``.
        """
        # Dynamic requests cannot be cloned
        content = self.content.clone()
        if content is not None:
            clone = self.new(content=content, method=self.method, url=self.url.clone(), version=self.version)
            if self._proxy:
                clone._proxy = self._proxy.clone()
            return clone
        else:
            return

    @property
    def cookies(self):
        """::

            cookies = req.cookies
            req.cookies = cookies

        Access request cookies, usually :mod:`Pyjo.Cookie.Request` objects. ::

            # Names of all cookies
            for cookie in req.cookies:
                print(cookie.name)
        """
        # Parse cookies
        headers = self.headers
        cookies = headers.cookie
        if cookies is not None:
            return Pyjo.Cookie.Request.parse(cookies)
        else:
            return

    @cookies.setter
    def cookies(self, value):
        headers = self.headers
        headers.cookies = []
        self.set_cookie(*value)

    def every_param(self, name):
        """::

            values = req.every_param('foo')

        Similar to :meth:`param`, but returns all values sharing the same name as an
        array reference. ::

            # Get first value
            print(req.every_param('foo')[0])
        """
        return self.params.every_param(name)

    def extract_start_line(self, buf):
        """::

            boolean = req.extract_start_line(buf)

        Extract request-line from string.
        """
        # Ignore any leading empty lines
        m = re_start_line.search(buf)
        if not m:
            return

        line = m.group(1)
        del buf[: m.end()]
        m = re_request.search(line)

        if not m:
            self.set_error(message='Bad request start-line')
            return

        self.method = u(m.group(1), 'ascii')
        self.version = u(m.group(3), 'ascii')
        url = self.url

        if self.method == 'CONNECT':
            url.host_port = u(m.group(2), 'latin-1')
        else:
            url.parse(m.group(2))

        return bool(url)

    def fix_headers(self):
        """::

            req = req.fix_headers()

        Make sure request has all required headers.
        """
        if self._fixed:
            return self

        super().fix_headers()

        # Host
        url = self.url
        headers = self.headers
        if not headers.host:
            headers.host = url.host_port

        # Basic authentication
        info = url.userinfo
        if info and not headers.authorization:
            headers.authorization = 'Basic ' + b64_encode(b(info), '')

        # Basic proxy authentication
        proxy = self.proxy
        if proxy:
            info = proxy.userinfo
            if info and not headers.proxy_authorization:
                headers.proxy_authorization = 'Basic ' + b64_encode(b(info), '')

        return self

    def get_start_line_chunk(self, offset):
        """::

            chunk = req.get_start_line_chunk(offset)

        Get a chunk of request-line data starting from a specific position.
        """
        if self._start_buffer is None:
            # Path
            url = self.url
            path = url.path_query
            if not path.startswith('/'):
                path = '/' + path

            # CONNECT
            method = self.method.upper()
            if method == 'CONNECT':
                port = url.port or (443 if url.protocol == 'https' else 80)
                path = f'{url.ihost}:{port}'

            # Proxy
            elif self.proxy and url.protocol != 'https':
                if not self.is_handshake:
                    path = url.clone().set(userinfo=None)

            self._start_buffer = bytearray(b(f'{method} {path} HTTP/{self.version}\x0d\x0a'))

        self.emit('progress', 'start_line', offset)
        return self._start_buffer[offset : offset + 131072]

    @property
    def is_handshake(self):
        """::

            boolean = req.is_handshake

        Check ``Upgrade`` header for ``websocket`` value.
        """
        return notnone(self.headers.upgrade, '').lower() == 'websocket'

    @property
    def is_secure(self):
        """::

            boolean = req.is_secure

        Check if connection is secure.
        """
        url = self.url
        return (url.protocol or url.base.protocol) == 'https'

    @property
    def is_xhr(self):
        """::

            boolean = req.is_xhr

        Check ``X-Requested-With`` header for ``XMLHttpRequest`` value.
        """
        return notnone(self.headers.header('X-Requested-With'), '').lower().find('xmlhttprequest') >= 0

    def param(self, name, *values):
        """::

            value = req.param('name')
            value = req.param('name', 'value')

        Access ``GET`` and ``POST`` parameters extracted from the query string and
        ``application/x-www-form-urlencoded`` or ``multipart/form-data`` message body. If
        there are multiple values sharing the same name, and you want to access more
        than just the last one, you can use :meth:`every_param`. Note that this method
        caches all data, so it should not be called before the entire request body has
        been received. Parts of the request body need to be loaded into memory to parse
        ``POST`` parameters, so you have to make sure it is not excessively large,
        there's a 16MB limit by default.
        """
        return self.params.param(name, *values)

    @property
    def params(self):
        """::

            params = req.params

        All ``GET`` and ``POST`` parameters extracted from the query string and
        ``application/x-www-form-urlencoded`` or ``multipart/form-data`` message body,
        usually a :mod:`Pyjo.Parameters` object. Note that this method caches all data, so
        it should not be called before the entire request body has been received. Parts
        of the request body need to be loaded into memory to parse ``POST`` parameters,
        so you have to make sure it is not excessively large, there's a 16MB limit by
        default. ::

            # Get parameter names and values
            params_dict = req.params.to_dict()
        """
        if not self._params:
            self._params = self.body_params.clone().append(self.query_params)
        return self._params

    def parse(self, request):
        """::

            req = req.parse(b'GET /foo/bar HTTP/1.1')
            req = req.parse({'REQUEST_METHOD': 'GET'})

        Parse HTTP request chunks or environment dict.
        """
        # Parse CGI environment
        if isinstance(request, (dict, type(os.environ))):
            chunk = b''
            self.environ = request
            self._parse_environ(request)
        else:
            chunk = request

        # Parse normal message
        if self._state != 'cgi':
            super().parse(chunk)

        # Parse CGI content
        else:
            self.content = self.content.parse_body(chunk)
            super().parse()

        # Check if we can fix things that require all headers
        if not self.is_finished:
            return self

        # Base URL
        base = self.url.base
        if not base.scheme:
            base.scheme = 'http'
        headers = self.headers
        if not base.host:
            host = headers.host
            if host:
                base.host_port = host

        # Basic authentication
        auth = self._parse_basic_auth(headers.authorization)
        if auth:
            base.userinfo = auth

        # Basic proxy authentication
        proxy_auth = self._parse_basic_auth(headers.proxy_authorization)
        if proxy_auth:
            self.proxy = Pyjo.URL.new().set(userinfo=proxy_auth)

        # "X-Forwarded-Proto"
        if self.reverse_proxy and headers.header('X-Forwarded-Proto') == 'https':
            base.scheme = 'https'

        return self

    @property
    def proxy(self):
        """::

            proxy = req.proxy
            req.proxy = 'http://foo:bar@127.0.0.1:3000'
            req.proxy = Pyjo.URL.new('http://127.0.0.1:3000')

        Proxy URL for request. ::

            # Disable proxy
            req.proxy = None
        """
        return self._proxy

    @proxy.setter
    def proxy(self, value):
        if isinstance(value, Pyjo.URL.object) or not value:
            self._proxy = value
        else:
            self._proxy = Pyjo.URL.new(value)

    @property
    def query_params(self):
        """::

            params = req.query_params

        All ``GET`` parameters, usually a :mod:`Pyjo.Parameters` object. ::

            # Turn GET parameters to hash and extract value
            print(req.query_params.to_hash()['foo'])
        """
        return self.url.query

    def set_cookie(self, *cookies):
        """::

            req = req.set_cookie(cookie, cookie, cookie)
            req = req.set_cookie(Pyjo.Message.Response.new(name='foo', value='bar'))
            req = req.set_cookie({'name': 'foo', 'value': 'bar'})

        Set message cookies, usually :mod:`Pyjo.Cookie.Response` object.
        """
        for cookie in cookies:
            if isinstance(cookie, dict):
                value = Pyjo.Cookie.Request.new(**cookie).to_str()
            else:
                value = str(cookie)

            if self.headers.cookie is not None:
                self.headers.cookie += '; ' + value
            else:
                self.headers.cookie = value

        return self

    def to_bytes(self):
        """::

            bstring = req.to_bytes()

        Turn message into a bytes string.
        """
        return self.build_start_line() + self.build_headers() + self.build_body()

    def _parse_basic_auth(self, header):
        if header:
            basic = 'Basic '
            offset = header.find(basic)
            if offset >= 0:
                offset += len(basic)
                auth = header[len(basic) :]
                try:
                    return u(b64_decode(auth))
                except:
                    pass
        return

    def _parse_environ(self, environ):
        # Extract headers
        headers = self.headers
        url = self.url
        base = url.base
        for name, value in environ.items():
            if not name.upper().startswith('HTTP_'):
                continue
            name = name[5:].replace('_', '-')
            headers.header(name, value)

            # Host/Port
            if name == 'HOST':
                host, port = value, None
                m = re_hostport.search(host)
                if m:
                    host = m.group(1)
                    port = convert(m.group(2), int, None)
                base.host = host
                base.port = port

        # Content-Type is a special case on some servers
        if environ.get('CONTENT_TYPE', ''):
            headers.content_type = environ['CONTENT_TYPE']

        # Content-Length is a special case on some servers
        if environ.get('CONTENT_LENGTH', ''):
            headers.content_length = environ['CONTENT_LENGTH']

        # Query
        if environ.get('QUERY_STRING', ''):
            url.query.parse(environ['QUERY_STRING'])

        # Method
        if environ.get('REQUEST_METHOD'):
            self.method = environ['REQUEST_METHOD']

        # Scheme/Version
        m = re_server_protocol.search(environ.get('SERVER_PROTOCOL', ''))
        if m:
            base.scheme = m.group(1)
            self.version = m.group(2)

        # HTTPS
        if environ.get('HTTPS', '').upper() == 'ON':
            base.scheme = 'https'

        # Path
        path = url.path.parse(environ.get('PATH_INFO', ''))

        # Base path
        value = environ.get('SCRIPT_NAME', '')
        if value:
            # Make sure there is a trailing slash (important for merging)
            if value.endswith('/'):
                base.path.parse(value)
            else:
                base.path.parse(value + '/')

            # Remove SCRIPT_NAME prefix if necessary
            buf = path.to_str()
            if value.startswith('/'):
                value = value[1:]
            if value.endswith('/'):
                value = value[:-1]
            if buf.startswith('/'):
                buf = buf[1:]
            if buf.find(value) == 0:
                buf = buf[len(value) :]
                if buf.startswith('/'):
                    buf = buf[1:]
            if buf.startswith('/'):
                buf = buf[1:]
            path.parse(buf)

        # Bypass normal message parser
        self._state = 'cgi'


new = Pyjo_Message_Request.new
object = Pyjo_Message_Request
