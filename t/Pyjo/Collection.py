from Pyjo.Collection import c
from Pyjo.JSON import encode_json
from Pyjo.Test import *

import re


with subtest('Array'):
    is_ok(c(1, 2, 3)[1], 2, 'right result')
    is_deeply_ok(list(c(3, 2, 1)), [3, 2, 1], 'right result')
    collection = c(1, 2)
    collection.extend([3, 4, 5])
    is_deeply_ok(list(collection), [1, 2, 3, 4, 5], 'right result')

with subtest('Tap into method chain'):
    is_deeply_ok(c(1, 2, 3).tap(lambda e: e.__setitem__(1, e[1] + 2)).to_list(), [1, 4, 3], 'right result')

with subtest('compact'):
    is_deeply_ok(c(None, 0, 1, '', 2, 3).compact().to_list(), [0, 1, 2, 3], 'right result')
    is_deeply_ok(c(3, 2, 1).compact().to_list(), [3, 2, 1], 'right result')
    is_deeply_ok(c().compact().to_list(), [], 'right result')

with subtest('flatten'):
    is_deeply_ok(c(1, 2, [3, 4], 5, c(6, 7)).flatten().to_list(), [1, 2, 3, 4, 5, 6, 7], 'right result')
    is_deeply_ok(
        c(None, 1, [2, {}, [3, c(4, 5)]], None, 6).flatten().to_list(),
        [None, 1, 2, {}, 3, 4, 5, None, 6],
        'right result',
    )

with subtest('each'):
    collection = c(3, 2, 1)
    is_deeply_ok(collection.each(), [3, 2, 1], 'right elements')
    collection = c([3], [2], [1])
    results = []
    collection.each(lambda e, num: results.append(e[0]))
    is_deeply_ok(results, [3, 2, 1], 'right elements')
    results = []
    collection.each(lambda e, num: results.extend([e[0], num]))
    is_deeply_ok(results, [3, 1, 2, 2, 1, 3], 'right elements')

with subtest('first'):
    collection = c(5, 4, [3, 2], 1)
    is_ok(collection.first(), 5, 'right result')
    is_deeply_ok(collection.first(lambda e: isinstance(e, list)), [3, 2], 'right result')
    is_ok(collection.first(lambda e: e < 5), 4, 'right result')
    is_ok(collection.first(re.compile(r'[1-4]')), 4, 'right result')
    is_ok(collection.first(lambda e: callable(e)), None, 'no result')
    collection = c(c(1, 2, 3), c(4, 5, 6), c(7, 8, 9))
    is_deeply_ok(collection.first('first', lambda e: e == 5).to_list(), [4, 5, 6], 'right result')
    collection = c()
    is_ok(collection.first(), None, 'no result')
    is_ok(collection.first(lambda e: e is not None), None, 'no result')

with subtest('last'):
    is_ok(c(5, 4, 3).last(), 3, 'right result')
    is_ok(c(5, 4, 3).reverse().last(), 5, 'right result')
    is_ok(c().last(), None, 'no result')

with subtest('grep'):
    collection = c(1, 2, 3, 4, 5, 6, 7, 8, 9)
    is_deeply_ok(collection.grep(re.compile(r'[6-9]')).to_list(), [6, 7, 8, 9], 'right elements')
    is_deeply_ok(collection.grep(lambda e: re.search(r'[6-9]', str(e))).to_list(), [6, 7, 8, 9], 'right elements')
    is_deeply_ok(collection.grep(lambda e: e > 5).to_list(), [6, 7, 8, 9], 'right elements')
    is_deeply_ok(collection.grep(lambda e: e < 5).to_list(), [1, 2, 3, 4], 'right elements')
    is_deeply_ok(collection.grep(lambda e: e == 5).to_list(), [5], 'right elements')
    is_deeply_ok(collection.grep(lambda e: e < 1).to_list(), [], 'no elements')
    is_deeply_ok(collection.grep(lambda e: e > 9).to_list(), [], 'no elements')
    collection = c(c(1, 2, 3), c(4, 5, 6), c(7, 8, 9))
    is_deeply_ok(collection.grep('first', lambda e: e >= 5).flatten().to_list(), [4, 5, 6, 7, 8, 9], 'right result')

with subtest('join'):
    collection = c(1, 2, 3)
    is_ok(collection.join(), '123', 'right result')
    is_ok(collection.join(''), '123', 'right result')
    is_ok(collection.join('---'), '1---2---3', 'right result')
    is_ok(collection.join('\n'), '1\n2\n3', 'right result')
    is_ok(collection.join('/').url_escape(), '1%2F2%2F3', 'right result')

with subtest('map'):
    collection = c(1, 2, 3)
    is_ok(collection.map(lambda e: e + 1).join(''), '234', 'right result')
    is_deeply_ok(list(collection), [1, 2, 3], 'right elements')
    is_ok(collection.map(lambda e: e + 2).join(''), '345', 'right result')
    is_deeply_ok(list(collection), [1, 2, 3], 'right elements')
    collection = c(c(1, 2, 3), c(4, 5, 6), c(7, 8, 9))
    is_ok(collection.map('reverse').map('join', '\n').join('\n'), '3\n2\n1\n6\n5\n4\n9\n8\n7', 'right result')
    is_ok(collection.map('join', '-').join('\n'), '1-2-3\n4-5-6\n7-8-9', 'right result')

