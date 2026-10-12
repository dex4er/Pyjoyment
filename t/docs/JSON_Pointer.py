import Pyjo.Test


class NoseTest(Pyjo.Test.NoseTest):
    script = __file__
    srcdir = '../..'


class UnitTest(Pyjo.Test.UnitTest):
    script = __file__


if __name__ == '__main__':
    from Pyjo.Test import *  # noqa

    import Pyjo.JSON.Pointer

    pointer = Pyjo.JSON.Pointer.new({'foo': [23, 'bar']})
    is_ok(pointer.get('/foo/1'), 'bar', 'get /foo/1')
    ok(pointer.contains('/foo'), 'contains /foo')

    # data
    pointer = Pyjo.JSON.Pointer.new()
    data = pointer.data
    is_deeply_ok(data, None, 'pointer.data')
    pointer.data = {'foo': 'bar'}
    is_deeply_ok(pointer.data, {'foo': 'bar'}, 'pointer.data')

    # new
    pointer = Pyjo.JSON.Pointer.new()
    is_deeply_ok(pointer.data, None, 'pointer.data')
    pointer = Pyjo.JSON.Pointer.new({'foo': 'bar'})
    is_deeply_ok(pointer.data, {'foo': 'bar'}, 'pointer.data')

    # contains
    pointer = Pyjo.JSON.Pointer.new()
    boolean = pointer.contains('/foo/1')
    is_ok(boolean, False, 'boolean')

    ok(Pyjo.JSON.Pointer.new({'♥': 'pyjo'}).contains('/♥'), 'contains')
    ok(Pyjo.JSON.Pointer.new({'foo': 'bar', 'baz': [4, 5]}).contains('/foo'), 'contains')
    ok(Pyjo.JSON.Pointer.new({'foo': 'bar', 'baz': [4, 5]}).contains('/baz/1'), 'contains')

    ok(not Pyjo.JSON.Pointer.new({'♥': 'pyjo'}).contains('/☃'), 'contains')
    ok(not Pyjo.JSON.Pointer.new({'foo': 'bar', 'baz': [4, 5]}).contains('/bar'), 'contains')
    ok(not Pyjo.JSON.Pointer.new({'foo': 'bar', 'baz': [4, 5]}).contains('/baz/9'), 'contains')

    # get
    pointer = Pyjo.JSON.Pointer.new()
    value = pointer.get('/foo/bar')
    is_ok(value, None, 'value')

    is_ok(Pyjo.JSON.Pointer.new({'♥': 'pyjo'}).get('/♥'), 'pyjo', 'get')
    is_ok(Pyjo.JSON.Pointer.new({'foo': 'bar', 'baz': [4, 5, 6]}).get('/foo'), 'bar', 'get')
    is_ok(Pyjo.JSON.Pointer.new({'foo': 'bar', 'baz': [4, 5, 6]}).get('/baz/0'), 4, 'get')
    is_ok(Pyjo.JSON.Pointer.new({'foo': 'bar', 'baz': [4, 5, 6]}).get('/baz/2'), 6, 'get')
    is_ok(Pyjo.JSON.Pointer.new({4: 'number', '4': 'string'}).get('/4'), 'number', 'get')

    done_testing()
