import Pyjo.Exception

from Pyjo.Exception import check
from Pyjo.Test import *

import pickle
import traceback


class MyError(Pyjo.Exception.object):
    pass


with subtest('An Exception'):
    isa_ok(Pyjo.Exception.new(), Exception, 'exception')
    try:
        MyError.throw('works')
    except MyError as e:
        is_ok(e.message, 'works', 'caught by class')
    try:
        raise Pyjo.Exception.new('raised')
    except Exception as e:
        is_ok(e.args, ('raised',), 'args')
        ok(e.__traceback__ is not None, '__traceback__')

with subtest('From an exception of Python'):
    try:
        int('x')
    except ValueError as caught:
        err = caught
        e = Pyjo.Exception.new(err)
    is_ok(e.message, str(err), 'message')
    is_deeply_ok(
        [(f.filename, f.lineno, f.name) for f in e.frames],
        [(f.filename, f.lineno, f.name) for f in reversed(traceback.extract_tb(err.__traceback__))],
        'frames from traceback.extract_tb(), the most recent first',
    )
    isa_ok(e.frames[0], traceback.FrameSummary, 'frame')

with subtest('check() with exceptions of Python'):
    results = []
    try:
        {}['missing']
    except Exception as e:
        check(e, [(KeyError, lambda e: results.append('KeyError')), ('default', lambda e: results.append('default'))])
    try:
        [][1]
    except Exception as e:
        check(e, [('IndexError', lambda e: results.append('IndexError'))])
    try:
        int('x')
    except Exception as e:
        check(e, [((KeyError, ValueError), lambda e: results.append('ValueError'))])
    is_deeply_ok(results, ['KeyError', 'IndexError', 'ValueError'], 'classes and names of Python')
    throws_ok(lambda: check(KeyError('k'), [(ValueError, lambda e: None)]), KeyError, 'raised again')

with subtest('Pickle'):
    e = pickle.loads(pickle.dumps(MyError.new('works')))
    isa_ok(e, MyError, 'class')
    is_ok(e.message, 'works', 'message')

done_testing()
