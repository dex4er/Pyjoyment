"""
Pyjo.JSON.RPC - JSON-RPC 2.0
============================
::

    from Pyjo.JSON.RPC import RPC

    rpc = RPC()

    @rpc.method
    def subtract(minuend: int, subtrahend: int) -> int:
        \"\"\"Subtract two numbers.\"\"\"
        return minuend - subtrahend

    # {'jsonrpc': '2.0', 'result': 19, 'id': 1}
    rpc.dispatch_p({'jsonrpc': '2.0', 'method': 'subtract', 'params': [42, 23], 'id': 1}).then(print).wait()

    # Or import the module, as in Google Python Style Guide

    import Pyjo.JSON.RPC

    rpc = Pyjo.JSON.RPC.new()
    rpc.method('subtract', lambda minuend, subtrahend: minuend - subtrahend)

    # A route of an application of Pyjoyment.Lite
    post('/rpc', rpc.to_action())

    # A client, which sends its requests with a user agent
    client = Pyjo.JSON.RPC.Client.new(lambda request: ua.post_p('/rpc', json=request).then(lambda tx: tx.res.json()))
    client.call_p('subtract', 42, 23).then(print).wait()

:mod:`Pyjo.JSON.RPC` is an implementation of `JSON-RPC 2.0
<https://www.jsonrpc.org/specification>`_, the requests, the notifications,
the responses and the batches of a server, which calls the methods that it
has, and of a client. It knows the messages, not how they travel: a message
is a value as :mod:`Pyjo.JSON` decodes it, or the JSON of one, and a server
or a client carries it over HTTP, as :meth:`~Pyjo_JSON_RPC.to_action` does
for a route of :mod:`Pyjoyment`, or over a stream of messages in both
directions, as :meth:`~Pyjo_JSON_RPC.serve` does for the standard input and
output of :mod:`Pyjo.IOLoop.Stdio` or a WebSocket, where both peers are
servers and clients.

A method gets the ``params`` of a request, the members of an array as its
positional arguments and those of an object as its keyword arguments, and
returns the ``result`` of the response, as a value, a :mod:`Pyjo.Promise` of
it, or a coroutine, of an ``async def``. A method that raises :class:`Error`
gives that error, and one that raises another exception gives ``-32603``,
``Internal error``, without its message, which the event ``exception`` gets.
The ``params`` that the parameters of a method do not take give ``-32602``,
``Invalid params``, and so do those that its JSON Schema does not validate,
with the errors of :mod:`Pyjo.JSON.Schema` as its ``data``. ::

    # {'jsonrpc': '2.0', 'error': {'code': -32602, 'message': 'Invalid params',
    #  'data': '/subtrahend: Expected integer - got string.'}, 'id': 2}
    @rpc.method('subtract', schema=True)
    def subtract(minuend: int, subtrahend: int) -> int:
        return minuend - subtrahend

    rpc.dispatch_p({'jsonrpc': '2.0', 'method': 'subtract', 'params': [42, 'x'], 'id': 2}).then(print).wait()

A notification, a request without an ``id``, gets no response, also when it
fails, and neither does a batch of notifications. A batch is answered with the
responses of its requests in one array, once the last of them is there.

See also
--------

:mod:`Pyjo.JSON`, :mod:`Pyjo.JSON.Schema`, https://mojolicious.org.

It has no counterpart in Mojolicious, and is written from the specification of
JSON-RPC 2.0.

Classes
-------
"""

import Pyjo.Base
import Pyjo.EventEmitter
import Pyjo.Exception
import Pyjo.JSON
import Pyjo.JSON.Schema
import Pyjo.Promise

import builtins
import inspect

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Self, cast, overload


if TYPE_CHECKING:
    import Pyjoyment.Controller

type Anything = builtins.object

