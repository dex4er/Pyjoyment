import Pyjo.Date

from Pyjo.Test import *

import time


with subtest('Synopsis'):
    # Parse
    date = Pyjo.Date.new('Sun, 06 Nov 1994 08:49:37 GMT')
    is_ok(date.epoch, 784111777, 'parse')

    # Build
    before = time.time()
    date = Pyjo.Date.new(time.time() + 60)
    ok(date.epoch > before, 'build')

with subtest('epoch'):
    date = Pyjo.Date.new()
    ok(date.epoch >= int(before), 'current time')
    date.epoch = 784111777
    is_ok(date.to_str(), 'Sun, 06 Nov 1994 08:49:37 GMT', 'set')

with subtest('new'):
    ok(Pyjo.Date.new().epoch >= int(before), 'current time')
    is_ok(Pyjo.Date.new('Sun Nov  6 08:49:37 1994').epoch, 784111777, 'parsed')

with subtest('parse'):
    date = Pyjo.Date.new().parse('Sun Nov  6 08:49:37 1994')
    is_ok(date.epoch, 784111777, 'chained')

    # Epoch
    is_ok(Pyjo.Date.new('784111777').epoch, 784111777, 'epoch')
    is_ok(Pyjo.Date.new('784111777.21').epoch, 784111777.21, 'epoch with fraction')

    # RFC 822/1123
    is_ok(Pyjo.Date.new('Sun, 06 Nov 1994 08:49:37 GMT').epoch, 784111777, 'RFC 822/1123')

    # RFC 850/1036
    is_ok(Pyjo.Date.new('Sunday, 06-Nov-94 08:49:37 GMT').epoch, 784111777, 'RFC 850/1036')

    # Ansi C asctime()
    is_ok(Pyjo.Date.new('Sun Nov  6 08:49:37 1994').epoch, 784111777, 'asctime()')

    # RFC 3339
    is_ok(Pyjo.Date.new('1994-11-06T08:49:37Z').epoch, 784111777, 'RFC 3339')
    is_ok(Pyjo.Date.new('1994-11-06T08:49:37').epoch, 784111777, 'RFC 3339 without offset')
    is_ok(Pyjo.Date.new('1994-11-06T08:49:37.21Z').epoch, 784111777.21, 'RFC 3339 with fraction')
    is_ok(Pyjo.Date.new('1994-11-06T08:49:37+01:00').epoch, 784108177, 'RFC 3339 with positive offset')
    is_ok(Pyjo.Date.new('1994-11-06T08:49:37-01:00').epoch, 784115377, 'RFC 3339 with negative offset')

with subtest('to_datetime'):
    is_ok(Pyjo.Date.new(784111777).to_datetime(), '1994-11-06T08:49:37Z', 'RFC 3339')
    is_ok(Pyjo.Date.new(784111777.21).to_datetime(), '1994-11-06T08:49:37.21Z', 'RFC 3339 with fraction')

with subtest('to_str'):
    is_ok(Pyjo.Date.new(784111777).to_str(), 'Sun, 06 Nov 1994 08:49:37 GMT', 'HTTP date')

with subtest('bool'):
    ok(bool(Pyjo.Date.new('Wrong')), 'always true')

with subtest('str'):
    is_ok(str(Pyjo.Date.new(784111777)), 'Sun, 06 Nov 1994 08:49:37 GMT', 'alias for to_str')

done_testing()
