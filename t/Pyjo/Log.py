
import Pyjo.Test


class NoseTest(Pyjo.Test.NoseTest):
    script = __file__
    srcdir = '../..'


class UnitTest(Pyjo.Test.UnitTest):
    script = __file__


if __name__ == '__main__':

    from Pyjo.Test import *  # noqa

    import codecs
    import os
    import time

    from Pyjo.Util import slurp, u

    from t.lib.TemporaryDirectory import TemporaryDirectory

    import Pyjo.Log

    with TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, 'test_path.log')
        with Pyjo.Log.new(level='error', path=path) as log:
            log.error('Just works')
            log.fatal('I ♥ Mojolicious')
            log.debug('Does not work')
            log = None
            content = u(slurp(path))
            like_ok(content, r'\[.*\] \[error\] Just works', 'right error message')
            like_ok(content, '\\[.*\\] \\[fatal\\] I ♥ Mojolicious', 'right fatal message')
            unlike_ok(content, r'\[.*\] \[debug\] Does not work', 'no debug message')

    with TemporaryDirectory() as tmpdir:
        # Logging to handle
        path = os.path.join(tmpdir, 'test_handle.log')
        handle = codecs.open(path, 'w', 'utf-8')
        with Pyjo.Log.new(handle=handle) as log:
            log.error('Just works')
            log.fatal('I ♥ Mojolicious')
            log.debug('Works too')
            content = u(slurp(path))
            like_ok(content, r'\[.*\] \[error\] Just works', 'right error message')
            like_ok(content, '\\[.*\\] \\[fatal\\] I ♥ Mojolicious', 'right fatal message')
            like_ok(content, r'\[.*\] \[debug\] Works too', 'no debug message')

    # Formatting
    log = Pyjo.Log.new()
    like_ok(log.format(time.time(), 'debug', 'Test 123'), r'^\[.*\] \[debug\] Test 123\n$', 'right format')
    like_ok(log.format(time.time(), 'debug', 'Test', '1', '2', '3'), r'^\[.*\] \[debug\] Test\n1\n2\n3\n$', 'right format')
    like_ok(log.format(time.time(), 'error', 'I ♥ Mojolicious'), '^\\[.*\\] \\[error\\] I ♥ Mojolicious\\n$', 'right format')
    log.format = lambda t, level, *lines: ':'.join(map(str, [level, int(t)] + list(lines)))
    like_ok(log.format(time.time(), 'debug', 'Test', '1', '2', '3'), r'^debug:\d+:Test:1:2:3$', 'right format')

    # Events
    log = Pyjo.Log.new()
    msgs = []
    log.unsubscribe('message')

    @log.on
    def message(log, level, lines):
        msgs.append(level)
        msgs.extend(lines)

    log.debug('Test', 1, 2, 3)
    is_deeply_ok(msgs, ['debug', 'Test', 1, 2, 3], 'right message')
    msgs = []
    log.info('Test', 1, 2, 3)
    is_deeply_ok(msgs, ['info', 'Test', 1, 2, 3], 'right message')
    msgs = []
    log.warn('Test', 1, 2, 3)
    is_deeply_ok(msgs, ['warn', 'Test', 1, 2, 3], 'right message')
    msgs = []
    log.error('Test', 1, 2, 3)
    is_deeply_ok(msgs, ['error', 'Test', 1, 2, 3], 'right message')
    msgs = []
    log.fatal('Test', 1, 2, 3)
    is_deeply_ok(msgs, ['fatal', 'Test', 1, 2, 3], 'right message')

    # History
    with TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, 'test_history.log')
        with Pyjo.Log.new(max_history_size=2, level='info', path=path) as log:
            log.error('First')
            log.fatal('Second')
            log.debug('Third')
            log.info('Fourth', 'Fifth')
            history = log.history
            content = u(slurp(path))
            like_ok(content, r'\[.*\] \[error\] First\n', 'right error message')
            like_ok(content, r'\[.*\] \[info\] Fourth\nFifth\n', 'right info message')
            unlike_ok(content, r'debug', 'no debug message')
            like_ok(str(history[0][0]), r'^[0-9.]+$', 'right epoch time')
            is_ok(history[0][1], 'fatal', 'right level')
            is_ok(history[0][2], 'Second', 'right message')
            is_ok(history[1][1], 'info', 'right level')
            is_ok(history[1][2], 'Fourth', 'right message')
            is_ok(history[1][3], 'Fifth', 'right message')
            throws_ok(lambda: history[2], IndexError, 'no more messages')

    # "debug"
    is_ok(log.set(level='debug').level, 'debug', 'right level')
    ok(log.is_debug, '"debug" log level is active')
    ok(log.is_info, '"info" log level is active')
    ok(log.is_warn, '"warn" log level is active')
    ok(log.is_error, '"error" log level is active')

    # "info"
    is_ok(log.set(level='info').level, 'info', 'right level')
    ok(not log.is_debug, '"debug" log level is inactive')
    ok(log.is_info, '"info" log level is active')
    ok(log.is_warn, '"warn" log level is active')
    ok(log.is_error, '"error" log level is active')

    # "warn"
    is_ok(log.set(level='warn').level, 'warn', 'right level')
    ok(not log.is_debug, '"debug" log level is inactive')
    ok(not log.is_info, '"info" log level is inactive')
    ok(log.is_warn, '"warn" log level is active')
    ok(log.is_error, '"error" log level is active')

    # "error"
    is_ok(log.set(level='error').level, 'error', 'right level')
    ok(not log.is_debug, '"debug" log level is inactive')
    ok(not log.is_info, '"info" log level is inactive')
    ok(not log.is_warn, '"warn" log level is inactive')
    ok(log.is_error, '"error" log level is active')

    # "fatal"
    is_ok(log.set(level='fatal').level, 'fatal', 'right level')
    ok(not log.is_debug, '"debug" log level is inactive')
    ok(not log.is_info, '"info" log level is inactive')
    ok(not log.is_warn, '"warn" log level is inactive')
    ok(not log.is_error, '"error" log level is inactive')

    done_testing()
