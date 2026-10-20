"""
Pyjo.URL - Uniform Resource Locator
===================================
::

    from Pyjo.URL import URL

    # Parse
    url = URL('http://sri:foo@example.com:3000/foo?foo=bar#23')
    print(url.scheme)
    print(url.userinfo)
    print(url.host)
    print(url.port)
    print(url.path)
    print(url.query)
    print(url.fragment)

    import Pyjo.URL

    # Parse
    url = Pyjo.URL.new('http://sri:foo@example.com:3000/foo?foo=bar#23')
    print(url.scheme)
    print(url.userinfo)
    print(url.host)
    print(url.port)
    print(url.path)
    print(url.query)
    print(url.fragment)

    # Build
    url = Pyjo.URL.new()
    url.scheme = 'http'
    url.host = 'example.com'
    url.port = 3000
    url.path = '/foo/bar'
    url.query = ('foo', 'bar')
    url.fragment = '23'
    print(url)

:mod:`Pyjo.URL` implements a subset of :rfc:`3986`, :rfc:`3987` and the
`URL Living Standard <https://url.spec.whatwg.org>`_ for Uniform Resource
Locators with support for IDNA and IRIs.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::URL <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/URL.pm>`_
of Mojolicious 9.49.

Classes
-------
"""

import Pyjo.Base
import Pyjo.Parameters
import Pyjo.Path
import Pyjo.String.Mixin

from Pyjo.Util import decode, punycode_decode, punycode_encode, url_escape, url_unescape

import builtins
import re

from typing import Self, cast
from urllib.parse import ParseResult, ParseResultBytes, SplitResult, SplitResultBytes, urlsplit


# The module ends with `object = Pyjo_URL`, which an annotation of `object`
# would mean, as annotations are evaluated lazily
type Anything = builtins.object

# A result of urllib.parse.urlsplit or urllib.parse.urlparse
type UrllibResult = SplitResult | ParseResult | SplitResultBytes | ParseResultBytes


