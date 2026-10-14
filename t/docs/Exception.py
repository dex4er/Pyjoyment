from Pyjo.Test import *

import contextlib
import io
import re
import traceback


with subtest('Synopsis'):
    import Pyjo.Exception

    # Create exception classes
    class MyApp_X_Foo(Pyjo.Exception.object):
        pass

    class MyApp_X_Bar(Pyjo.Exception.object):
        pass

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        # Throw exceptions and handle them gracefully
        from Pyjo.Exception import check

        try:
            MyApp_X_Foo.throw('Something went wrong!')
        except Exception as e:
            check(
                e,
                [
                    (MyApp_X_Foo, lambda e: print(f'Foo: {e}')),
                    (MyApp_X_Bar, lambda e: print(f'Bar: {e}')),
                ],
            )

        # Generate exception classes on demand
        from Pyjo.Exception import check, throw

        try:
            throw('MyApp.X.Name', 'The name Minion is already taken')
        except Exception as e:
            check(
                e,
                [
                    ('MyApp.X.Name', lambda e: print(f'Name error: {e}')),
                    ('default', lambda e: print(f'Error: {e}')),
                ],
            )
    like_ok(
        output.getvalue(),
        r'^Foo: Something went wrong! at .*\n\nName error: The name Minion is already taken at ',
        'output',
    )


def dangerous_code():
    raise OSError('Could not open file')


with subtest('check'):
    boolean = check(MyApp_X_Foo.new(), [(MyApp_X_Foo, lambda e: None)])
    ok(boolean, 'handled')

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        # Handle various types of exceptions
        try:
            dangerous_code()
        except Exception as e:
            check(
                e,
                [
                    (MyApp_X_Foo, lambda e: print(f'Foo: {e}')),
                    (re.compile(r'^Could not open'), lambda e: print(f'Open error: {e}')),
                    ('default', lambda e: print(f'Something went wrong: {e}')),
                ],
            )

        # Catch MyApp_X_Foo object or a specific string exception
        try:
            dangerous_code()
        except Exception as e:
            check(
                e,
                [
                    (MyApp_X_Foo, lambda e: print(f'Foo: {e}')),
                    (re.compile(r'^Could not open'), lambda e: print(f'Open error: {e}')),
                ],
            )
    is_ok(output.getvalue(), 'Open error: Could not open file\nOpen error: Could not open file\n', 'output')

    # Handle MyApp_X_Foo and MyApp_X_Bar the same
    def foo_bar():
        try:
            MyApp_X_Bar.throw('bar')
        except Exception as e:
            check(
                e,
                [
                    ([MyApp_X_Foo, MyApp_X_Bar], lambda e: Pyjo.Exception.object.throw(f'Foo/Bar: {e}')),
                ],
            )

    throws_ok(foo_bar, re.compile(r'^Foo/Bar: bar'), 'thrown by the handler')

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        # Use "default" to catch everything
        try:
            dangerous_code()
        except Exception as e:
            check(
                e,
                [
                    ('default', lambda e: print(f'Error: {e}')),
                ],
            )
    is_ok(output.getvalue(), 'Error: Could not open file\n', 'output')

with subtest('throw'):
    from Pyjo.Exception import raise_

    throws_ok(lambda: throw('Something went wrong!'), Pyjo.Exception.object, 'Pyjo.Exception')
    throws_ok(lambda: throw('MyApp.X.Foo', 'Something went wrong!'), re.compile(r'^Something'), 'by name')
    throws_ok(lambda: throw(MyApp_X_Foo, 'Something went wrong!'), MyApp_X_Foo, 'by class')
    is_ok(raise_, throw, 'alias')

with subtest('new'):
    e = Pyjo.Exception.new()
    is_ok(e.message, 'Exception!', 'default')
    e = Pyjo.Exception.new('Died at test.py line 3.')
    is_ok(e.message, 'Died at test.py line 3.', 'message')
    try:
        raise ValueError('Something went wrong!')
    except ValueError as err:
        e = Pyjo.Exception.new(err)
    is_ok(e.message, 'Something went wrong!', 'message of an exception')
    is_ok(e.frames[0].name, '<module>', 'frames of an exception')

with subtest('frames'):
    frames = e.frames
    frame1, frame2 = traceback.FrameSummary('a.py', 1, 'a'), traceback.FrameSummary('b.py', 2, 'b')
    e.frames = [frame1, frame2]
    is_ok(len(e.frames), 2, 'frames')

    # Extract information from the last frame
    filename, lineno, name, line = e.frames[-1]
    is_deeply_ok([filename, lineno, name], ['b.py', 2, 'b'], 'last frame')

with subtest('line'):
    line = e.line
    e.line = [3, 'raise Exception()']
    is_deeply_ok(e.line, [3, 'raise Exception()'], 'line')

with subtest('lines_after'):
    lines = e.lines_after
    e.lines_after = [[4, 'print(foo)'], [5, 'print(bar)']]
    is_ok(len(e.lines_after), 2, 'lines_after')

with subtest('lines_before'):
    lines = e.lines_before
    e.lines_before = [[1, 'foo = 23'], [2, 'bar = 24']]
    is_ok(len(e.lines_before), 2, 'lines_before')

with subtest('message'):
    msg = e.message
    e.message = 'Died at test.py line 3.'
    is_ok(e.message, 'Died at test.py line 3.', 'message')

with subtest('verbose'):
    boolean = e.verbose
    e.verbose = True
    ok(e.verbose, 'verbose')

with subtest('__bool__'):
    boolean = bool(Pyjo.Exception.new(''))
    ok(boolean, 'always true')

with subtest('__str__'):
    string = str(Pyjo.Exception.new('Test!'))
    is_ok(string, 'Test!\n', 'string')

with subtest('inspect'):
    e = Pyjo.Exception.new('Died at template line 2.')
    e = e.inspect()
    is_deeply_ok(e.line, [], 'no such file')
    source1, source2 = 'a\nb\nc', 'A\nB\nC'
    e = e.inspect(source1, source2)
    is_deeply_ok(e.line, [2, 'b', 'B'], 'from the sources')

with subtest('throw'):
    throws_ok(lambda: Pyjo.Exception.object.throw('Something went wrong!'), re.compile(r'^Something'), 'throw')

    # Longer version
    def longer():
        raise Pyjo.Exception.new('Something went wrong!').trace()

    throws_ok(longer, re.compile(r'^Something went wrong! at .* line'), 'longer version')

with subtest('to_str'):
    string = Pyjo.Exception.new('Test!').to_str()
    is_ok(string, 'Test!\n', 'string')

with subtest('trace'):
    e = e.trace()
    e = e.trace(1)
    is_ok(e.frames[0].name, '<module>', 'skip 1')

    # Skip 3 call frames
    e.trace(3)

    # Skip no call frames
    e.trace(0)
    is_ok(e.frames[0].name, 'trace', 'skip none')

done_testing()
