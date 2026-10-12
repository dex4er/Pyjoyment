
import Pyjo.Test


class NoseTest(Pyjo.Test.NoseTest):
    script = __file__
    srcdir = '../..'


class UnitTest(Pyjo.Test.UnitTest):
    script = __file__


if __name__ == '__main__':

    from Pyjo.Test import *  # noqa

    import Pyjo.Parameters

    # Basic functionality
    params = Pyjo.Parameters.new('foo=b%3Bar&baz=23')
    params2 = Pyjo.Parameters.new(('x', 1), ('y', 2))
    params3 = Pyjo.Parameters.new(a=1, b=2, c=3, d=4)
    is_ok(str(params), 'foo=b%3Bar&baz=23', 'right format')
    is_ok(str(params2), 'x=1&y=2', 'right format')
    is_ok(str(params3), 'a=1&b=2&c=3&d=4', 'right format')
    is_ok(str(params), 'foo=b%3Bar&baz=23', 'right format')
    is_deeply_ok(params.pairs, [('foo', 'b;ar'), ('baz', '23')], 'right structure')

    # Append
    params.append(('a', 4), ('a', 5), ('b', 6), ('b', 7))
    is_ok(str(params), 'foo=b%3Bar&baz=23&a=4&a=5&b=6&b=7', 'right format')
    params.append(('c', 'f;oo'),)
    is_ok(str(params), 'foo=b%3Bar&baz=23&a=4&a=5&b=6&b=7&c=f%3Boo', 'right format')
    is_ok(str(params.remove('a')), 'foo=b%3Bar&baz=23&b=6&b=7&c=f%3Boo', 'right format')

    # Clone
    clone = params.clone()
    is_ok(str(params), str(clone), 'equal parameters')
    clone.append(('c', 9),)
    isnt_ok(str(params), str(clone), 'unequal parameters')

    # Merge
    params = Pyjo.Parameters.new('foo=b%3Bar&baz=23&a=4&a=5&b=6&b=7&c=f%3Boo')
    params.merge(params2)
    is_ok(str(params), 'foo=b%3Bar&baz=23&a=4&a=5&b=6&b=7&c=f%3Boo&x=1&y=2', 'right format')
    is_ok(str(params2), 'x=1&y=2', 'right format')
    is_ok(str(params.merge(('baz', None),)), 'foo=b%3Bar&a=4&a=5&b=6&b=7&c=f%3Boo&x=1&y=2', 'right format')

    # Param
    params = Pyjo.Parameters.new('foo=b%3Bar&a=4&a=5&b=6&b=7&c=f%3Boo&x=1&y=3&z=6')
    is_deeply_ok(params.param('foo'), 'b;ar', 'right structure')
    is_deeply_ok(params.every_param('foo'), ['b;ar'], 'right structure')
    is_deeply_ok(params.every_param('a'), ['4', '5'], 'right structure')
    is_deeply_ok(params.param(['a']), ['5'], 'right structure')
    is_deeply_ok(params.param(['a', 'foo']), ['5', 'b;ar'], 'right structure')
    params.param('foo', 'bar')
    is_deeply_ok([params.param('foo')], ['bar'], 'right structure')
    is_deeply_ok(params.param('foo', ['baz', 'yada']).every_param('foo'), ['baz', 'yada'], 'right structure')

    # Remove
    params.parse('q=1&w=2&e=3&e=4&r=6&t=7')
    is_ok(str(params.remove('r')), 'q=1&w=2&e=3&e=4&t=7', 'right format')
    params.remove('e')
    is_ok(str(params), 'q=1&w=2&t=7', 'right format')

    # Hash
    is_deeply_ok(params.to_dict(), {'q': '1', 'w': '2', 't': '7'}, 'right structure')

    # List names
    is_deeply_ok(params.names, ['q', 't', 'w'], 'right structure')

    # Append
    params.append(('a', 4), ('a', 5), ('b', 6), ('b', 7))
    is_deeply_ok(params.to_dict(), {'a': [4, 5], 'b': [6, 7], 'q': '1', 'w': '2', 't': '7'}, 'right structure')
    params = Pyjo.Parameters.new(('foo', ''), ('bar', 'bar'))
    is_ok(str(params), 'foo=&bar=bar', 'right format')
    params = Pyjo.Parameters.new(('bar', 'bar'), ('foo', ''))
    is_ok(str(params), 'bar=bar&foo=', 'right format')
    params = Pyjo.Parameters.new('')
    params.append(Pyjo.Parameters.new(''))
    is_ok(str(params), '', 'right format')
    params.append(Pyjo.Parameters.new('foo=bar&baz=42'))
    is_ok(str(params), 'foo=bar&baz=42', 'right format')
    params.append(Pyjo.Parameters.new('yada=yada'))
    is_ok(str(params), 'foo=bar&baz=42&yada=yada', 'right format')

    # "0"
    params = Pyjo.Parameters.new(('foo', 0),)
    is_ok(params.param('foo'), 0, 'right value')
    is_deeply_ok(params.every_param('foo'), [0], 'right value')
    is_deeply_ok(params.every_param('bar'), [], 'no values')
    is_ok(str(params), 'foo=0', 'right format')
    params = Pyjo.Parameters.new(params)
    is_ok(params.param('foo'), '0', 'right value')
    is_deeply_ok(params.every_param('foo'), ['0'], 'right value')
    is_ok(params.to_dict()['foo'], '0', 'right value')
    is_deeply_ok(params.to_dict(), {'foo': '0'}, 'right structure')
    is_ok(str(params), 'foo=0', 'right format')

    # Semicolon
    params = Pyjo.Parameters.new('foo=bar;baz')
    is_ok(str(params), 'foo=bar;baz', 'right format')
    is_deeply_ok(params.pairs, [('foo', 'bar;baz')], 'right structure')
    is_deeply_ok(params.to_dict(), {'foo': 'bar;baz'}, 'right structure')
    is_ok(str(params), 'foo=bar%3Bbaz', 'right format')
    params = Pyjo.Parameters.new(params)
    is_deeply_ok(params.pairs, [('foo', 'bar;baz')], 'right structure')
    is_deeply_ok(params.to_dict(), {'foo': 'bar;baz'}, 'right structure')
    is_ok(str(params), 'foo=bar%3Bbaz', 'right format')

    # Reconstruction
    params = Pyjo.Parameters.new('foo=bar&baz=23')
    is_ok(str(params), 'foo=bar&baz=23', 'right format')
    params = Pyjo.Parameters.new('foo=bar;baz=23')
    is_ok(str(params), 'foo=bar;baz=23', 'right format')

    # Empty params
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

    # "+"
    params = Pyjo.Parameters.new('foo=%2B')
    is_ok(params.param('foo'), '+', 'right value')
    is_deeply_ok(params.to_dict(), {'foo': '+'}, 'right structure')
    params.param('foo ', 'a')
    is_ok(str(params), 'foo=%2B&foo+=a', 'right format')
    params.remove('foo ')
    is_deeply_ok(params.to_dict(), {'foo': '+'}, 'right structure')
    params.append(('1 2', '3+3'),)
    is_ok(params.param('1 2'), '3+3', 'right value')
    is_deeply_ok(params.to_dict(), {'foo': '+', '1 2': '3+3'}, 'right structure')
    params = Pyjo.Parameters.new('a=works+too')
    is_ok(str(params), 'a=works+too', 'right format')
    is_deeply_ok(params.to_dict(), {'a': 'works too'}, 'right structure')
    is_ok(params.param('a'), 'works too', 'right value')
    is_ok(str(params), 'a=works+too', 'right format')

    # Array values
    params = Pyjo.Parameters.new()
    params.append(('foo', ['bar', 'baz']), ('bar', ['bas', 'test']), ('a', 'b'))
    is_deeply_ok(params.every_param('foo'), ['bar', 'baz'], 'right values')
    is_ok(params.param('a'), 'b', 'right value')
    is_deeply_ok(params.every_param('bar'), ['bas', 'test'], 'right values')
    is_deeply_ok(params.to_dict(), {'foo': ['bar', 'baz'], 'a': 'b', 'bar': ['bas', 'test']}, 'right structure')
    params = Pyjo.Parameters.new(('foo', ['ba;r', 'b;az']),)
    is_deeply_ok(params.to_dict(), {'foo': ['ba;r', 'b;az']}, 'right structure')
    params.append(('foo', ['bar']), ('foo', ['baz', 'yada']))
    is_deeply_ok(params.to_dict(), {'foo': ['ba;r', 'b;az', 'bar', 'baz', 'yada']}, 'right structure')
    is_ok(params.param('foo'), 'yada', 'right value')
    is_deeply_ok(params.every_param('foo'), ['ba;r', 'b;az', 'bar', 'baz', 'yada'], 'right values')
    params = Pyjo.Parameters.new(('foo', ['ba;r', 'b;az']), ('bar', 23))
    is_deeply_ok(params.to_dict(), {'foo': ['ba;r', 'b;az'], 'bar': 23}, 'right structure')
    is_ok(params.param('foo'), 'b;az', 'right value')
    is_deeply_ok(params.every_param('foo'), ['ba;r', 'b;az'], 'right values')
    params = Pyjo.Parameters.new()
    is_ok(str(params.param('foo', ['ba;r', 'baz'])), 'foo=ba%3Br&foo=baz', 'right format')

    # Unicode
    params = Pyjo.Parameters.new()
    params.parse('input=say%20%22%C2%AB~%22;')
    is_deeply_ok(params.pairs, [('input', 'say "«~";')], 'right structure')
    is_ok(params.param('input'), 'say "«~";', 'right value')
    is_ok(str(params), 'input=say+%22%C2%AB~%22%3B', 'right result')
    params = Pyjo.Parameters.new('♥=☃')
    is_deeply_ok(params.pairs, [('♥', '☃')], 'right structure')
    is_ok(params.param('♥'), '☃', 'right value')
    is_ok(str(params), '%E2%99%A5=%E2%98%83', 'right result')
    params = Pyjo.Parameters.new('%E2%99%A5=%E2%98%83')
    is_deeply_ok(params.pairs, [('♥', '☃')], 'right structure')
    is_ok(params.param('♥'), '☃', 'right value')
    is_ok(str(params), '%E2%99%A5=%E2%98%83', 'right result')

    # Reparse
    params = Pyjo.Parameters.new('foo=bar&baz=23')
    params.parse('foo=bar&baz=23')
    is_ok(str(params), 'foo=bar&baz=23', 'right result')

    # Replace
    params = Pyjo.Parameters.new('a=1&b=2')
    params.pairs = [('a', 2), ('b', 3)]
    is_ok(str(params), 'a=2&b=3', 'right result')

    # Query string
    params = Pyjo.Parameters.new('%AZaz09-._~&;=+!$\'()*,%:@/?')
    is_ok(str(params), '%AZaz09-._~&;=+!$\'()*,%:@/?', 'right result')
    params = Pyjo.Parameters.new('foo{}bar')
    is_ok(str(params), 'foo%7B%7Dbar', 'right result')

    # "%"
    params = Pyjo.Parameters.new()
    params.param('%foo%', '%')
    is_ok(str(params), '%25foo%25=%25', 'right result')

    # Special characters
    params = Pyjo.Parameters.new('!$\'()*,:@/foo?=!$\'()*,:@/?&bar=23')
    is_ok(params.param('!$\'()*,:@/foo?'), '!$\'()*,:@/?', 'right value')
    is_ok(params.param('bar'), '23', 'right value')
    is_ok(str(params), '!$\'()*,:@/foo?=!$\'()*,:@/?&bar=23', 'right result')

    # No charset
    params = Pyjo.Parameters.new('%E5=%E4').set(charset=None)
    is_ok(params.param(b"\xe5"), b"\xe4", 'right value')
    is_ok(str(params), '%E5=%E4', 'right result')
    is_ok(str(params.clone()), '%E5=%E4', 'right result')

    done_testing()
