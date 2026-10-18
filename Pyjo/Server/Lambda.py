"""
Pyjo.Server.Lambda - AWS Lambda server
======================================
::

    import Pyjo.Server.Lambda

    server = Pyjo.Server.Lambda.new()


    @server.unsubscribe('request').on('request')
    def request(server, tx):
        # Request
        method = tx.req.method
        path = tx.req.url.path

        # Response
        tx.res.code = 200
        tx.res.headers.content_type = 'text/plain'
        tx.res.body = f'{method} request for {path}!'.encode()

        # Resume transaction
        tx.resume()


    handler = server.to_lambda_app()

:mod:`Pyjo.Server.Lambda` allows :mod:`Pyjoyment` applications to run as
event functions of `AWS Lambda <https://aws.amazon.com/lambda/>`_, whose
handler gets the event of an HTTP request and returns its response, with the
payload formats of API Gateway, of Function URLs and of Application Load
Balancers:

* the format 2.0 of HTTP APIs and Function URLs, whose ``cookies`` are the
  ``Cookie`` header of the request and the ``Set-Cookie`` headers of the
  response, and whose stage, other than ``$default``, is the base path of the
  URL;
* the format 1.0 of REST APIs, whose stage is the base path of the URL, and
  whose decoded parameters of the query are encoded again;
* the events of Application Load Balancers, whose parameters of the query are
  as they were sent, with the headers of multiple values when the target
  group has them, and only the last value of a header otherwise.

The event and the context of the invocation are ``lambda.event`` and
``lambda.context`` of :attr:`~Pyjo.Message.Request.Pyjo_Message_Request.env`
of the request. A body that the event has in Base64 is decoded, and the body
of a response is Base64 too, unless its content type is text, JSON, XML,
JavaScript or YAML that is UTF-8. The handler is synchronous, so the event
loop of :mod:`Pyjo.IOLoop` runs until the response is complete, which can
come later and in chunks, whose framing is left out, as the response of an
event function is the whole body. ::

    # The handler "myapp.handler" of an event function
    handler = Pyjo.Server.Lambda.new(app=app).to_lambda_app()

Events
------

:mod:`Pyjo.Server.Lambda` inherits all events from :mod:`Pyjo.Server`.

Attributes
----------

:mod:`Pyjo.Server.Lambda` inherits all attributes from :mod:`Pyjo.Server`.

See also
--------

:mod:`Pyjoyment.Command.lambda`, :mod:`Pyjo.Server.WSGI`, :mod:`Pyjoyment`,
https://mojolicious.org.

Classes
-------
"""

import Pyjo.Content.Single
import Pyjo.IOLoop
import Pyjo.Parameters
import Pyjo.Server
import Pyjo.Transaction

from Pyjo.Util import url_escape

import base64
import re
import wsgiref.util

from collections.abc import Callable
from typing import Any, cast


type Event = dict[str, Any]
type Response = dict[str, Any]
type Handler = Callable[[Event, Any], Response]

# The content types of a body that is text, which goes as it is, where other bodies go in Base64
_RE_TEXT = re.compile(r'(?:text/|application/(?:[\w.-]+\+)?(?:json|xml|javascript|yaml)\b)', re.I)


class Pyjo_Server_Lambda(Pyjo.Server.object):
    """
    :mod:`Pyjo.Server.Lambda` inherits all methods from :mod:`Pyjo.Server`
    and implements the following new ones.
    """

    # reportIncompatibleMethodOverride "Method "run" overrides class "Pyjo_Server" in an incompatible manner": run takes
    # the event and the context, as the run of Pyjo.Server.WSGI takes the environment
    def run(self, event: Event, context: Any = None) -> Response:  # pyright: ignore[reportIncompatibleMethodOverride]
        """::

            response = server.run(event, context)

        Run the event of an HTTP request and return its response.
        """
        request = _Request(event)
        env = request.environ()
        env['lambda.event'] = event
        env['lambda.context'] = context

        tx = self.build_tx()
        req = tx.req.parse(env)
        tx.remote_address = request.remote_address
        if request.body:
            req.parse(request.body)

        # The response, which the application can give later
        resumed: list[bool] = []

        def resume(tx: Pyjo.Transaction.object) -> None:
            resumed.append(True)

        tx.on('resume', resume)
        self.emit('request', tx)
        while not resumed:
            Pyjo.IOLoop.one_tick()

        # The whole body, which can come in chunks
        res = tx.res.fix_headers()
        body = b''
        offset = 0
        while not tx.is_empty:
            if (chunk := res.get_body_chunk(offset)) is None:
                Pyjo.IOLoop.one_tick()
                continue
            if not len(chunk):
                break
            offset += len(chunk)
            body += chunk
        if res.content.is_chunked:
            body = _unchunk(body)
        tx.closed()

        # The headers without the hop-by-hop ones, as the response is the whole body
        headers = [(name, value) for name, value in res.headers.to_list() if not wsgiref.util.is_hop_by_hop(name)]
        code = res.code or 404
        response = request.headers({'statusCode': code}, headers)
        if request.alb:
            response['statusDescription'] = f'{code} {res.message or res.default_message(code)}'

        # Text as it is, other content in Base64
        content_type = res.headers.content_type or ''
        if not body or _RE_TEXT.match(content_type) and _is_utf8(body):
            response['body'] = body.decode()
            response['isBase64Encoded'] = False
        else:
            response['body'] = base64.b64encode(body).decode('ascii')
            response['isBase64Encoded'] = True
        return response

    def to_lambda_app(self) -> Handler:
        """::

            handler = server.to_lambda_app()

        Turn :mod:`Pyjoyment` application into the handler of an event
        function of AWS Lambda.
        """
        # Preload application and wrap it
        self.app.server(self)

        def handler(event: Event, context: Any) -> Response:
            return self.run(event, context)

        return handler


