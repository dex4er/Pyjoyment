import Pyjo.Exception

from Pyjo.Exception import check, raise_, throw
from Pyjo.File import tempdir
from Pyjo.Test import *

import inspect
import os
import re
import traceback


class MojoTest:
    class X:
        class Foo(Pyjo.Exception.object):
            pass

        class Bar(Pyjo.Exception.object):
            pass

        class Yada(Bar):
            pass


def name(cls):
    return f'{cls.__module__}.{cls.__qualname__}'


def error(cb):
    try:
        cb()
    except Exception as e:
        return e


with subtest('Verbose'):
    ok(not Pyjo.Exception.new().verbose, 'not verbose')
    os.environ['PYJO_EXCEPTION_VERBOSE'] = '1'
    ok(Pyjo.Exception.new().verbose, 'verbose')
    del os.environ['PYJO_EXCEPTION_VERBOSE']

with subtest('Basics'):
    e = Pyjo.Exception.new()
    is_ok(e.message, 'Exception!', 'right message')
    is_ok(str(e), 'Exception!\n', 'right message')
    e = Pyjo.Exception.new('Test!')
    is_ok(e.message, 'Test!', 'right message')
    is_ok(str(e), 'Test!\n', 'right message')

with subtest('Context information'):
    # fmt: off
    line = inspect.currentframe().f_lineno
    try:

        # test

        wrapper = lambda: Pyjo.Exception.object.throw('Works!')  # noqa: E731
        wrapper()

        # test

    except Exception as err:
        e = err
    # fmt: on
    isa_ok(e, Pyjo.Exception.object, 'right class')
    like_ok(str(e.inspect()), r'^Works!', 'right result')
    like_ok(e.frames[0].filename, r'Exception\.py', 'right file')
    is_ok(e.lines_before[0][0], line, 'right number')
    is_ok(e.lines_before[0][1], '    line = inspect.currentframe().f_lineno', 'right line')
    is_ok(e.lines_before[1][0], line + 1, 'right number')
    is_ok(e.lines_before[1][1], '    try:', 'right line')
    is_ok(e.lines_before[2][0], line + 2, 'right number')
    ok(not e.lines_before[2][1], '  empty line')
    is_ok(e.lines_before[3][0], line + 3, 'right number')
    is_ok(e.lines_before[3][1], '        # test', 'right line')
    is_ok(e.lines_before[4][0], line + 4, 'right number')
    ok(not e.lines_before[4][1], 'empty line')
    is_ok(e.line[0], line + 5, 'right number')
    is_ok(e.line[1], "        wrapper = lambda: Pyjo.Exception.object.throw('Works!')  # noqa: E731", 'right line')
    is_ok(e.lines_after[0][0], line + 6, 'right number')
    is_ok(e.lines_after[0][1], '        wrapper()', 'right line')
    is_ok(e.lines_after[1][0], line + 7, 'right number')
    ok(not e.lines_after[1][1], 'empty line')
    is_ok(e.lines_after[2][0], line + 8, 'right number')
    is_ok(e.lines_after[2][1], '        # test', 'right line')
    is_ok(e.lines_after[3][0], line + 9, 'right number')
    ok(not e.lines_after[3][1], 'empty line')
    is_ok(e.lines_after[4][0], line + 10, 'right number')
    is_ok(e.lines_after[4][1], '    except Exception as err:', 'right line')

with subtest('Trace'):

    def wrapper2(*args):
        return Pyjo.Exception.new().trace(*args)

    def wrapper1(*args):
        return wrapper2(*args)

    like_ok(wrapper1().frames[0].name, r'wrapper2', 'right subroutine')
    like_ok(wrapper1(0).frames[0].name, r'trace', 'right subroutine')
    like_ok(wrapper1(1).frames[0].name, r'wrapper2', 'right subroutine')
    like_ok(wrapper1(2).frames[0].name, r'wrapper1', 'right subroutine')

