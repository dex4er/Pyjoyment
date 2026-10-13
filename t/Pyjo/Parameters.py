import Pyjo.Parameters

from Pyjo.Test import *


with subtest('Basic functionality'):
    params = Pyjo.Parameters.new('foo=b%3Bar&baz=23')
    params2 = Pyjo.Parameters.new('x', 1, 'y', 2)
    is_ok(params.to_str(), 'foo=b%3Bar&baz=23', 'right format')
    is_ok(params2.to_str(), 'x=1&y=2', 'right format')
    is_ok(params.to_str(), 'foo=b%3Bar&baz=23', 'right format')
    is_deeply_ok(params.pairs, [('foo', 'b;ar'), ('baz', '23')], 'right structure')
    params.append('a', 4, 'a', 5, 'b', 6, 'b', 7)
    is_ok(params.to_str(), 'foo=b%3Bar&baz=23&a=4&a=5&b=6&b=7', 'right format')
    params.pairs.append(('c', 'f;oo'))
    is_ok(params.to_str(), 'foo=b%3Bar&baz=23&a=4&a=5&b=6&b=7&c=f%3Boo', 'right format')
    is_ok(params.remove('a').to_str(), 'foo=b%3Bar&baz=23&b=6&b=7&c=f%3Boo', 'right format')

with subtest('Clone'):
    params = Pyjo.Parameters.new('foo=b%3Bar&baz=23')
    clone = params.clone()
    is_ok(str(params), str(clone), 'equal parameters')
    clone.pairs.append(('c', '9'))
    isnt_ok(str(params), str(clone), 'unequal parameters')

with subtest('Merge'):
    params = Pyjo.Parameters.new('foo=b%3Bar&baz=23&a=4&a=5&b=6&b=7&c=f%3Boo')
    params2 = Pyjo.Parameters.new('x', 1, 'y', 2)
    params.merge(params2)
    is_ok(params.to_str(), 'foo=b%3Bar&baz=23&a=4&a=5&b=6&b=7&c=f%3Boo&x=1&y=2', 'right format')
    is_ok(params2.to_str(), 'x=1&y=2', 'right format')
    is_ok(params.merge('baz', None).to_str(), 'foo=b%3Bar&a=4&a=5&b=6&b=7&c=f%3Boo&x=1&y=2', 'right format')
    is_ok(
        params.merge('y', 3, 'z', [4, 5]).to_str(),
        'foo=b%3Bar&a=4&a=5&b=6&b=7&c=f%3Boo&x=1&y=3&z=4&z=5',
        'right format',
    )
    is_ok(
        params.merge(Pyjo.Parameters.new('z', 6)).to_str(),
        'foo=b%3Bar&a=4&a=5&b=6&b=7&c=f%3Boo&x=1&y=3&z=6',
        'right format',
    )

with subtest('Merge (instances)'):
    params = Pyjo.Parameters.new().merge(Pyjo.Parameters.new('foo', [123, 456]))
    is_deeply_ok(params.to_dict(), {'foo': ['123', '456']}, 'right structure')
    params = Pyjo.Parameters.new('foo', 321).merge(Pyjo.Parameters.new('foo', [123, 456]))
    is_deeply_ok(params.to_dict(), {'foo': ['123', '456']}, 'right structure')
    params = Pyjo.Parameters.new('bar', 321).merge(Pyjo.Parameters.new('foo', [123, 456]))
    is_deeply_ok(params.to_dict(), {'foo': ['123', '456'], 'bar': '321'}, 'right structure')

with subtest('Param'):
    params = Pyjo.Parameters.new('foo=b%3Bar&a=4&a=5&b=6&b=7&c=f%3Boo&x=1&y=3&z=6')
    is_deeply_ok(params.param('foo'), 'b;ar', 'right structure')
    is_deeply_ok(params.every_param('foo'), ['b;ar'], 'right structure')
    is_deeply_ok(params.every_param('a'), ['4', '5'], 'right structure')
    params.param('foo', 'bar')
    is_deeply_ok([params.param('foo')], ['bar'], 'right structure')
    is_deeply_ok(params.param('foo', 'baz', 'yada').every_param('foo'), ['baz', 'yada'], 'right structure')
    is_deeply_ok(params.names(), ['a', 'b', 'c', 'foo', 'x', 'y', 'z'], 'right structure')

