r"""
Pyjo.UserAgent.Transactor - User agent transactor
=================================================
::

    from Pyjo.UserAgent.Transactor import Transactor

    # GET request with Accept header
    t = Transactor()
    print(t.tx('GET', 'http://example.com', {'Accept': '*/*'}).req.to_bytes())

    # Or import the module, as in Google Python Style Guide
    import Pyjo.UserAgent.Transactor

    # GET request with Accept header
    t = Pyjo.UserAgent.Transactor.new()
    print(t.tx('GET', 'http://example.com', {'Accept': '*/*'}).req.to_bytes())

    # POST request with form-data
    print(t.tx('POST', 'example.com', form={'a': 'b'}).req.to_bytes())

    # PUT request with JSON data
    print(t.tx('PUT', 'example.com', json={'a': 'b'}).req.to_bytes())

:mod:`Pyjo.UserAgent.Transactor` is the transaction building and manipulation
framework used by :mod:`Pyjo.UserAgent`.

Generators
----------

These content generators are available by default.

form
~~~~
::

    t.tx('POST', 'http://example.com', form={'a': 'b'})

Generate query string, ``application/x-www-form-urlencoded`` or
``multipart/form-data`` content. See :meth:`~Pyjo_UserAgent_Transactor.tx`
for more.

json
~~~~
::

    t.tx('PATCH', 'http://example.com', json={'a': 'b'})

Generate JSON content with :mod:`Pyjo.JSON`. See
:meth:`~Pyjo_UserAgent_Transactor.tx` for more.

multipart
~~~~~~~~~
::

    t.tx('PUT', 'http://example.com', multipart=['Hello', 'World!'])

Generate multipart content. See :meth:`~Pyjo_UserAgent_Transactor.tx` for
more.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::UserAgent::Transactor <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/UserAgent/Transactor.pm>`_
of Mojolicious 9.49.

Classes
-------
"""

import Pyjo.Asset
import Pyjo.Asset.File
import Pyjo.Asset.Memory
import Pyjo.Base
import Pyjo.Content
import Pyjo.Content.MultiPart
import Pyjo.Content.Single
import Pyjo.File
import Pyjo.Headers
import Pyjo.Message.Response
import Pyjo.Parameters
import Pyjo.Promise
import Pyjo.Transaction
import Pyjo.Transaction.HTTP
import Pyjo.Transaction.WebSocket
import Pyjo.URL

from Pyjo.JSON import encode_json
from Pyjo.Util import encode, url_escape
from Pyjo.WebSocket import challenge, client_handshake

import builtins
import os
import re
import weakref

from collections.abc import Callable, Mapping, Sequence
from typing import Any, Self, cast
from urllib.parse import SplitResult


type Anything = builtins.object

# A generator is called with the transactor, the transaction, its data and its options
type Generator = Callable[..., Anything]


