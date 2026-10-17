import Pyjo.GetOpt

from Pyjo.Test import *

import contextlib
import io
import re
import sys


# Not in Mojolicious: the tests of Pyjo.GetOpt, which follows Getopt::Long as Mojo::Util configures it; the expected
# values are those of getopt of Mojo::Util with the same arguments


def parse(args, *options, pass_through=False):
    getopt = Pyjo.GetOpt.new(pass_through=pass_through)
    for spec in options:
        getopt.option(spec)
    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr):
        result = getopt.parse(args)
    return result, stderr.getvalue()


with subtest('Strings'):
    args = ['--test=foo']
    result, _ = parse(args, 't|test=s')
    ok(result, 'success')
    is_ok(result.test, 'foo', 'long option with value')
    is_deeply_ok(args, [], 'option removed')
    is_ok(parse(['--t', 'foo'], 't|test=s')[0].test, 'foo', 'short name with two dashes')
    is_ok(parse(['-test', 'foo'], 't|test=s')[0].test, 'foo', 'long name with one dash')
    is_ok(parse(['-test=foo'], 't|test=s')[0].test, 'foo', 'long name with one dash and value')
    is_ok(parse(['-t', '-x'], 't|test=s')[0].test, '-x', 'value that starts with a dash')
    is_ok(parse(['-t', 'a', '-t', 'b'], 't|test=s')[0].test, 'b', 'last value')
    is_ok(parse([], 't|test=s')[0].test, None, 'no value')

with subtest('Numbers'):
    result, _ = parse(['-b', '23', '--ratio', '0.5'], 'b|backlog=i', 'r|ratio=f')
    is_ok(result.backlog, 23, 'integer')
    is_ok(result.ratio, 0.5, 'float')
    result, stderr = parse(['-b', 'x'], 'b|backlog=i')
    ok(not result, 'failure')
    is_ok(result.backlog, None, 'no value')
    like_ok(stderr, r'^Value "x" invalid for option b \(integer number expected\)\n', 'right warning')
    like_ok(parse(['-r', 'x'], 'r|ratio=f')[1], r'^Value "x" invalid for option r \(real number expected\)\n', 'real')
    is_ok(parse(['-c', '5', 'x'], 'c|count:i')[0].count, 5, 'optional number')

with subtest('Optional values'):
    result, _ = parse(['-p', '-l', 'x'], 'p|proxy:s@', 'l|lang=s')
    is_deeply_ok(result.proxy, [''], 'no value')
    is_ok(result.lang, 'x', 'next option')
    is_deeply_ok(parse(['-p', 'net', '-p'], 'p|proxy:s@')[0].proxy, ['net', ''], 'values')
    is_deeply_ok(parse(['--proxy='], 'p|proxy:s@')[0].proxy, [''], 'empty value')
    is_ok(parse(['-c'], 'c|count:i')[0].count, 0, 'no number')
    is_deeply_ok(parse([], 'p|proxy:s@')[0].proxy, [], 'no option')

with subtest('Flags'):
    result, _ = parse(['-h', '-v', '-v', '--no-color'], 'h|help', 'v|verbose+', 'color!')
    is_ok(result.help, True, 'flag')
    is_ok(result.verbose, 2, 'incremented')
    is_ok(result.color, False, 'negated')
    is_ok(parse(['--nocolor'], 'color!')[0].color, False, 'negated without dash')
    is_ok(parse(['--color'], 'color!')[0].color, True, 'negatable')
    is_ok(parse([], 'h|help')[0].help, None, 'no flag')

with subtest('Arguments'):
    args = ['a', '-t', 'foo', 'b', '--', '-t', 'bar']
    is_ok(parse(args, 't|test=s')[0].test, 'foo', 'right value')
    is_deeply_ok(args, ['a', 'b', '-t', 'bar'], 'arguments in order, without the end of the options')
    args = ['-', '-t', 'foo']
    parse(args, 't|test=s')
    is_deeply_ok(args, ['-'], 'a dash is an argument')

with subtest('Errors'):
    args = ['--lang', 'de', '--lnag', 'x']
    result, stderr = parse(args, 'l|lang=s')
    ok(not result, 'failure')
    is_ok(result.lang, 'de', 'value before the error')
    is_deeply_ok(args, ['x'], 'unknown option removed')
    like_ok(stderr, r'^Unknown option: lnag\n', 'right warning')
    like_ok(parse(['-T', 'foo'], 't|test=s')[1], r'^Unknown option: T\n', 'case sensitive')
    like_ok(parse(['--tes', 'foo'], 't|test=s')[1], r'^Unknown option: tes\n', 'no abbreviation')
    like_ok(parse(['-tfoo'], 't|test=s')[1], r'^Unknown option: tfoo\n', 'no bundling')
    result, stderr = parse(['-t'], 't|test=s')
    ok(not result, 'failure')
    like_ok(stderr, r'^Option t requires an argument\n', 'right warning')
    like_ok(parse(['--help=x'], 'h|help')[1], r'^Option help does not take an argument\n', 'flag with value')
    throws_ok(
        lambda: Pyjo.GetOpt.new().option('t|test=x'), re.compile(r'^Error in option spec: "t\|test=x"'), 'bad spec'
    )

with subtest('Pass through'):
    args = ['-t', 'foo', '-x', 'bar', '--', '-y']
    result, stderr = parse(args, 't|test=s', pass_through=True)
    ok(result, 'success')
    is_ok(result.test, 'foo', 'right value')
    is_deeply_ok(args, ['-x', 'bar', '--', '-y'], 'unknown options and the end of the options kept')
    is_ok(stderr, '', 'no warning')

with subtest('Targets'):
    getopt = Pyjo.GetOpt.new()
    listen = []
    getopt.option('l|listen=s', listen)
    called = []

    @getopt.on('b|backlog=i')
    def backlog(name, value):
        called.append((name, value))

    getopt.on('k|insecure', lambda name, value: called.append((name, value)))
    result = getopt.parse(['-l', 'a', '--listen', 'b', '-b', '5', '-k'])
    ok(result, 'success')
    is_deeply_ok(listen, ['a', 'b'], 'list')
    is_deeply_ok(called, [('backlog', 5), ('insecure', True)], 'callbacks')
    ok(callable(backlog), 'decorator returns the callback')
    ok(not hasattr(result, 'listen'), 'no value of a target in the result')

with subtest('sys.argv'):
    argv = sys.argv
    try:
        sys.argv = [argv[0], '-t', 'foo', 'bar']
        is_ok(Pyjo.GetOpt.new().option('t|test=s').parse().test, 'foo', 'right value')
        is_deeply_ok(sys.argv, [argv[0], 'bar'], 'options removed')
    finally:
        sys.argv = argv

done_testing()