with subtest('Inspect (UTF-8)'):
    # Unlike Mojolicious: the files that Mojo has in t/mojo/exception are made
    # in a temporary directory
    dir = tempdir()
    dir.child('utf8.txt').spew("use strict;\nuse warnings;\nuse utf8;\n\nmy $s = 'Über•résumé';\n")
    dir.child('non_utf8.txt').spew(b"use strict;\nuse warnings;\nno utf8;\n\nmy $s = '\xdcber\x95r\xe9sum\xe9';\n")
    file = dir.child('utf8.txt')
    e = Pyjo.Exception.new(f'Whatever at {file} line 3.')
    is_deeply_ok(e.lines_before, [], 'no lines')
    is_deeply_ok(e.line, [], 'no line')
    is_deeply_ok(e.lines_after, [], 'no lines')
    e.inspect()
    is_deeply_ok(e.lines_before[-1], [2, 'use warnings;'], 'right line')
    is_deeply_ok(e.line, [3, 'use utf8;'], 'right line')
    is_deeply_ok(e.lines_after[0], [4, ''], 'right line')

    e = Pyjo.Exception.new(f'Died at {file} line 4.').inspect()
    is_deeply_ok(e.lines_before[-1], [3, 'use utf8;'], 'right line')
    is_deeply_ok(e.line, [4, ''], 'right line')
    is_deeply_ok(e.lines_after[0], [5, "my $s = 'Über•résumé';"], 'right line')

    file = file.sibling('non_utf8.txt')
    e = Pyjo.Exception.new(f'Whatever at {file} line 3.')
    is_deeply_ok(e.lines_before, [], 'no lines')
    is_deeply_ok(e.line, [], 'no line')
    is_deeply_ok(e.lines_after, [], 'no lines')
    e.inspect().inspect()
    is_deeply_ok(e.lines_before[-1], [2, 'use warnings;'], 'right line')
    is_deeply_ok(e.line, [3, 'no utf8;'], 'right line')
    is_deeply_ok(e.lines_after[0], [4, ''], 'right line')
    e = Pyjo.Exception.new(f'Died at {file} line 4.').inspect()
    is_deeply_ok(e.lines_before[-1], [3, 'no utf8;'], 'right line')
    is_deeply_ok(e.line, [4, ''], 'right line')
    is_deeply_ok(e.lines_after[0], [5, "my $s = '\xdcber\x95r\xe9sum\xe9';"], 'right line')

# Not in Mojolicious: an additional source that is shorter, whose missing lines are empty, as undef is in Perl
with subtest('Context of a shorter source'):
    e = Pyjo.Exception.new('Died at template line 2.').inspect('a\nb\nc', 'x')
    is_deeply_ok(e.lines_before, [[1, 'a', 'x']], 'right lines')
    is_deeply_ok(e.line, [2, 'b', ''], 'right line')
    is_deeply_ok(e.lines_after, [[3, 'c', '']], 'right lines')

with subtest('Context'):
    e = Pyjo.Exception.new()
    is_ok(e, 'Exception!\n', 'right result')
    e = Pyjo.Exception.new().inspect().inspect()
    is_ok(e, 'Exception!\n', 'right result')
    e = Pyjo.Exception.new('Test!')
    e.frames = [
        traceback.FrameSummary('template', 4, 'Sandbox::sub', lookup_line=False),
        traceback.FrameSummary('MyApp/Test.pm', 3, 'MyApp::Test::sub', lookup_line=False),
        traceback.FrameSummary('foo.pl', 4, 'main::sub', lookup_line=False),
    ]
    e.set(lines_before=[[3, 'foo();']], line=[4, 'die;'], lines_after=[[5, 'bar();']])
    is_ok(e, 'Test! at template line 4.\n', 'right result')
    is_ok(
        e.set(verbose=True),
        """\
Test! at template line 4.
Context:
  3: foo();
  4: die;
  5: bar();
Traceback (most recent call first):
  File "template", line 4, in "Sandbox::sub"
  File "MyApp/Test.pm", line 3, in "MyApp::Test::sub"
  File "foo.pl", line 4, in "main::sub"
""",
        'right result',
    )
    e.set(message='Works!\n', lines_before=[], lines_after=[])
    is_ok(
        e,
        """\
Works!
Context:
  4: die;
Traceback (most recent call first):
  File "template", line 4, in "Sandbox::sub"
  File "MyApp/Test.pm", line 3, in "MyApp::Test::sub"
  File "foo.pl", line 4, in "main::sub"
""",
        'right result',
    )