PARSE_ERROR = -32700
"""The code of the error of a message that is not JSON."""
INVALID_REQUEST = -32600
"""The code of the error of a message that is not a request."""
METHOD_NOT_FOUND = -32601
"""The code of the error of a method that the server does not have."""
INVALID_PARAMS = -32602
"""The code of the error of parameters that the method does not take."""
INTERNAL_ERROR = -32603
"""The code of the error of a method that fails."""

# The messages of the errors of the specification
MESSAGES = {
    PARSE_ERROR: 'Parse error',
    INVALID_REQUEST: 'Invalid Request',
    METHOD_NOT_FOUND: 'Method not found',
    INVALID_PARAMS: 'Invalid params',
    INTERNAL_ERROR: 'Internal error',
}

_MISSING = builtins.object()


class Error(Pyjo.Exception.object):
    """
    An error of JSON-RPC, which a method raises for the response of its
    request, and which rejects the promise of a call of :class:`Client`. ::

        raise Pyjo.JSON.RPC.Error.new(-32000, 'Not enough credit', {'balance': 3})
    """

    def __init__(self, code: int = INTERNAL_ERROR, message: str | None = None, data: Any = _MISSING) -> None:
        """::

            e = Pyjo.JSON.RPC.Error.new(-32000, 'Not enough credit')
            e = Pyjo.JSON.RPC.Error.new(-32000, 'Not enough credit', {'balance': 3})
            e = Pyjo.JSON.RPC.Error.new(Pyjo.JSON.RPC.INVALID_PARAMS)

        Construct a new :class:`Error` object, with the message of the
        specification for one of its codes by default.
        """
        super().__init__(message if message is not None else MESSAGES.get(code, 'Server error'))

        self.code = code
        """::

            code = e.code

        The code of the error, an integer.
        """

        self.data = None if data is _MISSING else data
        """::

            data = e.data

        What the server tells about the error, ``None`` if it tells nothing.
        """

        self._data = data is not _MISSING

    def __json__(self) -> dict[str, Any]:
        """::

            error = e.__json__()

        The error object of a response, as :mod:`Pyjo.JSON` encodes it, with
        ``code``, ``message`` and ``data``, where it has one.
        """
        error: dict[str, Any] = {'code': self.code, 'message': self.message}
        if self._data:
            error['data'] = self.data
        return error

    @classmethod
    def from_json(cls, error: Any) -> Self:
        """::

            e = Pyjo.JSON.RPC.Error.from_json({'code': -32601, 'message': 'Method not found'})

        The :class:`Error` of the error object of a response.
        """
        if not isinstance(error, dict):
            return cls(INTERNAL_ERROR, 'Invalid error', error)
        error_ = cast(dict[str, Any], error)
        code, message = error_.get('code'), error_.get('message')
        return cls(
            code if isinstance(code, int) and not isinstance(code, bool) else INTERNAL_ERROR,
            message if isinstance(message, str) else None,
            error_.get('data', _MISSING),
        )


class _Method:
    """A method of the server, with its signature and its schema."""

    def __init__(self, cb: Callable[..., Any], context: bool, schema: Pyjo.JSON.Schema.object | None) -> None:
        self.cb = cb
        self.context = context
        self.schema = schema
        self.signature = inspect.signature(cb)


