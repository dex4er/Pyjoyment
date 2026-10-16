import Pyjo.Log

from Pyjo.File import tempdir
from Pyjo.Test import *

import contextlib
import io
import logging
import pathlib


def logger(name):
    logger = logging.getLogger(f't.stdlib.Log.{name}')
    logger.propagate = False
    logger.setLevel(1)
    return logger


with subtest('Levels of the logging module'):
    log = Pyjo.Log.new(handle=None)
    log.unsubscribe('message')
    got = []
    log.on('message', lambda log, level, *lines: got.append((level, *lines)))
    lg = logger('levels')
    lg.addHandler(Pyjo.Log.Handler(log))
    lg.log(5, 'Five')
    lg.debug('Debug')
    lg.info('Info')
    lg.warning('Warning')
    lg.error('Error')
    lg.critical('Critical')
    lg.log(25, 'Between')
    is_deeply_ok(
        got,
        [
            ('trace', 'Five'),
            ('debug', 'Debug'),
            ('info', 'Info'),
            ('warn', 'Warning'),
            ('error', 'Error'),
            ('fatal', 'Critical'),
            ('info', 'Between'),
        ],
        'mapped levels',
    )

with subtest('Records are formatted'):
    log = Pyjo.Log.new(handle=None)
    lg = logger('format')
    handler = Pyjo.Log.Handler(log)
    handler.setFormatter(logging.Formatter('%(name)s: %(message)s'))
    lg.addHandler(handler)
    with log.capture() as messages:
        lg.info('%s and %d', 'args', 2)
        try:
            raise ValueError('Oops')
        except ValueError:
            lg.exception('Failed')
    like_ok(messages[0], r'\[info\] t\.stdlib\.Log\.format: args and 2\n$', 'formatted')
    like_ok(messages[1], r'\[error\] t\.stdlib\.Log\.format: Failed\nTraceback', 'traceback')
    like_ok(messages[1], r'ValueError: Oops\n$', 'exception')

with subtest('Levels filter'):
    log = Pyjo.Log.new(handle=None, level='warn')
    lg = logger('filter')
    lg.addHandler(Pyjo.Log.Handler(log, logging.ERROR))
    with log.capture() as messages:
        lg.info('Info')
        lg.warning('Warning')
        lg.error('Error')
    is_ok(len(messages), 1, 'handler level')
    like_ok(messages[0], r'\[error\] Error\n$', 'error passed')

    with log.capture('error') as messages:
        lg.error('Error')
        lg.critical('Critical')
    is_ok(len(messages), 2, 'log level')

with subtest('Text streams'):
    with contextlib.redirect_stderr(io.StringIO()) as stderr:
        Pyjo.Log.new().info('I ♥ Pyjoyment')
    like_ok(stderr.getvalue(), r'\[info\] I ♥ Pyjoyment\n$', 'redirect_stderr')

    handle = io.StringIO()
    Pyjo.Log.new(handle=handle).warn('Memory')
    like_ok(handle.getvalue(), r'\[warn\] Memory\n$', 'StringIO')

    log = Pyjo.Log.new(handle=None)
    log.error('Nowhere')
    is_ok(log.handle, None, 'no handle')
    is_ok(len(log.history), 1, 'history still kept')

with subtest('Paths'):
    dir = tempdir()
    file = pathlib.Path(dir.to_str(), 'pathlib.log')
    file.write_text('Existing line\n', encoding='UTF-8')
    log = Pyjo.Log.new(path=file)
    log.info('I ♥ Pyjoyment')
    log.handle.close()
    content = file.read_text(encoding='UTF-8')
    like_ok(content, r'^Existing line\n', 'appended')
    like_ok(content, r'\[info\] I ♥ Pyjoyment\n$', 'UTF-8')

    log = Pyjo.Log.new(path=dir.child('pyjo.log'))
    log.info('Pyjo.File')
    log.handle.close()
    like_ok(dir.child('pyjo.log').slurp().decode(), r'\[info\] Pyjo.File\n$', 'Pyjo.File')

with subtest('Capture is a container'):
    log = Pyjo.Log.new(handle=None)
    with log.capture() as messages:
        ok(not messages, 'empty capture is false')
        log.info('One').info('Two')
    ok(messages, 'true with messages')
    is_ok(len(messages), 2, 'len')
    is_ok(len(list(messages)), 2, 'iterable')
    is_ok(len(log.subscribers('message')), 1, 'default logger restored')

with subtest('Context manager'):
    tmp = tempdir()
    path = tmp.child('test.log')
    with Pyjo.Log.new(path=path) as log:
        log.error('First')
        handle = log.handle
    ok(handle.closed, 'file closed at the end of the block')
    log.error('Second')
    ok(not log.handle.closed, 'opened again when the log is used again')
    log.handle.close()
    like_ok(path.slurp().decode(), (r'First.*Second', 's'), 'messages')

done_testing()
