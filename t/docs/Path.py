import Pyjo.Test


class NoseTest(Pyjo.Test.NoseTest):
    script = __file__
    srcdir = '../..'


class UnitTest(Pyjo.Test.UnitTest):
    script = __file__


if __name__ == '__main__':
    from Pyjo.Test import *  # noqa

    import Pyjo.Path
    from Pyjo.String.Unicode import u

    # __init __
    path = Pyjo.Path.new()
    is_ok(str(path), '', 'path')
    path = Pyjo.Path.new('/foo%2Fbar%3B/baz.html')
    is_ok(str(path), '/foo%2Fbar%3B/baz.html', 'path')

    # charset
    path = Pyjo.Path.new('/foo%2Fbar%3B/baz.html')
    charset = path.charset
    is_ok(charset, 'utf-8', 'charset')
    path.charset = 'utf-8'
    charset = path.charset
    is_ok(charset, 'utf-8', 'charset')

    # __iter__
    path = Pyjo.Path.new('/foo%2Fbar%3B/baz.html')
    l = [v for v in path]
    is_deeply_ok(l, ['foo', 'bar;', 'baz.html'], '[v for v in path]')

    # __bool__
    ok(Pyjo.Path.new(), 'Pyjo.Path.new()')

    # canonicalize
    path = Pyjo.Path.new('/foo/./bar/../baz').canonicalize()
    is_ok(str(path), '/foo/baz', 'path')

    path = Pyjo.Path.new('/foo/../bar/../../baz').canonicalize()
    is_ok(str(path), '/../baz', 'path')

    path = Pyjo.Path.new('/foo/.../bar').canonicalize()
    is_ok(str(path), '/foo/bar', 'path')

    # clone
    path = Pyjo.Path.new('/foo%2Fbar%3B/baz.html')
    path2 = path.clone()
    is_ok(str(path2), '/foo%2Fbar%3B/baz.html', 'path2')
    isnt_ok(id(path), id(path2), 'path')

    # contains
    boolean = Pyjo.Path.new('/foo/bar').contains('/')
    is_ok(boolean, True, 'boolean')
    boolean = Pyjo.Path.new('/foo/bar').contains('/foo')
    is_ok(boolean, True, 'boolean')
    boolean = Pyjo.Path.new('/foo/bar').contains('/foo/bar')
    is_ok(boolean, True, 'boolean')

    boolean = Pyjo.Path.new('/foo/bar').contains('/f')
    is_ok(boolean, False, 'boolean')
    boolean = Pyjo.Path.new('/foo/bar').contains('/bar')
    is_ok(boolean, False, 'boolean')
    boolean = Pyjo.Path.new('/foo/bar').contains('/whatever')
    is_ok(boolean, False, 'boolean')

    # leading_slash
    path = Pyjo.Path.new('/foo%2Fbar%3B/baz.html')
    leading_slash = path.leading_slash
    is_ok(leading_slash, True, 'leading_slash')
    path.leading_slash = False
    leading_slash = path.leading_slash
    is_ok(leading_slash, False, 'leading_slash')

    # merge
    path = Pyjo.Path.new('/foo/bar').merge('/baz/yada')
    is_ok(str(path), '/baz/yada', 'path')

    path = Pyjo.Path.new('/foo/bar').merge('baz/yada')
    is_ok(str(path), '/foo/baz/yada', 'path')

    path = Pyjo.Path.new('/foo/bar/').merge('baz/yada')
    is_ok(str(path), '/foo/bar/baz/yada', 'path')

    # parse
    path = Pyjo.Path.new()
    path = path.parse('/foo%2Fbar%3B/baz.html')
    is_deeply_ok(path.parts, ['foo', 'bar;', 'baz.html'], 'path.parts')

    # paths
    path = Pyjo.Path.new()
    path.parts = ['foo', 'bar', 'baz']
    is_ok(str(path), 'foo/bar/baz', 'path')

    path.parts.append('foo/bar')
    is_ok(str(path), 'foo/bar/baz/foo%2Fbar', 'path')

    # to_abs_str
    path = Pyjo.Path.new('/i/%E2%99%A5/pyjo').to_abs_str()
    is_ok(str(path), '/i/%E2%99%A5/pyjo', 'path')

    path = Pyjo.Path.new('i/%E2%99%A5/pyjo').to_abs_str()
    is_ok(str(path), '/i/%E2%99%A5/pyjo', 'path')

    # to_bytes
    path = Pyjo.Path.new('/i/%E2%99%A5/pyjo')
    is_ok(bytes(path), b'/i/%E2%99%A5/pyjo', 'path')

    path = Pyjo.Path.new('i/%E2%99%A5/pyjo')
    is_ok(bytes(path), b'i/%E2%99%A5/pyjo', 'path')

    # to_dir
    path = Pyjo.Path.new('/i/%E2%99%A5/pyjo').to_dir()
    is_ok(str(path), '/i/%E2%99%A5/', 'path')

    path = Pyjo.Path.new('i/%E2%99%A5/pyjo').to_dir()
    is_ok(str(path), 'i/%E2%99%A5/', 'path')

    # to_route
    path = Pyjo.Path.new('/i/%E2%99%A5/pyjo').to_route()
    is_ok(u(path), '/i/♥/pyjo', 'path')

    path = Pyjo.Path.new('i/%E2%99%A5/pyjo').to_route()
    is_ok(u(path), '/i/♥/pyjo', 'path')

    # to_str
    path = Pyjo.Path.new('/i/%E2%99%A5/pyjo')
    is_ok(str(path), '/i/%E2%99%A5/pyjo', 'path')

    path = Pyjo.Path.new('i/%E2%99%A5/pyjo')
    is_ok(str(path), 'i/%E2%99%A5/pyjo', 'path')

    # trailing_slash
    path = Pyjo.Path.new('/foo%2Fbar%3B/baz.html')
    trailing_slash = path.trailing_slash
    is_ok(trailing_slash, False, 'trailing_slash')
    path.trailing_slash = True
    trailing_slash = path.trailing_slash
    is_ok(trailing_slash, True, 'trailing_slash')

    done_testing()