class Pyjo_UserAgent_Transactor(Pyjo.Base.object):
    """
    :mod:`Pyjo.UserAgent.Transactor` inherits all methods from
    :mod:`Pyjo.Base` and implements the following new ones.
    """

    def __init__(
        self,
        *,
        compressed: bool | None = None,
        generators: dict[str, Generator] | None = None,
        # Unlike Mojolicious: Pyjoyment names itself
        name: str = 'Pyjoyment (Python)',
    ) -> None:
        """::

            t = Pyjo.UserAgent.Transactor.new()
            t = Pyjo.UserAgent.Transactor.new(compressed=False)

        Construct a new :mod:`Pyjo.UserAgent.Transactor` object.
        """
        self._compressed: bool | None = compressed

        self.generators: dict[str, Generator] = (
            generators if generators is not None else {'form': _form, 'json': _json, 'multipart': _multipart}
        )
        """::

            generators = t.generators
            t.generators = {'foo': lambda t, tx, *args, **options: ...}

        Registered content generators, by default only ``form``, ``json`` and
        ``multipart`` are already defined.
        """

        self.name = name
        """::

            name = t.name
            t.name = 'Pyjoyment'

        Value for ``User-Agent`` request header of generated transactions,
        defaults to ``Pyjoyment (Python)``.
        """

    @property
    def compressed(self) -> bool:
        """::

            boolean = t.compressed
            t.compressed = boolean

        Try to negotiate compression for the response content and decompress it
        automatically, defaults to the value of the ``PYJO_GZIP`` environment
        variable or true.
        """
        if self._compressed is None:
            self._compressed = os.environ.get('PYJO_GZIP', '1') not in ('', '0')
        return self._compressed

    @compressed.setter
    def compressed(self, value: bool) -> None:
        self._compressed = value

    def add_generator(self, name: str, cb: Generator) -> Self:
        """::

            t = t.add_generator('foo', lambda t, tx, *args, **options: ...)

        Register a content generator. ::

            def foo(t, tx, data, **options): ...

            t.add_generator('foo', foo)
        """
        self.generators[name] = cb
        return self

    def download(
        self, head: Pyjo.Transaction.HTTP.object, path: str | os.PathLike[str]
    ) -> Pyjo.Transaction.HTTP.object:
        """::

            tx = t.download(Pyjo.Transaction.HTTP.new(), '/home/sri/test.tar.gz')

        Build :mod:`Pyjo.Transaction.HTTP` resumable file download request as
        follow-up to a ``HEAD`` request. Note that this method is
        **EXPERIMENTAL** and might change without warning!
        """
        req = head.req
        tx = self.tx('GET', req.url.clone(), req.headers.to_dict())
        res = tx.res
        if error := head.error:
            res.error = error
            return tx

        headers = head.res.headers
        accept_ranges = 'bytes' in (headers.accept_ranges or '')
        size = int(headers.content_length or 0)

        current_size = 0
        file = Pyjo.File.path(path)
        if os.path.isfile(file):
            current_size = os.path.getsize(file)
            if not size:
                res.error = {'message': 'Unknown file size'}
                return tx
            if current_size > size:
                res.error = {'message': 'File size mismatch'}
                return tx
            if current_size == size:
                res.error = {'message': 'Download complete'}
                return tx
            if not accept_ranges:
                res.error = {'message': 'Server does not support partial requests'}
                return tx
            tx.req.headers.range = f'bytes={current_size}-{size}'

        fh = file.open('ab', buffering=0)

        # Not in Mojolicious: the file is closed with the transaction that is not finished, as Perl closes it with the
        # last reference
        weakref.finalize(tx, fh.close)

        @res.content.unsubscribe('read').on('read')
        def read(content: Pyjo.Content.object, chunk: bytes) -> None:
            nonlocal current_size
            current_size += len(chunk)
            try:
                if fh.write(chunk) != len(chunk):
                    raise OSError('Short write')
            except OSError as e:
                res.error = {'message': f'Can\'t write to file "{os.fspath(path)}": {e.strerror or e}'}

        @res.on('finish')
        def finish(res: Pyjo.Message.Response.object) -> None:
            # Not in Mojolicious: the file is closed at the end, as PyPy frees it only when its garbage collector runs
            fh.close()
            if current_size < size:
                res.error = {'message': 'Download incomplete'}

        return tx

    def endpoint(self, tx: Pyjo.Transaction.object) -> tuple[str, str | None, int]:
        """::

            proto, host, port = t.endpoint(Pyjo.Transaction.HTTP.new())

        Actual endpoint for transaction.
        """
        # Basic endpoint
        req = tx.req
        url = req.url
        proto = url.protocol or 'http'
        host = url.ihost
        port = url.port if url.port is not None else (443 if proto == 'https' else 80)

        # Proxy for normal HTTP requests
        socks = False
        if (proxy := req.proxy) is not None:
            socks = proxy.protocol == 'socks'
        if proto == 'http' and not req.is_handshake and not socks:
            return _proxy(tx, proto, host, port)

        return proto, host, port

    def peer(self, tx: Pyjo.Transaction.object) -> tuple[str, str | None, int]:
        """::

            proto, host, port = t.peer(Pyjo.Transaction.HTTP.new())

        Actual peer for transaction.
        """
        return _proxy(tx, *self.endpoint(tx))

    def promisify(self, promise: Pyjo.Promise.object, tx: Pyjo.Transaction.object) -> Pyjo.Promise.object:
        """::

            t.promisify(Pyjo.Promise.new(), Pyjo.Transaction.HTTP.new())

        Resolve or reject :mod:`Pyjo.Promise` object with
        :mod:`Pyjo.Transaction.HTTP` object.
        """
        err = tx.error
        if err and not err.get('code'):
            return promise.reject(err['message'])
        if tx.req.is_handshake and not tx.is_websocket:
            return promise.reject('WebSocket handshake failed')
        return promise.resolve(tx)

    def proxy_connect(self, old: Pyjo.Transaction.object) -> Pyjo.Transaction.HTTP.object | None:
        """::

            tx = t.proxy_connect(Pyjo.Transaction.HTTP.new())

        Build :mod:`Pyjo.Transaction.HTTP` proxy ``CONNECT`` request for
        transaction if possible.
        """
        # Already a CONNECT request
        req = old.req
        if req.method.upper() == 'CONNECT':
            return None

        # No proxy
        if (proxy := req.proxy) is None or not req.via_proxy:
            return None
        if proxy.protocol == 'socks':
            return None

        # WebSocket and/or HTTPS
        url = req.url
        if not req.is_handshake and url.protocol != 'https':
            return None

        # CONNECT request (expect a bad response)
        target = url.clone()
        target.userinfo = None
        new = self.tx('CONNECT', target)
        new.req.proxy = proxy
        content = new.res.content
        content.auto_relax = False
        content.headers.connection = 'keep-alive'

        return new

    def redirect(self, old: Pyjo.Transaction.HTTP.object) -> Pyjo.Transaction.HTTP.object | None:
        """::

            tx = t.redirect(Pyjo.Transaction.HTTP.new())

        Build :mod:`Pyjo.Transaction.HTTP` follow-up request for ``301``,
        ``302``, ``303``, ``307`` or ``308`` redirect response if possible.
        Since ``QUERY`` requests are safe and idempotent, they are never
        redirected as ``GET`` requests and keep their content, except for
        ``303`` responses.
        """
        # Commonly used codes
        res = old.res
        code = res.code or 0
        if code not in (301, 302, 303, 307, 308):
            return None

        # CONNECT requests cannot be redirected
        req = old.req
        if req.method.upper() == 'CONNECT':
            return None

        # Fix location without authority and/or scheme
        if not (locations := res.headers.every_header('Location')) or not locations[0]:
            return None
        location = Pyjo.URL.new(locations[0])
        if not location.is_abs:
            location.base = req.url
            location = location.to_abs()
        proto = location.protocol
        if (proto != 'http' and proto != 'https') or not location.host:
            return None

        # Clone request if necessary (QUERY is safe and idempotent, so it keeps its content like 307 and 308)
        new = Pyjo.Transaction.HTTP.new()
        method = req.method.upper()
        if code == 307 or code == 308 or (method == 'QUERY' and code != 303):
            if (clone := req.clone()) is None:
                return None
            new.req = clone
        else:
            new.req.method = 'GET' if code == 303 or method == 'POST' else method
            new.req.content.headers = headers = req.headers.clone()
            for name in [name for name in headers.names() if re.match(r'content-', name, re.I)]:
                headers.remove(name)

        content = new.res.content
        if not self.compressed:
            content.auto_decompress = False
        new.req.url = location
        headers = new.req.headers
        for name in ('Authorization', 'Cookie', 'Host', 'Referer'):
            headers.remove(name)
        if res.content.has_subscribers('sse'):
            for cb in res.content.subscribers('sse'):
                content.on('sse', cb)

        new.previous = old
        return new

    def tx(
        self,
        method: str,
        url: str | Pyjo.URL.object | SplitResult,
        *args: Mapping[str, Any] | bytes | str,
        **generator: Any,
    ) -> Pyjo.Transaction.HTTP.object:
        r"""::

            tx = t.tx('GET', 'example.com')
            tx = t.tx('POST', 'http://example.com')
            tx = t.tx('GET', 'http://example.com', {'Accept': '*/*'})
            tx = t.tx('PUT', 'http://example.com', b'Content!')
            tx = t.tx('PUT', 'http://example.com', form={'a': 'b'})
            tx = t.tx('PUT', 'http://example.com', json={'a': 'b'})
            tx = t.tx('PUT', 'https://example.com', multipart=['a', 'b'])
            tx = t.tx('POST', 'example.com', {'Accept': '*/*'}, b'Content!')
            tx = t.tx('PUT', 'example.com', {'Accept': '*/*'}, form={'a': 'b'})
            tx = t.tx('PUT', 'example.com', {'Accept': '*/*'}, json={'a': 'b'})
            tx = t.tx('PUT', 'example.com', {'Accept': '*/*'}, multipart=['a', 'b'])

        Versatile general purpose :mod:`Pyjo.Transaction.HTTP` transaction
        builder for requests, with support for generators. The URL is also a
        :class:`urllib.parse.SplitResult` of the standard library, and the
        content a ``str``, which is encoded as UTF-8. ::

            # Generate and inspect custom GET request with DNT header and content
            print(t.tx('GET', 'example.com', {'DNT': 1}, b'Bye!').req.to_bytes())

            # Stream response content to STDOUT
            tx = t.tx('GET', 'http://example.com')
            tx.res.content.unsubscribe('read').on('read', lambda content, chunk: print(chunk))

            # PUT request with content streamed from file
            tx = t.tx('PUT', 'http://example.com')
            tx.req.content.asset = Pyjo.Asset.File.new(path='/foo.txt')

        The ``json`` content generator uses :mod:`Pyjo.JSON` for encoding and
        sets the content type to ``application/json``. ::

            # POST request with "application/json" content
            tx = t.tx('POST', 'http://example.com', json={'a': 'b', 'c': [1, 2, 3]})

        The ``form`` content generator will automatically use query parameters
        for ``GET`` and ``HEAD`` requests. ::

            # GET request with query parameters
            tx = t.tx('GET', 'http://example.com', form={'a': 'b'})

        For all other request methods the ``application/x-www-form-urlencoded``
        content type is used. ::

            # POST request with "application/x-www-form-urlencoded" content
            tx = t.tx('POST', 'http://example.com', form={'a': 'b', 'c': 'd'})

        Parameters may be encoded with the ``charset`` option. ::

            # PUT request with Shift_JIS encoded form values
            tx = t.tx('PUT', 'example.com', form={'a': 'b'}, charset='Shift_JIS')

        A list can be used for multiple form values sharing the same name. ::

            # POST request with form values sharing the same name
            tx = t.tx('POST', 'http://example.com', form={'a': ['b', 'c', 'd']})

        A dict with a ``content`` or ``file`` value can be used to switch to
        the ``multipart/form-data`` content type for file uploads. ::

            # POST request with "multipart/form-data" content
            tx = t.tx('POST', 'http://example.com', form={'mytext': {'content': 'lala'}})

            # POST request with multiple files sharing the same name
            tx = t.tx('POST', 'http://example.com', form={'mytext': [{'content': 'first'}, {'content': 'second'}]})

        The ``file`` value should contain the path to the file you want to
        upload or an asset object, like :mod:`Pyjo.Asset.File` or
        :mod:`Pyjo.Asset.Memory`. ::

            # POST request with upload streamed from file
            tx = t.tx('POST', 'http://example.com', form={'mytext': {'file': '/foo.txt'}})

            # POST request with upload streamed from asset
            asset = Pyjo.Asset.Memory.new().add_chunk(b'lalala')
            tx = t.tx('POST', 'http://example.com', form={'mytext': {'file': asset}})

        A ``filename`` value will be generated automatically, but can also be
        set manually if necessary. All remaining values in the dict get merged
        into the ``multipart/form-data`` content as headers. ::

            # POST request with form values and customized upload (filename and header)
            tx = t.tx(
                'POST',
                'http://example.com',
                form={
                    'a': 'b',
                    'c': 'd',
                    'mytext': {'content': 'lalala', 'filename': 'foo.txt', 'Content-Type': 'text/plain'},
                },
            )

        The ``multipart/form-data`` content type can also be enforced by
        setting the ``Content-Type`` header manually. ::

            # Force "multipart/form-data"
            headers = {'Content-Type': 'multipart/form-data'}
            tx = t.tx('POST', 'example.com', headers, form={'a': 'b'})

        The ``multipart`` content generator can be used to build custom
        multipart requests and does not set a content type. ::

            # POST request with multipart content ("foo" and "bar")
            tx = t.tx('POST', 'http://example.com', multipart=['foo', 'bar'])

        Similar to the ``form`` content generator you can also pass dicts with
        ``content`` or ``file`` values, as well as headers. ::

            # POST request with multipart content streamed from file
            tx = t.tx('POST', 'http://example.com', multipart=[{'file': '/foo.txt'}])

            # PUT request with multipart content streamed from asset
            headers = {'Content-Type': 'multipart/custom'}
            asset = Pyjo.Asset.Memory.new().add_chunk(b'lalala')
            tx = t.tx('PUT', 'http://example.com', headers, multipart=[{'file': asset}])

            # POST request with multipart content and custom headers
            tx = t.tx(
                'POST',
                'http://example.com',
                multipart=[
                    {'content': 'Hello', 'Content-Type': 'text/plain', 'Content-Language': 'en-US'},
                    {'content': 'World!', 'Content-Type': 'text/plain', 'Content-Language': 'en-US'},
                ],
            )

        Values of the form and of the multipart content that are ``bytes`` are
        sent as they are, and a ``str`` is encoded with the charset, as UTF-8
        without one.
        """
        # Method and URL
        tx = Pyjo.Transaction.HTTP.new()
        req = tx.req
        req.method = method
        if isinstance(url, Pyjo.URL.object):
            req.url = url
        # Not in Mojolicious: a URL of urllib.parse
        elif isinstance(url, SplitResult):
            req.url = Pyjo.URL.new(url)
        else:
            req.url.parse(url if re.search(r'^/|://', url) else f'http://{url}')

        # Headers (we identify ourselves and accept gzip compression)
        headers = req.headers
        if args and isinstance(args[0], Mapping):
            headers.from_dict(dict(args[0]))
            args = args[1:]
        if not headers.user_agent:
            headers.user_agent = self.name
        if not self.compressed:
            tx.res.content.auto_decompress = False
        elif not headers.accept_encoding:
            headers.accept_encoding = 'gzip'

        # Generator
        if generator:
            if not (names := [name for name in generator if name in self.generators]):
                raise TypeError(f'Unknown generator: {", ".join(generator)}')
            data = generator.pop(names[0])
            self.generators[names[0]](self, tx, data, **generator)

        # Body
        elif args:
            body = args[0]
            # Not in Mojolicious: a str is encoded as UTF-8
            req.body = body.encode() if isinstance(body, str) else bytes(cast(bytes, body))

        return tx

    def upgrade(self, tx: Pyjo.Transaction.HTTP.object) -> Pyjo.Transaction.WebSocket.object | None:
        """::

            tx = t.upgrade(Pyjo.Transaction.HTTP.new())

        Build :mod:`Pyjo.Transaction.WebSocket` follow-up transaction for
        WebSocket handshake if possible.
        """
        code = tx.res.code or 0
        if not tx.req.is_handshake or code != 101:
            return None
        ws = Pyjo.Transaction.WebSocket.new(handshake=tx, masked=True)
        if not challenge(ws):
            return None
        ws.established = True
        return ws

    def websocket(
        self, url: str | Pyjo.URL.object | SplitResult, *args: Mapping[str, Any] | Sequence[str]
    ) -> Pyjo.Transaction.HTTP.object:
        """::

            tx = t.websocket('ws://example.com')
            tx = t.websocket('ws://example.com', {'DNT': 1}, ['v1.proto'])

        Versatile :mod:`Pyjo.Transaction.HTTP` transaction builder for
        WebSocket handshake requests.
        """
        # New WebSocket transaction
        sub: list[str] = []
        if args and isinstance(args[-1], list):
            sub, args = args[-1], args[:-1]
        tx = self.tx('GET', url, *cast(tuple[Mapping[str, Any], ...], args))
        req = tx.req
        if sub:
            req.headers.sec_websocket_protocol = ', '.join(sub)

        # Handshake protocol
        url = req.url
        proto = url.protocol or ''
        if proto == 'ws':
            url.scheme = 'http'
        elif proto == 'wss':
            url.scheme = 'https'
        elif proto == 'ws+unix':
            url.scheme = 'http+unix'

        return client_handshake(tx)


