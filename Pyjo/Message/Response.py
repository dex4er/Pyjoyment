r"""
Pyjo.Message.Response - HTTP response
=====================================
::

    import Pyjo.Message.Response

    # Parse
    res = Pyjo.Message.Response.new()
    res.parse(b'HTTP/1.0 200 OK\x0d\x0a')
    res.parse(b'Content-Length: 12\x0d\x0a')
    res.parse(b'Content-Type: text/plain\x0d\x0a\x0d\x0a')
    res.parse(b'Hello World!')
    print(res.code)
    print(res.headers.content_type)
    print(res.body)

    # Build
    res = Pyjo.Message.Response.new()
    res.code = 200
    res.headers.content_type = 'text/plain'
    res.body = b'Hello World!'
    print(res.to_bytes())

:mod:`Pyjo.Message.Response` is a container for HTTP responses, based on
`RFC 7230 <https://tools.ietf.org/html/rfc7230>`_ and
`RFC 7231 <https://tools.ietf.org/html/rfc7231>`_.

Events
------

:mod:`Pyjo.Message.Response` inherits all events from :mod:`Pyjo.Message`.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::Message::Response <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/Message/Response.pm>`_
of Mojolicious 9.49.
"""

import Pyjo.Cookie
import Pyjo.Cookie.Response
import Pyjo.Date
import Pyjo.Message

import builtins
import re

from collections.abc import Mapping
from typing import Any, Self, cast, overload


type Anything = builtins.object

# Unmarked codes are from RFC 7231
MESSAGES = {
    100: 'Continue',
    101: 'Switching Protocols',
    102: 'Processing',  # RFC 2518 (WebDAV)
    103: 'Early Hints',  # RFC 8297
    200: 'OK',
    201: 'Created',
    202: 'Accepted',
    203: 'Non-Authoritative Information',
    204: 'No Content',
    205: 'Reset Content',
    206: 'Partial Content',
    207: 'Multi-Status',  # RFC 2518 (WebDAV)
    208: 'Already Reported',  # RFC 5842
    226: 'IM Used',  # RFC 3229
    300: 'Multiple Choices',
    301: 'Moved Permanently',
    302: 'Found',
    303: 'See Other',
    304: 'Not Modified',
    305: 'Use Proxy',
    307: 'Temporary Redirect',
    308: 'Permanent Redirect',  # RFC 7538
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
    418: "I'm a teapot",  # RFC 2324 :)
    421: 'Misdirected Request',  # RFC 7540
    422: 'Unprocessable Entity',  # RFC 2518 (WebDAV)
    423: 'Locked',  # RFC 2518 (WebDAV)
    424: 'Failed Dependency',  # RFC 2518 (WebDAV)
    425: 'Too Early',  # RFC 8470
    426: 'Upgrade Required',  # RFC 2817
    428: 'Precondition Required',  # RFC 6585
    429: 'Too Many Requests',  # RFC 6585
    431: 'Request Header Fields Too Large',  # RFC 6585
    451: 'Unavailable For Legal Reasons',  # RFC 7725
    500: 'Internal Server Error',
    501: 'Not Implemented',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    504: 'Gateway Timeout',
    505: 'HTTP Version Not Supported',
    506: 'Variant Also Negotiates',  # RFC 2295
    507: 'Insufficient Storage',  # RFC 2518 (WebDAV)
    508: 'Loop Detected',  # RFC 5842
    509: 'Bandwidth Limit Exceeded',  # Unofficial
    510: 'Not Extended',  # RFC 2774
    511: 'Network Authentication Required',  # RFC 6585
}


