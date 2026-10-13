from Pyjo.Test import *


with subtest('Synopsis'):
    import Pyjo.Parameters

    from urllib.parse import parse_qsl, urlencode

    # Parse
    params = Pyjo.Parameters.new('foo=bar&baz=23')
    is_ok(params.param('baz'), '23', "params.param('baz')")

    # Build
    params = Pyjo.Parameters.new('foo', 'bar', 'baz', 23)
    params.pairs.append(('i', '♥ pyjoyment'))
    is_ok(str(params), 'foo=bar&baz=23&i=%E2%99%A5+pyjoyment', 'params')

with subtest('Description'):
    params = Pyjo.Parameters.new()
    params.append(('foo', 'bar'), ('baz', 23))
    params.append('foo', 'bar', 'baz', 23)
    params.append(foo='bar', baz=23)
    is_ok(str(params), 'foo=bar&baz=23&foo=bar&baz=23&foo=bar&baz=23', 'params')

with subtest('new'):
    params = Pyjo.Parameters.new()
    is_ok(str(params), '', 'new()')
    params = Pyjo.Parameters.new('foo=b%3Bar&baz=23')
    is_ok(str(params), 'foo=b%3Bar&baz=23', 'string')
    params = Pyjo.Parameters.new('foo', 'b&ar')
    is_ok(str(params), 'foo=b%26ar', 'pair')
    params = Pyjo.Parameters.new('foo', ['ba&r', 'baz'])
    is_ok(str(params), 'foo=ba%26r&foo=baz', 'multiple values')
    params = Pyjo.Parameters.new('foo', ['bar', 'baz'], 'bar', 23)
    is_ok(str(params), 'foo=bar&foo=baz&bar=23', 'pairs')
    params = Pyjo.Parameters.new(foo=['bar', 'baz'], bar=23)
    is_ok(str(params), 'foo=bar&foo=baz&bar=23', 'keyword arguments')

with subtest('charset'):
    charset = params.charset
    is_ok(charset, 'UTF-8', 'charset')
    params.charset = 'UTF-8'
    is_ok(params.charset, 'UTF-8', 'params.charset')

    # Disable encoding and decoding
    params.charset = None
    is_ok(params.charset, None, 'params.charset')

with subtest('__bool__'):
    boolean = bool(params)
    is_ok(boolean, True, 'boolean')

with subtest('__getitem__'):
    params = Pyjo.Parameters.new('foo=bar&baz=23')
    pair = params[0]
    is_ok(pair, ('foo', 'bar'), 'pair')

with subtest('__iter__'):
    pairs = list(params)
    is_deeply_ok(pairs, [('foo', 'bar'), ('baz', '23')], 'pairs')
    is_deeply_ok([(name, value) for name, value in params], [('foo', 'bar'), ('baz', '23')], 'for name, value')

with subtest('__len__'):
    size = len(params)
    is_ok(size, 2, 'size')

with subtest('__str__'):
    string = str(params)
    is_ok(string, 'foo=bar&baz=23', 'string')

with subtest('append'):
    params = Pyjo.Parameters.new()
    params = params.append('foo', 'ba&r')
    params = params.append('foo', ['ba&r', 'baz'])
    params = params.append('foo', ['bar', 'baz'], 'bar', 23)
    params = params.append(Pyjo.Parameters.new())
    is_ok(str(params), 'foo=ba%26r&foo=ba%26r&foo=baz&foo=bar&foo=baz&bar=23', 'params')

    # "foo=bar&foo=baz"
    is_ok(
        str(Pyjo.Parameters.new('foo=bar').append(Pyjo.Parameters.new('foo=baz'))),
        'foo=bar&foo=baz',
        'append(Pyjo.Parameters)',
    )

    # "foo=bar&foo=baz"
    is_ok(str(Pyjo.Parameters.new('foo=bar').append('foo', 'baz')), 'foo=bar&foo=baz', 'append pair')

    # "foo=bar&foo=baz&foo=yada"
    is_ok(
        str(Pyjo.Parameters.new('foo=bar').append('foo', ['baz', 'yada'])),
        'foo=bar&foo=baz&foo=yada',
        'append multiple values',
    )

    # "foo=bar&foo=baz&foo=yada&bar=23"
    is_ok(
        str(Pyjo.Parameters.new('foo=bar').append('foo', ['baz', 'yada'], 'bar', 23)),
        'foo=bar&foo=baz&foo=yada&bar=23',
        'append pairs',
    )

