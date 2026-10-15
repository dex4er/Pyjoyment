"""
Pyjo.Log - Simple logger
========================
::

    import Pyjo.Log

    # Log to STDERR
    log = Pyjo.Log.new()

    # Customize log file location and minimum log level
    log = Pyjo.Log.new(path='/var/log/pyjo.log', level='warn')

    # Log messages
    log.trace('Doing stuff')
    log.debug('Not sure what is happening here')
    log.info('FYI: it happened again')
    log.warn('This might be a problem')
    log.error('Garden variety error')
    log.fatal('Boom')

:mod:`Pyjo.Log` is a simple logger for :mod:`Pyjo` projects.

Events
------

:mod:`Pyjo.Log` inherits all events from :mod:`Pyjo.EventEmitter` and can
emit the following new ones.

message
~~~~~~~
::

    log.on('message', lambda log, level, *lines: ...)

Emitted when a new message gets logged. ::

    log.on('message', lambda log, level, *lines: print(f'{level}: ', *lines, sep=''))

The logging module
------------------

:class:`Pyjo.Log.Handler` is a :class:`logging.Handler` that passes the records
of the standard library's :mod:`logging` to a :mod:`Pyjo.Log`. ::

    import logging

    logging.getLogger().addHandler(Pyjo.Log.Handler(log))
    logging.getLogger().warning('Disk is %d%% full', 95)

The levels of :mod:`logging` are mapped to the closest level of the log:
``CRITICAL`` is ``fatal``, ``ERROR`` is ``error``, ``WARNING`` is ``warn``,
``INFO`` is ``info``, ``DEBUG`` is ``debug``, and a level below ``DEBUG`` is
``trace``.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::Log <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/Log.pm>`_
of Mojolicious 9.49.
"""

import Pyjo.EventEmitter
import Pyjo.Exception
import Pyjo.File

import builtins
import logging
import os
import sys
import time
import weakref

from collections.abc import Callable, Iterable, Iterator
from types import TracebackType
from typing import IO, Any, Self, cast


type Anything = builtins.object

# A callback for formatting log messages, it gets the time, the level and the lines
type Format = Callable[..., str]

# Supported log levels
LEVEL = {'trace': 1, 'debug': 2, 'info': 3, 'warn': 4, 'error': 5, 'fatal': 6}

# Systemd magic numbers
MAGIC = {'trace': 7, 'debug': 6, 'info': 5, 'warn': 4, 'error': 3, 'fatal': 2}

# Colors, as Term::ANSIColor has yellow, red and white on red
COLORS = {'warn': '33', 'error': '31', 'fatal': '37;41'}

# A handle that is not set yet, as None is no handle
_UNSET: Any = builtins.object()


