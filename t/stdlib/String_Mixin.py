import Pyjo.Date
import Pyjo.Path
import Pyjo.URL

from Pyjo.Test import *

import math
import statistics
import string
import urllib.parse


url = Pyjo.URL.new('http://example.com/a')
number = Pyjo.Path.new('2.5')
date = Pyjo.Date.new(784111777.5)

with subtest('Formatting'):
    # UP031 "Use format specifiers instead of percent format": the percent format is what is tested
    is_ok('%s' % url, 'http://example.com/a', '%s')  # noqa: UP031
    is_ok('%.1f' % number, '2.5', '%f of the string form')  # noqa: UP031
    is_ok('%d' % date, '784111777', '%d of the epoch')  # noqa: UP031
    is_ok(f'{url!s:>22}', '  http://example.com/a', 'f-string with a conversion')
    is_ok(f'{url:>22}', '  http://example.com/a', 'f-string')
    # UP032 "Use f-string instead of `format` call": str.format is what is tested
    is_ok('{:.4}'.format(url), 'http', 'str.format')  # noqa: UP032
    is_ok(string.Template('$url').substitute(url=url), 'http://example.com/a', 'string.Template')

with subtest('Strings as keys'):
    is_ok({url: 1}['http://example.com/a'], 1, 'dict by the string form')
    ok('http://example.com/a' in {url}, 'set by the string form')
    is_deeply_ok(
        [str(u) for u in sorted([Pyjo.URL.new('b'), Pyjo.URL.new('a')])], ['a', 'b'], 'sorted by the string form'
    )

with subtest('Numbers'):
    is_ok(round(number), 2, 'round')
    is_ok(math.floor(number), 2, 'math.floor')
    is_ok(math.ceil(number), 3, 'math.ceil')
    is_ok(math.trunc(number), 2, 'math.trunc')
    ok(math.isclose(number, 2.5), 'math.isclose')
    is_ok(math.fsum([number, number]), 5.0, 'math.fsum')
    is_ok(statistics.mean([float(number), 3.5]), 3.0, 'statistics.mean')
    is_ok(round(date), 784111778, 'round of the epoch')
    is_ok(math.floor(date), 784111777, 'math.floor of the epoch')

with subtest('Functions that take only a str'):
    throws_ok(lambda: '/'.join([url]), TypeError, 'str.join')
    is_ok('/'.join([str(url)]), 'http://example.com/a', 'str.join of str(url)')
    throws_ok(lambda: urllib.parse.quote(url), TypeError, 'urllib.parse.quote')
    is_ok(urllib.parse.quote(str(url)), 'http%3A//example.com/a', 'urllib.parse.quote of str(url)')

done_testing()
