from Pyjo.Test import *


with subtest('Synopsis'):
    from Pyjo.Path import Path

    # Parse
    path = Path('/foo%2Fbar%3B/baz.html')
    is_ok(path[0], 'foo', 'path[0]')

    # Or import the module, as in Google Python Style Guide

    import Pyjo.Path

    # Parse
    path = Pyjo.Path.new('/foo%2Fbar%3B/baz.html')
    is_ok(path[0], 'foo', 'path[0]')

    # Build
    path = Pyjo.Path.new('/i/♥')
    path.parts.append('pyjoyment')
    is_ok(str(path), '/i/%E2%99%A5/pyjoyment', 'path')

with subtest('new'):
    path = Pyjo.Path.new()
    is_ok(str(path), '', 'path')
    path = Pyjo.Path.new('/foo%2Fbar%3B/baz.html')
    is_ok(str(path), '/foo%2Fbar%3B/baz.html', 'path')

with subtest('charset'):
    charset = path.charset
    is_ok(charset, 'UTF-8', 'charset')
    path.charset = 'UTF-8'
    is_ok(path.charset, 'UTF-8', 'path.charset')

    # Disable encoding and decoding
    path.charset = None
    is_ok(path.charset, None, 'path.charset')

with subtest('__bool__'):
    boolean = bool(path)
    is_ok(boolean, True, 'boolean')

with subtest('__getitem__'):
    path = Pyjo.Path.new('/foo%2Fbar%3B/baz.html')
    part = path[0]
    is_ok(part, 'foo', 'part')

with subtest('__iter__'):
    parts = list(path)
    is_deeply_ok(parts, ['foo', 'bar;', 'baz.html'], 'parts')
    is_deeply_ok([part for part in path], ['foo', 'bar;', 'baz.html'], 'for part in path')

with subtest('__len__'):
    size = len(path)
    is_ok(size, 3, 'size')

with subtest('__str__'):
    string = str(path)
    is_ok(string, '/foo/bar;/baz.html', 'string')

with subtest('canonicalize'):
    path = Pyjo.Path.new('/foo/../bar').canonicalize()
    is_ok(str(path), '/bar', 'path')

    # "/foo/baz"
    is_ok(str(Pyjo.Path.new('/foo/./bar/../baz').canonicalize()), '/foo/baz', "'/foo/./bar/../baz'")

    # "/../baz"
    is_ok(str(Pyjo.Path.new('/foo/../bar/../../baz').canonicalize()), '/../baz', "'/foo/../bar/../../baz'")

    # "/foo/bar"
    is_ok(str(Pyjo.Path.new('/foo/.../bar').canonicalize()), '/foo/bar', "'/foo/.../bar'")

with subtest('clone'):
    clone = path.clone()
    is_ok(str(clone), '/bar', 'clone')
    isnt_ok(id(clone), id(path), 'another object')

with subtest('contains'):
    boolean = Pyjo.Path.new('/i/♥/pyjoyment').contains('/i/♥/pyjoyment')
    is_ok(boolean, True, 'boolean')

    # True
    is_ok(Pyjo.Path.new('/foo/bar').contains('/'), True, "contains('/')")
    is_ok(Pyjo.Path.new('/foo/bar').contains('/foo'), True, "contains('/foo')")
    is_ok(Pyjo.Path.new('/foo/bar').contains('/foo/bar'), True, "contains('/foo/bar')")

    # False
    is_ok(Pyjo.Path.new('/foo/bar').contains('/f'), False, "contains('/f')")
    is_ok(Pyjo.Path.new('/foo/bar').contains('/bar'), False, "contains('/bar')")
    is_ok(Pyjo.Path.new('/foo/bar').contains('/whatever'), False, "contains('/whatever')")

with subtest('leading_slash'):
    boolean = path.leading_slash
    is_ok(boolean, True, 'boolean')
    path.leading_slash = boolean
    is_ok(path.leading_slash, True, 'path.leading_slash')

    # "/foo/bar"
    is_ok(str(Pyjo.Path.new('foo/bar').set(leading_slash=True)), '/foo/bar', 'leading_slash=True')

    # "foo/bar"
    is_ok(str(Pyjo.Path.new('/foo/bar').set(leading_slash=False)), 'foo/bar', 'leading_slash=False')

