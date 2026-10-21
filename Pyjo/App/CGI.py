"""
Pyjo.App.CGI - CGI application
==============================
::

    from Pyjo.App.CGI import CGI

    app = CGI(script='/usr/lib/cgi-bin/hello.cgi')

    # Or import the module, as in Google Python Style Guide

    import Pyjo.App.CGI

    app = Pyjo.App.CGI.new(script='/usr/lib/cgi-bin/hello.cgi')

    # The programs of a directory, as cgi-bin
    app = Pyjo.App.CGI.new(document_root='/usr/lib/cgi-bin')

    # PHP on php-cgi, with the files of its directory
    app = Pyjo.App.CGI.new(
        command=['php-cgi'], document_root='/var/www', script_extensions=['.php'], static=True
    )

    # Mount it in an application of Pyjoyment
    import Pyjoyment

    pyjoyment = Pyjoyment.new()
    pyjoyment.plugin('Mount', {'/cgi-bin': app})

:mod:`Pyjo.App.CGI` is an application of :mod:`Pyjo` that runs a ``CGI``
program, as :rfc:`3875` describes it, in a process of its own for each
request, so that a server of :mod:`Pyjo` serves it, a route of
:mod:`Pyjoyment` embeds it, as :mod:`Pyjoyment.Plugin.Mount` does, and
:mod:`Pyjo.Test.Pyjo` tests it.

The environment of the process is the one of ``CGI`` of the request: the part
of the path that a route embeds the application under is ``SCRIPT_NAME``, after
the base path of the request, which a part of the path that does not end with
a slash, as ``/cgi`` of ``/cgix``, cannot be, so that the application is not
found there, the rest of the path is ``PATH_INFO``, ``REQUEST_URI`` is the path
with the query, without the header ``Proxy``, whose ``HTTP_PROXY`` a program
may take for the proxy of its own requests, as with httpoxy, with ``PATH`` of
the process of Pyjoyment, and :attr:`env` adds to them. The program runs in
the directory of its file, and the body of the request goes to its standard
input, each chunk once the one before has been written.

The standard output of the program is its response of ``CGI``, read through
the event loop, as it comes. A response that comes whole, before the program
closes its standard output, is written with its ``Content-Length``. Another one
is written as it comes, each chunk once the one before has been written to the
client, with the chunked transfer encoding when it does not give its
``Content-Length``. What the program writes to its standard error is logged.

A program that does not start or ends before its response is a response
``502``, and one that ends otherwise after the start of the response closes
the connection of the client, as one that is quiet for longer than
:attr:`inactivity_timeout` does, which, until the response starts, the
connection of the client waits for without the inactivity timeout of the
server. The process of a request whose client is gone is killed.

The event loop watches the pipes of the process, which it can on POSIX
systems, not on Windows, where the response is ``502``.

Attributes
----------

:mod:`Pyjo.App.CGI` inherits all attributes from :mod:`Pyjo.App` and
implements the following new ones.

See also
--------

:mod:`Pyjoyment`, :mod:`Pyjoyment.Plugin.Mount`, :mod:`Pyjo.App.FastCGI`,
:mod:`Pyjo.Server.CGI`, https://mojolicious.org.

It has no counterpart in Mojolicious; it is the reverse of
:mod:`Pyjo.Server.CGI`, inspired by ``Mojolicious::Plugin::CGI`` of CPAN.

Classes
-------
"""

import Pyjo.App
import Pyjo.Exception
import Pyjo.IOLoop
import Pyjo.IOLoop.Stream
import Pyjo.Transaction

import atexit
import functools
import os
import re
import subprocess
import wsgiref.util

from typing import Any


# The headers of a response by X-Sendfile that the file takes the place of
_SENT = ('content-length', 'x-sendfile')

# The processes that the event loop has not reaped yet, which the end of the interpreter kills and reaps, as Python
# warns of a process that still runs when it frees its object
_processes: set[subprocess.Popen[bytes]] = set()


