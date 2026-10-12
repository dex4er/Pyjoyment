
r"""
Pyjo.Message.Response - HTTP Response
=====================================
::

    import Pyjo.Message.Response

    # Parse
    res = Pyjo.Message.Response.new()
    res.parse(b"HTTP/1.0 200 OK\x0d\x0a")
    res.parse(b"Content-Length: 12\x0d\x0a")
    res.parse(b"Content-Type: text/plain\x0d\x0a\x0d\x0a")
    res.parse(b'Hello World!')
    print(res.code)
    print(res.headers.content_type)
    print(res.body)

    # Build
    res = Pyjo.Message.Response.new()
    res.code = 200
    res.headers.content_type = 'text/plain'
    res.body = b'Hello World!'
    print(res)

:mod:`Pyjo.Message.Response` is a container for HTTP Responses based on
:rfc:`7230` and
:rfc:`7231`.

Events
------

:mod:`Pyjo.Message.Response` inherits all events from :mod:`Pyjo.Message`.

Classes
-------
"""

import Pyjo.Cookie.Response
import Pyjo.Message

from Pyjo.Regexp import r
from Pyjo.Util import b, convert, notnone


re_line = r(br'^(.*?)\x0d?\x0a')
re_http = r(br'^\s*HTTP/(\d\.\d)\s+(\d\d\d)\s*(.+)?$')


# Umarked codes are from RFC 7231
MESSAGES = {
    100: 'Continue',
    101: 'Switching Protocols',
    102: 'Processing',                         # RFC 2518 (WebDAV)
    200: 'OK',
    201: 'Created',
    202: 'Accepted',
    203: 'Non-Authoritative Information',
    204: 'No Content',
    205: 'Reset Content',
    206: 'Partial Content',
    207: 'Multi-Status',                       # RFC 2518 (WebDAV)
    208: 'Already Reported',                   # RFC 5842
    226: 'IM Used',                            # RFC 3229
    300: 'Multiple Choices',
    301: 'Moved Permanently',
    302: 'Found',
    303: 'See Other',
    304: 'Not Modified',
    305: 'Use Proxy',
    307: 'Temporary Redirect',
    308: 'Permanent Redirect',                 # RFC 7238
    400: 'Bad Request',
    401: 'Unauthorized',
    402: 'Payment Required',
    403: 'Forbidden',
    404: 'Not Found',
    405: 'Method Not Allowed',
    406: 'Not Acceptable',
    407: 'Proxy Authentication Required',
    408: 'Request Timeout',
    409: 'Conflict',
    410: 'Gone',
    411: 'Length Required',
    412: 'Precondition Failed',
    413: 'Request Entity Too Large',
    414: 'Request-URI Too Long',
    415: 'Unsupported Media Type',
    416: 'Request Range Not Satisfiable',
    417: 'Expectation Failed',
    418: "I'm a teapot",                       # RFC 2324 :)
    422: 'Unprocessable Entity',               # RFC 2518 (WebDAV)
    423: 'Locked',                             # RFC 2518 (WebDAV)
    424: 'Failed Dependency',                  # RFC 2518 (WebDAV)
    425: 'Unordered Colection',                # RFC 3648 (WebDAV)
    426: 'Upgrade Required',                   # RFC 2817
    428: 'Precondition Required',              # RFC 6585
    429: 'Too Many Requests',                  # RFC 6585
    431: 'Request Header Fields Too Large',    # RFC 6585
    500: 'Internal Server Error',
    501: 'Not Implemented',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    504: 'Gateway Timeout',
    505: 'HTTP Version Not Supported',
    506: 'Variant Also Negotiates',            # RFC 2295
    507: 'Insufficient Storage',               # RFC 2518 (WebDAV)
    508: 'Loop Detected',                      # RFC 5842
    509: 'Bandwidth Limit Exceeded',           # Unofficial
    510: 'Not Extended',                       # RFC 2774
    511: 'Network Authentication Required'     # RFC 6585
}