def _content(headers: Pyjo.Headers.object, parts: list[Pyjo.Content.object]) -> Pyjo.Content.MultiPart.object:
    return Pyjo.Content.MultiPart.new(headers=headers, parts=parts)


def _form(
    t: Pyjo_UserAgent_Transactor,
    tx: Pyjo.Transaction.HTTP.object,
    form: Mapping[str, Any],
    *,
    charset: str | None = 'UTF-8',
) -> Pyjo.Transaction.HTTP.object:
    # Check for uploads and force multipart if necessary
    req = tx.req
    headers = req.headers
    multipart = bool(re.search(r'multipart/form-data', headers.content_type or '', re.I))
    for value in (v for values in form.values() for v in _list(values)):
        if isinstance(value, Mapping):
            multipart = True
            break

    # Multipart
    if multipart:
        req.content = _content(headers, _form_parts(charset, form))
        _type(headers, 'multipart/form-data')
        return tx

    # Query parameters or urlencoded
    method = req.method.upper()
    pairs = [item for name in sorted(form) for item in (name, form[name])]
    if method == 'GET' or method == 'HEAD':
        req.url.query.merge(*pairs)
    else:
        params = Pyjo.Parameters.new(*pairs)
        params.charset = charset
        req.body = params.to_str().encode()
        _type(headers, 'application/x-www-form-urlencoded')

    return tx


