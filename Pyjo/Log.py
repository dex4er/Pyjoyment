
r"""
Pyjo.Log - Simple logger
========================
::

    import Pyjo.Log

    # Log to STDERR
    log = Pyjo.Log.new()

    # Customize log file location and minimum log level
    log = Pyjo.Log.new(path='/var/log/pyjo.log', level='warn')

    # Log messages
    log.debug('Not sure what is happening here')
    log.info('FYI: it happened again')
    log.warn('This might be a problem')
    log.error('Garden variety error')
    log.fatal('Boom')

:mod:`Pyjo.Log` is a simple logger for :mod:`Pyjo` projects.

Events
------

:mod:`Pyjo.Log` inherits all events from :mod:`Pyjo.EventEmitter` and can emit the
following new ones.

message
~~~~~~~
::

    @log.on
    def message(log, level, lines):
       ...

Emitted when a new message gets logged. ::

    log.unsubscribe('message')

    @log.on
    def message(log, level, lines):
        print("{0}: {1}".format(level, "\n".join(lines)))

Classes
-------
"""

import Pyjo.EventEmitter

import codecs
import os
import sys
import time

from Pyjo.Util import getenv, notnone, u


if os.name == 'posix':
    import fcntl


LEVEL = {'debug': 1, 'info': 2, 'warn': 3, 'error': 4, 'fatal': 5}


class LockException(Exception):
    LOCK_FAILED = 1


if os.name == 'posix':
    def lock(file):
        try:
            fcntl.flock(file.fileno(), fcntl.LOCK_EX)
        except OSError as err:
            #  IOError: [Errno 11] Resource temporarily unavailable
            if err[0] == 11:
                raise LockException(LockException.LOCK_FAILED, err[1])
            else:
                raise

    def unlock(file):
        fcntl.flock(file.fileno(), fcntl.LOCK_UN)

else:
    def lock(file):
        pass

    def unlock(file):
        pass


class Pyjo_Log(Pyjo.EventEmitter.object):
    """
    :mod:`Pyjo.Log` inherits all attributes and methods from
    :mod:`Pyjo.EventEmitter` and implements the following new ones.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        """::

            log = Pyjo.Log.new()

        Construct a new :mod:`Pyjo.Log` object and subscribe to ``message`` event with
        default logger.
        """

        self.format = notnone(kwargs.get('format'), lambda: self._format)
        r"""::

            cb = log.format
            log.format = lambda t, level, *lines: ...

        A callback for formatting log messages. ::

            def my_format(t, level, *lines):
                return u"[Thu May 15 17:47:04 2014] [info] I ♥ Mojolicious\n"

            log.format = my_format
        """

        self.history = kwargs.get('history', [])
        """::

            history = log.history
            log.history = [[time.time(), 'debug', 'That went wrong']]

        The last few logged messages.
        """

        self.level = kwargs.get('level', 'debug')
        """::

            level = log.level
            log.level = 'debug'

        Active log level, defaults to ``debug``. Available log levels are ``debug``,
        ``info``, ``warn``, ``error`` and ``fatal``, in that order. Note that the
        ``PYJO_LOG_LEVEL`` environment variable can override this value.
        """

        self.max_history_size = kwargs.get('max_history_size', 10)
        """::

            size = log.max_history_size
            log.max_history_size = 5

        Maximum number of logged messages to store in :attr:`history`, defaults to ``10``.
        """

        self.path = kwargs.get('path')
        """::

            path = log.path
            log.path = '/var/log/pyjo.log'

        Log file path used by :attr:`handle`.
        """

        self.handle = notnone(kwargs.get('handle'), lambda: self._build_handle())
        """::

            handle = log.handle
            log.handle = open('file.log', 'a')

        Log filehandle used by default ``message`` event, defaults to opening
        :attr:`path` or :attr:`sys.stderr`. Filehandle should accept unicode.
        If :attr:`sys.stderr` is not in ``utf-8`` mode, then this stream is
        re-attached to accept unicode.
        """

        def message_cb(log, level, lines):
            log._message(level, lines)

        self.on(message_cb, 'message')

    def __del__(self):
        try:
            self.close()
        except:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def append(self, msg):
        r"""::

            log.append(u"[Thu May 15 17:47:04 2014] [info] I ♥ Pyjoyment\n")

        Append message to :attr:`handle`.
        """
        handle = self.handle
        if not handle:
            return

        if handle != sys.stderr:
            lock(handle)
        handle.write(msg)
        handle.flush()
        if handle != sys.stderr:
            unlock(handle)

    def close(self):
        handle = self.handle
        if handle and handle != sys.stderr:
            handle.close()

    def debug(self, *lines):
        """::

            log = log.debug('You screwed up, but that is ok')
            log = log.debug('All', 'cool')

        Emit ``message`` event and log debug message.
        """
        self._log('debug', lines)

    def error(self, *lines):
        """::

            log = log.error('You really screwed up this time')
            log = log.error('Wow', 'seriously')

        Emit ``message`` event and log error message.
        """
        self._log('error', lines)

    def fatal(self, *lines):
        """::

            log = log.fatal('Its over...')
            log = log.fatal('Bye', 'bye')

        Emit ``message`` event and log fatal message.
        """
        self._log('fatal', lines)

    def info(self, *lines):
        """::

            log = log.info('You are bad, but you prolly know already')
            log = log.info('Ok', 'then')

        Emit ``message`` event and log info message.
        """
        self._log('info', lines)

    @property
    def is_debug(self):
        """::

            boolean = log.is_debug

        Check for debug log level.
        """
        return self._now('debug')

    @property
    def is_error(self):
        """::

            boolean = log.is_error

        Check for error log level.
        """
        return self._now('error')

    @property
    def is_info(self):
        """::

            boolean = log.is_info

        Check for info log level.
        """
        return self._now('info')

    @property
    def is_warn(self):
        """::

            boolean = log.is_warn

        Check for warn log level.
        """
        return self._now('warn')

    def warn(self, *lines):
        """::

            log = log.warn('Dont do that Dave...')
            log = log.warn('No', 'really')

        Emit ``message`` event and log warn message.
        """
        self._log('warn', lines)

    def _build_handle(self):
        if self.path:
            return codecs.open(self.path, mode='a', encoding='utf-8', errors='replace')
        elif (getattr(sys.stderr, 'encoding', '') or '').lower() == 'utf-8':
            return sys.stderr
        elif not hasattr(sys.stderr, 'encoding'):
            return sys.stderr
        else:
            encoding = sys.stderr.encoding or 'ascii'
            if hasattr(sys.stderr, 'detach'):
                sys.stderr = codecs.getwriter(encoding)(sys.stderr.detach(), 'backslashreplace')
            else:
                sys.stderr = codecs.getwriter(encoding)(sys.stderr, 'backslashreplace')
            return sys.stderr

    def _format(self, t, level, *lines):
        return "[{0}] [{1}] {2}\n".format(time.asctime(time.localtime(t)), level, "\n".join(map(u, lines)))

    def _log(self, level, lines):
        self.emit('message', level, lines)

    def _message(self, level, lines):
        if not self._now(level):
            return

        max_history_size = self.max_history_size
        history = self.history
        msg = [time.time(), level]
        msg.extend(lines)
        history.append(msg)
        while len(history) > max_history_size:
            history.pop(0)

        self.append(self.format(*msg))

    def _now(self, level):
        return LEVEL.get(level, 0) >= LEVEL.get(getenv('PYJO_LOG_LEVEL', self.level), 0)


new = Pyjo_Log.new
object = Pyjo_Log
