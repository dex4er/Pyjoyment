"""
Pyjo.Server.FastCGI - FastCGI connections of the servers
========================================================
::

    import Pyjo.Server.Daemon

    daemon = Pyjo.Server.Daemon.new(listen=['fcgi://127.0.0.1:9000'])


    @daemon.unsubscribe('request').on('request')
    def request(daemon, tx):
        # Request
        method = tx.req.method
        path = tx.req.url.path

        # Response
        tx.res.code = 200
        tx.res.headers.content_type = 'text/plain'
        tx.res.body = f'{method} request for {path}!'.encode()

        # Resume transaction
        tx.resume()


    daemon.run()

:mod:`Pyjo.Server.FastCGI` speaks `FastCGI 1.0
<https://fastcgi-archives.github.io/FastCGI_Specification.html>`_ on the
connections of the listen locations ``fcgi://`` and ``fcgi+unix://`` of
:mod:`Pyjo.Server.Daemon`, and so of the servers built on it,
:mod:`Pyjo.Server.Prefork`, :mod:`Pyjo.Server.Hot` and
:mod:`Pyjo.Server.Reload`, with the same applications, timeouts, signals and
graceful shutdown as HTTP. ::

    $ ./myapp.py daemon -l fcgi://127.0.0.1:9000
    $ ./myapp.py prefork -l fcgi+unix://%2Ftmp%2Fmyapp.sock

A web server in front of the application speaks HTTP to the clients and
FastCGI to the application, which gets the request as the environment of
:rfc:`3875`, as :mod:`Pyjo.Server.CGI` does, but in a process that keeps
running. A connection takes one request at a time, in the role of a
responder, the only one that it supports, and stays open after it when the
web server asks for it with ``FCGI_KEEP_CONN``. The content of the response
can come later, as with :mod:`Pyjo.Server.Daemon`, and goes to the web server
as soon as it is written. WebSockets are not available, as FastCGI has no
protocol for them.

The application can also be started by the web server, which gives it its
listen socket as the file descriptor ``0``, as Apache with ``mod_fcgid`` and
lighttpd do; the command :mod:`Pyjoyment.Command.fastcgi` serves it, and is
detected by :mod:`Pyjoyment.Commands`, so the script of the application
needs no command.

Environment
-----------

The request is read from the parameters of FastCGI, as the environment of
CGI that :meth:`Pyjo.Message.Request.Pyjo_Message_Request.parse` takes, with
a few changes for what the web servers send:

* A path in ``SCRIPT_NAME`` without ``PATH_INFO`` is the path of the request,
  as nginx with its ``fastcgi_params`` and Caddy send the whole path in
  ``SCRIPT_NAME``. An application deployed under a path prefix gets it in
  ``SCRIPT_NAME`` and the rest of the path in ``PATH_INFO``.
* The bytes of the paths beyond ASCII are percent-encoded, as the path is
  escaped, as with :mod:`Pyjo.Server.WSGI`.
* A request body without ``CONTENT_LENGTH``, of a chunked request whose
  framing the web server removed, is read whole before the request is parsed.

Web servers
-----------

* Caddy, with ``transport fastcgi``: it sends the response to the client with
  the ``Status`` header next to its status line. ::

    example.com {
      reverse_proxy 127.0.0.1:9000 {
        transport fastcgi
      }
    }

* Apache with ``mod_proxy_fcgi``: ::

    ProxyPass / fcgi://127.0.0.1:9000/ enablereuse=on

* Apache with ``mod_fcgid``, which starts the application: ::

    <VirtualHost *:80>
      ServerName localhost
      ScriptAlias / /home/sri/myapp/myapp.py/
      <Directory /home/sri/myapp>
        SetHandler fcgid-script
        Options +ExecCGI
        Require all granted
      </Directory>
    </VirtualHost>

* nginx: ::

    location / {
      include fastcgi_params;
      fastcgi_pass 127.0.0.1:9000;
      fastcgi_keep_conn on;
    }

See also
--------

:mod:`Pyjoyment.Command.fastcgi`, :mod:`Pyjo.Server.Daemon`, :mod:`Pyjoyment`,
https://mojolicious.org.

It has no counterpart in Mojolicious; :mod:`Pyjo.Server.CGI` is the
counterpart of `Mojo::Server::CGI
<https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/Server/CGI.pm>`_.

Classes
-------
"""

