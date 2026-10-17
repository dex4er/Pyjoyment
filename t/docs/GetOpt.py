import Pyjo.GetOpt

from Pyjo.Test import *

import contextlib
import io


with subtest('Synopsis'):
    getopt = Pyjo.GetOpt.new()

    # The value goes to the result
    getopt.option('m|mode=s')

    # The values go to a list
    listen = []
    getopt.option('l|listen=s', listen)

    # A callback gets the value
    timeouts = []

    @getopt.on('i|inactivity-timeout=i')
    def timeout(name, value):
        timeouts.append(f'{name}: {value}')

    opts = getopt.parse(['-m', 'production', '-l', 'http://*:8080', '-i', '5', 'myapp.py'])
    ok(opts, 'success')
    is_ok(opts.mode, 'production', 'result')
    is_deeply_ok(listen, ['http://*:8080'], 'list')
    is_deeply_ok(timeouts, ['inactivity_timeout: 5'], 'callback')

with subtest('Description'):
    for args in (['--mode', 'production'], ['--mode=production'], ['-m', 'production']):
        is_ok(Pyjo.GetOpt.new().option('m|mode=s').parse(args).mode, 'production', ' '.join(args))
    args = ['a', '-m', 'production', 'b', '--', '-m']
    Pyjo.GetOpt.new().option('m|mode=s').parse(args)
    is_deeply_ok(args, ['a', 'b', '-m'], 'arguments')

    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr):
        ok(not Pyjo.GetOpt.new().parse(['--unknown']), 'error')
    is_ok(stderr.getvalue(), 'Unknown option: unknown\n', 'warning')

with subtest('Options'):
    getopt = Pyjo.GetOpt.new()

    # A flag, True
    getopt.option('v|verbose')
    ok(getopt.parse(['-v']).verbose, 'flag')

    # A flag that --no-color and --nocolor negate, False
    getopt.option('color!')
    is_ok(getopt.parse(['--no-color']).color, False, 'negated')

    # A counter, which each -v increments
    getopt.option('v|verbose+')
    is_ok(getopt.parse(['-v', '-v']).verbose, 2, 'counter')

    # A string, an integer or a float
    getopt.option('m|mode=s')
    getopt.option('b|backlog=i')
    getopt.option('r|ratio=f')
    opts = getopt.parse(['-m', 'x', '-b', '1', '-r', '0.5'])
    is_deeply_ok([opts.mode, opts.backlog, opts.ratio], ['x', 1, 0.5], 'types')

    # An optional value, which is "" or 0 without it
    getopt.option('p|proxy:s')
    is_ok(getopt.parse(['-p']).proxy, '', 'optional')

    # A list of values in the result
    getopt.option('H|header=s@')
    is_deeply_ok(getopt.parse(['-H', 'a', '-H', 'b']).header, ['a', 'b'], 'list')

    is_ok(Pyjo.GetOpt.new().option('i|inactivity-timeout=i').parse(['-i', '1']).inactivity_timeout, 1, 'name')

with subtest('new'):
    getopt = Pyjo.GetOpt.new(pass_through=True)
    args = ['--unknown', '--', 'x']
    ok(getopt.parse(args), 'pass through')
    is_deeply_ok(args, ['--unknown', '--', 'x'], 'kept')

with subtest('on'):
    getopt = Pyjo.GetOpt.new()
    called = []
    cb = getopt.on('b|backlog=i', lambda name, value: called.append(value))

    @getopt.on('k|keep=i')
    def keep(name, value):
        called.append(value)

    getopt.parse(['-b', '1', '-k', '2'])
    is_deeply_ok(called, [1, 2], 'callbacks')
    ok(callable(cb) and callable(keep), 'returned')

with subtest('option'):
    listen = []
    getopt = Pyjo.GetOpt.new().option('m|mode=s').option('l|listen=s', listen).option('b|backlog=i', lambda n, v: None)
    ok(getopt.parse(['-m', 'x', '-l', 'y', '-b', '1']), 'chained')
    is_deeply_ok(listen, ['y'], 'list')

with subtest('parse'):
    import sys

    argv = sys.argv
    try:
        sys.argv = [argv[0], '--mode', 'production', 'myapp.py']
        opts = Pyjo.GetOpt.new().option('m|mode=s').parse()
        is_ok(opts.mode, 'production', 'sys.argv')
        is_deeply_ok(sys.argv[1:], ['myapp.py'], 'removed')
    finally:
        sys.argv = argv
    opts = Pyjo.GetOpt.new().option('m|mode=s').parse(['--mode', 'production', 'myapp.py'])
    is_ok(opts.mode, 'production', 'list')

done_testing()
