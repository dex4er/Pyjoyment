if __name__ == '__main__':
    from Pyjo.Test import *  # noqa

    import Pyjo.Parameters

    # Parse
    params = Pyjo.Parameters.new('foo=bar&baz=23')
    is_ok(params.param('baz'), '23', "params.param('baz')")

    # Build
    params = Pyjo.Parameters.new(('foo', 'bar'), ('baz', 23))
    params.append(i='♥ pyjo')
    is_ok(str(params), 'foo=bar&baz=23&i=%E2%99%A5+pyjo', 'params')

    # __init__
    params = Pyjo.Parameters.new()
    is_ok(str(params), '', 'params')

    params = Pyjo.Parameters.new('foo=b%3Bar&baz=23')
    is_ok(str(params), 'foo=b%3Bar&baz=23', 'params')

    params = Pyjo.Parameters.new(foo='b&ar')
    is_ok(str(params), 'foo=b%26ar', 'params')

    params = Pyjo.Parameters.new(foo=['ba&r', 'baz'])
    is_ok(str(params), 'foo=ba%26r&foo=baz', 'params')

    params = Pyjo.Parameters.new(foo=['bar', 'baz'], bar=23)
    is_ok(str(params), 'bar=23&foo=bar&foo=baz', 'params')

    # charset
    params = Pyjo.Parameters.new('foo=bar&baz=23')
    charset = params.charset
    is_ok(charset, 'utf-8', 'charset')
    params.charset = 'utf-8'
    charset = params.charset
    is_ok(charset, 'utf-8', 'charset')

    # __iter__
    params = Pyjo.Parameters.new('foo=bar&baz=23')
    l = [v for v in params]
    is_deeply_ok(l, [('foo', 'bar'), ('baz', '23')], '[v for v in params]')

    # __bool__
    ok(Pyjo.Parameters.new(), 'Pyjo.Parameters.new()')

    # append
    params = Pyjo.Parameters.new('foo=bar').append(Pyjo.Parameters.new('foo=baz'))
    is_ok(str(params), 'foo=bar&foo=baz', 'params')

    params = Pyjo.Parameters.new('foo=bar').append(foo='baz')
    is_ok(str(params), 'foo=bar&foo=baz', 'params')

    params = Pyjo.Parameters.new('foo=bar').append(foo=['baz', 'yada'])
    is_ok(str(params), 'foo=bar&foo=baz&foo=yada', 'params')

    params = Pyjo.Parameters.new('foo=bar').append(('foo', ['baz', 'yada']), ('bar', 23))
    is_ok(str(params), 'foo=bar&foo=baz&foo=yada&bar=23', 'params')

    # clone
    params = Pyjo.Parameters.new('foo=b%3Bar&baz=23')
    params2 = params.clone()
    is_ok(str(params2), 'foo=b%3Bar&baz=23', 'params2')
    isnt_ok(id(params), id(params2), 'params')

    # every_param
    params = Pyjo.Parameters.new('bar=23&foo=bar&foo=baz')
    values = params.every_param('foo')
    is_deeply_ok(values, ['bar', 'baz'], "params.every_param('foo')")

    # Get first value
    value = params.every_param('foo')[0]
    is_ok(value, 'bar', "params.every_param('foo')[0]")

    # merge
    params = Pyjo.Parameters.new()
    params = params.merge(
        ('foo', 'ba&r'),
    )
    is_ok(str(params), 'foo=ba%26r', 'params')
    params = params.merge(foo='baz')
    is_ok(str(params), 'foo=baz', 'params')
    params = params.merge(foo=['ba&r', 'baz'])
    is_ok(str(params), 'foo=ba%26r&foo=baz', 'params')
    params = params.merge(('foo', ['bar', 'baz']), ('bar', 23))
    is_ok(str(params), 'foo=bar&foo=baz&bar=23', 'params')
    params = params.merge(Pyjo.Parameters.new())
    is_ok(str(params), 'foo=bar&foo=baz&bar=23', 'params')

    params = Pyjo.Parameters.new('foo=bar').merge(Pyjo.Parameters.new('foo=baz'))
    is_ok(str(params), 'foo=baz', 'params')

    params = Pyjo.Parameters.new('foo=bar&yada=yada').merge(foo='baz')
    is_ok(str(params), 'foo=baz&yada=yada', 'params')

    params = Pyjo.Parameters.new('foo=bar&yada=yada').merge(foo=None)
    is_ok(str(params), 'yada=yada', 'params')

    # names
    params = Pyjo.Parameters.new('foo=bar&baz=23')
    names = params.names
    is_deeply_ok(names, ['baz', 'foo'], 'params.param()')

    # pairs
    pairs = Pyjo.Parameters.new('foo=bar&baz=23')
    array = params.pairs
    is_deeply_ok(array, [('foo', 'bar'), ('baz', '23')], 'params.pairs')
    params.pairs = [('foo', 'b&ar'), ('baz', 23)]
    is_ok(str(params), 'foo=b%26ar&baz=23', 'pairs')

    # param
    params = Pyjo.Parameters.new('foo=bar&baz=23')
    value = params.param('foo')
    is_ok(value, 'bar', "params.param('foo')")
    foo, baz = params.param(['foo', 'baz'])
    is_ok(foo, 'bar', "params.param(['foo', 'baz'])[0]")
    is_ok(baz, '23', "params.param(['foo', 'baz'])[1]")
    params = params.param('foo', 'ba&r')
    is_ok(str(params), 'foo=ba%26r&baz=23', "params.param('foo', 'ba&r')")
    params = params.param('foo', ['ba;r', 'baz'])
    is_ok(str(params), 'foo=ba%3Br&baz=23&foo=baz', "params.param('foo', ['ba;r', 'baz'])")

    # parse
    params = Pyjo.Parameters.new()
    params = params.parse('foo=b%3Bar&baz=23')
    is_deeply_ok(params.pairs, [('foo', 'b;ar'), ('baz', '23')], "params.parse('foo=b%3Bar&baz=23')")

    # remove
    params = Pyjo.Parameters.new('foo=bar&foo=baz&bar=yada').remove('foo')
    is_ok(str(params), 'bar=yada', "params.remove('foo')")

    # to_dict
    d = Pyjo.Parameters.new('foo=bar&foo=baz').to_dict()
    is_deeply_ok(d, {'foo': ['bar', 'baz']}, 'params.to_dict()')

    done_testing()