with subtest('merge'):
    path = Pyjo.Path.new('/baz/')
    path = path.merge('/foo/bar')
    is_ok(str(path), '/foo/bar', "merge('/foo/bar')")
    path = path.merge('foo/bar')
    is_ok(str(path), '/foo/foo/bar', "merge('foo/bar')")
    path = path.merge(Pyjo.Path.new())
    is_ok(str(path), '/foo/foo', 'merge(Pyjo.Path.new())')

    # "/baz/yada"
    is_ok(str(Pyjo.Path.new('/foo/bar').merge('/baz/yada')), '/baz/yada', "merge('/baz/yada')")

    # "/foo/baz/yada"
    is_ok(str(Pyjo.Path.new('/foo/bar').merge('baz/yada')), '/foo/baz/yada', "merge('baz/yada')")

    # "/foo/bar/baz/yada"
    is_ok(str(Pyjo.Path.new('/foo/bar/').merge('baz/yada')), '/foo/bar/baz/yada', "'/foo/bar/' merge('baz/yada')")

with subtest('parse'):
    path = path.parse('/foo%2Fbar%3B/baz.html')
    is_deeply_ok(path.parts, ['foo', 'bar;', 'baz.html'], 'path.parts')

with subtest('parts'):
    parts = path.parts
    is_deeply_ok(parts, ['foo', 'bar;', 'baz.html'], 'parts')
    path.parts = ['foo', 'bar', 'baz']
    is_ok(str(path), '/foo/bar/baz', 'path')

    # Part with slash
    path.parts.append('foo/bar')
    is_ok(str(path), '/foo/bar/baz/foo%2Fbar', 'path')

with subtest('to_abs_str'):
    string = path.to_abs_str()
    is_ok(string, '/foo/bar/baz/foo%2Fbar', 'string')

    # "/i/%E2%99%A5/pyjoyment"
    is_ok(Pyjo.Path.new('/i/%E2%99%A5/pyjoyment').to_abs_str(), '/i/%E2%99%A5/pyjoyment', 'absolute')
    is_ok(Pyjo.Path.new('i/%E2%99%A5/pyjoyment').to_abs_str(), '/i/%E2%99%A5/pyjoyment', 'relative')

with subtest('to_dir'):
    route = Pyjo.Path.new('/foo/bar')
    dir = route.to_dir()
    is_ok(str(dir), '/foo/', 'dir')

    # "/i/%E2%99%A5/"
    is_ok(Pyjo.Path.new('/i/%E2%99%A5/pyjoyment').to_dir().to_abs_str(), '/i/%E2%99%A5/', 'absolute')

    # "i/%E2%99%A5/"
    is_ok(Pyjo.Path.new('i/%E2%99%A5/pyjoyment').to_dir().to_abs_str(), '/i/%E2%99%A5/', 'relative')

with subtest('to_route'):
    route = path.to_route()
    is_ok(route, '/foo/bar/baz/foo/bar', 'route')

    # "/i/♥/pyjoyment"
    is_ok(Pyjo.Path.new('/i/%E2%99%A5/pyjoyment').to_route(), '/i/♥/pyjoyment', 'absolute')
    is_ok(Pyjo.Path.new('i/%E2%99%A5/pyjoyment').to_route(), '/i/♥/pyjoyment', 'relative')

with subtest('to_str'):
    string = path.to_str()
    is_ok(string, '/foo/bar/baz/foo%2Fbar', 'string')

    # "/i/%E2%99%A5/pyjoyment"
    is_ok(Pyjo.Path.new('/i/%E2%99%A5/pyjoyment').to_str(), '/i/%E2%99%A5/pyjoyment', 'absolute')

    # "i/%E2%99%A5/pyjoyment"
    is_ok(Pyjo.Path.new('i/%E2%99%A5/pyjoyment').to_str(), 'i/%E2%99%A5/pyjoyment', 'relative')

with subtest('trailing_slash'):
    boolean = path.trailing_slash
    is_ok(boolean, False, 'boolean')
    path.trailing_slash = boolean
    is_ok(path.trailing_slash, False, 'path.trailing_slash')

    # "/foo/bar/"
    is_ok(str(Pyjo.Path.new('/foo/bar').set(trailing_slash=True)), '/foo/bar/', 'trailing_slash=True')

    # "/foo/bar"
    is_ok(str(Pyjo.Path.new('/foo/bar/').set(trailing_slash=False)), '/foo/bar', 'trailing_slash=False')

done_testing()
