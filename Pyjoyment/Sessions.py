"""
Pyjoyment.Sessions - Session manager based on signed cookies
============================================================
::

    import Pyjoyment.Sessions

    sessions = Pyjoyment.Sessions.new()
    sessions.cookie_name = 'myapp'
    sessions.default_expiration = 86400

:mod:`Pyjoyment.Sessions` manages sessions based on signed cookies for
:mod:`Pyjoyment`. All data gets serialized with :mod:`Pyjo.JSON` and stored
Base64 encoded on the client-side, but is protected from unwanted changes with
a HMAC-SHA256 signature.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojolicious::Sessions <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojolicious/Sessions.pm>`_
of Mojolicious 9.49.
"""

import Pyjo.Base
import Pyjo.JSON

from Pyjo.Util import b64_decode, b64_encode

import time

from collections.abc import Callable
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    import Pyjoyment.Controller


class Pyjoyment_Sessions(Pyjo.Base.object):
    """
    :mod:`Pyjoyment.Sessions` inherits all methods from :mod:`Pyjo.Base` and
    implements the following new ones.
    """

    def __init__(self) -> None:
        """::

            sessions = Pyjoyment.Sessions.new()

        Construct a new :mod:`Pyjoyment.Sessions` object.
        """
        self.cookie_domain: str | None = None
        """::

            domain = sessions.cookie_domain
            sessions.cookie_domain = '.example.com'

        Domain for session cookies, not defined by default.
        """

        # Unlike Mojolicious: the cookie is named after Pyjoyment, where Mojo names it "mojolicious"
        self.cookie_name = 'pyjoyment'
        """::

            name = sessions.cookie_name
            sessions.cookie_name = 'session'

        Name for session cookies, defaults to ``pyjoyment``.
        """

        self.cookie_path = '/'
        """::

            path = sessions.cookie_path
            sessions.cookie_path = '/foo'

        Path for session cookies, defaults to ``/``.
        """

        self.default_expiration = 3600
        """::

            time = sessions.default_expiration
            sessions.default_expiration = 3600

        Default time for sessions to expire in seconds from now, defaults to
        ``3600``. The expiration timeout gets refreshed for every request.
        Setting the value to ``0`` will allow sessions to persist until the
        browser window is closed, this can have security implications though.
        For more control you can also use the ``expiration`` and ``expires``
        session values. ::

            # Expiration date in seconds from now (persists between requests)
            c.session(expiration=604800)

            # Expiration date as absolute epoch time (only valid for one request)
            c.session(expires=time.time() + 604800)

            # Delete whole session by setting an expiration date in the past
            c.session(expires=1)
        """

        self.deserialize: Callable[[bytes], Any] = Pyjo.JSON.decode_json
        """::

            cb = sessions.deserialize
            sessions.deserialize = lambda data: ...

        A callback used to deserialize sessions, defaults to
        :func:`Pyjo.JSON.decode_json`. ::

            sessions.deserialize = lambda data: {}
        """

        # Left out from Mojolicious: encrypted, as encrypt_cookie and decrypt_cookie of Pyjo.Util are left out

        self.partitioned: bool | None = None
        """::

            boolean = sessions.partitioned
            sessions.partitioned = boolean

        Partitioned flag, this is to be used in accordance to the CHIPS
        amendment to :rfc:`6265`.

        Note that this attribute is **EXPERIMENTAL** because even though most
        commonly used browsers support the feature, there is no specification
        yet besides `this draft
        <https://www.ietf.org/archive/id/draft-cutler-httpbis-partitioned-cookies-00.html>`_.

        Partitioned cookies are held within a separate cookie jar per top-level
        site.
        """

        self.samesite: str | None = 'Lax'
        """::

            samesite = sessions.samesite
            sessions.samesite = 'Strict'

        Set the SameSite value on all session cookies, defaults to ``Lax``. ::

            # Disable SameSite feature
            sessions.samesite = None
        """

        self.secure: bool | None = None
        """::

            boolean = sessions.secure
            sessions.secure = boolean

        Set the secure flag on all session cookies, so that browsers send them
        only over HTTPS connections.
        """

        self.serialize: Callable[[dict[str, Any]], bytes] = Pyjo.JSON.encode_json
        """::

            cb = sessions.serialize
            sessions.serialize = lambda session: ...

        A callback used to serialize sessions, defaults to
        :func:`Pyjo.JSON.encode_json`. ::

            sessions.serialize = lambda session: b''
        """

    def load(self, c: 'Pyjoyment.Controller.object') -> None:
        """::

            sessions.load(Pyjoyment.Controller.new())

        Load session data from signed cookie.
        """
        if not (value := c.signed_cookie(self.cookie_name)):
            return
        if not (session := self.deserialize(b64_decode(value.replace('-', '=')))):
            return

        # "expiration" value is inherited
        expiration = session.get('expiration')
        if expiration is None:
            expiration = self.default_expiration
        if not (expires := session.pop('expires', None)) and expiration:
            return
        if expires is not None and expires <= time.time():
            return

        stash = c.stash()
        stash['mojo.active_session'] = len(session)
        if not session:
            return
        stash['mojo.session'] = session
        if session.get('new_flash'):
            session['flash'] = session.pop('new_flash')

    def store(self, c: 'Pyjoyment.Controller.object') -> None:
        """::

            sessions.store(Pyjoyment.Controller.new())

        Store session data in signed cookie.
        """
        # Make sure session was active
        stash = c.stash()
        if (session := stash.get('mojo.session')) is None:
            return
        if not session and not stash.get('mojo.active_session'):
            return

        # Don't reset flash for static files
        old = session.pop('flash', None)
        if stash.get('mojo.static'):
            session['new_flash'] = old
        if not session.get('new_flash'):
            session.pop('new_flash', None)

        # Generate "expires" value from "expiration" if necessary
        expiration = session.get('expiration')
        if expiration is None:
            expiration = self.default_expiration
        default = session.pop('expires', None)
        if expiration or default:
            session['expires'] = default or int(time.time()) + expiration

        value = b64_encode(self.serialize(session), '').replace('=', '-')
        options = {
            'domain': self.cookie_domain,
            'expires': session.get('expires'),
            'httponly': True,
            'partitioned': self.partitioned,
            'path': self.cookie_path,
            'samesite': self.samesite,
            'secure': self.secure,
        }
        c.signed_cookie(self.cookie_name, value, options)

    # Left out from Mojolicious: the removal of the padding of old sessions in _deserialize, which is deprecated, as
    # Pyjoyment has never padded them


new = Pyjoyment_Sessions.new
object = Pyjoyment_Sessions
