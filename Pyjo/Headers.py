
r"""
Pyjo.Headers - Headers
======================
::

    import Pyjo.Headers

    # Parse
    headers = Pyjo.Headers.new()
    headers.parse("Content-Length: 42\x0d\x0a")
    headers.parse("Content-Type: text/html\x0d\x0a\x0d\x0a")
    print(headers.content_length)
    print(headers.content_type)

    # Build
    headers = Pyjo.Headers.new()
    headers.content_length = 42
    headers.content_type = 'text/plain'
    print(headers.to_str())

:mod:`Pyjo.Headers` is a container for HTTP headers based on
:rfc:`7230` and
:rfc:`7231`.

Classes
-------
"""

import Pyjo.Base
import Pyjo.String.Mixin

from Pyjo.Regexp import r
from Pyjo.Util import b, convert, getenv, notnone, u

import collections
import sys


re_line = r(br'(.*?)\x0d?\x0a')
re_field = r(br'^(\S[^:]*)\s*:\s*(.*)$')
re_startswith_space = r(br'^\s+')


NORMALCASE = dict(map(lambda i: (b(i.lower()), b(i)), [
    'Accept', 'Accept-Charset', 'Accept-Encoding', 'Accept-Language', 'Accept-Ranges',
    'Access-Control-Allow-Origin', 'Allow', 'Authorization', 'Cache-Control', 'Connection',
    'Content-Disposition', 'Content-Encoding', 'Content-Language', 'Content-Length',
    'Content-Location', 'Content-Range', 'Content-Security-Policy', 'Content-Type',
    'Cookie', 'DNT', 'Date', 'ETag', 'Expect',
    'Expires', 'Host', 'If-Modified-Since', 'If-None-Match', 'Last-Modified', 'Link', 'Location',
    'Origin', 'Proxy-Authenticate', 'Proxy-Authorization', 'Range', 'Sec-WebSocket-Accept',
    'Sec-WebSocket-Extensions', 'Sec-WebSocket-Key', 'Sec-WebSocket-Protocol',
    'Sec-WebSocket-Version', 'Server', 'Set-Cookie', 'Status', 'Strict-Transport-Security',
    'TE', 'Trailer', 'Transfer-Encoding', 'Upgrade', 'User-Agent', 'Vary', 'WWW-Authenticate',
]))