with subtest('Traceback (real frames)'):

    def mock_frames(e):
        return frame_level2(e)

    def frame_level2(e):
        e.trace()
        e.frames = [f for f in e.frames if os.path.realpath(f.filename) == os.path.realpath(__file__)]
        return e.frames

    e = Pyjo.Exception.new()
    frames = mock_frames(e)
    expected_backtrace = '\n'.join(f'  File "{f.filename}", line {f.lineno}, in "{f.name}"' for f in frames)

    is_ok(
        e.set(verbose=True),
        f"""\
Exception! at {frames[0].filename} line {frames[0].lineno}.
Traceback (most recent call first):
{expected_backtrace}
""",
        'right result',
    )

with subtest('Missing error'):
    e = Pyjo.Exception.new().inspect()
    is_deeply_ok(e.lines_before, [], 'no lines')
    is_deeply_ok(e.line, [], 'no line')
    is_deeply_ok(e.lines_after, [], 'no lines')
    is_ok(e.message, 'Exception!', 'right message')

    e = Pyjo.Exception.new(None).inspect()
    is_deeply_ok(e.lines_before, [], 'no lines')
    is_deeply_ok(e.line, [], 'no line')
    is_deeply_ok(e.lines_after, [], 'no lines')
    is_ok(e.message, 'Exception!', 'right message')

    e = Pyjo.Exception.new('').inspect()
    is_deeply_ok(e.lines_before, [], 'no lines')
    is_deeply_ok(e.line, [], 'no line')
    is_deeply_ok(e.lines_after, [], 'no lines')
    is_ok(e.message, '', 'right message')

with subtest('Check (string exception)'):
    result = None

    def handler(e):
        global result
        result = e

    def result_is(value):
        def cb(e):
            global result
            result = value

        return cb

    err = error(lambda: Pyjo.Exception.object.throw('test1\n'))
    ok(check(err, [('default', handler)]), 'exception handled')
    is_ok(str(result), 'test1\n', 'exception arrived in handler')
    result = None
    err = error(lambda: Pyjo.Exception.object.throw('test2\n'))
    ok(check(err, [('default', handler)]), 'exception handled')
    is_ok(str(result), 'test2\n', 'exception arrived in handler')
    result = None
    err = error(lambda: Pyjo.Exception.object.throw('test3\n'))
    check(
        err,
        [
            ('default', result_is('fail')),
            (re.compile(r'^test2'), result_is('fail')),
            (re.compile(r'^test3'), result_is('test10')),
            (re.compile(r'^test4'), result_is('fail')),
        ],
    )
    is_ok(result, 'test10', 'regular expression matched')
    result = None
    check(
        'test4\n',
        [
            (re.compile(r'^test3'), result_is('fail')),
            (re.compile(r'^test4'), result_is('test11')),
            (re.compile(r'^test5'), result_is('fail')),
        ],
    )
    is_ok(result, 'test11', 'regular expression matched')