class Pyjo_App_CGI(Pyjo.App.object):
    """
    :mod:`Pyjo.App.CGI` inherits all methods from :mod:`Pyjo.App` and
    implements the following new ones.
    """

    def __init__(self, attrs: dict[str, Any] | None = None, /, **kwargs: Any) -> None:
        """::

            app = Pyjo.App.CGI.new(script='/usr/lib/cgi-bin/hello.cgi')

        Construct a new :mod:`Pyjo.App.CGI` object.
        """
        self.command: list[str] | None = None
        """::

            command = app.command
            app.command = ['php-cgi']

        Command that runs the script, with its file as the last argument, as an
        interpreter, the script itself otherwise, which has to be executable.
        With it, ``REDIRECT_STATUS`` is ``200``, as Apache gives it to the
        command of ``Action``, without which php-cgi runs no script.
        """

        self.document_root: str | os.PathLike[str] | None = None
        """::

            root = app.document_root
            app.document_root = '/usr/lib/cgi-bin'

        Directory of the scripts, which takes the script of each request from
        its path, as a web server does: the path after the mount, up to its
        first part that is a file of the directory, or that ends with one of
        :attr:`script_extensions`, names the script, whose file is
        ``SCRIPT_FILENAME`` and whose path after the mount is ``SCRIPT_NAME``,
        the rest of the path is ``PATH_INFO``, and a path that ends with a
        slash names ``index`` with the first of :attr:`script_extensions` in
        it, as ``index.php``. A path with ``..``, or that names no file, or no
        script of :attr:`script_extensions`, is not found. With :attr:`script`, a path that names no script of the
        directory is the one of :attr:`script`, as the one entry of an
        application that takes every path, as with ``try_files`` of nginx.
        ``SCRIPT_FILENAME`` of :attr:`env` takes its place.
        """

        self.env: dict[str, str] = {}
        """::

            env = app.env
            app.env = {'PERL5LIB': '/usr/local/lib/perl5'}

        Variables that are added to the environment of ``CGI`` of each
        request, and replace the ones of the same name.
        """

        self.inactivity_timeout: float = 60
        """::

            timeout = app.inactivity_timeout
            app.inactivity_timeout = 300

        Maximum amount of time in seconds the standard output of the program
        can be inactive before the process gets killed, defaults to ``60``.
        Until the response starts, the connection of the client waits for it
        without the inactivity timeout of the server, so that this one gives
        the response ``502`` to a program that takes longer.
        """

        self.nph: bool | None = None
        """::

            boolean = app.nph
            app.nph = True

        The program writes the start line of an HTTP response, in non-parsed
        header mode, as :mod:`Pyjo.Server.CGI` does with its attribute ``nph``,
        which takes the place of the header ``Status``, true by default for a
        script whose file name starts with ``nph-``, as web servers have it.
        """

        self.script: str | None = None
        """::

            script = app.script
            app.script = '/usr/lib/cgi-bin/hello.cgi'
            app.script = 'index.php'

        Script of the application for every path, with the path after the
        mount as ``PATH_INFO``, or for every path that names no script of
        :attr:`document_root`, in which it is then.
        """

        self.script_extensions: list[str] | None = None
        """::

            extensions = app.script_extensions
            app.script_extensions = ['.php']

        Extensions of the names of the scripts of :attr:`document_root`, every
        file of which is a script without them, as cgi-bin.
        """

        self.sendfile: str | os.PathLike[str] | None = None
        """::

            directory = app.sendfile
            app.sendfile = '/var/www/private'

        Directory of the files that the program may reply with by the header
        ``X-Sendfile``, as Apache and lighttpd take it, with the path of the
        file, as the private files that are not in :attr:`document_root`, or
        :attr:`document_root` with :attr:`static`, none otherwise. A route that
        embeds the application replies then with the file, as the helper
        ``reply.file`` of :mod:`Pyjoyment` does, with the status and the other
        headers of the program, and a file that is not in the directory is not
        found.
        """

        self.static: bool = False
        """::

            boolean = app.static
            app.static = True

        Reply with a file of :attr:`document_root` for a path that names it and
        no script of :attr:`script_extensions`, as ``try_files`` of nginx does,
        as the helper ``reply.file`` of :mod:`Pyjoyment` does, with ranges and
        conditional requests, false by default. A route that embeds the
        application replies with them, as :mod:`Pyjoyment.Plugin.Mount` makes.
        """

        super().__init__(attrs, **kwargs)

    def handler(self, tx: Any) -> None:
        """::

            app.handler(Pyjo.Transaction.HTTP.new())
            app.handler(Pyjoyment.Controller.new())

        Run the program for the request of the transaction, or of the
        controller of a route that embeds the application, and write its
        response.
        """
        if self.script is None and self.document_root is None and 'SCRIPT_FILENAME' not in self.env:
            raise Pyjo.Exception.new('No CGI application')
        config = {
            'extensions': self.script_extensions,
            'inactivity': self.inactivity_timeout,
            'root': os.fspath(self.document_root) if self.document_root is not None else None,
            'script': self.script,
            'sendfile': os.fspath(self.sendfile) if self.sendfile is not None else None,
            'static': self.static,
        }
        _Call.run(self, config, tx)