class Pyjo_URL(Pyjo.Base.object, Pyjo.String.Mixin.object):
    """
    :mod:`Pyjo.URL` inherits all methods from :mod:`Pyjo.Base` and
    :mod:`Pyjo.String.Mixin` and implements the following new ones.
    """

    def __init__(self, url: 'str | bytes | UrllibResult | None' = None) -> None:
        """::

            url = Pyjo.URL.new()
            url = Pyjo.URL.new('http://127.0.0.1:3000/foo?f=b&baz=2#foo')
            url = Pyjo.URL.new(urlsplit('http://127.0.0.1:3000/foo?f=b&baz=2#foo'))

        Construct a new :mod:`Pyjo.URL` object and :meth:`parse` URL if necessary.
        """
        self._base: Pyjo_URL | None = None
        self._path: Pyjo.Path.object | None = None
        self._query: Pyjo.Parameters.object | None = None

        self.fragment: str | None = None
        """::

            fragment = url.fragment
            url.fragment = '♥pyjoyment♥'

        Fragment part of this URL. ::

            # "yada"
            Pyjo.URL.new('http://example.com/foo?bar=baz#yada').fragment
        """

        self.host: str | None = None
        """::

            host = url.host
            url.host = '127.0.0.1'

        Host part of this URL. ::

            # "example.com"
            Pyjo.URL.new('http://sri:t3st@example.com:8080/foo').host
        """

        self.port: int | None = None
        """::

            port = url.port
            url.port = 8080

        Port part of this URL. ::

            # 8080
            Pyjo.URL.new('http://sri:t3st@example.com:8080/foo').port
        """

        self.scheme: str | None = None
        """::

            scheme = url.scheme
            url.scheme = 'http'

        Scheme part of this URL. ::

            # "http"
            Pyjo.URL.new('http://example.com/foo').scheme
        """

        self.userinfo: str | None = None
        """::

            info = url.userinfo
            url.userinfo = 'root:♥'

        Userinfo part of this URL. ::

            # "sri:t3st"
            Pyjo.URL.new('https://sri:t3st@example.com/foo').userinfo
        """

        if url is not None:
            self.parse(url)

    def __bool__(self) -> bool:
        """::

            boolean = bool(url)

        Always true.
        """
        return True

    def __str__(self) -> str:
        """::

            string = str(url)

        Alias for :meth:`to_str`.
        """
        return self.to_str()

    @property
    def base(self) -> 'Pyjo_URL':
        """::

            base = url.base
            url.base = Pyjo.URL.new()

        Base of this URL, defaults to a :mod:`Pyjo.URL` object. ::

            # "http://example.com/a/b?c"
            Pyjo.URL.new('/a/b?c').set(base=Pyjo.URL.new('http://example.com')).to_abs()
        """
        if self._base is None:
            self._base = Pyjo_URL()
        return self._base

    @base.setter
    def base(self, value: 'Pyjo_URL') -> None:
        self._base = value

    def clone(self) -> Self:
        """::

            url2 = url.clone()

        Return a new :mod:`Pyjo.URL` object cloned from this URL.
        """
        clone = self.new()
        clone.fragment, clone.host, clone.port = self.fragment, self.host, self.port
        clone.scheme, clone.userinfo = self.scheme, self.userinfo
        clone._base = self._base.clone() if self._base is not None else None
        clone._path = self._path.clone() if self._path is not None else None
        clone._query = self._query.clone() if self._query is not None else None
        return clone

    @property
    def host_port(self) -> str | None:
        """::

            host_port = url.host_port
            url.host_port = 'example.com:8080'

        Normalized version of :attr:`host` and :attr:`port`. ::

            # "xn--n3h.net:8080"
            Pyjo.URL.new('http://☃.net:8080/test').host_port

            # "example.com"
            Pyjo.URL.new('http://example.com/test').host_port
        """
        if (host := self.ihost) is None:
            return None
        if (port := self.port) is None:
            return host
        return f'{host}:{port}'

    @host_port.setter
    def host_port(self, value: str | None) -> None:
        if value is None:
            return
        if m := re.search(r':(\d+)$', value):
            self.port = int(m[1])
            value = value[: m.start()]
        host = url_unescape(value)
        if re.search(r'[^\x00-\x7f]', host):
            self.ihost = host
        else:
            self.host = host

    @property
    def ihost(self) -> str | None:
        """::

            ihost = url.ihost
            url.ihost = 'xn--bcher-kva.ch'

        Host part of this URL in punycode format. ::

            # "xn--n3h.net"
            Pyjo.URL.new('http://☃.net').ihost

            # "example.com"
            Pyjo.URL.new('http://example.com').ihost
        """
        # Check if host needs to be encoded
        if (host := self.host) is None:
            return None
        if not re.search(r'[^\x00-\x7f]', host):
            return host

        # Encode
        return '.'.join(
            f'xn--{punycode_encode(label)}' if re.search(r'[^\x00-\x7f]', label) else label for label in host.split('.')
        )

    @ihost.setter
    def ihost(self, value: str) -> None:
        # Decode
        self.host = '.'.join(
            punycode_decode(m[1]) if (m := re.match(r'^xn--(.+)$', label)) else label for label in value.split('.')
        )

    @property
    def is_abs(self) -> bool:
        """::

            boolean = url.is_abs

        Check if URL is absolute. ::

            # True
            Pyjo.URL.new('http://example.com').is_abs
            Pyjo.URL.new('http://example.com/test/index.html').is_abs

            # False
            Pyjo.URL.new('test/index.html').is_abs
            Pyjo.URL.new('/test/index.html').is_abs
            Pyjo.URL.new('//example.com/test/index.html').is_abs
        """
        return bool(self.scheme)

    def parse(self, url: 'str | bytes | UrllibResult') -> Self:
        """::

            url = url.parse('http://127.0.0.1:3000/foo/bar?fo=o&baz=23#foo')
            url = url.parse(urlsplit('http://127.0.0.1:3000/foo/bar?fo=o&baz=23#foo'))

        Parse relative or absolute URL. Bytes are characters 0-255, as a Perl
        byte string, and a result of :func:`urllib.parse.urlsplit` or
        :func:`urllib.parse.urlparse` is taken as the URL it holds. ::

            # "/test/123"
            Pyjo.URL.new().parse('/test/123?foo=bar').path

            # "example.com"
            Pyjo.URL.new().parse('http://example.com/test/123?foo=bar').host

            # "sri@example.com"
            Pyjo.URL.new().parse('mailto:sri@example.com').path
        """
        # Not in Mojolicious: urllib of the standard library
        if isinstance(url, (SplitResult, ParseResult, SplitResultBytes, ParseResultBytes)):
            url = url.geturl()

        # Not in Mojolicious: bytes, which are characters 0-255, as a Perl byte string
        if isinstance(url, bytes):
            url = url.decode('latin-1')

        # Official regex from RFC 3986
        m = re.match(r'^(([^:/?#]+):)?(//([^/?#]*))?([^?#]*)(\?([^#]*))?(#(.*))?', url)
        assert m is not None
        if m[2] is not None:
            self.scheme = m[2]
        if m[5] is not None:
            self.path = m[5]
        if m[7] is not None:
            self.query = m[7]
        if m[9] is not None:
            self.fragment = _decode(url_unescape(m[9]))
        if (auth := m[4]) is not None:
            if info := re.match(r'^([^@]+)@', auth):
                self.userinfo = _decode(url_unescape(info[1]))
                auth = auth[info.end() :]
            self.host_port = auth

        return self

    @property
    def password(self) -> str | None:
        """::

            password = url.password

        Password part of :attr:`userinfo`. ::

            # "s3cret"
            Pyjo.URL.new('http://isabel:s3cret@pyjoyment.org').password

            # "s:3:c:r:e:t"
            Pyjo.URL.new('http://isabel:s:3:c:r:e:t@pyjoyment.org').password
        """
        m = re.search(r':(.*)$', self.userinfo or '')
        return m[1] if m else None

    @property
    def path(self) -> Pyjo.Path.object:
        """::

            path = url.path
            url.path = 'foo/bar'
            url.path = '/foo/bar'
            url.path = Pyjo.Path.new()

        Path part of this URL, relative paths will be merged with
        :meth:`Pyjo.Path.Pyjo_Path.merge`, defaults to a :mod:`Pyjo.Path` object. ::

            # "test"
            Pyjo.URL.new('http://example.com/test/Pyjo').path.parts[0]

            # "/test/DOM/HTML"
            Pyjo.URL.new('http://example.com/test/Pyjo').path.merge('DOM/HTML')

            # "http://example.com/DOM/HTML"
            Pyjo.URL.new('http://example.com/test/Pyjo').set(path='/DOM/HTML')

            # "http://example.com/test/DOM/HTML"
            Pyjo.URL.new('http://example.com/test/Pyjo').set(path='DOM/HTML')

            # "http://example.com/test/Pyjo/DOM/HTML"
            Pyjo.URL.new('http://example.com/test/Pyjo/').set(path='DOM/HTML')
        """
        # Old path
        if self._path is None:
            self._path = Pyjo.Path.new()
        return self._path

    @path.setter
    def path(self, value: str | bytes | Pyjo.Path.object) -> None:
        # New path
        self._path = value if isinstance(value, Pyjo.Path.object) else self.path.merge(value)

    @property
    def path_query(self) -> str:
        """::

            path_query = url.path_query
            url.path_query = '/foo/bar?a=1&b=2'

        Normalized version of :attr:`path` and :attr:`query`. ::

            # "/test?a=1&b=2"
            Pyjo.URL.new('http://example.com/test?a=1&b=2').path_query

            # "/"
            Pyjo.URL.new('http://example.com/').path_query
        """
        query = self.query.to_str()
        return self.path.to_str() + (f'?{query}' if query else '')

    @path_query.setter
    def path_query(self, value: str | None) -> None:
        if value is None:
            return
        m = re.match(r'^([^?#]*)(?:\?([^#]*))?', value)
        assert m is not None
        self.path = m[1]
        if m[2] is not None:
            self.query = m[2]

    @property
    def protocol(self) -> str:
        """::

            proto = url.protocol

        Normalized version of :attr:`scheme`. ::

            # "http"
            Pyjo.URL.new('HtTp://example.com').protocol
        """
        return (self.scheme or '').lower()

    @property
    def query(self) -> Pyjo.Parameters.object:
        """::

            query = url.query
            url.query = {'merge': 'to'}
            url.query = ['append', 'with']
            url.query = ('replace', 'with')
            url.query = 'a=1&b=2'
            url.query = Pyjo.Parameters.new()

        Query part of this URL, key/value pairs in a ``list`` will be appended with
        :meth:`Pyjo.Parameters.Pyjo_Parameters.append`, key/value pairs in a
        ``dict`` merged with :meth:`Pyjo.Parameters.Pyjo_Parameters.merge`, and
        key/value pairs in a ``tuple`` replace the parameters, defaults to a
        :mod:`Pyjo.Parameters` object. ::

            # "2"
            Pyjo.URL.new('http://example.com?a=1&b=2').query.param('b')

            # "b=2&a=2&c=3"
            Pyjo.URL.new('http://example.com?a=1&b=2').query.merge('a', 2, 'c', 3)

            # "http://example.com?a=2&c=3"
            Pyjo.URL.new('http://example.com?a=1&b=2').set(query=('a', 2, 'c', 3))

            # "http://example.com?a=2&a=3"
            Pyjo.URL.new('http://example.com?a=1&b=2').set(query=('a', [2, 3]))

            # "http://example.com?b=2&a=2&c=3"
            Pyjo.URL.new('http://example.com?a=1&b=2').set(query={'a': 2, 'c': 3})

            # "http://example.com?b=2"
            Pyjo.URL.new('http://example.com?a=1&b=2').set(query={'a': None})

            # "http://example.com?a=1&b=2&a=2&c=3"
            Pyjo.URL.new('http://example.com?a=1&b=2').set(query=['a', 2, 'c', 3])
        """
        # Old parameters
        if self._query is None:
            self._query = Pyjo.Parameters.new()
        return self._query

    @query.setter
    def query(self, value: Anything) -> None:
        q = self.query

        # Replace with tuple
        if isinstance(value, tuple):
            q.pairs = []
            q.append(*cast(tuple[Anything, ...], value))

        # Merge with dict
        elif isinstance(value, dict):
            q.merge(*(x for pair in cast(dict[Anything, Anything], value).items() for x in pair))

        # Append list
        elif isinstance(value, list):
            q.append(*cast(list[Anything], value))

        # New parameters
        elif isinstance(value, Pyjo.Parameters.object):
            self._query = value
        else:
            q.parse(value)

    def to_abs(self, base: 'Pyjo_URL | None' = None) -> Self:
        """::

            abs = url.to_abs()
            abs = url.to_abs(Pyjo.URL.new('http://example.com/foo'))

        Return a new :mod:`Pyjo.URL` object cloned from this relative URL and turn it
        into an absolute one using :attr:`base` or provided base URL. ::

            # "http://example.com/foo/baz.xml?test=123"
            Pyjo.URL.new('baz.xml?test=123').to_abs(Pyjo.URL.new('http://example.com/foo/bar.html'))

            # "http://example.com/baz.xml?test=123"
            Pyjo.URL.new('/baz.xml?test=123').to_abs(Pyjo.URL.new('http://example.com/foo/bar.html'))

            # "http://example.com/foo/baz.xml?test=123"
            Pyjo.URL.new('//example.com/foo/baz.xml?test=123').to_abs(Pyjo.URL.new('http://example.com/foo/bar.html'))
        """
        abs = self.clone()
        if abs.is_abs:
            return abs

        # Scheme
        base = base if base is not None else abs.base
        abs.base = base
        abs.scheme = base.scheme

        # Authority
        if abs.host:
            return abs
        abs.userinfo, abs.host, abs.port = base.userinfo, base.host, base.port

        # Absolute path
        path = abs.path
        if path.leading_slash:
            return abs

        # Inherit path
        if not path.parts:
            abs.path = base.path.clone().canonicalize()

            # Query
            if not abs.query.to_str():
                abs.query = base.query.clone()

        # Merge paths
        else:
            abs.path = base.path.clone().merge(path).canonicalize()

        return abs

    def to_str(self) -> str:
        """::

            string = url.to_str()

        Turn URL into a string. Note that :attr:`userinfo` will not be included for
        security reasons. ::

            # "http://pyjoyment.org"
            Pyjo.URL.new().set(scheme='http', host='pyjoyment.org').to_str()

            # "http://pyjoyment.org"
            Pyjo.URL.new('http://daniel:s3cret@pyjoyment.org').to_str()
        """
        return self._string(False)

    def to_unsafe_str(self) -> str:
        """::

            string = url.to_unsafe_str()

        Same as :meth:`to_str`, but includes :attr:`userinfo`. ::

            # "http://daniel:s3cret@pyjoyment.org"
            Pyjo.URL.new('http://daniel:s3cret@pyjoyment.org').to_unsafe_str()
        """
        return self._string(True)

    # Not in Mojolicious: urllib of the standard library
    def to_urllib(self) -> SplitResult:
        """::

            split = url.to_urllib()

        Turn URL into a :class:`urllib.parse.SplitResult`, for the standard library.
        Unlike :meth:`to_str`, it includes :attr:`userinfo`, as the result holds all
        parts of the URL. ::

            # "isabel"
            Pyjo.URL.new('http://isabel:s3cret@pyjoyment.org/foo').to_urllib().username
        """
        return urlsplit(self.to_unsafe_str())

    @property
    def username(self) -> str | None:
        """::

            username = url.username

        Username part of :attr:`userinfo`. ::

            # "isabel"
            Pyjo.URL.new('http://isabel:s3cret@pyjoyment.org').username
        """
        m = re.match(r'^([^:]+)', self.userinfo or '')
        return m[1] if m else None

    def _string(self, unsafe: bool) -> str:
        # Scheme
        url = ''
        if proto := self.protocol:
            url += f'{proto}:'

        # Authority
        auth = self.host_port
        if auth is not None:
            auth = _encode(auth, rb"^A-Za-z0-9\-._~!$&'()*+,;=:\[\]")
        if unsafe and (info := self.userinfo) is not None:
            auth = _encode(info, rb"^A-Za-z0-9\-._~!$&'()*+,;=:") + '@' + (auth or '')
        if auth is not None:
            url += f'//{auth}'

        # Path and query
        path = self.path_query
        url += path if not auth or not path or re.match(r'[/?]', path) else f'/{path}'

        # Fragment
        if (fragment := self.fragment) is None:
            return url
        return url + '#' + _encode(fragment, rb"^A-Za-z0-9\-._~!$&'()*+,;=:@/?")


def _decode(string: str) -> str:
    return decoded if (decoded := decode('UTF-8', string)) is not None else string


def _encode(string: str, pattern: bytes) -> str:
    return url_escape(string.encode('UTF-8'), pattern).decode('ascii')


new = Pyjo_URL.new
object = Pyjo_URL
URL = Pyjo_URL