def _form_parts(charset: str | None, form: Mapping[str, Any]) -> list[Pyjo.Content.object]:
    parts: list[Pyjo.Content.object] = []
    for name in sorted(form):
        if (values := form[name]) is None:
            continue
        parts.extend(_parts(charset, name, _list(values)))

    return parts


def _json(
    t: Pyjo_UserAgent_Transactor, tx: Pyjo.Transaction.HTTP.object, data: Anything
) -> Pyjo.Transaction.HTTP.object:
    tx.req.body = encode_json(data)
    _type(tx.req.headers, 'application/json')
    return tx


def _list(values: Anything) -> list[Any]:
    return list(cast(list[Any], values)) if isinstance(values, (list, tuple)) else [values]


def _multipart(
    t: Pyjo_UserAgent_Transactor, tx: Pyjo.Transaction.HTTP.object, parts: list[Any]
) -> Pyjo.Transaction.HTTP.object:
    req = tx.req
    req.content = _content(req.headers, _parts(None, None, parts))
    return tx


def _parts(charset: str | None, name: str | None, values: list[Any]) -> list[Pyjo.Content.object]:
    parts: list[Pyjo.Content.object] = []
    for value in values:
        part = Pyjo.Content.Single.new()
        parts.append(part)

        filename: str | None = None
        headers = part.headers
        if isinstance(value, Mapping):
            # Unlike Mojolicious: the values are taken from a copy, where Mojo deletes them from the hash of the caller
            value = dict(cast(Mapping[str, Any], value))

            # File
            if file := value.pop('file', None):
                if not isinstance(file, Pyjo.Asset.object):
                    file = Pyjo.Asset.File.new(path=os.fspath(cast(str, file)))
                part.asset = file
                if isinstance(file, Pyjo.Asset.File.object) and value.get('filename') is None:
                    value['filename'] = Pyjo.File.path(file.path).basename()

            # Memory
            elif (content := value.pop('content', None)) is not None:
                part.asset = Pyjo.Asset.Memory.new().add_chunk(_bytes(content, None))

            # Filename and headers
            filename = value.pop('filename', None)
            headers.from_dict(value)
            if name is None:
                continue
            filename = url_escape(filename if filename is not None else name, '"')
            if charset:
                filename = encode(charset, filename).decode('latin-1')

        # Field
        else:
            part.asset = Pyjo.Asset.Memory.new().add_chunk(_bytes(value, charset))

        # Content-Disposition
        if name is None or headers.content_disposition is not None:
            continue
        name = url_escape(name, '"')
        if charset:
            name = encode(charset, name).decode('latin-1')
        disposition = f'form-data; name="{name}"'
        if filename is not None:
            disposition += f'; filename="{filename}"'
        headers.content_disposition = disposition

    return parts


# Not in Mojolicious: bytes are taken as they are, and other values are encoded with the charset, as UTF-8 without one
def _bytes(value: Anything, charset: str | None) -> bytes:
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    return encode(charset or 'UTF-8', str(value))


def _proxy(tx: Pyjo.Transaction.object, proto: str, host: str | None, port: int) -> tuple[str, str | None, int]:
    req = tx.req
    if req.via_proxy and (proxy := req.proxy) is not None:
        return proxy.protocol, proxy.ihost, proxy.port if proxy.port is not None else (443 if proto == 'https' else 80)

    return proto, host, port


def _type(headers: Pyjo.Headers.object, content_type: str) -> None:
    if not headers.content_type:
        headers.content_type = content_type


new = Pyjo_UserAgent_Transactor.new
object = Pyjo_UserAgent_Transactor
Transactor = Pyjo_UserAgent_Transactor