with subtest('Append'):
    params = Pyjo.Parameters.new('q=1')
    params2 = Pyjo.Parameters.new('x', 1, 'y', 2)
    params.append('a', 4, 'a', 5, 'b', 6, 'b', 7, 'c', None, 'c', [])
    is_deeply_ok(params.to_dict(), {'a': ['4', '5'], 'b': ['6', '7'], 'q': '1'}, 'right structure')
    is_deeply_ok(params.names(), ['a', 'b', 'q'], 'right structure')
    params = Pyjo.Parameters.new('foo', '', 'bar', 'bar')
    is_ok(params.to_str(), 'foo=&bar=bar', 'right format')
    params = Pyjo.Parameters.new('bar', 'bar', 'foo', '')
    is_ok(params.to_str(), 'bar=bar&foo=', 'right format')
    is_ok(params.append(params2).to_str(), 'bar=bar&foo=&x=1&y=2', 'right format')
    is_ok(params2.to_str(), 'x=1&y=2', 'right format')

with subtest('"0"'):
    params = Pyjo.Parameters.new(0, 0)
    is_ok(params.param(0), '0', 'right value')
    is_deeply_ok(params.every_param(0), ['0'], 'right value')
    is_deeply_ok(params.every_param('foo'), [], 'no values')
    is_ok(params.to_str(), '0=0', 'right format')
    params = Pyjo.Parameters.new(params.to_str())
    is_ok(params.param(0), '0', 'right value')
    is_deeply_ok(params.every_param(0), ['0'], 'right value')
    is_ok(params.to_dict()['0'], '0', 'right value')
    is_deeply_ok(params.to_dict(), {'0': '0'}, 'right structure')
    is_ok(params.to_str(), '0=0', 'right format')

with subtest('Semicolon'):
    params = Pyjo.Parameters.new('foo=bar;baz')
    is_ok(params.to_str(), 'foo=bar;baz', 'right format')
    is_deeply_ok(params.pairs, [('foo', 'bar;baz')], 'right structure')
    is_deeply_ok(params.to_dict(), {'foo': 'bar;baz'}, 'right structure')
    is_ok(params.to_str(), 'foo=bar%3Bbaz', 'right format')
    params = Pyjo.Parameters.new(params.to_str())
    is_deeply_ok(params.pairs, [('foo', 'bar;baz')], 'right structure')
    is_deeply_ok(params.to_dict(), {'foo': 'bar;baz'}, 'right structure')
    is_ok(params.to_str(), 'foo=bar%3Bbaz', 'right format')

with subtest('Reconstruction'):
    params = Pyjo.Parameters.new('foo=bar&baz=23')
    is_ok(str(params), 'foo=bar&baz=23', 'right format')
    params = Pyjo.Parameters.new('foo=bar;baz=23')
    is_ok(str(params), 'foo=bar;baz=23', 'right format')

with subtest('Empty params'):
    params = Pyjo.Parameters.new('c=')
    is_ok(params.to_dict()['c'], '', 'right value')
    is_deeply_ok(params.to_dict(), {'c': ''}, 'right structure')
    params = Pyjo.Parameters.new('c=&c=&d')
    is_deeply_ok(params.to_dict()['c'], ['', ''], 'right values')
    is_ok(params.to_dict()['d'], '', 'right value')
    is_deeply_ok(params.to_dict(), {'c': ['', ''], 'd': ''}, 'right structure')
    params = Pyjo.Parameters.new('c&d=0&e=')
    is_ok(params.to_dict()['c'], '', 'right value')
    is_ok(params.to_dict()['d'], '0', 'right value')
    is_ok(params.to_dict()['e'], '', 'right value')
    is_deeply_ok(params.to_dict(), {'c': '', 'd': '0', 'e': ''}, 'right structure')

with subtest('"+"'):
    params = Pyjo.Parameters.new('foo=%2B')
    is_ok(params.param('foo'), '+', 'right value')
    is_deeply_ok(params.to_dict(), {'foo': '+'}, 'right structure')
    params.param('foo ', ' bar')
    is_ok(params.to_str(), 'foo=%2B&foo+=+bar', 'right format')
    params.remove('foo ')
    is_deeply_ok(params.to_dict(), {'foo': '+'}, 'right structure')
    params.append('1 2', '3+3')
    is_ok(params.param('1 2'), '3+3', 'right value')
    is_deeply_ok(params.to_dict(), {'foo': '+', '1 2': '3+3'}, 'right structure')
    params = Pyjo.Parameters.new('a=works+too')
    is_ok(str(params), 'a=works+too', 'right format')
    is_deeply_ok(params.to_dict(), {'a': 'works too'}, 'right structure')
    is_ok(params.param('a'), 'works too', 'right value')
    is_ok(str(params), 'a=works+too', 'right format')