class Pyjo_JSON_RPC(Pyjo.EventEmitter.object):
    """
    :mod:`Pyjo.JSON.RPC` inherits all events and methods from
    :mod:`Pyjo.EventEmitter` and implements the following new ones.

    Events
    ------

    ``exception`` ::

        @rpc.on('exception')
        def exception(rpc, e, context):
            ...

    Emitted when a method raises an exception that is not an :class:`Error`,
    which the response does not tell, with the context of the request. ::

        rpc.on('exception', lambda rpc, e, context: print(f'Failed: {e}'))
    """

    def __init__(self) -> None:
        """::

            rpc = Pyjo.JSON.RPC.new()

        Construct a new :mod:`Pyjo.JSON.RPC` object.
        """
        super().__init__()
        self._methods: dict[str, _Method] = {}

    def dispatch_p(self, message: Any, context: Any = None) -> Pyjo.Promise.object:
        """::

            promise = rpc.dispatch_p({'jsonrpc': '2.0', 'method': 'subtract', 'params': [42, 23], 'id': 1})
            promise = rpc.dispatch_p(b'{"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": 1}')
            promise = rpc.dispatch_p(request, context=c)

        Dispatch a request, a notification or a batch, as :mod:`Pyjo.JSON`
        decodes it, or the JSON of one, as :class:`bytes` or :class:`str`, to
        the methods, and return a :mod:`Pyjo.Promise` of the response, or of
        ``None`` for a notification or a batch of notifications. The promise
        is not rejected: an error is a response. ``context`` is what a method
        that asks for it gets, as the controller of :meth:`to_action`. ::

            # {'jsonrpc': '2.0', 'error': {'code': -32601, 'message': 'Method not found'}, 'id': 1}
            rpc.dispatch_p({'jsonrpc': '2.0', 'method': 'foobar', 'id': 1}).then(print).wait()
        """

        def exception(e: Exception) -> None:
            self.emit('exception', e, context)

        return self._dispatch_p(message, context, exception)

    @overload
    def method[F: Callable[..., Any]](self, name: F, cb: None = None) -> F: ...

    @overload
    def method[F: Callable[..., Any]](
        self,
        name: str | None = None,
        cb: None = None,
        *,
        context: bool = False,
        schema: bool | dict[str, Any] | Pyjo.JSON.Schema.object | None = None,
    ) -> Callable[[F], F]: ...

    @overload
    def method[F: Callable[..., Any]](
        self,
        name: str,
        cb: F,
        *,
        context: bool = False,
        schema: bool | dict[str, Any] | Pyjo.JSON.Schema.object | None = None,
    ) -> F: ...

    def method(
        self,
        name: str | Callable[..., Any] | None = None,
        cb: Callable[..., Any] | None = None,
        *,
        context: bool = False,
        schema: bool | dict[str, Any] | Pyjo.JSON.Schema.object | None = None,
    ) -> Any:
        """::

            cb = rpc.method('subtract', lambda minuend, subtrahend: minuend - subtrahend)
            cb = rpc.method('whoami', lambda c: c.req.headers.user_agent, context=True)
            cb = rpc.method('subtract', subtract, schema=True)
            cb = rpc.method('subtract', subtract, schema={'type': 'object'})

        Add a method, and return its callback. Without a callback, it is a
        decorator, with the name of the method or of the function. ::

            @rpc.method
            def subtract(minuend: int, subtrahend: int) -> int:
                return minuend - subtrahend

            @rpc.method('math.add', schema=True)
            def add(a: int, b: int) -> int:
                return a + b

        With ``context``, the method gets the context of the request before
        its parameters, as the controller of :meth:`to_action`. ``schema``
        validates the parameters with a :mod:`Pyjo.JSON.Schema` object or a
        schema of its own, or, with ``True``, with
        :meth:`~Pyjo.JSON.Schema.Pyjo_JSON_Schema.parameters` of the function,
        the schema of its type hints. Positional parameters are validated as
        the members of an object that the names of the parameters of the
        function have.
        """
        if callable(name):
            return self.method(name.__name__, name, context=context, schema=schema)
        if cb is None:

            def decorator(cb: Callable[..., Any]) -> Callable[..., Any]:
                return self.method(name if name is not None else cb.__name__, cb, context=context, schema=schema)

            return decorator

        if schema is True:
            compiled = Pyjo.JSON.Schema.parameters(cb, skip=1 if context else 0)
        elif isinstance(schema, Pyjo.JSON.Schema.object):
            compiled = schema
        elif schema:
            compiled = Pyjo.JSON.Schema.new(schema)
        else:
            compiled = None
        self._methods[name or cb.__name__] = _Method(cb, context, compiled)
        return cb

    @property
    def methods(self) -> list[str]:
        """::

            names = rpc.methods

        The names of the methods, in the order that they were added.
        """
        return list(self._methods)

    def serve(
        self, peer: Any, context: Any = None, *, dispatch_p: Callable[[Any, 'Client'], Any] | None = None
    ) -> 'Client':
        """::

            client = rpc.serve(messages)
            client = rpc.serve(messages, context=app)
            client = rpc.serve(messages, dispatch_p=lambda message, client: rpc.dispatch_p(message, {'client': client}))

        Serve the methods to a peer on a stream of messages in both directions,
        as a :mod:`Pyjo.IOLoop.Messages` object, a
        :mod:`Pyjo.Transaction.WebSocket` object or the controller of a
        WebSocket, anything with the event ``message`` and the method
        ``send``, and return the :class:`Client` of the peer, whose requests
        go on the same stream, so that both peers are servers and clients.

        A message that is a response to a call of the client settles it, and a
        response to no call is dropped, as an error of it would go back and
        forth between two peers. Any other message is dispatched, with
        ``context``, the client by default, so that a method that asks for it
        calls the peer back, and its response is sent once it is there: the
        requests are served at the same time, and their responses may go out
        in another order.

        The event ``end`` of the peer, the end of its input, rejects the calls
        of the client, which get no response anymore, and closes the peer
        gracefully once the requests in progress have their responses, and the
        events ``close`` and ``finish`` reject them too.

        ``dispatch_p`` is a function that dispatches each message in the place
        of :meth:`dispatch_p` with ``context``, which the function chooses
        itself, so it is an error to give both. It gets the message, as
        :mod:`Pyjo.JSON` decodes it, which is not a response, and the client,
        and returns the response, a :mod:`Pyjo.Promise` of it, or a coroutine,
        or ``None`` for a notification, so that a protocol on JSON-RPC gives
        each request a context of its own or rules of its own. A function that
        raises, or whose promise is rejected, gives ``-32603``, ``Internal
        error``, to the requests of the message that have an ``id``, and the
        event ``exception``, with the client as the context. ::

            # Standard input and output, whose method asks the client
            @rpc.method(context=True)
            def greet(client, name):
                return client.call_p('confirm', f'Greet {name}?').then(lambda yes: f'Hello, {name}!' if yes else 'Bye')

            messages = Pyjo.IOLoop.Messages.new(Pyjo.IOLoop.Stdio.new())
            rpc.serve(messages)
            messages.start()

            # A WebSocket of Pyjoyment.Lite
            websocket('/rpc', lambda c: rpc.serve(c))

            # A context of its own for each request, and no batches
            def dispatch_p(message, client):
                if isinstance(message, list):
                    return {'jsonrpc': '2.0', 'error': {'code': -32600, 'message': 'No batches'}, 'id': None}
                return rpc.dispatch_p(message, {'client': client})

            rpc.serve(messages, dispatch_p=dispatch_p)
        """
        if context is not None and dispatch_p is not None:
            raise Pyjo.Exception.new('The context of serve is the one of its dispatch_p, not both')
        client = Client()
        if context is None:
            context = client
        pending = 0
        ended = False

        def send(message: Any) -> None:
            peer.send(Pyjo.JSON.to_json(message))

        def exception(e: Exception) -> None:
            self.emit('exception', e, context)

        def respond(response: Any = None) -> None:
            nonlocal pending
            pending -= 1
            if response is not None:
                send(response)
            if ended and not pending:
                peer.close_gracefully()

        def dispatch(message: Any, client: Client) -> Any:
            if isinstance(message, list):
                return self._dispatch_p(message, context, exception)
            return self._request_p(message, context, exception)

        def message(peer: Any, message: Any) -> None:
            nonlocal pending
            try:
                decoded = Pyjo.JSON.decode_json(message)
            except ValueError:
                send(_response(None, error=Error(PARSE_ERROR)))
                return
            if not isinstance(decoded, str) and client.receive(decoded) or _is_response(decoded):
                return
            pending += 1

            # A function that fails answers the requests with an id, which wait for their responses
            def failed(e: Any = None) -> None:
                exception(e if isinstance(e, Exception) else Pyjo.Exception.new(e))
                respond(_internal_errors(decoded))

            try:
                response = (dispatch_p or dispatch)(decoded, client)
                if inspect.iscoroutine(response):
                    response = Pyjo.Promise.new(response)
            except Exception as e:
                response = Pyjo.Promise.reject(e)
            if not isinstance(response, Pyjo.Promise.object):
                response = Pyjo.Promise.resolve(response)
            response.then(respond, failed)

        def end(peer: Any) -> None:
            nonlocal ended
            ended = True
            client.fail(Pyjo.Exception.new('End of input'))
            if not pending:
                peer.close_gracefully()

        def close(peer: Any, *args: Any) -> None:
            client.fail(Pyjo.Exception.new('Connection closed'))

        client.send = send
        peer.on('message', message)
        peer.on('end', end)
        peer.on('close', close)
        peer.on('finish', close)
        return client

    def to_action(self) -> Callable[['Pyjoyment.Controller.object'], Pyjo.Promise.object]:
        """::

            action = rpc.to_action()

        The action of a route of :mod:`Pyjoyment`, which dispatches the body
        of the request, with the controller as the context, and renders the
        response in JSON, ``202 Accepted`` without a body for a notification
        or a batch of notifications, and ``400 Bad Request`` for a body that is
        not JSON or not a request. A method that fails is logged. ::

            # Pyjoyment.Lite
            post('/rpc', rpc.to_action())

            # Pyjoyment
            app.routes.post('/rpc').to(cb=rpc.to_action())
        """

        def action(c: 'Pyjoyment.Controller.object') -> Pyjo.Promise.object:
            def exception(e: Exception) -> None:
                c.helpers.log().error(Pyjo.Exception.new(e).inspect())
                self.emit('exception', e, c)

            def respond(response: Any = None) -> None:
                if response is None:
                    c.rendered(202)
                    return
                error = _member(response, 'error') if _member(response, 'id') is None else None
                status = 400 if _member(error, 'code') in (PARSE_ERROR, INVALID_REQUEST) else 200
                c.render(json=response, status=status)

            c.render_later()
            return self._dispatch_p(c.req.body, c, exception).then(respond)

        return action

    def _call(self, request: dict[str, Any], context: Any) -> Any:
        # The result of a method, or the error of its request
        if (method := self._methods.get(request['method'])) is None:
            raise Error(METHOD_NOT_FOUND)
        params: list[Any] | dict[str, Any] = request.get('params', [])
        args: list[Any] = params if isinstance(params, list) else []
        kwargs: dict[str, Any] = params if isinstance(params, dict) else {}
        try:
            bound = method.signature.bind(*([context] if method.context else []), *args, **kwargs)
        except TypeError as e:
            raise Error(INVALID_PARAMS, data=str(e)) from None

        if (schema := method.schema) is not None:
            arguments: dict[str, Any] = {}
            for i, (name, value) in enumerate(bound.arguments.items()):
                if method.context and not i:
                    continue
                if method.signature.parameters[name].kind is inspect.Parameter.VAR_KEYWORD:
                    arguments.update(value)
                else:
                    arguments[name] = value
            if not (result := schema.validate(arguments)):
                raise Error(INVALID_PARAMS, data=str(result))

        value = method.cb(*bound.args, **bound.kwargs)
        if inspect.iscoroutine(value):
            value = Pyjo.Promise.new(value)
        return value

    def _dispatch_p(self, message: Any, context: Any, exception: Callable[[Exception], None]) -> Pyjo.Promise.object:
        if isinstance(message, bytes | bytearray | str):
            try:
                message = Pyjo.JSON.decode_json(message)
            except ValueError:
                return Pyjo.Promise.resolve(_response(None, error=Error(PARSE_ERROR)))

        # A batch, whose responses come together, without the notifications
        if isinstance(message, list):
            if not message:
                return Pyjo.Promise.resolve(_response(None, error=Error(INVALID_REQUEST)))
            promises = [self._request_p(request, context, exception) for request in cast(list[Any], message)]
            return Pyjo.Promise.all(*promises).then(
                lambda *results: [r[0] for r in results if r and r[0] is not None] or None
            )

        return self._request_p(message, context, exception)

    def _request_p(self, request: Any, context: Any, exception: Callable[[Exception], None]) -> Pyjo.Promise.object:
        if not _is_request(request):
            id = _member(request, 'id')
            return Pyjo.Promise.resolve(_response(id if _is_id(id) else None, error=Error(INVALID_REQUEST)))
        notification = 'id' not in request
        id = request.get('id')

        def result(value: Any = None) -> Any:
            return None if notification else _response(id, result=value)

        def error(e: Any = None) -> Any:
            if not isinstance(e, Error):
                exception(e if isinstance(e, Exception) else Pyjo.Exception.new(e))
                e = Error(INTERNAL_ERROR)
            return None if notification else _response(id, error=e)

        try:
            value = self._call(request, context)
        except Exception as e:
            return Pyjo.Promise.resolve(error(e))
        if isinstance(value, Pyjo.Promise.object):
            return value.then(result, error)
        return Pyjo.Promise.resolve(result(value))


