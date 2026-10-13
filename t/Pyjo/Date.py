import Pyjo.Date

from Pyjo.Test import *

import time


with subtest('RFC 822/1123'):
    date = Pyjo.Date.new('Sun, 06 Nov 1994 08:49:37 GMT')
    is_ok(date.epoch, 784111777, 'right epoch value')
    date = Pyjo.Date.new('Fri, 13 May 2011 10:00:24 GMT')
    is_ok(date.epoch, 1305280824, 'right epoch value')

with subtest('RFC 850/1036'):
    is_ok(Pyjo.Date.new('Sunday, 06-Nov-94 08:49:37 GMT').epoch, 784111777, 'right epoch value')
    is_ok(Pyjo.Date.new('Friday, 13-May-11 10:00:24 GMT').epoch, 1305280824, 'right epoch value')

with subtest('RFC 3339'):
    is_ok(Pyjo.Date.new('2014-08-20T20:45:00').epoch, 1408567500, 'right epoch value')
    is_ok(Pyjo.Date.new(1408567500).to_rfc3339(), '2014-08-20T20:45:00Z', 'right format')
    is_ok(Pyjo.Date.new('2014-08-20T20:45:00.01').epoch, 1408567500.01, 'right epoch value')
    is_ok(Pyjo.Date.new('2014-08-20T20:45:00-00:46').epoch, 1408570260, 'right epoch value')
    is_ok(Pyjo.Date.new(1408570260).to_rfc3339(), '2014-08-20T21:31:00Z', 'right format')
    is_ok(Pyjo.Date.new('2014-08-20t20:45:00-01:46').epoch, 1408573860, 'right epoch value')
    is_ok(Pyjo.Date.new('2014-08-20t20:45:00+01:46').epoch, 1408561140, 'right epoch value')
    is_ok(Pyjo.Date.new(1408561140).to_rfc3339(), '2014-08-20T18:59:00Z', 'right format')
    is_ok(Pyjo.Date.new('1994-11-06T08:49:37Z').epoch, 784111777, 'right epoch value')
    is_ok(Pyjo.Date.new('1994-11-06t08:49:37.33z').epoch, 784111777.33, 'right epoch value')
    is_ok(Pyjo.Date.new(784111777.33).to_rfc3339(), '1994-11-06T08:49:37.33Z', 'right format')

with subtest('Special cases'):
    is_ok(Pyjo.Date.new('Sun ,  06-Nov-1994  08:49:37  UTC').epoch, 784111777, 'right epoch value')
    is_ok(Pyjo.Date.new('Sunday,06  Nov  94  08:49:37  UTC').epoch, 784111777, 'right epoch value')
    is_ok(Pyjo.Date.new('Sunday 06 Nov 94 08:49:37UTC').epoch, 784111777, 'right epoch value')
    is_ok(Pyjo.Date.new('2014-08-20  20:45:00').epoch, 1408567500, 'right epoch value')

with subtest('ANSI C asctime()'):
    is_ok(Pyjo.Date.new('Sun Nov  6 08:49:37 1994').epoch, 784111777, 'right epoch value')
    is_ok(Pyjo.Date.new('Fri May 13 10:00:24 2011').epoch, 1305280824, 'right epoch value')

with subtest('Invalid string'):
    is_ok(Pyjo.Date.new('').epoch, None, 'no epoch value')
    is_ok(Pyjo.Date.new('123 abc').epoch, None, 'no epoch value')
    is_ok(Pyjo.Date.new('abc').epoch, None, 'no epoch value')
    is_ok(Pyjo.Date.new('Xxx, 00 Xxx 0000 00:00:00 XXX').epoch, None, 'no epoch value')
    is_ok(Pyjo.Date.new('Sun, 06 Nov 1994 08:49:37 GMT GARBAGE').epoch, None, 'no epoch value')
    is_ok(Pyjo.Date.new('Sunday, 06-Nov-94 08:49:37 GMT GARBAGE').epoch, None, 'no epoch value')
    is_ok(Pyjo.Date.new('Sun Nov  6 08:49:37 1994 GARBAGE').epoch, None, 'no epoch value')
    is_ok(Pyjo.Date.new('Fri, 75 May 2011 99:99:99 GMT').epoch, None, 'no epoch value')
    is_ok(Pyjo.Date.new('0000-00-00T00:00:00+01:00').epoch, None, 'no epoch value')

with subtest('to_str'):
    date = Pyjo.Date.new(784111777)
    is_ok(str(date), 'Sun, 06 Nov 1994 08:49:37 GMT', 'right format')
    date = Pyjo.Date.new(1305280824)
    is_ok(date.to_str(), 'Fri, 13 May 2011 10:00:24 GMT', 'right format')
    date = Pyjo.Date.new('1305280824.23')
    is_ok(date.to_str(), 'Fri, 13 May 2011 10:00:24 GMT', 'right format')

with subtest('Current time roundtrips'):
    before = int(time.time())
    ok(Pyjo.Date.new(Pyjo.Date.new().to_str()).epoch >= before, 'successful roundtrip')
    ok(Pyjo.Date.new(Pyjo.Date.new().to_rfc3339()).epoch >= before, 'successful roundtrip')

with subtest('Zero time checks'):
    date = Pyjo.Date.new(0)
    is_ok(date.epoch, 0, 'right epoch value')
    is_ok(str(date), 'Thu, 01 Jan 1970 00:00:00 GMT', 'right format')
    is_ok(Pyjo.Date.new('Thu, 01 Jan 1970 00:00:00 GMT').epoch, 0, 'right epoch value')

with subtest('No epoch value'):
    date = Pyjo.Date.new()
    ok(date.parse('Mon, 01 Jan 1900 00:00:00'), 'right format')
    is_ok(date.epoch, None, 'no epoch value')

done_testing()