with subtest('Array values'):
    params = Pyjo.Parameters.new()
    params.append('foo', ['bar', 'baz'], 'bar', ['bas', 'test'], 'a', 'b')
    is_deeply_ok(params.every_param('foo'), ['bar', 'baz'], 'right values')
    is_ok(params.param('a'), 'b', 'right value')
    is_deeply_ok(params.every_param('bar'), ['bas', 'test'], 'right values')
    is_deeply_ok(params.to_dict(), {'foo': ['bar', 'baz'], 'a': 'b', 'bar': ['bas', 'test']}, 'right structure')
    params = Pyjo.Parameters.new('foo', ['ba;r', 'b;az'])
    is_deeply_ok(params.to_dict(), {'foo': ['ba;r', 'b;az']}, 'right structure')
    params.append('foo', ['bar'], 'foo', ['baz', 'yada'])
    is_deeply_ok(params.to_dict(), {'foo': ['ba;r', 'b;az', 'bar', 'baz', 'yada']}, 'right structure')
    is_ok(params.param('foo'), 'yada', 'right value')
    is_deeply_ok(params.every_param('foo'), ['ba;r', 'b;az', 'bar', 'baz', 'yada'], 'right values')
    params = Pyjo.Parameters.new('foo', ['ba;r', 'b;az'], 'bar', 23)
    is_deeply_ok(params.to_dict(), {'foo': ['ba;r', 'b;az'], 'bar': '23'}, 'right structure')
    is_ok(params.param('foo'), 'b;az', 'right value')
    is_deeply_ok(params.every_param('foo'), ['ba;r', 'b;az'], 'right values')
    params = Pyjo.Parameters.new()
    is_ok(params.param('foo', ['ba;r', 'baz']).to_str(), 'foo=ba%3Br&foo=baz', 'right format')

with subtest('Unicode'):
    params = Pyjo.Parameters.new()
    params.parse('input=say%20%22%C2%AB~%22;')
    is_deeply_ok(params.pairs, [('input', 'say "«~";')], 'right structure')
    is_ok(params.param('input'), 'say "«~";', 'right value')
    is_ok(str(params), 'input=say+%22%C2%AB%7E%22%3B', 'right result')
    params = Pyjo.Parameters.new('♥=☃')
    is_deeply_ok(params.pairs, [('♥', '☃')], 'right structure')
    is_ok(params.param('♥'), '☃', 'right value')
    is_ok(str(params), '%E2%99%A5=%E2%98%83', 'right result')
    params = Pyjo.Parameters.new('%E2%99%A5=%E2%98%83')
    is_deeply_ok(params.pairs, [('♥', '☃')], 'right structure')
    is_ok(params.param('♥'), '☃', 'right value')
    is_ok(str(params), '%E2%99%A5=%E2%98%83', 'right result')

with subtest('Reparse'):
    params = Pyjo.Parameters.new('foo=bar&baz=23')
    params.parse('foo=bar&baz=23')
    is_ok(str(params), 'foo=bar&baz=23', 'right string result after assigning new string')
    is_deeply_ok(params.pairs, [('foo', 'bar'), ('baz', '23')], 'right pairs after assigning new string')

    params.parse(None)
    is_ok(str(params), '', 'right result after assigning undef string')
    is_deeply_ok(params.pairs, [], 'right pairs after assigning undef string')

with subtest('Replace'):
    params = Pyjo.Parameters.new('a=1&b=2')
    params.pairs = [('a', '2'), ('b', '3')]
    is_ok(params.to_str(), 'a=2&b=3', 'right result')
    is_ok(params.set(pairs=[]).to_str(), '', 'right result')

with subtest('Query string'):
    params = Pyjo.Parameters.new("AZaz09-._~%!$&'()*+,;=:@/?")
    is_ok(str(params), "AZaz09-._~%!$&'()*+,;=:@/?", 'right result')
    params = Pyjo.Parameters.new('foo{}bar')
    is_ok(str(params), 'foo%7B%7Dbar', 'right result')

with subtest('"%"'):
    params = Pyjo.Parameters.new()
    params.param('%foo%', '%')
    is_ok(str(params), '%25foo%25=%25', 'right result')

with subtest('Special characters'):
    params = Pyjo.Parameters.new("!$'()*,:@/foo?=!$'()*,:@/?&bar=23")
    is_ok(params.param("!$'()*,:@/foo?"), "!$'()*,:@/?", 'right value')
    is_ok(params.param('bar'), '23', 'right value')
    is_ok(str(params), '%21%24%27%28%29*%2C%3A%40%2Ffoo%3F=%21%24%27%28%29*%2C%3A%40%2F%3F&bar=23', 'right result')

with subtest('No charset'):
    params = Pyjo.Parameters.new('%E5=%E4').set(charset=None)
    is_ok(params.param('\xe5'), '\xe4', 'right value')
    is_ok(str(params), '%E5=%E4', 'right result')
    is_ok(params.clone().to_str(), '%E5=%E4', 'right result')

done_testing()