class Client(Pyjo.Base.object):
    """
    A client of JSON-RPC, which sends its requests with a function of the
    transport, and settles the promise of a call with the response that
    comes back, from what the function returns or from :meth:`receive`. ::

        # HTTP, whose response comes back from the request
        client = Pyjo.JSON.RPC.Client.new(lambda request: ua.post_p(url, json=request).then(lambda tx: tx.res.json()))

        # A WebSocket, whose responses come back on their own
        client = Pyjo.JSON.RPC.Client.new(lambda request: ws.send({'json': request}))
        ws.on('json', lambda ws, message: client.receive(message))
    """

    def __init__(self, send: Callable[[dict[str, Any]], Any] | None = None) -> None:
        """::

            client = Pyjo.JSON.RPC.Client.new()
            client = Pyjo.JSON.RPC.Client.new(send)

        Construct a new :class:`Client` object.
        """
        self.send = send
        """::

            send = client.send
            client.send = lambda request: ...

        The function of the transport, which gets a request or a notification,
        and returns the response, as :meth:`receive` takes it, or a
        :mod:`Pyjo.Promise` of it, or anything else, as ``None``, when the
        response comes back to :meth:`receive`.
        """

        self._id = 0
        self._pending: dict[Any, Pyjo.Promise.object] = {}

    def call_p(self, method: str, *args: Any, **kwargs: Any) -> Pyjo.Promise.object:
        """::

            promise = client.call_p('subtract', 42, 23)
            promise = client.call_p('subtract', minuend=42, subtrahend=23)

        Call a method, with its positional or its keyword arguments as the
        ``params``, and return a :mod:`Pyjo.Promise` of the ``result``, which
        an error of the response rejects with an :class:`Error`. ::

            client.call_p('subtract', 42, 23).then(print).catch(lambda e: print(f'{e.code}: {e.message}')).wait()
        """
        self._id += 1
        id = self._id
        promise = self._pending[id] = Pyjo.Promise.new()
        try:
            response = self._send(_request(method, args, kwargs, id))
        except Exception as e:
            self._pending.pop(id, None)
            return promise.reject(e)

        def received(response: Any = None) -> None:
            if isinstance(response, dict | list | bytes | bytearray | str):
                self.receive(response)

        def failed(e: Any = None) -> None:
            if (pending := self._pending.pop(id, None)) is not None:
                pending.reject(e)

        if isinstance(response, Pyjo.Promise.object):
            response.then(received, failed)
        else:
            received(response)
        return promise

    def fail(self, e: Any) -> None:
        """::

            client.fail(Pyjo.Exception.new('Connection closed'))

        Reject the calls that wait for their responses, as the transport does
        when no response can come anymore, as at its end.
        """
        pending, self._pending = self._pending, {}
        for promise in pending.values():
            promise.reject(e)

    def notify(self, method: str, *args: Any, **kwargs: Any) -> Any:
        """::

            client.notify('update', 1, 2, 3)
            client.notify('update', values=[1, 2, 3])

        Send a notification, a request without a response, and return what
        :attr:`send` returns.
        """
        return self._send(_request(method, args, kwargs))

    def receive(self, message: Any) -> bool:
        """::

            boolean = client.receive({'jsonrpc': '2.0', 'result': 19, 'id': 1})
            boolean = client.receive(b'{"jsonrpc": "2.0", "result": 19, "id": 1}')

        Settle the calls of a response or of a batch of them, as :mod:`Pyjo.JSON`
        decodes it, or the JSON of one, and return whether it was a response to
        a call, so that another message, as a request of the server on the same
        stream, goes elsewhere.
        """
        if isinstance(message, bytes | bytearray | str):
            try:
                message = Pyjo.JSON.decode_json(message)
            except ValueError:
                return False
        responses = cast(list[Any], message) if isinstance(message, list) else [message]
        received = False
        for response in responses:
            if not isinstance(response, dict) or 'method' in response:
                continue
            response_ = cast(dict[str, Any], response)
            id = response_.get('id')
            if not _is_id(id) or (promise := self._pending.pop(id, None)) is None:
                continue
            received = True
            if 'error' in response_:
                promise.reject(Error.from_json(response_['error']))
            else:
                promise.resolve(response_.get('result'))
        return received

    def _send(self, request: dict[str, Any]) -> Any:
        if self.send is None:
            raise Pyjo.Exception.new('No function to send the request')
        return self.send(request)


