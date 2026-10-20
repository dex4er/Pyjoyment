from Pyjo.Test import *


with subtest('Synopsis'):
    from Pyjo.JSON.Pointer import Pointer

    pointer = Pointer({'foo': [23, 'bar']})
    is_ok(pointer.get('/foo/1'), 'bar', "pointer.get('/foo/1')")
    ok(pointer.contains('/foo'), 'Contains "/foo".')

    # Or import the module, as in Google Python Style Guide

    import Pyjo.JSON.Pointer

    pointer = Pyjo.JSON.Pointer.new({'foo': [23, 'bar']})
    is_ok(pointer.get('/foo/1'), 'bar', "pointer.get('/foo/1')")
    ok(pointer.contains('/foo'), 'Contains "/foo".')

with subtest('data'):
    data = pointer.data
    is_ok(data, {'foo': [23, 'bar']}, 'data')
    pointer.data = {'foo': 'bar'}
    is_ok(pointer.data, {'foo': 'bar'}, 'pointer.data')

with subtest('new'):
    pointer = Pyjo.JSON.Pointer.new()
    is_ok(pointer.data, None, 'no data')
    pointer = Pyjo.JSON.Pointer.new({'foo': 'bar'})
    is_ok(pointer.data, {'foo': 'bar'}, 'data')

with subtest('contains'):
    pointer = Pyjo.JSON.Pointer.new({'foo': ['bar', 'baz']})
    boolean = pointer.contains('/foo/1')
    is_ok(boolean, True, 'boolean')

    # True
    ok(Pyjo.JSON.Pointer.new('just a string').contains(''), 'just a string')
    ok(Pyjo.JSON.Pointer.new({'♥': 'pyjoyment'}).contains('/♥'), '/♥')
    ok(Pyjo.JSON.Pointer.new({'foo': 'bar', 'baz': [4, 5]}).contains('/foo'), '/foo')
    ok(Pyjo.JSON.Pointer.new({'foo': 'bar', 'baz': [4, 5]}).contains('/baz/1'), '/baz/1')

    # False
    ok(not Pyjo.JSON.Pointer.new({'♥': 'pyjoyment'}).contains('/☃'), '/☃')
    ok(not Pyjo.JSON.Pointer.new({'foo': 'bar', 'baz': [4, 5]}).contains('/bar'), '/bar')
    ok(not Pyjo.JSON.Pointer.new({'foo': 'bar', 'baz': [4, 5]}).contains('/baz/9'), '/baz/9')

with subtest('get'):
    pointer = Pyjo.JSON.Pointer.new({'foo': {'bar': 'baz'}})
    value = pointer.get('/foo/bar')
    is_ok(value, 'baz', 'value')

    # "just a string"
    is_ok(Pyjo.JSON.Pointer.new('just a string').get(''), 'just a string', 'just a string')

    # "pyjoyment"
    is_ok(Pyjo.JSON.Pointer.new({'♥': 'pyjoyment'}).get('/♥'), 'pyjoyment', '/♥')

    # "bar"
    is_ok(Pyjo.JSON.Pointer.new({'foo': 'bar', 'baz': [4, 5, 6]}).get('/foo'), 'bar', '/foo')

    # 4
    is_ok(Pyjo.JSON.Pointer.new({'foo': 'bar', 'baz': [4, 5, 6]}).get('/baz/0'), 4, '/baz/0')

    # 6
    is_ok(Pyjo.JSON.Pointer.new({'foo': 'bar', 'baz': [4, 5, 6]}).get('/baz/2'), 6, '/baz/2')

done_testing()