import Pyjo.Base
import Pyjo.Content.Single
import Pyjo.Transaction

from Pyjo.Util import url_escape

import struct
import weakref
import wsgiref.util

from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    import Pyjo.Server.Daemon


# The types of the records
BEGIN_REQUEST = 1
ABORT_REQUEST = 2
END_REQUEST = 3
PARAMS = 4
STDIN = 5
STDOUT = 6
GET_VALUES = 9
GET_VALUES_RESULT = 10
UNKNOWN_TYPE = 11

# The role, the flag of BEGIN_REQUEST and the statuses of END_REQUEST
RESPONDER = 1
KEEP_CONN = 1
REQUEST_COMPLETE = 0
CANT_MPX_CONN = 1
UNKNOWN_ROLE = 3

# The header of a record: version, type, request id, content length, padding length and a reserved byte
HEADER = struct.Struct('>BBHHBx')

# The longest content of a record
MAX_CONTENT = 65535


class Pyjo_Server_FastCGI(Pyjo.Base.object):
    """
    :mod:`Pyjo.Server.FastCGI` is the FastCGI side of a connection of
    :mod:`Pyjo.Server.Daemon`, which makes it for the connections of its
    listen locations ``fcgi://`` and ``fcgi+unix://``.
    """

    def __init__(self, daemon: 'Pyjo.Server.Daemon.object', id: str) -> None:
        """::

            fcgi = Pyjo.Server.FastCGI.new(daemon, id)

        Construct a new :mod:`Pyjo.Server.FastCGI` object for the connection
        ``id`` of the daemon.
        """
        super().__init__()

        self.id = id
        """::

            id = fcgi.id

        Id of the connection in the event loop of the daemon.
        """

        self._daemon = weakref.ref(daemon)
        self._buffer = bytearray()
        self._closing = False
        self._request: dict[str, Any] | None = None
        self._writing = False

    def closed(self) -> None:
        """::

            fcgi.closed()

        The connection has been closed, which finishes the transaction of the
        request in progress.
        """
        self._closing = True
        if (req := self._request) is not None:
            self._finish(req)

    def read(self, chunk: bytes) -> None:
        """::

            fcgi.read(chunk)

        Read the records of a chunk of data from the web server.
        """
        buffer = self._buffer
        buffer += chunk
        while len(buffer) >= HEADER.size and not self._closing:
            version, type, id, length, padding = HEADER.unpack_from(buffer)

            # Not FastCGI
            if version != 1:
                self._trace(f'FastCGI version {version} is not supported')
                return self._close()

            end = HEADER.size + length + padding
            if len(buffer) < end:
                break
            content = bytes(buffer[HEADER.size : HEADER.size + length])
            del buffer[:end]
            self._record(type, id, content)

    def _begin(self, id: int, content: bytes) -> None:
        role, flags = struct.unpack_from('>HB', content)
        keep = bool(flags & KEEP_CONN)

        # One request at a time
        if self._request is not None:
            return self._send(_end(id, CANT_MPX_CONN))

        # Only responders
        if role != RESPONDER:
            self._send(_end(id, UNKNOWN_ROLE))
            if not keep:
                self._close()
            return

        self._request = {'id': id, 'keep': keep, 'params': bytearray()}
        if (daemon := self._daemon()) is not None:
            daemon.ioloop.stream(self.id).timeout = daemon.inactivity_timeout

    def _close(self) -> None:
        self._closing = True
        if (daemon := self._daemon()) is not None and (stream := daemon.ioloop.stream(self.id)) is not None:
            stream.close_gracefully()

    def _env(self, req: dict[str, Any]) -> None:
        if (daemon := self._daemon()) is None:
            return
        env = _environ(_pairs(bytes(req.pop('params'))))

        tx = req['tx'] = daemon.build_tx()
        tx.connection = self.id
        # Unlike Mojolicious: Pyjoyment names itself
        tx.res.headers.server = 'Pyjoyment (Python)'

        # A body of unknown length is read whole before the request is parsed
        if env.get('CONTENT_LENGTH'):
            tx.req.parse(env)
        else:
            req['env'], req['body'] = env, bytearray()

        tx.local_address = env.get('SERVER_ADDR')
        tx.local_port = int(port) if (port := env.get('SERVER_PORT')) else None
        tx.remote_address = env.get('REMOTE_ADDR')
        tx.remote_port = int(port) if (port := env.get('REMOTE_PORT')) else None

    def _finish(self, req: dict[str, Any]) -> None:
        # Once, as an aborted request may still be written
        if req.get('finished'):
            return
        req['finished'] = True
        if self._request is req:
            self._request = None
        if (tx := req.get('tx')) is not None:
            if (resume := req.get('resume')) is not None:
                tx.unsubscribe('resume', resume)
            tx.closed()

        if self._closing:
            return
        if not req['keep']:
            return self._close()
        if (daemon := self._daemon()) is not None and (stream := daemon.ioloop.stream(self.id)) is not None:
            stream.timeout = daemon.keep_alive_timeout

    def _get_values(self, content: bytes) -> None:
        daemon = self._daemon()
        max = daemon.ioloop.max_connections if daemon is not None else 1
        values = {'FCGI_MAX_CONNS': str(max), 'FCGI_MAX_REQS': str(max), 'FCGI_MPXS_CONNS': '0'}
        result = {name: values[name] for name in _pairs(content) if name in values}
        self._send(_record(GET_VALUES_RESULT, 0, _encode_pairs(result)))

    def _record(self, type: int, id: int, content: bytes) -> None:
        # Management records
        if id == 0:
            if type == GET_VALUES:
                return self._get_values(content)
            return self._send(_record(UNKNOWN_TYPE, 0, struct.pack('>B7x', type)))

        if type == BEGIN_REQUEST:
            return self._begin(id, content)

        # Records of another request are ignored, as the ones of a request that is not active
        if (req := self._request) is None or req['id'] != id:
            return

        if type == ABORT_REQUEST:
            self._send(_end(id))
            return self._finish(req)

        if type == PARAMS and 'params' in req:
            if len(content):
                req['params'] += content
            else:
                self._env(req)

        elif type == STDIN and req.get('tx') is not None and 'resume' not in req:
            if (body := req.get('body')) is not None:
                body += content
            elif len(content):
                req['tx'].req.parse(content)
            if not len(content):
                self._request_ready(req)

    def _request_ready(self, req: dict[str, Any]) -> None:
        if (daemon := self._daemon()) is None:
            return
        tx = req['tx']

        # The request of unknown length with its body
        if (body := req.pop('body', None)) is not None:
            env = req.pop('env')
            if len(body):
                env['CONTENT_LENGTH'] = str(len(body))
            tx.req.parse(env)
            if len(body):
                tx.req.parse(bytes(body))

        if error := tx.req.error:
            self._trace(error['message'])

        ref = weakref.ref(self)

        # The response is written once the transaction is resumed, as the content of a response can come later
        def resume(tx: Pyjo.Transaction.object) -> None:
            req['resumed'] = True
            if (this := ref()) is not None:
                this._write()

        req['resume'] = resume
        tx.on('resume', resume)
        daemon.emit('request', tx)
        self._write()

    def _send(self, data: bytes, cb: Any = None) -> None:
        if (daemon := self._daemon()) is not None and (stream := daemon.ioloop.stream(self.id)) is not None:
            stream.write(data, cb)

    def _trace(self, message: str) -> None:
        if (daemon := self._daemon()) is not None:
            daemon.app.log.trace(message)

    def _write(self) -> None:
        # Protect from resume event recursion
        if (req := self._request) is None or not req.get('resumed') or req.get('ended') or self._writing:
            return
        self._writing = True
        try:
            tx = req['tx']
            res = tx.res
            finished = False

            # Response headers, with the status in a header as CGI has it
            if 'offset' not in req:
                res.fix_headers()
                code = res.code or 404
                lines = [f'Status: {code} {res.message or res.default_message()}']
                # Unlike Mojolicious: without the hop-by-hop headers, so chunked content goes without its framing,
                # which the web server adds
                lines += [f'{name}: {value}' for name, value in res.headers.to_list() if not _hop_by_hop(name)]
                data = ('\x0d\x0a'.join(lines) + '\x0d\x0a\x0d\x0a').encode('latin-1')
                req['offset'] = 0
                req['unchunk'] = _Unchunk() if res.content.is_chunked else None
                finished = tx.is_empty

            # Response body
            else:
                chunk = res.get_body_chunk(req['offset'])

                # No content yet, the resume event comes when there is some
                if chunk is None:
                    return
                if not len(chunk):
                    finished = True
                req['offset'] += len(chunk)
                data = req['unchunk'].parse(chunk) if req['unchunk'] is not None else chunk
        finally:
            self._writing = False

        records = b''.join(
            _record(STDOUT, req['id'], data[i : i + MAX_CONTENT]) for i in range(0, len(data), MAX_CONTENT)
        )
        ref = weakref.ref(self)

        # Finish the request
        if finished:
            req['ended'] = True
            records += _record(STDOUT, req['id']) + _end(req['id'])

            def done(stream: Any) -> None:
                if (this := ref()) is not None:
                    this._finish(req)

            return self._send(records, done)

        # Next chunk
        def written(stream: Any) -> None:
            if (this := ref()) is not None:
                this._write()

        self._send(records, written)


