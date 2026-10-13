if __name__ == '__main__':
    from Pyjo.Test import *  # noqa

    import Pyjo.JSON.Pointer

    # "contains" (dict)
    pointer = Pyjo.JSON.Pointer.new({'foo': 23})
    ok(pointer.contains(''), 'contains ""')
    ok(pointer.contains('/foo'), 'contains "/foo"')
    ok(not pointer.contains('/bar'), 'does not contains "/bar"')
    ok(pointer.new({'foo': {'bar': None}}).contains('/foo/bar'), 'contains "/foo/bar"')

    # "contains" (mixed)
    pointer = Pyjo.JSON.Pointer.new({'foo': [0, 1, 2]})
    ok(pointer.contains(''), 'contains ""')
    ok(pointer.contains('/foo/0'), 'contains "/foo/0"')
    ok(not pointer.contains('/foo/9'), 'does not contain "/foo/9"')
    ok(not pointer.contains('/foo/bar'), 'does not contain "/foo/bar"')
    ok(not pointer.contains('/0'), 'does not contain "/0"')

    # "get" (dict)
    pointer = Pyjo.JSON.Pointer.new({'foo': 'bar'})
    is_deeply_ok(pointer.get(''), {'foo': 'bar'}, '"" is "{foo: "bar"}"')
    is_ok(pointer.get('/foo'), 'bar', '"/foo" is "bar"')
    is_ok(pointer.new({'foo': {'bar': 42}}).get('/foo/bar'), 42, '"/foo/bar" is "42"')
    is_deeply_ok(pointer.new({'foo': {23: {'baz': 0}}}).get('/foo/23'), {'baz': 0}, '"/foo/23" is "{baz: 0}"')

    # "get" (mixed)
    is_deeply_ok(pointer.new({'foo': {'bar': [1, 2, 3]}}).get('/foo/bar'), [1, 2, 3], '"/foo/bar" is "[1, 2, 3]"')
    pointer = Pyjo.JSON.Pointer.new({'foo': {'bar': [0, None, 3]}})
    is_ok(pointer.get('/foo/bar/0'), 0, '"/foo/bar/0" is "0"')
    is_ok(pointer.get('/foo/bar/1'), None, '"/foo/bar/1" is "None"')
    is_ok(pointer.get('/foo/bar/2'), 3, '"/foo/bar/2" is "3"')
    is_ok(pointer.get('/foo/bar/6'), None, '"/foo/bar/6" is "None"')

    # "get" (encoded)
    is_ok(pointer.new([{'foo/bar': 'bar'}]).get('/0/foo~1bar'), 'bar', '"/0/foo~1bar" is "bar"')
    is_ok(pointer.new([{'foo/bar/baz': 'yada'}]).get('/0/foo~1bar~1baz'), 'yada', '"/0/foo~1bar~1baz" is "yada"')
    is_ok(pointer.new([{'foo~/bar': 'bar'}]).get('/0/foo~0~1bar'), 'bar', '"/0/foo~0~1bar" is "bar"')
    is_ok(
        pointer.new([{'f~o~o~/b~': {'a~': {'r': 'baz'}}}]).get('/0/f~0o~0o~0~1b~0/a~0/r'),
        'baz',
        '"/0/f~0o~0o~0~1b~0/a~0/r" is "baz"',
    )
    is_ok(pointer.new({'~1': 'foo'}).get('/~01'), 'foo', '"/~01" is "foo"')

    # Unicode
    is_ok(pointer.new({'☃': 'snowman'}).get('/☃'), 'snowman', 'found the snowman')
    is_ok(pointer.new().set(data={'☃': ['snowman']}).get('/☃/0'), 'snowman', 'found the snowman')

    # RFC 6901
    d = {'foo': ['bar', 'baz'], '': 0, 'a/b': 1, 'c%d': 2, 'e^f': 3, r'g|h': 4, r'i\\j': 5, 'k"l': 6, ' ': 7, 'm~n': 8}
    pointer = Pyjo.JSON.Pointer.new(d)
    is_deeply_ok(pointer.get(''), d, 'empty pointer is whole document')
    is_deeply_ok(pointer.get('/foo'), ['bar', 'baz'], '"/foo" is "["bar", "baz"]"')
    is_ok(pointer.get('/foo/0'), 'bar', '"/foo/0" is "bar"')
    is_ok(pointer.get('/'), 0, '"/" is 0')
    is_ok(pointer.get('/a~1b'), 1, '"/a~1b" is 1')
    is_ok(pointer.get('/c%d'), 2, '"/c%d" is 2')
    is_ok(pointer.get('/e^f'), 3, '"/e^f" is 3')
    is_ok(pointer.get(r'/g|h'), 4, r'"/g|h" is 4')
    is_ok(pointer.get(r'/i\\j'), 5, r'"/i\\\\j" is 5')
    is_ok(pointer.get('/k"l'), 6, '"/k\\"l" is 6')
    is_ok(pointer.get('/ '), 7, '"/ " is 7')
    is_ok(pointer.get('/m~0n'), 8, '"/m~0n" is 8')

    done_testing()
