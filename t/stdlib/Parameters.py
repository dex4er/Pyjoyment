import Pyjo.Parameters

from Pyjo.Test import *

from urllib.parse import parse_qs, parse_qsl, urlencode


with subtest('From urllib'):
    params = Pyjo.Parameters.new(parse_qsl('a=1&a=2&b=x+y'))
    is_deeply_ok(params.pairs, [('a', '1'), ('a', '2'), ('b', 'x y')], 'from parse_qsl')
    params = Pyjo.Parameters.new(parse_qs('a=1&a=2&b=3'))
    is_deeply_ok(params.pairs, [('a', '1'), ('a', '2'), ('b', '3')], 'from parse_qs')
    params = Pyjo.Parameters.new().parse(parse_qsl('x=1'))
    is_ok(str(params), 'x=1', 'parse')
    params = Pyjo.Parameters.new('x=1').append(parse_qsl('y=2'))
    is_ok(str(params), 'x=1&y=2', 'append')
    params = Pyjo.Parameters.new('a=1&b=2').merge(parse_qs('a=3'))
    is_ok(str(params), 'b=2&a=3', 'merge')

with subtest('To urllib'):
    params = Pyjo.Parameters.new('foo=bar&foo=baz&♥=☃')
    is_deeply_ok(params.to_urllib(), [('foo', 'bar'), ('foo', 'baz'), ('♥', '☃')], 'list of pairs')
    is_ok(urlencode(params.to_urllib()), 'foo=bar&foo=baz&%E2%99%A5=%E2%98%83', 'urlencode')
    pairs = params.to_urllib()
    pairs.append(('x', '1'))
    is_ok(len(params), 3, 'a copy')

with subtest('Roundtrip'):
    params = Pyjo.Parameters.new('a=1&a=2&b=x+y&c=')
    is_deeply_ok(parse_qsl(str(params), keep_blank_values=True), params.to_urllib(), 'parse_qsl(str(params))')
    is_ok(str(Pyjo.Parameters.new(params.to_urllib())), str(params), 'Pyjo.Parameters -> urllib -> Pyjo.Parameters')

with subtest('Protocols'):
    params = Pyjo.Parameters.new('a=1&a=2&b=3')
    is_deeply_ok(dict(params), {'a': '2', 'b': '3'}, 'dict, the last value')
    is_deeply_ok(list(params), [('a', '1'), ('a', '2'), ('b', '3')], 'list')

done_testing()