class Pyjo_Log(Pyjo.EventEmitter.object):
    """
    :mod:`Pyjo.Log` inherits all methods from :mod:`Pyjo.EventEmitter` and
    implements the following new ones.
    """

    def __init__(
        self,
        *,
        color: bool | None = None,
        format: Format | None = None,
        handle: IO[str] | None = _UNSET,
        history: list[list[Any]] | None = None,
        level: str = 'trace',
        max_history_size: int = 10,
        path: str | os.PathLike[str] | None = None,
        short: bool | None = None,
    ) -> None:
        """::

            log = Pyjo.Log.new()
            log = Pyjo.Log.new(level='warn')

        Construct a new :mod:`Pyjo.Log` object and subscribe to the
        ``message`` event with the default logger.
        """
        super().__init__()

        self._color: bool | None = color

        self.history: list[list[Any]] = history if history is not None else []
        """::

            history = log.history
            log.history = [[time.time(), 'debug', 'That went wrong']]

        The last few logged messages.
        """

        self.level = level
        """::

            level = log.level
            log.level = 'debug'

        Active log level, defaults to ``trace``. Available log levels are
        ``trace``, ``debug``, ``info``, ``warn``, ``error`` and ``fatal``, in
        that order.
        """

        self.max_history_size = max_history_size
        """::

            size = log.max_history_size
            log.max_history_size = 5

        Maximum number of logged messages to store in :attr:`history`,
        defaults to ``10``.
        """

        self.path = path
        """::

            path = log.path
            log.path = '/var/log/pyjo.log'

        Log file path used by :attr:`handle`.
        """

        self._short: bool | None = short

        self._capturing = False
        self._context: list[Any] = []
        self._format = format
        self._handle = handle
        self._parent: Pyjo_Log | None = None

        self.on('message', _message)

    @property
    def color(self) -> bool:
        """::

            boolean = log.color
            log.color = boolean

        Colorize log messages with the levels ``warn``, ``error`` and
        ``fatal`` using ANSI escape sequences, defaults to the value of the
        ``PYJO_LOG_COLOR`` environment variable.
        """
        if self._color is None:
            self._color = bool(os.environ.get('PYJO_LOG_COLOR'))
        return self._color

    @color.setter
    def color(self, value: bool) -> None:
        self._color = value

    @property
    def short(self) -> bool:
        """::

            boolean = log.short
            log.short = boolean

        Generate short log messages without a timestamp but with journald log
        level prefix, suitable for systemd environments, defaults to the value
        of the ``PYJO_LOG_SHORT`` environment variable.
        """
        if self._short is None:
            self._short = bool(os.environ.get('PYJO_LOG_SHORT'))
        return self._short

    @short.setter
    def short(self, value: bool) -> None:
        self._short = value

    @property
    def format(self) -> Format:
        """::

            cb = log.format
            log.format = lambda time, level, *lines: ...

        A callback for formatting log messages. ::

            log.format = lambda time, level, *lines: '[2018-11-08 14:20:13.77168] [28320] [info] I ♥ Pyjoyment\\n'
        """
        if self._format is None:
            self._format = _short if self.short else _color if self.color else _default
        return self._format

    @format.setter
    def format(self, value: Format) -> None:
        self._format = value

    @property
    def handle(self) -> IO[str] | None:
        """::

            handle = log.handle
            log.handle = io.StringIO()

        Log text stream used by the default ``message`` event, defaults to
        opening :attr:`path` for appending in UTF-8 or :data:`sys.stderr`.
        """
        if self._handle is _UNSET:
            # STDERR, or the file
            path = self.path
            if path is None:
                self._handle = sys.stderr
            else:
                handle = self._handle = Pyjo.File.new(path).open('a', encoding='UTF-8')

                # Not in Mojolicious: the file is closed with the object, as Perl closes it with the last reference
                weakref.finalize(self, handle.close)
        return self._handle

    @handle.setter
    def handle(self, value: IO[str] | None) -> None:
        self._handle = value

    def append(self, msg: str) -> None:
        """::

            log.append('[2018-11-08 14:20:13.77168] [28320] [info] I ♥ Pyjoyment\\n')

        Append message to :attr:`handle`.
        """
        if (handle := self.handle) is None:
            return
        fd = _fileno(handle)
        _flock(fd, True)
        try:
            handle.write(msg)
            handle.flush()
        except OSError as e:
            error = type(e)(f"Can't write to log: {e.strerror}" if e.strerror else "Can't write to log")
            error.errno = e.errno
            raise error from e
        finally:
            _flock(fd, False)

    def capture(self, level: str | None = None) -> '_Capture':
        """::

            with log.capture() as messages:
                ...
            with log.capture('debug') as messages:
                ...

        Capture log messages until the end of the ``with`` block, useful for
        testing log messages. The messages stay in the returned object after
        the block. ::

            # Test your log messages
            with log.capture('trace') as messages:
                log.fatal('Something very bad happened')
                log.trace('Just some debug information')
            like_ok(str(messages), r'Something very bad happened', 'logs contain fatal message')
            like_ok(messages[-1], r'Just some debug information', 'trace message was last')
        """
        if self._capturing:
            Pyjo.Exception.object.throw('Log messages are already being captured')
        self._capturing = True

        original = self.level
        self.level = level or original
        subscribers = self.subscribers('message')
        self.unsubscribe('message')

        def restore() -> None:
            self.level = original
            self.unsubscribe('message')
            self._capturing = False
            for cb in subscribers:
                self.on('message', cb)

        capture = _Capture(restore)
        messages = capture.messages

        def message(log: Pyjo_Log, level: str, *lines: Any) -> None:
            messages.append(log.format(time.time(), level, *lines))

        self.on('message', message)

        return capture

    def context(self, *context: Any) -> Self:
        """::

            new = log.context('[extra]', '[information]')

        Construct a new child :mod:`Pyjo.Log` object that will include context
        information with every log message. ::

            # Log with context
            log = Pyjo.Log.new()
            context = log.context('[17a60115]')
            context.debug('This is a log message with context information')
            context.info('And another')
        """
        log = self.new(level=self.level)
        log._parent = self
        log._context = list(context)
        return log

    def debug(self, *msgs: Any) -> Self:
        """::

            log = log.debug('You screwed up, but that is ok')
            log = log.debug('All', 'cool')
            log = log.debug(lambda: ...)

        Emit ``message`` event and log ``debug`` message.
        """
        return self._log('debug', *msgs) if 2 >= LEVEL[self.level] else self

    def error(self, *msgs: Any) -> Self:
        """::

            log = log.error('You really screwed up this time')
            log = log.error('Wow', 'seriously')
            log = log.error(lambda: ...)

        Emit ``message`` event and log ``error`` message.
        """
        return self._log('error', *msgs) if 5 >= LEVEL[self.level] else self

    def fatal(self, *msgs: Any) -> Self:
        """::

            log = log.fatal('Its over...')
            log = log.fatal('Bye', 'bye')
            log = log.fatal(lambda: ...)

        Emit ``message`` event and log ``fatal`` message.
        """
        return self._log('fatal', *msgs) if 6 >= LEVEL[self.level] else self

    def info(self, *msgs: Any) -> Self:
        """::

            log = log.info('You are bad, but you prolly know already')
            log = log.info('Ok', 'then')
            log = log.info(lambda: ...)

        Emit ``message`` event and log ``info`` message.
        """
        return self._log('info', *msgs) if 3 >= LEVEL[self.level] else self

    def is_level(self, level: str) -> bool:
        """::

            boolean = log.is_level('debug')

        Check active log :attr:`level`. ::

            # True
            log.set(level='debug').is_level('debug')
            log.set(level='debug').is_level('info')

            # False
            log.set(level='info').is_level('debug')
            log.set(level='fatal').is_level('warn')
        """
        return LEVEL[level] >= LEVEL[self.level]

    def trace(self, *msgs: Any) -> Self:
        """::

            log = log.trace('Whatever')
            log = log.trace('Who', 'cares')
            log = log.trace(lambda: ...)

        Emit ``message`` event and log ``trace`` message.
        """
        return self._log('trace', *msgs) if 1 >= LEVEL[self.level] else self

    def warn(self, *msgs: Any) -> Self:
        """::

            log = log.warn('Dont do that Dave...')
            log = log.warn('No', 'really')
            log = log.warn(lambda: ...)

        Emit ``message`` event and log ``warn`` message.
        """
        return self._log('warn', *msgs) if 4 >= LEVEL[self.level] else self

    def _log(self, level: str, *msgs: Any) -> Self:
        if msgs and callable(msgs[0]):
            result: Any = msgs[0]()
            msgs = tuple(cast(Iterable[Any], result)) if isinstance(result, (tuple, list)) else (result,)
        msgs = (*self._context, *msgs)
        (self._parent or self).emit('message', level, *msgs)
        # Unlike Mojolicious: Mojo returns what emit() returns, the parent of a context, where the POD says the log
        return self