with subtest('clone'):
    params2 = params.clone()
    is_ok(str(params2), str(params), 'params2')
    isnt_ok(id(params2), id(params), 'another object')

with subtest('every_param'):
    params = Pyjo.Parameters.new('foo=bar&foo=baz')
    values = params.every_param('foo')
    is_deeply_ok(values, ['bar', 'baz'], 'values')

    # Get first value
    is_ok(params.every_param('foo')[0], 'bar', 'first value')

with subtest('merge'):
    params = Pyjo.Parameters.new()
    params = params.merge('foo', 'ba&r')
    params = params.merge('foo', ['ba&r', 'baz'])
    params = params.merge('foo', ['bar', 'baz'], 'bar', 23)
    params = params.merge(Pyjo.Parameters.new())
    is_ok(str(params), 'bar=23&foo=bar&foo=baz', 'params')

    # "foo=baz"
    is_ok(
        str(Pyjo.Parameters.new('foo=bar').merge(Pyjo.Parameters.new('foo=baz'))), 'foo=baz', 'merge(Pyjo.Parameters)'
    )

    # "yada=yada&foo=baz"
    is_ok(str(Pyjo.Parameters.new('foo=bar&yada=yada').merge('foo', 'baz')), 'yada=yada&foo=baz', 'merge pair')

    # "yada=yada"
    is_ok(str(Pyjo.Parameters.new('foo=bar&yada=yada').merge('foo', None)), 'yada=yada', 'merge None')

with subtest('names'):
    params = Pyjo.Parameters.new('foo=bar&baz=23&foo=yada')
    names = params.names()
    is_deeply_ok(names, ['baz', 'foo'], 'names')

    # Names of all parameters
    is_deeply_ok([name for name in params.names()], ['baz', 'foo'], 'for name in params.names()')

with subtest('pairs'):
    pairs = params.pairs
    is_deeply_ok(pairs, [('foo', 'bar'), ('baz', '23'), ('foo', 'yada')], 'pairs')
    params.pairs = [('foo', 'b&ar'), ('baz', '23')]
    is_ok(str(params), 'foo=b%26ar&baz=23', 'params')

    # Remove all parameters
    params.pairs = []
    is_ok(str(params), '', 'params')

with subtest('param'):
    params = Pyjo.Parameters.new('foo=bar')
    value = params.param('foo')
    is_ok(value, 'bar', 'value')
    params = params.param('foo', 'ba&r')
    is_ok(str(params), 'foo=ba%26r', 'single value')
    params = params.param('foo', 'ba&r', 'baz')
    is_ok(str(params), 'foo=ba%26r&foo=baz', 'values')
    params = params.param('foo', ['ba;r', 'baz'])
    is_ok(str(params), 'foo=ba%3Br&foo=baz', 'list of values')

with subtest('parse'):
    params = params.parse('foo=b%3Bar&baz=23')
    is_deeply_ok(params.pairs, [('foo', 'b;ar'), ('baz', '23')], 'params.pairs')
    params = Pyjo.Parameters.new().parse(parse_qsl('foo=b%3Bar&baz=23'))
    is_deeply_ok(params.pairs, [('foo', 'b;ar'), ('baz', '23')], 'parse_qsl')

with subtest('remove'):
    params = params.remove('foo')
    is_ok(str(params), 'baz=23', 'params')

    # "bar=yada"
    is_ok(str(Pyjo.Parameters.new('foo=bar&foo=baz&bar=yada').remove('foo')), 'bar=yada', "remove('foo')")

with subtest('to_dict'):
    d = params.to_dict()
    is_deeply_ok(d, {'baz': '23'}, 'd')

    # "baz"
    is_ok(Pyjo.Parameters.new('foo=bar&foo=baz').to_dict()['foo'][1], 'baz', "to_dict()['foo'][1]")

with subtest('to_str'):
    string = params.to_str()
    is_ok(string, 'baz=23', 'string')

    # "foo=bar&baz=23"
    is_ok(Pyjo.Parameters.new().set(pairs=[('foo', 'bar'), ('baz', '23')]).to_str(), 'foo=bar&baz=23', 'set(pairs=...)')

with subtest('to_urllib'):
    pairs = params.to_urllib()
    is_deeply_ok(pairs, [('baz', '23')], 'pairs')

    # "foo=bar&foo=baz"
    is_ok(urlencode(Pyjo.Parameters.new('foo=bar&foo=baz').to_urllib()), 'foo=bar&foo=baz', 'urlencode')

done_testing()