# A request to an application, whose response of CGI is written as it comes, which a subclass sends and reads
class _Response:
    name = 'CGI'

    # The path of the mount itself, which a server takes for the whole path in SCRIPT_NAME without PATH_INFO
    mount_path = ''

    def __init__(self, app: Any, config: dict[str, Any], tx: Any, c: Any) -> None:
        self.app = app
        self.extensions: list[str] | None = config['extensions']
        self.inactivity: float = config['inactivity']
        self.root: str | None = config['root']
        self.script: str | None = config['script']
        self.sendfile: str | None = config['sendfile']
        self.static: bool = config['static']
        self.waiting: tuple[str, float] | None = None
        self.c = c
        self.tx = tx
        self.aborted = False
        self.chunked = False
        self.closed = False
        self.done = False
        self.head = bytearray()
        self.headers: list[tuple[str, str]] | None = None
        self.nph = False
        self.offset = 0
        self.pending: list[bytes] = []
        self.started = False
        self.stream: Any = None

    # The request of the transaction, or of the controller of a route that embeds the application
    @classmethod
    def run(cls, app: Any, config: dict[str, Any], tx: Any, *args: Any) -> None:
        c = None
        if not isinstance(tx, Pyjo.Transaction.object):
            c = tx
            tx = c.tx
            if not Pyjo.App._within(c):  # pyright: ignore[reportPrivateUsage]
                return c.helpers.reply.not_found()
            c.render_later()
        cls(app, config, tx, c, *args).start()

    def start(self) -> None:
        self.tx.on('finish', self._finish)
        params = {**Pyjo.App._cgi(self.tx, self.c), **_extra(self.tx)}  # pyright: ignore[reportPrivateUsage]

        # Not the header Proxy, whose HTTP_PROXY an application may take for the proxy of its own requests, as httpoxy
        # (CVE-2016-5385) does, as nginx and Apache leave it out
        params.pop('HTTP_PROXY', None)

        # A file of the directory of the scripts, as try_files of nginx serves it
        root, extensions = self.root, self.extensions
        if (c := self.c) is not None and self.static and root is not None and extensions is not None:
            if (file := _file(root, params['PATH_INFO'], extensions)) is not None:
                self.done = True
                return c.helpers.reply.file(file)

        env = self.app.env

        # The script of the path in the directory of the scripts, or the one script for a path that names none
        if root is not None and 'SCRIPT_FILENAME' not in env:
            if not self._script(params, root):
                return self._not_found()

        else:
            # The one script for every path
            if (script := self.script) is not None and 'SCRIPT_FILENAME' not in env:
                params['SCRIPT_FILENAME'] = _chars(script)
            if not params['PATH_INFO'] and params['SCRIPT_NAME']:
                params['PATH_INFO'] = self.mount_path
        params.update(self._defaults())
        params.update({name: _chars(value) for name, value in env.items()})

        # The connection of the client waits for the response without its inactivity timeout, which the one of the
        # application takes the place of, so that an application that takes longer gives 502
        if (connection := self.tx.connection) is not None and (stream := Pyjo.IOLoop.stream(connection)) is not None:
            self.waiting = (connection, stream.timeout)
            stream.timeout = 0

        self._open(params)

    def _close(self) -> None:
        if (connection := self.tx.connection) is not None and (stream := Pyjo.IOLoop.stream(connection)) is not None:
            stream.close()

    # The variables of the environment of the application before the ones of the attribute env
    def _defaults(self) -> dict[str, str]:
        return {}

    # End of the response
    def _end(self) -> None:
        self.done = True
        content = self.tx.res.content
        (content.write_chunk if self.chunked else content.write)(b'')
        self._rendered()
        self._stop()

    def _failed(self, message: str) -> None:
        if self.done:
            return
        self.aborted = True

        # The response has started, so the connection is closed, as the response cannot change
        if self.started:
            self.done = True
            if not self.closed:
                self.app.log.error(message)
                self._close()
            return self._stop()

        self.done = True
        self._stop()
        self._waited()
        self.app.log.error(message)
        res = self.tx.res
        res.code = 502
        res.headers.content_type = 'text/plain'
        res.body = b'Bad Gateway'
        self._rendered()

    # The end of the transaction, also when the connection of the client is gone before the end of the response
    def _finish(self, *args: Any) -> None:
        self.closed = True
        if not self.done:
            self.aborted = True
        self._stop()

    # The response of CGI of the output that has come
    def _flush(self, ended: bool) -> None:
        if self.headers is None:
            if ended:
                self._failed(f'{self.name} application ended without a response')
            return

        # Whole response
        res = self.tx.res
        if not self.started:
            self.started = True
            self._waited()
            if self._sendfile():
                return
            _status(res, self.headers)
            if ended:
                self.done = True
                res.body = b''.join(self.pending)
                self.pending = []
                self._rendered()
                return self._stop()

            # Response as it comes, with the headers only for a HEAD request
            self.chunked = res.headers.content_length is None and self.tx.req.version == '1.1'
            if self.tx.is_empty:
                return self._end()

        if len(self.pending):
            chunk, self.pending = b''.join(self.pending), []
            content = res.content
            stream = self.stream

            # The next output once the chunk has been written to the client
            def drained(*args: Any) -> None:
                if (stream := self.stream) is not None and not self.done:
                    stream.start()

            if stream is not None and not ended:
                stream.stop()
            (content.write_chunk if self.chunked else content.write)(chunk, drained)
            self._rendered()
        if ended:
            self._end()

    def _not_found(self) -> None:
        self.done = True
        if (c := self.c) is not None:
            return c.helpers.reply.not_found()
        res = self.tx.res
        res.code = 404
        res.headers.content_type = 'text/plain'
        res.body = b'Not Found'
        self.tx.resume()

    # The request to the application, with its parameters
    def _open(self, params: dict[str, str]) -> None:
        raise NotImplementedError('Method "_open" not implemented by subclass')

    def _rendered(self) -> None:
        if (c := self.c) is not None:
            c.rendered()
        else:
            self.tx.resume()

    # The script of the path in the directory of the scripts, as nginx has it with fastcgi_split_path_info and
    # $document_root$fastcgi_script_name, or the one script for a path that names none
    def _script(self, params: dict[str, str], root: str) -> bool:
        extensions = self.extensions or []
        if (script := self.script) is not None and not _names_script(params['PATH_INFO'], extensions):
            params['PATH_INFO'] = f'/{script.lstrip("/")}'
        return _script(params, root, extensions)

    # The file of the header X-Sendfile of the application, in the directory of the files that it may reply with
    def _sendfile(self) -> bool:
        # The directory of sendfile, or the one of the files that static replies with
        directory = self.sendfile if self.sendfile is not None else self.root if self.static else None
        if (c := self.c) is None or directory is None or (headers := self.headers) is None:
            return False
        if (value := next((value for name, value in headers if name.lower() == 'x-sendfile'), None)) is None:
            return False
        self.done = True
        self._stop()
        if (file := _inside(directory, value)) is None:
            self.app.log.error(f'{self.name} application sent the file "{value}", which is not in "{directory}"')
            c.helpers.reply.not_found()
            return True
        _status(self.tx.res, [(name, value) for name, value in headers if name.lower() not in _SENT])
        c.helpers.reply.file(file)
        return True

    # The headers of the response of CGI, and the start of its body
    def _stdout(self, content: bytes) -> None:
        if self.headers is not None:
            if len(content):
                self.pending.append(content)
            return
        self.head += content
        if (m := re.search(rb'\r?\n\r?\n', self.head)) is None:
            return
        head, body = bytes(self.head[: m.start()]), bytes(self.head[m.end() :])
        self.head = bytearray()
        lines = re.split(r'\r?\n', head.decode('latin-1'))

        # The start line of non-parsed header mode, whose status takes the place of the header Status
        status = []
        if self.nph and lines[0].startswith('HTTP/'):
            status = [('Status', lines.pop(0).partition(' ')[2])]
        self.headers = status + [
            (name.strip(), value.strip()) for name, _, value in (line.partition(':') for line in lines) if name.strip()
        ]
        if len(body):
            self.pending.append(body)

    # The end of the request to the application
    def _stop(self) -> None:
        raise NotImplementedError('Method "_stop" not implemented by subclass')

    # The inactivity timeout of the connection of the client again, once the response starts
    def _waited(self) -> None:
        if (waiting := self.waiting) is not None:
            self.waiting = None
            connection, timeout = waiting
            if (stream := Pyjo.IOLoop.stream(connection)) is not None:
                stream.timeout = timeout