# The request of an event, in one of its payload formats
class _Request:
    def __init__(self, event: Event) -> None:
        self.event = event
        context: dict[str, Any] = event.get('requestContext') or {}
        self.alb = 'elb' in context
        self.v2 = event.get('version') == '2.0'
        self.pairs: list[tuple[str, str]]

        # The body, which can be in Base64
        body: str | None = event.get('body')
        if body is None:
            self.body = b''
        elif event.get('isBase64Encoded'):
            self.body = base64.b64decode(body)
        else:
            self.body = body.encode()

        # The format 2.0, of HTTP APIs and Function URLs
        if self.v2:
            http: dict[str, Any] = context.get('http') or {}
            self.method: str = http.get('method') or 'GET'
            self.path: str = event.get('rawPath') or '/'
            self.query: str = event.get('rawQueryString') or ''
            self.pairs = _pairs(event.get('headers'))
            if cookies := event.get('cookies'):
                self.pairs.append(('cookie', '; '.join(cookies)))
            self.remote_address: str | None = http.get('sourceIp')
            self.protocol: str | None = http.get('protocol')
            self.https = True

            # A stage other than the default one in front of the path
            stage = context.get('stage')
            prefix = f'/{stage}'
            within = stage and stage != '$default' and (self.path == prefix or self.path.startswith(f'{prefix}/'))
            self.base = prefix if within else None
            return

        # The format 1.0, of REST APIs, and Application Load Balancers
        self.method = event.get('httpMethod') or 'GET'
        self.path = event.get('path') or '/'
        multi = event.get('multiValueHeaders')
        self.pairs = _pairs(multi if multi is not None else event.get('headers'))
        pairs = _pairs(event.get('multiValueQueryStringParameters') or event.get('queryStringParameters'))

        # The parameters of an Application Load Balancer as they were sent, and the decoded ones of a REST API
        if self.alb:
            self.query = '&'.join(f'{name}={value}' for name, value in pairs)
        else:
            query = Pyjo.Parameters.new()
            for name, value in pairs:
                query.append(name, value)
            self.query = query.to_str()
        identity: dict[str, Any] = context.get('identity') or {}
        self.remote_address = identity.get('sourceIp')
        self.protocol = context.get('protocol')
        self.https = any(name.lower() == 'x-forwarded-proto' and value == 'https' for name, value in self.pairs)

        # The stage of a REST API in front of the path
        path: str = context.get('path') or ''
        self.base = path[: -len(self.path)] or None if path != self.path and path.endswith(self.path) else None

    def environ(self) -> dict[str, Any]:
        # The CGI environment that Pyjo.Message.Request parses, with a path whose bytes beyond ASCII are
        # percent-encoded, as the path is escaped
        env: dict[str, Any] = {
            'REQUEST_METHOD': self.method,
            'PATH_INFO': url_escape(self.path.encode(), rb'\x80-\xff').decode('ascii'),
            'QUERY_STRING': self.query,
            'SERVER_PROTOCOL': self.protocol or 'HTTP/1.1',
        }
        if self.base is not None:
            env['SCRIPT_NAME'] = self.base
        if self.https:
            env['HTTPS'] = 'on'
        for name, value in self.pairs:
            key = 'HTTP_' + name.upper().replace('-', '_')

            # The body is whole, without the chunked framing
            if key == 'HTTP_TRANSFER_ENCODING':
                continue
            env[key] = f'{env[key]}{"; " if key == "HTTP_COOKIE" else ", "}{value}' if key in env else value
        if self.body:
            env['CONTENT_LENGTH'] = str(len(self.body))
        return env

    def headers(self, response: Response, pairs: list[tuple[str, str]]) -> Response:
        # The format 2.0 with its cookies, and its other headers of multiple values with commas
        if self.v2:
            headers: dict[str, str] = {}
            cookies: list[str] = []
            for name, value in pairs:
                if (name := name.lower()) == 'set-cookie':
                    cookies.append(value)
                else:
                    headers[name] = f'{headers[name]},{value}' if name in headers else value
            response['headers'] = headers
            if cookies:
                response['cookies'] = cookies

        # The headers of multiple values of the event, or the last value of each header
        elif 'multiValueHeaders' in self.event:
            multi: dict[str, list[str]] = {}
            for name, value in pairs:
                multi.setdefault(name, []).append(value)
            response['multiValueHeaders'] = multi
        else:
            response['headers'] = dict(pairs)
        return response


def _is_utf8(body: bytes) -> bool:
    try:
        body.decode()
    except UnicodeDecodeError:
        return False
    return True


# The pairs of names and values of a dict of the event, whose values can be lists of values
def _pairs(values: Any) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for name, value in cast(dict[str, Any], values or {}).items():
        for item in cast(list[Any], value) if isinstance(value, list) else [value]:
            pairs.append((name, str(item)))
    return pairs


# Chunked content without its framing, as in Pyjo.Server.WSGI
def _unchunk(body: bytes) -> bytes:
    chunks: list[bytes] = []

    def read(content: Pyjo.Content.Single.object, chunk: bytes) -> None:
        chunks.append(chunk)

    parser = Pyjo.Content.Single.new()
    parser.unsubscribe('read').on('read', read)
    parser.parse(b'Transfer-Encoding: chunked\x0d\x0a\x0d\x0a' + body)
    return b''.join(chunks)


new = Pyjo_Server_Lambda.new
object = Pyjo_Server_Lambda