# Chunked content without its framing, as in Pyjo.Server.WSGI
class _Unchunk:
    def __init__(self) -> None:
        self._chunks: list[bytes] = []
        self._parser = Pyjo.Content.Single.new()
        self._parser.unsubscribe('read').on('read', self._read)
        self._parser.parse(b'Transfer-Encoding: chunked\x0d\x0a\x0d\x0a')

    def _read(self, content: Pyjo.Content.Single.object, chunk: bytes) -> None:
        self._chunks.append(chunk)

    def parse(self, chunk: bytes) -> bytes:
        self._parser.parse(chunk)
        chunks, self._chunks = self._chunks, []
        return b''.join(chunks)


def _encode_length(value: bytes) -> bytes:
    return struct.pack('>B', len(value)) if len(value) < 128 else struct.pack('>I', len(value) | 0x80000000)


def _encode_pairs(pairs: dict[str, str]) -> bytes:
    data = b''
    for name, value in pairs.items():
        name_bytes, value_bytes = name.encode('latin-1'), value.encode('latin-1')
        data += _encode_length(name_bytes) + _encode_length(value_bytes) + name_bytes + value_bytes
    return data


def _end(id: int, status: int = REQUEST_COMPLETE) -> bytes:
    # The application status of a request is 0, as a process of CGI that exits normally
    return _record(END_REQUEST, id, struct.pack('>IB3x', 0, status))