with subtest('Check (exception objects)'):
    result = None
    err = error(lambda: MojoTest.X.Foo.throw('fail'))
    check(
        err,
        [
            ('default', result_is('fail')),
            ('MojoTest.X.Foo', result_is('test12')),
            ('MojoTest.X.Bar', result_is('fail')),
        ],
    )
    is_ok(result, 'test12', 'class matched')
    result = None
    err = error(lambda: MojoTest.X.Bar.throw('fail'))
    check(err, [('MojoTest.X.Foo', result_is('fail')), ('MojoTest.X.Bar', result_is('test13'))])
    is_ok(result, 'test13', 'class matched')
    result = None
    check(
        MojoTest.X.Yada.new('fail'),
        [
            (re.compile(r'^MojoTest'), result_is('fail')),
            ('MojoTest.X.Foo', result_is('fail')),
            ('MojoTest.X.Bar', result_is('test14')),
        ],
    )
    is_ok(result, 'test14', 'class matched')
    result = None
    check(
        MojoTest.X.Yada.new('whatever'),
        [('MojoTest.X.Foo', result_is('fail')), (re.compile(r'^whatever'), result_is('test23'))],
    )
    is_ok(result, 'test23', 'regex matched')

with subtest('Check (multiple)'):
    result = None
    check(
        MojoTest.X.Yada.new('whatever'),
        [(['MojoTest.X.Foo', 'MojoTest.X.Bar'], result_is('test15')), ('default', result_is('fail'))],
    )
    is_ok(result, 'test15', 'class matched')
    result = None
    check(
        MojoTest.X.Bar.new('whatever'),
        [
            (['MojoTest.X.Foo', 'MojoTest.X.Yada'], result_is('fail')),
            (['MojoTest.X.Bar'], result_is('test16')),
        ],
    )
    is_ok(result, 'test16', 'class matched')

with subtest('Check (rethrow)'):
    err = error(lambda: check('test5\n', [(re.compile(r'test4'), lambda e: Pyjo.Exception.object.throw('fail'))]))
    is_ok(err, 'test5\n', 'exception has been rethrown')

with subtest('Check (nothing)'):
    ok(not check(None, [('default', lambda e: Pyjo.Exception.object.throw('fail'))]), 'no exception')
    ok(not check('', [('default', lambda e: Pyjo.Exception.object.throw('fail'))]), 'no exception')

with subtest('Check (bad spec)'):
    # Unlike Mojolicious: Mojo asks for an "Array reference"
    throws_ok(
        lambda: check('test', {'default': lambda e: None}),
        re.compile(r'List of pattern/handler pairs required to dispatch exceptions'),
        'right error',
    )

    throws_ok(
        lambda: check('test', ['default']),
        re.compile(r'List of pattern/handler pairs required to dispatch exceptions'),
        'right error',
    )

with subtest('Raise'):
    err = error(lambda: raise_('MyApp.X.Baz', 'test19'))
    is_ok(name(type(err)), 'MyApp.X.Baz', 'is a MyApp.X.Baz')
    isa_ok(err, Pyjo.Exception.object, 'is a Pyjo.Exception')
    like_ok(str(err), r'^test19', 'right error')
    baz = type(err)
    err = error(lambda: raise_('MyApp.X.Baz', 'test20'))
    isa_ok(err, baz, 'is a MyApp.X.Baz')
    isa_ok(err, Pyjo.Exception.object, 'is a Pyjo.Exception')
    like_ok(str(err), r'^test20', 'right error again')
    err = error(lambda: raise_('test22'))
    isa_ok(err, Pyjo.Exception.object, 'is a Pyjo.Exception')
    like_ok(str(err), r'^test22', 'right error')
    err = error(lambda: raise_(f'{__name__}.MojoTest.X.Foo', 'test21'))
    isa_ok(err, MojoTest.X.Foo, 'is a MojoTest.X.Foo')
    like_ok(str(err), r'^test21', 'right error')
    err = error(lambda: raise_('Pyjo.Base.object', 'fail'))
    like_ok(str(err), r'^Pyjo.Base.object is not a Pyjo.Exception subclass', 'right error')
    # Not in Mojolicious: throw, the name of raise_ that is not a keyword of Python
    err = error(lambda: throw('MyApp.X.Baz', 'test23'))
    isa_ok(err, baz, 'is a MyApp.X.Baz')
    like_ok(str(err), r'^test23', 'right error')

done_testing()