def _internal_errors(message: Anything) -> Any:
    # The responses of -32603 of the requests of a message with an id, in an array for a batch
    requests: list[Any] = cast(list[Any], message) if isinstance(message, list) else [message]
    responses = [
        _response(request['id'], error=Error(INTERNAL_ERROR))
        for request in requests
        if _is_request(request) and 'id' in request
    ]
    if isinstance(message, list):
        return responses or None
    return responses[0] if responses else None


def _is_id(id: Anything) -> bool:
    return id is None or isinstance(id, str) or (isinstance(id, int | float) and not isinstance(id, bool))


def _is_request(request: Anything) -> bool:
    if not isinstance(request, dict):
        return False
    request_ = cast(dict[str, Any], request)
    return (
        request_.get('jsonrpc') == '2.0'
        and isinstance(request_.get('method'), str)
        and isinstance(request_.get('params', []), list | dict)
        and _is_id(request_.get('id'))
    )


def _is_response(message: Anything) -> bool:
    # A response, or a batch of them, which a server does not answer
    if isinstance(message, list):
        responses = cast(list[Any], message)
        return bool(responses) and all(_is_response(response) for response in responses)
    return isinstance(message, dict) and 'method' not in message and ('result' in message or 'error' in message)


def _member(message: Anything, name: str) -> Any:
    # A member of an object of JSON, or None for another value
    return cast(dict[str, Any], message).get(name) if isinstance(message, dict) else None


def _request(method: str, args: tuple[Any, ...], kwargs: dict[str, Any], id: Any = _MISSING) -> dict[str, Any]:
    if args and kwargs:
        raise Pyjo.Exception.new('The params of JSON-RPC are positional or named, not both')
    request: dict[str, Any] = {'jsonrpc': '2.0', 'method': method}
    if args or kwargs:
        request['params'] = list(args) if args else kwargs
    if id is not _MISSING:
        request['id'] = id
    return request


def _response(id: Any, result: Any = None, error: Error | None = None) -> dict[str, Any]:
    if error is not None:
        return {'jsonrpc': '2.0', 'error': error.__json__(), 'id': id}
    return {'jsonrpc': '2.0', 'result': result, 'id': id}


new = Pyjo_JSON_RPC.new
object = Pyjo_JSON_RPC
RPC = Pyjo_JSON_RPC