# The environment of CGI that Pyjo.Message.Request parses, from the parameters that the web server sends
def _environ(params: dict[str, str]) -> dict[str, str]:
    env = dict(params)

    # The whole path in SCRIPT_NAME, as nginx with fastcgi_params and Caddy send it
    if not env.get('PATH_INFO') and env.get('SCRIPT_NAME'):
        env['PATH_INFO'], env['SCRIPT_NAME'] = env['SCRIPT_NAME'], ''

    # A path is bytes as the characters 0-255, so the bytes beyond ASCII are percent-encoded, as the path is escaped
    for key in ('PATH_INFO', 'SCRIPT_NAME'):
        if key in env:
            env[key] = url_escape(env[key].encode('latin-1'), rb'\x80-\xff').decode('ascii')

    # The web server removes the chunked framing of a request
    env.pop('HTTP_TRANSFER_ENCODING', None)
    return env


def _hop_by_hop(name: str) -> bool:
    return wsgiref.util.is_hop_by_hop(name)


# The name-value pairs of FastCGI, whose lengths take one byte, or four with the high bit set, as characters 0-255
def _pairs(data: bytes) -> dict[str, str]:
    pairs: dict[str, str] = {}
    offset = 0
    while offset < len(data):
        lengths: list[int] = []
        for _ in range(2):
            if offset >= len(data):
                return pairs
            if data[offset] < 128:
                lengths.append(data[offset])
                offset += 1
            else:
                lengths.append(struct.unpack_from('>I', data, offset)[0] & 0x7FFFFFFF)
                offset += 4
        name = data[offset : offset + lengths[0]].decode('latin-1')
        offset += lengths[0]
        pairs[name] = data[offset : offset + lengths[1]].decode('latin-1')
        offset += lengths[1]
    return pairs


def _record(type: int, id: int, content: bytes = b'') -> bytes:
    padding = -len(content) % 8
    return HEADER.pack(1, type, id, len(content), padding) + content + b'\0' * padding


new = Pyjo_Server_FastCGI.new
object = Pyjo_Server_FastCGI
FastCGI = Pyjo_Server_FastCGI