class _Capture:
    def __init__(self, restore: Callable[[], None]) -> None:
        self.messages: list[str] = []
        self._restore: Callable[[], None] | None = restore

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> None:
        if (restore := self._restore) is not None:
            self._restore = None
            restore()

    # Left out from Mojolicious: the bool overload, an empty capture is false as an empty container is

    def __getitem__(self, index: int) -> str:
        return self.messages[index]

    def __iter__(self) -> Iterator[str]:
        return iter(self.messages)

    def __len__(self) -> int:
        return len(self.messages)

    def __str__(self) -> str:
        return ''.join(self.messages)


# Not in Mojolicious: a handler of the logging module
class Handler(logging.Handler):
    """::

        handler = Pyjo.Log.Handler(log)
        handler = Pyjo.Log.Handler(log, logging.INFO)

    A :class:`logging.Handler` that formats the records of :mod:`logging` and
    logs them with the given :mod:`Pyjo.Log`, at the closest level.
    """

    def __init__(self, log: Pyjo_Log, level: int = logging.NOTSET) -> None:
        super().__init__(level)
        self.log = log

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            log = self.log
            level = _level(record.levelno)
            if log.is_level(level):
                getattr(log, level)(msg)
        except Exception:
            self.handleError(record)


def _color(time: float, level: str, *lines: Any) -> str:
    msg = _default(time, level, *lines)
    return f'\x1b[{COLORS[level]}m{msg}\x1b[0m' if level in COLORS else msg


def _default(time_: float, level: str, *lines: Any) -> str:
    t = time.localtime(time_)
    # The fraction of the seconds is the one of the time as a string
    fraction = str(time_).split('.')[1] if '.' in str(time_) else '0'
    seconds = float(f'{t.tm_sec}.{fraction}')
    timestamp = f'{t.tm_year:04d}-{t.tm_mon:02d}-{t.tm_mday:02d} {t.tm_hour:02d}:{t.tm_min:02d}:{seconds:08.5f}'
    return f'[{timestamp}] [{os.getpid()}] [{level}] {" ".join(map(str, lines))}\n'


def _fileno(handle: IO[str]) -> int | None:
    try:
        return handle.fileno()
    except (AttributeError, OSError, ValueError):
        return None


# Perl ignores what flock returns, as on a handle that cannot be locked
def _flock(fd: int | None, lock: bool) -> None:
    if fd is None or sys.platform == 'win32':
        return
    import fcntl

    try:
        fcntl.flock(fd, fcntl.LOCK_EX if lock else fcntl.LOCK_UN)
    except OSError:
        pass


# The closest level of Pyjo.Log for a level of the logging module
def _level(levelno: int) -> str:
    if levelno >= logging.CRITICAL:
        return 'fatal'
    if levelno >= logging.ERROR:
        return 'error'
    if levelno >= logging.WARNING:
        return 'warn'
    if levelno >= logging.INFO:
        return 'info'
    if levelno >= logging.DEBUG:
        return 'debug'
    return 'trace'


def _message(log: Pyjo_Log, level: str, *lines: Any) -> None:
    max = log.max_history_size
    history = log.history
    msg = [time.time(), level, *lines]
    history.append(msg)
    while len(history) > max:
        history.pop(0)

    log.append(log.format(*msg))


def _short(time: float, level: str, *lines: Any) -> str:
    magic, short = f'<{MAGIC[level]}>', level[0]
    return f'{magic}[{os.getpid()}] [{short}] {" ".join(map(str, lines))}\n'


new = Pyjo_Log.new
object = Pyjo_Log