with subtest('reverse'):
    collection = c(3, 2, 1)
    is_deeply_ok(collection.reverse().to_list(), [1, 2, 3], 'right order')
    collection = c(3)
    is_deeply_ok(collection.reverse().to_list(), [3], 'right order')
    collection = c()
    is_deeply_ok(collection.reverse().to_list(), [], 'no elements')

with subtest('shuffle'):
    collection = c(*range(0, 10001))
    random = collection.shuffle()
    is_ok(collection.size, random.size, 'same number of elements')
    isnt_ok(' '.join(map(str, collection)), ' '.join(map(str, random)), 'different order')
    is_deeply_ok(c().shuffle().to_list(), [], 'no elements')

with subtest('size'):
    collection = c()
    is_ok(collection.size, 0, 'right size')
    collection = c(None)
    is_ok(collection.size, 1, 'right size')
    collection = c(23)
    is_ok(collection.size, 1, 'right size')
    collection = c([2, 3])
    is_ok(collection.size, 1, 'right size')
    collection = c(5, 4, 3, 2, 1)
    is_ok(collection.size, 5, 'right size')

with subtest('reduce'):
    collection = c(2, 5, 4, 1)
    is_ok(collection.reduce(lambda a, b: a + b), 12, 'right result')
    is_ok(collection.reduce(lambda a, b: a + b, 5), 17, 'right result')
    is_ok(c().reduce(lambda a, b: a + b), None, 'no result')

with subtest('sort'):
    collection = c(2, 5, 4, 1)
    is_deeply_ok(collection.sort().to_list(), [1, 2, 4, 5], 'right order')
    # Unlike Mojolicious: Python 3 has no comparison functions, sort() takes
    # the key and reverse arguments of sorted()
    is_deeply_ok(collection.sort(reverse=True).to_list(), [5, 4, 2, 1], 'right order')
    is_deeply_ok(collection.sort(key=lambda e: -e).to_list(), [5, 4, 2, 1], 'right order')
    collection = c('Test', 'perl', 'Mojo')
    is_deeply_ok(collection.sort(key=str.upper).to_list(), ['Mojo', 'perl', 'Test'], 'right order')
    collection = c()
    is_deeply_ok(collection.sort().to_list(), [], 'no elements')
    is_deeply_ok(collection.sort(key=str).to_list(), [], 'no elements')

with subtest('uniq'):
    collection = c(1, 2, 3, 2, 3, 4, 5, 4)
    is_deeply_ok(collection.uniq().to_list(), [1, 2, 3, 4, 5], 'right result')
    is_deeply_ok(collection.uniq().reverse().uniq().to_list(), [5, 4, 3, 2, 1], 'right result')
    collection = c([1, 2, 3], [3, 2, 1], [3, 1, 2])
    is_deeply_ok(collection.uniq(lambda e: e[1]), [[1, 2, 3], [3, 1, 2]], 'right result')
    collection = c(c(1, 2), c(1, 2), c(2, 1))
    is_deeply_ok(collection.uniq('join', ',').flatten().to_list(), [1, 2, 2, 1], 'right result')
    collection = c(None, '', 3, 2, 1, 0)
    is_deeply_ok(collection.uniq().to_list(), [None, 3, 2, 1, 0], 'right result')
    collection = c(None, '', 3, 2, 1, 0)
    is_deeply_ok(collection.uniq(lambda e: e).to_list(), [None, 3, 2, 1, 0], 'right result')

with subtest('TO_JSON'):
    is_ok(encode_json(c(1, 2, 3)), b'[1,2,3]', 'right result')

with subtest('head'):
    collection = c(1, 2, 5, 4, 3)
    is_deeply_ok(collection.head(0).to_list(), [], 'right result')
    is_deeply_ok(collection.head(1).to_list(), [1], 'right result')
    is_deeply_ok(collection.head(2).to_list(), [1, 2], 'right result')
    is_deeply_ok(collection.head(-1).to_list(), [1, 2, 5, 4], 'right result')
    is_deeply_ok(collection.head(-3).to_list(), [1, 2], 'right result')
    is_deeply_ok(collection.head(5).to_list(), [1, 2, 5, 4, 3], 'right result')
    is_deeply_ok(collection.head(6).to_list(), [1, 2, 5, 4, 3], 'right result')
    is_deeply_ok(collection.head(-5).to_list(), [], 'right result')
    is_deeply_ok(collection.head(-6).to_list(), [], 'right result')

with subtest('tail'):
    collection = c(1, 2, 5, 4, 3)
    is_deeply_ok(collection.tail(0).to_list(), [], 'right result')
    is_deeply_ok(collection.tail(1).to_list(), [3], 'right result')
    is_deeply_ok(collection.tail(2).to_list(), [4, 3], 'right result')
    is_deeply_ok(collection.tail(-1).to_list(), [2, 5, 4, 3], 'right result')
    is_deeply_ok(collection.tail(-3).to_list(), [4, 3], 'right result')
    is_deeply_ok(collection.tail(5).to_list(), [1, 2, 5, 4, 3], 'right result')
    is_deeply_ok(collection.tail(6).to_list(), [1, 2, 5, 4, 3], 'right result')
    is_deeply_ok(collection.tail(-5).to_list(), [], 'right result')
    is_deeply_ok(collection.tail(-6).to_list(), [], 'right result')

done_testing()