# A request to a program, in a process of its own
class _Call(_Response):
    def __init__(self, app: Pyjo_App_CGI, config: dict[str, Any], tx: Any, c: Any) -> None:
        super().__init__(app, config, tx, c)
        self.buffer = b''
        self.command = app.command
        self.input: Any = None
        self.process: subprocess.Popen[bytes] | None = None

    def _closed(self, stream: Any) -> None:
        self.stream = None
        if self.done or self.closed:
            return
        self._flush(True)

    def _defaults(self) -> dict[str, str]:
        defaults = {'PATH': path} if (path := os.environ.get('PATH')) is not None else {}
        if self.command is not None:
            defaults['REDIRECT_STATUS'] = '200'
        return defaults

    def _error(self, stream: Any, err: Any) -> None:
        self._failed(f'CGI application failed: {err}')

    def _ignore(self, stream: Any, err: Any) -> None:
        pass

    # The standard error of the program
    def _log(self, stream: Any, chunk: bytes) -> None:
        if message := chunk.decode('utf-8', 'replace').rstrip():
            self.app.log.warn(f'CGI application: {message}')

    def _open(self, params: dict[str, str]) -> None:
        if os.name == 'nt':
            return self._failed('CGI applications need pipes that the event loop watches, which Windows does not have')

        # The program, or the command that runs the script, in the directory of its file
        file = params['SCRIPT_FILENAME'].encode('latin-1')
        nph = self.app.nph
        self.nph = os.path.basename(file).startswith(b'nph-') if nph is None else nph
        env = {name.encode('latin-1'): value.encode('latin-1') for name, value in params.items()}
        try:
            self.process = process = subprocess.Popen(
                [*(self.command or []), file],
                bufsize=0,
                cwd=os.path.dirname(file) or None,
                env=env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except OSError as e:
            return self._failed(f"Can't run CGI application: {e.strerror or e}")
        _processes.add(process)
        assert process.stdin is not None and process.stdout is not None and process.stderr is not None
        for handle in (process.stdin, process.stdout, process.stderr):
            os.set_blocking(handle.fileno(), False)

        # The standard output, the response, and the standard error, which is logged until its end
        self.stream = stream = Pyjo.IOLoop.Stream.new(process.stdout)
        stream.timeout = 0
        Pyjo.IOLoop.stream(stream)
        stream.timeout = self.inactivity
        stream.on('read', self._read)
        stream.on('close', self._closed)
        stream.on('error', self._error)
        stream.on('timeout', self._timeout)
        errors = Pyjo.IOLoop.Stream.new(process.stderr)
        errors.timeout = 0
        Pyjo.IOLoop.stream(errors)
        errors.on('read', self._log)
        errors.on('error', self._ignore)

        # The standard input, the body of the request, which the event loop writes to without reading
        self.input = process.stdin
        reactor = Pyjo.IOLoop.singleton.reactor
        reactor.io(process.stdin, self._write)
        reactor.watch(process.stdin, False, True)

    def _read(self, stream: Any, chunk: bytes) -> None:
        if self.done:
            return
        self._stdout(chunk)
        self._flush(False)

    def _stop(self) -> None:
        self._stop_input()
        if (stream := self.stream) is not None:
            self.stream = None
            stream.close()

        # The process of a response that has failed, or of a client that is gone, which the end of its output does not
        # end
        if (process := self.process) is not None:
            self.process = None
            if self.aborted and process.poll() is None:
                process.kill()
            _reap(process)

    def _stop_input(self) -> None:
        if (handle := self.input) is not None:
            self.input = None
            Pyjo.IOLoop.singleton.reactor.remove(handle)
            handle.close()

    # The program of the first parts of the path that are a file of the directory, as cgi-bin, or of the path up to its
    # first part with one of the extensions, which is a file of the directory, as the command runs no other file
    def _script(self, params: dict[str, str], root: str) -> bool:
        if (extensions := self.extensions) is not None:
            if not super()._script(params, root):
                return False
            return _is_script(params['SCRIPT_FILENAME'], extensions) and _program(params, root)
        for path in (params['PATH_INFO'], f'/{self.script.lstrip("/")}' if self.script is not None else None):
            if path is None:
                continue
            parts = (path or '/').split('/')
            if '..' in parts:
                return False
            for end in range(2, len(parts) + 1):
                if _inside(root, os.fsdecode('/'.join(parts[1:end]).encode('latin-1'))) is not None:
                    _split(params, root, parts, end)
                    return True
        return False

    def _timeout(self, stream: Any) -> None:
        self._failed('CGI application inactive')

    # The body of the request, a chunk once the one before has been written, and the end of the input after it
    def _write(self, reactor: Any, writable: bool) -> None:
        if (handle := self.input) is None:
            return
        if not len(self.buffer):
            chunk = self.tx.req.content.get_body_chunk(self.offset) or b''
            if not len(chunk):
                return self._stop_input()
            self.offset += len(chunk)
            self.buffer = chunk
        try:
            written = os.write(handle.fileno(), self.buffer)
        except BlockingIOError:
            return

        # The program does not read its input
        except OSError:
            return self._stop_input()
        self.buffer = self.buffer[written:]


@atexit.register
def _kill() -> None:
    for process in list(_processes):
        if process.poll() is None:
            process.kill()
        process.wait()
    _processes.clear()


# A process, once it has ended
def _reap(process: subprocess.Popen[bytes], *args: Any) -> None:
    if process.poll() is None:
        Pyjo.IOLoop.timer(0.1, functools.partial(_reap, process))
    else:
        _processes.discard(process)


# Characters of the bytes of a string of the system, as the parameters have them
def _chars(value: str) -> str:
    return os.fsencode(value).decode('latin-1')


# The parameters that CGI servers add, which the applications of PHP need
def _extra(tx: Any) -> dict[str, str]:
    req = tx.req
    url = req.url
    uri = url.path.to_abs_str()
    if base := url.base.path.to_str().rstrip('/'):
        uri = base + uri
    if query := url.query.to_str():
        uri += f'?{query}'
    extra = {'GATEWAY_INTERFACE': 'CGI/1.1', 'REQUEST_URI': uri, 'SERVER_SOFTWARE': 'Pyjoyment (Python)'}
    if req.is_secure:
        extra['HTTPS'] = 'on'
    return extra


# A file of the directory for a path that names no script and no directory, as try_files of nginx takes it
def _file(root: str, path: str, extensions: list[str]) -> str | None:
    if not path or path.endswith('/') or _names_script(path, extensions) or '..' in path.split('/'):
        return None
    return _inside(root, os.fsdecode(path.lstrip('/').encode('latin-1')))


# A file in a directory, also once its symbolic links are resolved, so that no link leads out of it
def _inside(directory: str, path: str) -> str | None:
    base = os.path.realpath(directory)
    file = os.path.realpath(os.path.join(base, path))
    if os.path.commonpath([base, file]) != base or not os.path.isfile(file):
        return None
    return file


# A program of the directory of the scripts
def _program(params: dict[str, str], root: str) -> bool:
    return _inside(root, os.fsdecode(params['SCRIPT_FILENAME'].encode('latin-1'))) is not None


def _is_script(part: str, extensions: list[str]) -> bool:
    return any(part.endswith(extension) for extension in extensions)


# A path that names a script, by the extension of one of its parts
def _names_script(path: str, extensions: list[str]) -> bool:
    return any(_is_script(part, extensions) for part in path.split('/'))


# The script of the path in the directory of the scripts, up to its first part with one of the extensions, unless the
# path has ..
def _script(params: dict[str, str], root: str, extensions: list[str]) -> bool:
    parts = (params['PATH_INFO'] or '/').split('/')
    if '..' in parts:
        return False
    end = next((i + 1 for i, part in enumerate(parts) if _is_script(part, extensions)), len(parts))
    _split(params, root, parts, end)
    if end == len(parts) and params['SCRIPT_FILENAME'].endswith('/') and extensions:
        params['SCRIPT_FILENAME'] += f'index{extensions[0]}'
        params['SCRIPT_NAME'] += f'index{extensions[0]}'
    return True


# The script of the first parts of the path, and the rest of the path
def _split(params: dict[str, str], root: str, parts: list[str], end: int) -> None:
    script, rest = '/'.join(parts[:end]), '/'.join(parts[end:])
    root = _chars(root)
    params['SCRIPT_FILENAME'] = root.rstrip('/') + script
    params['SCRIPT_NAME'] += script
    params['PATH_INFO'] = f'/{rest}' if end < len(parts) else ''
    params['DOCUMENT_ROOT'] = root


# The status of a response of CGI from its header Status, or a redirect for a header Location, and its other headers
def _status(res: Any, headers: list[tuple[str, str]]) -> None:
    res.code = 200
    location = False
    for name, value in headers:
        if name.lower() == 'status':
            code, _, message = value.partition(' ')
            res.code = int(code)
            res.message = message or None
            continue
        if name.lower() == 'location':
            location = True
        if not wsgiref.util.is_hop_by_hop(name):
            res.headers.add(name, value)
    if location and not any(name.lower() == 'status' for name, _ in headers):
        res.code = 302


new = Pyjo_App_CGI.new
object = Pyjo_App_CGI
CGI = Pyjo_App_CGI
