"""
Pyjo.Cookie.Response - HTTP response cookie
===========================================
::

    from Pyjo.Cookie.Response import Response

    cookie = Response()
    cookie.name = 'foo'
    cookie.value = 'bar'
    print(cookie)

    import Pyjo.Cookie.Response

    cookie = Pyjo.Cookie.Response.new()
    cookie.name = 'foo'
    cookie.value = 'bar'
    print(cookie)

:mod:`Pyjo.Cookie.Response` is a container for HTTP response cookies, based on
:rfc:`6265`.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::Cookie::Response <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/Cookie/Response.pm>`_
of Mojolicious 9.49.

Classes
-------
"""

import Pyjo.Cookie
import Pyjo.Date

from Pyjo.Util import quote, split_cookie_header

import contextlib
import re

from http.cookies import BaseCookie, CookieError, Morsel


ATTRS = {'domain', 'expires', 'httponly', 'max-age', 'partitioned', 'path', 'samesite', 'secure'}


class Pyjo_Cookie_Response(Pyjo.Cookie.object):
    """
    :mod:`Pyjo.Cookie.Response` inherits all attributes and methods from
    :mod:`Pyjo.Cookie` and implements the following new ones.
    """

    def __init__(
        self,
        morsel: Morsel[str] | None = None,
        *,
        name: str | None = None,
        value: str | None = None,
        domain: str | None = None,
        expires: int | float | None = None,
        host_only: bool | None = None,
        httponly: bool | None = None,
        max_age: int | None = None,
        partitioned: bool | None = None,
        path: str | None = None,
        samesite: str | None = None,
        secure: bool | None = None,
    ) -> None:
        super().__init__(morsel, name=name, value=value)

        self.domain = domain
        """::

            domain = cookie.domain
            cookie.domain = 'localhost'

        Cookie domain.
        """

        self.expires = expires
        """::

            expires = cookie.expires
            cookie.expires = time.time() + 60

        Expiration for cookie.
        """

        self.host_only = host_only
        """::

            boolean = cookie.host_only
            cookie.host_only = boolean

        Host-only flag, indicating that the canonicalized request-host is identical
        to the cookie's :attr:`domain`.
        """

        self.httponly = httponly
        """::

            boolean = cookie.httponly
            cookie.httponly = boolean

        HttpOnly flag, which can prevent client-side scripts from accessing this
        cookie.
        """

        self.max_age = max_age
        """::

            max_age = cookie.max_age
            cookie.max_age = 60

        Max age for cookie.
        """

        self.partitioned = partitioned
        """::

            partitioned = cookie.partitioned
            cookie.partitioned = True

        Partitioned flag, this is to be used in accordance to the CHIPS amendment to
        :rfc:`6265`. Note that this attribute is **EXPERIMENTAL** because even though
        most commonly used browsers support the feature, there is no specification
        yet besides `this draft
        <https://www.ietf.org/archive/id/draft-cutler-httpbis-partitioned-cookies-00.html>`_.
        """

        self.path = path
        """::

            path = cookie.path
            cookie.path = '/test'

        Cookie path.
        """

        self.samesite = samesite
        """::

            samesite = cookie.samesite
            cookie.samesite = 'Lax'

        SameSite value.
        """

        self.secure = secure
        """::

            boolean = cookie.secure
            cookie.secure = boolean

        Secure flag, which instructs browsers to only send this cookie over HTTPS
        connections.
        """

        # Not in Mojolicious: the attributes of a Morsel of http.cookies, as a
        # "Set-Cookie" header gives them
        if morsel is not None:
            vars(self).update(vars(self.parse(morsel.OutputString())[0]))

    @classmethod
    def parse[C: Pyjo_Cookie_Response](cls: type[C], string: str | BaseCookie[str] | None = None) -> list[C]:
        """::

            cookies = Pyjo.Cookie.Response.parse('f=b; path=/')
            cookies = Pyjo.Cookie.Response.parse(SimpleCookie('f=b; path=/'))

        Parse cookies, also from a :class:`http.cookies.SimpleCookie` of the standard
        library.
        """
        # Not in Mojolicious: http.cookies of the standard library
        if isinstance(string, BaseCookie):
            return [cls.new(morsel) for morsel in string.values()]

        cookies: list[C] = []
        tree = split_cookie_header(string or '')
        for pairs in tree:
            (name, value), *attrs = pairs
            cookie = cls.new(name=name, value=value or '')
            cookies.append(cookie)

            for name, value in attrs:
                if (attr := name.lower()) not in ATTRS:
                    continue
                if attr == 'domain':
                    cookie.domain = value.removeprefix('.') if value is not None else None
                elif attr == 'expires':
                    cookie.expires = Pyjo.Date.new(value or '').epoch
                elif attr == 'max-age':
                    # Unlike Mojolicious: a value that is not an integer is ignored, as RFC 6265
                    # says; Mojo keeps it
                    if value is not None and re.fullmatch(r'-?\d+', value):
                        cookie.max_age = int(value)
                elif attr == 'path':
                    cookie.path = value
                elif attr == 'samesite':
                    cookie.samesite = value
                else:
                    setattr(cookie, attr, True)

        return cookies

    # Not in Mojolicious: http.cookies of the standard library
    def to_morsel(self) -> Morsel[str]:
        """::

            morsel = cookie.to_morsel()

        Turn cookie into a :class:`http.cookies.Morsel`, for the standard library.
        The partitioned flag is left out before Python 3.14, as ``Morsel`` has no
        such attribute there. ::

            # "foo=bar; Path=/; Secure"
            Pyjo.Cookie.Response.new(name='foo', value='bar', path='/', secure=True).to_morsel().OutputString()
        """
        morsel = super().to_morsel()
        if (expires := self.expires) is not None:
            morsel['expires'] = Pyjo.Date.new(expires).to_str()
        if domain := self.domain:
            morsel['domain'] = domain
        if path := self.path:
            morsel['path'] = path
        if self.partitioned:
            with contextlib.suppress(CookieError):
                morsel['partitioned'] = True
        if self.secure:
            morsel['secure'] = True
        if self.httponly:
            morsel['httponly'] = True
        if samesite := self.samesite:
            morsel['samesite'] = samesite
        if (max_age := self.max_age) is not None:
            morsel['max-age'] = str(max_age)
        return morsel

    def to_str(self) -> str:
        """::

            string = cookie.to_str()

        Render cookie.
        """
        # Name and value
        if not (name := self.name or ''):
            return ''
        value = self.value or ''
        cookie = '='.join([name, quote(value) if re.search(r'[,;" ]', value) else value])

        # "expires"
        if (expires := self.expires) is not None:
            cookie += f'; expires={Pyjo.Date.new(expires)}'

        # "domain"
        if domain := self.domain:
            cookie += f'; domain={domain}'

        # "path"
        if path := self.path:
            cookie += f'; path={path}'

        # "Partitioned"
        if self.partitioned:
            cookie += '; Partitioned'

        # "secure"
        if self.secure:
            cookie += '; secure'

        # "HttpOnly"
        if self.httponly:
            cookie += '; HttpOnly'

        # "Same-Site"
        if samesite := self.samesite:
            cookie += f'; SameSite={samesite}'

        # "Max-Age"
        if (max_age := self.max_age) is not None:
            cookie += f'; Max-Age={max_age}'

        return cookie


parse = Pyjo_Cookie_Response.parse
new = Pyjo_Cookie_Response.new
object = Pyjo_Cookie_Response
Response = Pyjo_Cookie_Response
