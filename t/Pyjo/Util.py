from Pyjo.Test import *
from Pyjo.Util import header_params


# Pyjo.Util is brought to Mojolicious 9.49 one function at a time, so only the
# subtests of t/mojo/util.t for those functions are here

with subtest('header_params'):
    is_deeply_ok(header_params(''), ({}, ''), 'right result')
    is_deeply_ok(header_params('foo=b=a=r'), ({'foo': 'b=a=r'}, ''), 'right result')
    is_deeply_ok(header_params('a=b; c, d=e'), ({'a': 'b'}, ', d=e'), 'right result')
    is_deeply_ok(header_params('a=b; a=c'), ({'a': 'b'}, ''), 'right result')
    is_deeply_ok(header_params('a=b; a="c"'), ({'a': 'b'}, ''), 'right result')
    is_deeply_ok(header_params('a=b; b="c=d"'), ({'a': 'b', 'b': 'c=d'}, ''), 'right result')
    is_deeply_ok(header_params('a=b, c=d'), ({'a': 'b'}, ', c=d'), 'right result')
    is_deeply_ok(
        header_params('rel="x"; t*=UTF-8\'de\'a%20b'), ({'rel': 'x', 't*': "UTF-8'de'a%20b"}, ''), 'right result'
    )

done_testing()