class Pyjo_Message_Response(Pyjo.Message.object):
    """
    :mod:`Pyjo.Message.Response` inherits all methods from :mod:`Pyjo.Message`
    and implements the following new ones.
    """

    # The default of max_message_size, which a response raises
    _MAX_MESSAGE_SIZE = 2147483648

    def __init__(self, *, code: int | None = None, message: str | None = None, **kwargs: Any) -> None:
        """::

            res = Pyjo.Message.Response.new()
            res = Pyjo.Message.Response.new(code=200, message='OK')

        Construct a new :mod:`Pyjo.Message.Response` object.
        """
        super().__init__(**kwargs)

        self.code = code
        """::

            code = res.code
            res.code = 200

        HTTP response status code.
        """

        self.message = message
        """::

            message = res.message
            res.message = 'OK'

        HTTP response status message.
        """

        self._start_buffer: bytes | None = None

    @overload
    def cookies(self) -> list[Pyjo.Cookie.Response.object]: ...

    @overload
    def cookies(self, cookie: Pyjo.Cookie.object | Mapping[str, Any], /, *cookies: Anything) -> Self: ...

    def cookies(self, *cookies: Anything) -> list[Pyjo.Cookie.Response.object] | Self:
        """::

            cookies = res.cookies()
            res = res.cookies(Pyjo.Cookie.Response.new())
            res = res.cookies({'name': 'foo', 'value': 'bar'})

        Access response cookies, usually :mod:`Pyjo.Cookie.Response` objects. ::

            # Names of all cookies
            for cookie in res.cookies():
                print(cookie.name)
        """
        # Parse cookies
        headers = self.headers
        if not cookies:
            return Pyjo.Cookie.Response.parse(headers.set_cookie)

        # Add cookies
        for cookie in cookies:
            if isinstance(cookie, Mapping):
                cookie = Pyjo.Cookie.Response.new(**cast(Mapping[str, Any], cookie))
            headers.add('Set-Cookie', str(cookie))

        return self

    def default_message(self, code: int | None = None) -> str:
        """::

            message = res.default_message()
            message = res.default_message(418)

        Generate default response message for status code, defaults to using
        :attr:`code`.
        """
        code = code or self.code
        return MESSAGES.get(code if code is not None else 404, '')

    @property
    def max_message_size(self) -> int:
        """::

            size = res.max_message_size
            res.max_message_size = 1024

        Maximum message size in bytes, defaults to the value of the
        ``PYJO_MAX_MESSAGE_SIZE`` environment variable or ``2147483648``
        (2GiB). Setting the value to ``0`` will allow messages of indefinite
        size.
        """
        return self._max_message_size

    @max_message_size.setter
    def max_message_size(self, value: int) -> None:
        self._max_message_size = value

    def extract_start_line(self, buffer: bytearray) -> bool | None:
        """::

            boolean = res.extract_start_line(buffer)

        Extract status-line from a :class:`bytearray`, which loses it.
        """
        # We have a full response line
        if not (m := re.match(rb'(.*?)\x0d?\x0a', bytes(buffer))):
            return None
        del buffer[: m.end()]
        if not (m := re.fullmatch(rb'\s*HTTP/(\d\.\d)\s+(\d\d\d)\s*(.+)?', m[1])):
            self.error = {'message': 'Bad response start-line'}
            return False

        content = self.content
        self.code = int(m[2])
        if self.is_empty:
            content.skip_body = True
        if content.auto_decompress is None:
            content.auto_decompress = True
        if content.auto_relax is None:
            content.auto_relax = True
        self.version = m[1].decode('latin-1')
        self.message = m[3].decode('latin-1') if m[3] is not None else None
        return True

    def fix_headers(self) -> Self:
        """::

            res = res.fix_headers()

        Make sure response has all required headers.
        """
        if self._fix:
            return self
        super().fix_headers()

        # Date
        headers = self.headers
        if not headers.date:
            headers.date = Pyjo.Date.new().to_str()

        # RFC 7230 3.3.2
        if self.is_empty:
            headers.remove('Content-Length')

        return self

    def get_start_line_chunk(self, offset: int) -> bytes:
        """::

            data = res.get_start_line_chunk(offset)

        Get a chunk of status-line data starting from a specific position.
        Note that this method finalizes the response.
        """
        buffer = self._start_line()
        self.emit('progress', 'start_line', offset)
        return buffer[offset : offset + 131072]

    @property
    def is_client_error(self) -> bool:
        """::

            boolean = res.is_client_error

        Check if this response has a ``4xx`` status :attr:`code`.
        """
        return self._status_class(400)

    @property
    def is_empty(self) -> bool:
        """::

            boolean = res.is_empty

        Check if this response has a ``1xx``, ``204`` or ``304`` status
        :attr:`code`.
        """
        if not (code := self.code):
            return False
        return self.is_info or code == 204 or code == 304

    @property
    def is_error(self) -> bool:
        """::

            boolean = res.is_error

        Check if this response has a ``4xx`` or ``5xx`` status :attr:`code`.
        """
        return self._status_class(400, 500)

    @property
    def is_info(self) -> bool:
        """::

            boolean = res.is_info

        Check if this response has a ``1xx`` status :attr:`code`.
        """
        return self._status_class(100)

    @property
    def is_redirect(self) -> bool:
        """::

            boolean = res.is_redirect

        Check if this response has a ``3xx`` status :attr:`code`.
        """
        return self._status_class(300)

    @property
    def is_server_error(self) -> bool:
        """::

            boolean = res.is_server_error

        Check if this response has a ``5xx`` status :attr:`code`.
        """
        return self._status_class(500)

    @property
    def is_success(self) -> bool:
        """::

            boolean = res.is_success

        Check if this response has a ``2xx`` status :attr:`code`.
        """
        return self._status_class(200)

    @property
    def start_line_size(self) -> int:
        """::

            size = res.start_line_size

        Size of the status-line in bytes. Note that this method finalizes the
        response.
        """
        return len(self._start_line())

    def _start_line(self) -> bytes:
        if self._start_buffer is not None:
            return self._start_buffer
        code = self.code or 404
        message = self.message or self.default_message()
        self._start_buffer = f'HTTP/{self.version} {code} {message}\x0d\x0a'.encode('latin-1')
        return self._start_buffer

    def _status_class(self, *classes: int) -> bool:
        if not (code := self.code):
            return False
        return any(code >= c and code < c + 100 for c in classes)


new = Pyjo_Message_Response.new
object = Pyjo_Message_Response