class Pyjo_Headers(Pyjo.Base.object, Pyjo.String.Mixin.object):
    """
    :mod:`Pyjo.Headers` inherits all attributes and methods from
    :mod:`Pyjo.Base` and :mod:`Pyjo.String.Mixin` and implements the following new ones.
    """

    def __init__(self, chunk=None, **kwargs):
        r"""::

            headers = Pyjo.Headers.new()
            headers = Pyjo.Headers.new("Content-Type: text/html\x0d\x0a\x0d\x0a")

        Construct a new :mod`Pyjo.Headers` object.
        """

        self.charset = kwargs.get('charset', 'utf-8')
        """::

            charset = headers.charset
            headers.charset = 'ascii'

        Charset used for encoding and decoding, defaults to ``ascii``.
        """

        self.max_line_size = notnone(kwargs.get('max_line_size'), lambda: convert(getenv('PYJO_MAX_LINE_SIZE'), int) or 8192)
        """::

            size = headers.max_line_size
            headers.max_line_size = 1024

        Maximum header line size in bytes, defaults to the value of the
        ``PYJO_MAX_LINE_SIZE`` environment variable or ``8192`` (8KB).
        """

        self.max_lines = notnone(kwargs.get('max_lines'), lambda: convert(getenv('PYJO_MAX_LINES'), int) or 100)
        """::

            num = headers.max_lines
            headers.max_lines = 200

        Maximum number of header lines, defaults to the value of the ``PYJO_MAX_LINES``
        environment variable or ``100``.
        """

        self._buffer = bytearray()
        self._cache = []
        self._headers = collections.OrderedDict()
        self._limit = False
        self._normalcase = {}
        self._state = None

        if chunk is not None:
            self.parse(chunk)

    def __repr__(self):
        """::

            reprstring = headers()

        String representation of an object shown in console.
        """
        return "{0}.new().parse({1})".format(self.__module__, repr(self.to_str() + '\x0d\x0a\x0d\x0a'))

    @property
    def accept(self):
        """::

            accept = headers.accept
            headers.accept = 'application/json'

        Shortcut for the ``Accept`` header.
        """
        return self.header(b'Accept')

    @accept.setter
    def accept(self, value):
        self.header(b'Accept', value)

    @property
    def accept_charset(self):
        """::

            charset = headers.accept_charset
            headers.accept_charset = 'UTF-8'

        Shortcut for the ``Accept-Charset`` header.
        """
        return self.header(b'Accept-Charset')

    @accept_charset.setter
    def accept_charset(self, value):
        self.header(b'Accept-Charset', value)

    @property
    def accept_encoding(self):
        """::

            encoding = headers.accept_encoding
            headers.accept_encoding = 'gzip'

        Shortcut for the ``Accept-Encoding`` header.
        """
        return self.header(b'Accept-Encoding')

    @accept_encoding.setter
    def accept_encoding(self, value):
        self.header(b'Accept-Encoding', value)

    @property
    def accept_language(self):
        """::

            language = headers.accept_language
            headers.accept_language = 'de, en'

        Shortcut for the ``Accept-Language`` header.
        """
        return self.header(b'Accept-Language')

    @accept_language.setter
    def accept_language(self, value):
        self.header(b'Accept-Language', value)

    @property
    def accept_ranges(self):
        """::

            ranges = headers.accept_ranges
            headers.accept_ranges = 'bytes'

        Shortcut for the ``Accept-Ranges`` header.
        """
        return self.header(b'Accept-Ranges')

    @accept_ranges.setter
    def accept_ranges(self, value):
        self.header(b'Accept-Ranges', value)

    @property
    def access_control_allow_origin(self):
        """::

            origin = headers.access_control_allow_origin
            headers.accept_ranges = 'bytes'

        Shortcut for the ``Access-Control-Allow-Origin`` header from
        `Cross-Origin Resource Sharing <http://www.w3.org/TR/cors/>`_.
        """
        return self.header(b'Access-Control-Allow-Origin')

    @access_control_allow_origin.setter
    def access_control_allow_origin(self, value):
        self.header(b'Access-Control-Allow-Origin', value)

    def add(self, name, *args):
        """::

            headers = headers.add('Foo', 'one value')
            headers = headers.add('Foo', 'first value', 'second value')

        Add one or more header values with one or more lines. ::

            # "Vary: Accept"
            # "Vary: Accept-Encoding"
            headers.set(vary='Accept').add('Vary', 'Accept-Encoding').to_str()
        """
        # Make sure we have a normal case entry for name
        name = b(name, 'ascii')
        key = name.lower()
        if key not in NORMALCASE:
            self._normalcase[key] = name
        if key not in self._headers:
            self._headers[key] = []
        for value in args:
            self._headers[key].append(b(value, 'ascii'))

        return self

    @property
    def allow(self):
        """::

            allow = headers.allow
            headers.allow = 'GET, POST'

        Shortcut for the ``Allow`` header.
        """
        return self.header(b'Allow')

    @allow.setter
    def allow(self, value):
        self.header(b'Allow', value)

    def append(self, name, value):
        """::

            headers = headers.append('Vary', 'Accept-Encoding')

        Append value to header and flatten it if necessary. ::

            # "Vary: Accept"
            headers.append('Vary', 'Accept').to_str()

            # "Vary: Accept, Accept-Encoding"
            headers.set(vary='Accept').append('Vary', 'Accept-Encoding').to_str()
        """
        old = self.header(name)
        return self.header(name, old + ', ' + value if old is not None else value)

    @property
    def authorization(self):
        """::

            authorization = headers.authorization
            headers.authorization = 'Basic Zm9vOmJhcg=='

        Shortcut for the ``Authorization`` header.
        """
        return self.header(b'Authorization')

    @authorization.setter
    def authorization(self, value):
        self.header(b'Authorization', value)

    @property
    def cache_control(self):
        """::

            control = headers.cache_control
            headers.cache_control = 'max-age=1, no-cache'

        Shortcut for the ``Cache-Control`` header.
        """
        return self.header(b'Cache-Control')

    @cache_control.setter
    def cache_control(self, value):
        self.header(b'Cache-Control', value)

    def clone(self):
        """::

            clone = headers.clone

        Clone headers.
        """
        return self.new().from_dict(self.to_dict_list())

    @property
    def connection(self):
        """::

            connection = headers.connection
            headers.connection = 'close'

        Shortcut for the ``Connection`` header.
        """
        return self.header(b'Connection')

    @connection.setter
    def connection(self, value):
        self.header(b'Connection', value)

    @property
    def content_disposition(self):
        """::

            disposition = headers.content_disposition
            headers.content_disposition = 'foo'

        Shortcut for the ``Content-Disposition`` header.
        """
        return self.header(b'Content-Disposition')

    @content_disposition.setter
    def content_disposition(self, value):
        self.header(b'Content-Disposition', value)

    @property
    def content_encoding(self):
        """::

            encoding = headers.content_encoding
            headers.content_encoding = 'gzip'

        Shortcut for the ``Content-Encoding`` header.
        """
        return self.header(b'Content-Encoding')

    @content_encoding.setter
    def content_encoding(self, value):
        self.header(b'Content-Encoding', value)

    @property
    def content_language(self):
        """::

            language = headers.content_language
            headers.content_language = 'en'

        Shortcut for the ``Content-Language`` header.
        """
        return self.header(b'Content-Language')

    @content_language.setter
    def content_language(self, value):
        self.header(b'Content-Language', value)

    @property
    def content_length(self):
        """::

            length = int(headers.content_length)
            headers.content_length = 4000

        Shortcut for the ``Content-Length`` header.
        """
        return self.header(b'Content-Length')

    @content_length.setter
    def content_length(self, value):
        self.header(b'Content-Length', value)

    @property
    def content_location(self):
        """::

            location = headers.content_location
            headers.content_location = 'http://127.0.0.1/foo'

        Shortcut for the ``Content-Location`` header.
        """
        return self.header(b'Content-Location')

    @content_location.setter
    def content_location(self, value):
        self.header(b'Content-Location', value)

    @property
    def content_range(self):
        """::

            content_range = headers.content_range
            headers.content_range = 'bytes 2-8/100'

        Shortcut for the ``Content-Range`` header.
        """
        return self.header(b'Content-Range')

    @content_range.setter
    def content_range(self, value):
        self.header(b'Content-Range', value)

    @property
    def content_security_policy(self):
        """::

            policy = headers.content_security_policy
            headers.content_security_policy = 'default-src https:'

        Shortcut for the ``Content-Security-Policy`` header from
        `Content Security Policy 1.0 <http://www.w3.org/TR/CSP/>`_.
        """
        return self.header(b'Content-Security-Policy')

    @content_security_policy.setter
    def content_security_policy(self, value):
        self.header(b'Content-Security-Policy', value)

    @property
    def content_type(self):
        """::

            content_type = headers.content_type
            headers.content_type = 'text/plain'

        Shortcut for the ``Content-Type`` header.
        """
        return self.header(b'Content-Type')

    @content_type.setter
    def content_type(self, value):
        self.header(b'Content-Type', value)

    @property
    def cookie(self):
        """::

            cookie = headers.cookie
            headers.cookie = 'f=b'

        Shortcut for the ``Cookie`` header from
        :rfc:`6265`.
        """
        return self.header(b'Cookie')

    @cookie.setter
    def cookie(self, value):
        self.header(b'Cookie', value)

    @property
    def date(self):
        """::

            date = headers.date
            headers.date = 'Sun, 17 Aug 2008 16:27:35 GMT'

        Shortcut for the ``Date`` header.
        """
        return self.header(b'Date')

    @date.setter
    def date(self, value):
        self.header(b'Date', value)

    @property
    def dnt(self):
        """::

            dnt = headers.dnt
            headers.dnt = 1

        Shortcut for the ``DNT`` (Do Not Track) header, which has no specification yet,
        but is very commonly used.
        """
        return self.header(b'DNT')

    @dnt.setter
    def dnt(self, value):
        self.header(b'DNT', value)

    @property
    def etag(self):
        """::

            etag = headers.etag
            headers.etag = '"abc321"'

        Shortcut for the ``ETag`` header.
        """
        return self.header(b'ETag')

    @etag.setter
    def etag(self, value):
        self.header(b'ETag', value)

    @property
    def expect(self):
        """::

            expect = headers.expect
            headers.expect = '100-continue'

        Shortcut for the ``Expect`` header.
        """
        return self.header(b'Expect')

    @expect.setter
    def expect(self, value):
        self.header(b'Expect', value)

    @property
    def expires(self):
        """::

            expires = headers.expires
            headers.expires = 'Thu, 01 Dec 1994 16:00:00 GMT'

        Shortcut for the ``Expires`` header.
        """
        return self.header(b'Expires')

    @expires.setter
    def expires(self, value):
        self.header(b'Expires', value)

    def from_dict(self, d):
        """::

            headers = headers.from_dict({'Cookie': 'a=b'})
            headers = headers.from_dict({'Cookie': ['a=b', 'c=d']})
            headers = headers.from_dict({})

        Parse headers from a hash reference, an empty hash removes all headers.
        """
        # Empty hash deletes all headers
        if not d:
            self._headers = {}

        # Merge
        for header in d.keys():
            value = d[header]
            if isinstance(value, list):
                self.add(header, *value)
            else:
                self.add(header, value)

        return self

    def header(self, name, *args):
        """::

            value = headers.header('Foo')
            headers = headers.header('Foo', 'one value')
            headers = headers.header('Foo', 'first value', 'second value')

        Get or replace the current header values.
        """
        # Replace
        if args:
            return self.remove(name).add(name, *args)

        key = b(name, 'ascii').lower()
        if key not in self._headers:
            return

        return ', '.join(map(lambda i: u(i, self.charset), self._headers[key]))

    @property
    def host(self):
        """::

            host = headers.host
            headers.host = '127.0.0.1'

        Shortcut for the ``Host`` header.
        """
        return self.header(b'Host')

    @host.setter
    def host(self, value):
        self.header(b'Host', value)

    @property
    def if_modified_since(self):
        """::

            date = headers.if_modified_since
            headers.if_modified_since = 'Sun, 17 Aug 2008 16:27:35 GMT'

        Shortcut for the ``If-Modified-Since`` header.
        """
        return self.header(b'If-Modified-Since')

    @if_modified_since.setter
    def if_modified_since(self, value):
        self.header(b'If-Modified-Since', value)

    @property
    def if_none_match(self):
        """::

            etag = headers.if_none_match
            headers.if_none_match = '"abc321"'

        Shortcut for the ``If-None-Match`` header.
        """
        return self.header(b'If-None-Match')

    @if_none_match.setter
    def if_none_match(self, value):
        self.header(b'If-None-Match', value)

    @property
    def is_finished(self):
        """::

            boolean = headers.is_finished

        Check if header parser is finished.
        """
        return self._state == 'finished'

    @property
    def is_limit_exceeded(self):
        """::

            boolean = headers.is_limit_exceeded

        Check if headers have exceeded :attr:`max_line_size` or :attr:`max_lines`.
        """
        return bool(self._limit)

    @property
    def last_modified(self):
        """::

            date = headers.last_modified
            headers.last_modified = 'Sun, 17 Aug 2008 16:27:35 GMT'

        Shortcut for the ``Last-Modified`` header.
        """
        return self.header(b'Last-Modified')

    @last_modified.setter
    def last_modified(self, value):
        self.header(b'Last-Modified', value)

    @property
    def leftovers(self):
        """::

          chunk = headers.leftovers

        Get and remove leftover data from header parser.
        """
        chunk = self._buffer
        self._buffer = bytearray()
        return chunk

    @property
    def link(self):
        """::

            link = headers.link
            headers.link = '<http://127.0.0.1/foo/3>; rel="next"'

        Shortcut for the ``Link`` header from
        :rfc:`5988`.
        """
        return self.header(b'Link')

    @link.setter
    def link(self, value):
        self.header(b'Link', value)

    @property
    def location(self):
        """::

            location = headers.location
            headers.location = 'http://127.0.0.1/foo'

        Shortcut for the ``Location`` header.
        """
        return self.header(b'Location')

    @location.setter
    def location(self, value):
        self.header(b'Location', value)

    @property
    def names(self):
        """::

            names = headers.names

        Return a list of all currently defined headers. ::

            # Names of all headers
            for n in headers.name:
                print(n)
        """
        return list(map(lambda i: u(i, 'ascii'),
                        map(lambda i: NORMALCASE[i] if i in NORMALCASE else self._normalcase[i] if i in self._normalcase else i,
                        self._headers.keys())))

    @property
    def origin(self):
        """::

            origin = headers.origin
            headers.origin = 'http://example.com'

        Shortcut for the ``Origin`` header from
        :rfc:`6454`.
        """
        return self.header(b'Origin')

    @origin.setter
    def origin(self, value):
        self.header(b'Origin', value)

    def parse(self, string):
        r"""::

            headers = headers.parse(b"Content-Type: text/plain\x0d\x0a\x0d\x0a")

        Parse formatted headers.
        """
        self._state = 'headers'
        self._buffer.extend(b(string, 'ascii'))
        headers = self._cache
        size = self.max_line_size
        lines = self.max_lines
        pos = 0

        for m in re_line.finditer(self._buffer):
            chunk = m.group(0)
            pos += len(chunk)
            line = m.group(1)

            # Check line size limit
            if len(chunk) > size or len(headers) >= lines:
                self._state = 'finished'
                self._limit = True
                break

            # New header
            m = re_field.search(line)
            if m:
                headers.append(list(m.groups()))

            else:
                # Multiline
                if re_startswith_space.search(line):
                    line = re_startswith_space.sub(b'', bytes(line), 1)
                    if headers:
                        headers[-1][1] += b' ' + line

                # Empty line
                else:
                    for h in headers:
                        self.add(h[0], h[1])
                    self._state = 'finished'
                    self._cache = []
                    break

        del self._buffer[:pos]
        if self._state == 'finished':
            return self

        # Check line size limit
        if len(self._buffer) > size:
            self._state = 'finished'
            self._limit = True

        return self

    @property
    def proxy_authenticate(self):
        """::

            authenticate = headers.proxy_authenticate
            headers.proxy_authenticate = 'Basic "realm"'

        Shortcut for the ``Proxy-Authenticate`` header.
        """
        return self.header(b'Proxy-Authenticate')

    @proxy_authenticate.setter
    def proxy_authenticate(self, value):
        self.header(b'Proxy-Authenticate', value)

    @property
    def proxy_authorization(self):
        """::

            authorization = headers.proxy_authorization
            headers.proxy_authorization = 'Basic Zm9vOmJhcg=='

        Shortcut for the ``Proxy-Authorization`` header.
        """
        return self.header(b'Proxy-Authorization')

    @proxy_authorization.setter
    def proxy_authorization(self, value):
        self.header(b'Proxy-Authorization', value)

    @property
    def range(self):
        """::

            range = headers.range
            headers.range = 'bytes=2-8'

        Shortcut for the ``Range`` header.
        """
        return self.header(b'Range')

    @range.setter
    def range(self, value):
        self.header(b'Range', value)

    @property
    def referrer(self):
        """::

            referrer = headers.referrer
            headers.referrer = 'http://example.com'

        Shortcut for the ``Referer`` header, there was a typo in
        :rfc:`2068` which resulted in ``Referer``
        becoming an official header.
        """
        return self.header(b'Referer')

    @referrer.setter
    def referrer(self, value):
        self.header(b'Referer', value)

    def remove(self, name):
        """::

            headers = headers.remove('Foo')

        Remove a header.
        """
        key = b(name, 'ascii').lower()
        if key in self._headers:
            del self._headers[key]
        return self

    @property
    def sec_websocket_accept(self):
        """::

            accept = headers.sec_websocket_accept
            headers.sec_websocket_accept = 's3pPLMBiTxaQ9kYGzzhZRbK+xOo='

        Shortcut for the ``Sec-WebSocket-Accept`` header from
        :rfc:`6455`.
        """
        return self.header(b'Sec-WebSocket-Accept')

    @sec_websocket_accept.setter
    def sec_websocket_accept(self, value):
        self.header(b'Sec-WebSocket-Accept', value)

    @property
    def sec_websocket_extensions(self):
        """::

            extensions = headers.sec_websocket_extensions
            headers.sec_websocket_extensions = 'foo'

        Shortcut for the ``Sec-WebSocket-Extensions`` header from
        :rfc:`6455`.
        """
        return self.header(b'Sec-WebSocket-Extensions')

    @sec_websocket_extensions.setter
    def sec_websocket_extensions(self, value):
        self.header(b'Sec-WebSocket-Extensions', value)

    @property
    def sec_websocket_key(self):
        """::

            key = headers.sec_websocket_key
            headers.sec_websocket_key = 'dGhlIHNhbXBsZSBub25jZQ=='

        Shortcut for the ``Sec-WebSocket-Key`` header from
        :rfc:`6455`.
        """
        return self.header(b'Sec-WebSocket-Key')

    @sec_websocket_key.setter
    def sec_websocket_key(self, value):
        self.header(b'Sec-WebSocket-Key', value)

    @property
    def sec_websocket_protocol(self):
        """::

            protocol = headers.sec_websocket_protocol
            headers.sec_websocket_protocol = 'sample'

        Shortcut for the ``Sec-WebSocket-Protocol`` header from
        :rfc:`6455`.
        """
        return self.header(b'Sec-WebSocket-Protocol')

    @sec_websocket_protocol.setter
    def sec_websocket_protocol(self, value):
        self.header(b'Sec-WebSocket-Protocol', value)

    @property
    def sec_websocket_version(self):
        """::

            version = int(headers.sec_websocket_version)
            headers.sec_websocket_version = 13

        Shortcut for the ``Sec-WebSocket-Version`` header from
        :rfc:`6455`.
        """
        return self.header(b'Sec-WebSocket-Version')

    @sec_websocket_version.setter
    def sec_websocket_version(self, value):
        self.header(b'Sec-WebSocket-Version', value)

    @property
    def server(self):
        """::

            server = headers.server
            headers.server = 'Pyjo'

        Shortcut for the ``Server`` header.
        """
        return self.header(b'Server')

    @server.setter
    def server(self, value):
        self.header(b'Server', value)

    @property
    def set_cookie(self):
        """::

            cookie = headers.set_cookie
            headers.set_cookie = 'f=b; path=/'

        Shortcut for the ``Set-Cookie`` header from
        :rfc:`6265`.
        """
        return self.header(b'Set-Cookie')

    @set_cookie.setter
    def set_cookie(self, value):
        self.header(b'Set-Cookie', value)

    @property
    def status(self):
        """::

            status = headers.status
            headers.status = '200 OK'

        Shortcut for the ``Status`` header from
        :rfc:`3875`.
        """
        return self.header(b'Status')

    @status.setter
    def status(self, value):
        self.header(b'Status', value)

    @property
    def strict_transport_security(self):
        """::

            policy = headers.strict_transport_security
            headers.strict_transport_security = 'max-age=31536000'

        Shortcut for the ``Strict-Transport-Security`` header from
        :rfc:`6797`.
        """
        return self.header(b'Strict-Transport-Security')

    @strict_transport_security.setter
    def strict_transport_security(self, value):
        self.header(b'Strict-Transport-Security', value)

    @property
    def te(self):
        """::

            te = headers.te
            headers.te = 'chunked'

        Shortcut for the ``TE`` header.
        """
        return self.header(b'TE')

    @te.setter
    def te(self, value):
        self.header(b'TE', value)

    def to_dict(self):
        """::

            single = headers.to_dict()

        Turn headers into :class:`dict`.
        """
        return dict(map(lambda i: (i, self.header(i)), self.names))

    def to_dict_list(self):
        """::

            multi = headers.to_dict_list()

        Turn headers into :class:`dict` with :class:`list` as its values.
        """
        return dict(map(lambda i: (i, list(map(lambda i: u(i, 'ascii'), self._headers[b(i.lower(), 'ascii')]))),
                        self.names))

    def to_bytes(self):
        """::

            bstring = headers.to_bytes()

        Turn headers into a bytes string, suitable for HTTP messages.
        """
        headers = []

        # Make sure multiline values are formatted correctly
        for name in map(lambda i: b(i, 'ascii'), self.names):
            for v in self._headers[name.lower()]:
                headers.append(name + b': ' + v)

        return b"\x0d\x0a".join(headers)

    def to_str(self):
        """::

            string = headers.to_str()

        Turn headers into a string, suitable for HTTP messages.
        """
        if sys.version_info >= (3, 0):
            return u(self.to_bytes(), 'ascii')
        else:
            return self.to_bytes()

    @property
    def trailer(self):
        """::

            trailer = headers.trailer
            headers.trailer = 'X-Foo'

        Shortcut for the ``Trailer`` header.
        """
        return self.header(b'Trailer')

    @trailer.setter
    def trailer(self, value):
        self.header(b'Trailer', value)

    @property
    def transfer_encoding(self):
        """::

            encoding = headers.transfer_encoding
            headers.transfer_encoding = 'chunked'

        Shortcut for the ``Transfer-Encoding`` header.
        """
        return self.header(b'Transfer-Encoding')

    @transfer_encoding.setter
    def transfer_encoding(self, value):
        self.header(b'Transfer-Encoding', value)

    @property
    def upgrade(self):
        """::

            upgrade = headers.upgrade
            headers.upgrade = 'websocket'

        Shortcut for the ``Upgrade`` header.
        """
        return self.header(b'Upgrade')

    @upgrade.setter
    def upgrade(self, value):
        self.header(b'Upgrade', value)

    @property
    def user_agent(self):
        """::

            agent = headers.user_agent
            headers.user_agent = 'Mojo/1.0'

        Shortcut for the ``User-Agent`` header.
        """
        return self.header(b'User-Agent')

    @user_agent.setter
    def user_agent(self, value):
        self.header(b'User-Agent', value)

    @property
    def vary(self):
        """::

            vary = headers.vary
            headers.vary = '*'

        Shortcut for the ``Vary`` header.
        """
        return self.header(b'Vary')

    @vary.setter
    def vary(self, value):
        self.header(b'Vary', value)

    @property
    def www_authenticate(self):
        """::

            authenticate = headers.www_authenticate
            headers.www_authenticate = 'Basic realm="realm"'

        Shortcut for the ``WWW-Authenticate`` header.
        """
        return self.header(b'WWW-Authenticate')

    @www_authenticate.setter
    def www_authenticate(self, value):
        self.header(b'WWW-Authenticate', value)


new = Pyjo_Headers.new
object = Pyjo_Headers