class Pyjo_Message_Response(Pyjo.Message.object):
    """
    :mod:`Pyjo.Message.Response` inherits all attributes and methods from
    :mod:`Pyjo.Message` and implements the following new ones.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.code = kwargs.get('code')
        """::

            code = res.code
            res.code = 200

        HTTP response status code.
        """

        self.message = kwargs.get('message')
        """::

            msg = res.message
            res.message = 'OK'

        HTTP response status message.
        """

        self._start_buffer = None

    def __repr__(self):
        """::

            string = repr(res)

        String representation of an object shown in console.
        """
        return f"<{self.__class__.__module__}.{self.__class__.__name__} code={repr(self.code)} message={repr(self.message)}>"

    @property
    def cookies(self):
        """::

            cookies = res.cookies
            res.cookies = cookies

        Access response cookies, usually :mod:`Pyjo.Cookie.Response` objects. ::

            # Names of all cookies
            for cookie in res.cookies:
                print(cookie.name)
        """
        # Parse cookies
        headers = self.headers
        cookies = headers.set_cookie
        if cookies is not None:
            return Pyjo.Cookie.Response.parse(cookies)
        else:
            return

    @cookies.setter
    def cookies(self, value):
        headers = self.headers
        headers.cookies = []
        for cookie in value:
            self.set_cookie(cookie)

    def default_message(self, code=None):
        """::

            msg = res.default_message()
            msg = res.default_message(418)

        Generate default response message for status code, defaults to using
        :attr:`code`.
        """
        return MESSAGES.get(code or notnone(self.code, 404), 0) or ''

    def extract_start_line(self, buf):
        """::

            boolean = res.extract_start_line(buf)

        Extract status-line from string.
        """
        # We have a full response line
        m = re_line.search(buf)
        if m:
            line = m.group(1)
            del buf[:m.end()]
        else:
            return

        m = re_http.search(line)
        if not m:
            return not self.set_error(message='Bad response start-line')

        try:
            self.version = m.group(1).decode('ascii')
        except:
            self.version = None

        self.code = convert(m.group(2), int)

        try:
            self.message = m.group(3).decode('ascii')
        except:
            self.message = None

        content = self.content
        if self.is_empty:
            content.skip_body = 1

        if content.auto_decompress is None:
            content.auto_decompress = True
        if content.auto_relax is None:
            content.auto_relax = True

        if self.version == '1.0':
            content.expect_close = True

        return True

    def fix_headers(self):
        """::

            res = res.fix_headers()

        Make sure response has all required headers.
        """
        if self._fixed:
            return self
        super().fix_headers()

        # Date
        headers = self.headers
        if not headers.date:
            headers.date = Pyjo.Date.new().to_str()

        return self

    def get_start_line_chunk(self, offset):
        """::

            chunk = res.get_start_line_chunk(offset)

        Get a chunk of status-line data starting from a specific position.
        """
        if self._start_buffer is None:
            code = self.code or 404
            msg = self.message or self.default_message()
            self._start_buffer = bytearray(b(f"HTTP/{self.version} {code} {msg}\x0d\x0a"))

        self.emit('progress', 'start_line', offset)
        return self._start_buffer[offset:offset + 131072]

    @property
    def is_empty(self):
        """::

            boolean = res.is_empty

        Check if this is a ``1xx``, ``204`` or ``304`` response.
        """
        code = self.code
        if not code:
            return
        else:
            return self.is_status_class(100) or code == 204 or code == 304

    def is_status_class(self, status_class):
        """::

            boolean = res.is_status_class(200)

        Check response status class.
        """
        code = self.code
        if not code:
            return
        else:
            return code >= status_class and code < (status_class + 100)

    def set_cookie(self, cookie):
        """::

            res = res.set_cookie(Pyjo.Message.Response.new(name='foo', value='bar'))
            res = res.set_cookie({'name': 'foo', 'value': 'bar'})

        Set message cookies, usually :mod:`Pyjo.Cookie.Response` object.
        """
        if isinstance(cookie, dict):
            value = str(Pyjo.Cookie.Response.new(**cookie))
        else:
            value = str(cookie)
        self.headers.add('Set-Cookie', value)
        return self


new = Pyjo_Message_Response.new
object = Pyjo_Message_Response
