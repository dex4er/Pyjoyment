# coding: utf-8

import Pyjo.Test


class NoseTest(Pyjo.Test.NoseTest):
    script = __file__
    srcdir = '../..'


class UnitTest(Pyjo.Test.UnitTest):
    script = __file__


if __name__ == '__main__':

    from Pyjo.Test import *  # @UnusedWildImport

    import Pyjo.Path

    # Basic functionality
    path = Pyjo.Path.new()
    is_ok(str(path.parse('/path')), '/path', 'right path')
    is_ok(str(path.to_dir()), '/', 'right directory')
    is_deeply_ok(path.parts, ['path'], 'right structure')
    ok(path.leading_slash, 'has leading slash')
    ok(not path.trailing_slash, 'no trailing slash')
    is_ok(str(path.parse('path/')), 'path/', 'right path')
    is_ok(str(path.to_dir()), 'path/', 'right directory')
    is_ok(path.to_dir().to_abs_str(), '/path/', 'right directory')
    is_deeply_ok(path.parts, ['path'], 'right structure')
    ok(not path.leading_slash, 'no leading slash')
    ok(path.trailing_slash, 'has trailing slash')
    path = Pyjo.Path.new()
    is_ok(path.to_str(), '', 'no path')
    is_ok(path.to_abs_str(), '/', 'right absolute path')
    is_ok(path.to_route(), '/', 'right route')

    # Advanced
    path = Pyjo.Path.new('/AZaz09-._~!$&\'()*+,;=:@')
    is_ok(path.parts[0], 'AZaz09-._~!$&\'()*+,;=:@', 'right part')
    is_ok(len(path.parts), 1, 'no part')
    ok(path.leading_slash, 'has leading slash')
    ok(not path.trailing_slash, 'no trailing slash')
    is_ok(str(path), '/AZaz09-._~!$&\'()*+,;=:@', 'right path')
    path.parts.append('f/oo')
    is_ok(str(path), '/AZaz09-._~!$&\'()*+,;=:@/f%2Foo', 'right path')

    # Unicode
    is_ok(str(path.parse(u'/foo/♥/bar')), '/foo/%E2%99%A5/bar', 'right path')
    is_ok(str(path.to_dir()), '/foo/%E2%99%A5/', 'right directory')
    is_deeply_ok(path.parts, ['foo', u'♥', 'bar'], 'right structure')
    ok(path.leading_slash, 'has leading slash')
    ok(not path.trailing_slash, 'no trailing slash')
    is_ok(path.to_route(), u'/foo/♥/bar', 'right route')
    is_ok(str(path.parse('/foo/%E2%99%A5/~b@a:r+')), '/foo/%E2%99%A5/~b@a:r+', 'right path')
    is_deeply_ok(path.parts, ['foo', u'♥', '~b@a:r+'], 'right structure')
    ok(path.leading_slash, 'has leading slash')
    ok(not path.trailing_slash, 'no trailing slash')
    is_ok(path.to_route(), u'/foo/♥/~b@a:r+', 'right route')

    # Zero in path
    is_ok(str(path.parse('/path/0')), '/path/0', 'right path')
    is_deeply_ok(path.parts, ['path', '0'], 'right structure')
    ok(path.leading_slash, 'has leading slash')
    ok(not path.trailing_slash, 'no trailing slash')
    path = Pyjo.Path.new('0')
    is_deeply_ok(path.parts, ['0'], 'right structure')
    is_ok(str(path), '0', 'right path')
    is_ok(path.to_abs_str(), '/0', 'right absolute path')
    is_ok(path.to_route(), '/0', 'right route')

    # Canonicalizing
    path = Pyjo.Path.new('/%2f..%2f..%2f..%2f..%2f..%2f..%2f..%2f..%2f..%2f..%2fetc%2fpasswd')
    is_ok(str(path), '/%2f..%2f..%2f..%2f..%2f..%2f..%2f..%2f..%2f..%2f..%2fetc%2fpasswd', 'same path')
    is_deeply_ok(path.parts, ['', '..', '..', '..', '..', '..', '..', '..', '..', '..', '..', 'etc', 'passwd'], 'right structure')
    is_ok(str(path), '//../../../../../../../../../../etc/passwd', 'normalized path')
    is_ok(str(path.canonicalize()), '/../../../../../../../../../../etc/passwd', 'canonicalized path')
    is_deeply_ok(path.parts, ['..', '..', '..', '..', '..', '..', '..', '..', '..', '..', 'etc', 'passwd'], 'right structure')
    ok(path.leading_slash, 'has leading slash')
    ok(not path.trailing_slash, 'no trailing slash')

    # Canonicalizing (alternative)
    path = Pyjo.Path.new('%2ftest%2f..%2f..%2f..%2f..%2f..%2f..%2f..%2f..%2f..%2fetc%2fpasswd')
    is_ok(str(path), '%2ftest%2f..%2f..%2f..%2f..%2f..%2f..%2f..%2f..%2f..%2fetc%2fpasswd', 'same path')
    is_deeply_ok(path.parts, ['test', '..', '..', '..', '..', '..', '..', '..', '..', '..', 'etc', 'passwd'], 'right structure')
    is_ok(str(path), '/test/../../../../../../../../../etc/passwd', 'normalized path')
    is_ok(str(path.canonicalize()), '/../../../../../../../../etc/passwd', 'canonicalized path')
    is_deeply_ok(path.parts, ['..', '..', '..', '..', '..', '..', '..', '..', 'etc', 'passwd'], 'right structure')
    ok(path.leading_slash, 'has leading slash')
    ok(not path.trailing_slash, 'no trailing slash')

    # Canonicalizing (with escaped "%")
    path = Pyjo.Path.new('%2ftest%2f..%252f..%2f..%2f..%2f..%2fetc%2fpasswd')
    is_ok(str(path), '%2ftest%2f..%252f..%2f..%2f..%2f..%2fetc%2fpasswd', 'same path')
    is_deeply_ok(path.parts, ['test', '..%2f..', '..', '..', '..', 'etc', 'passwd'], 'right structure')
    is_ok(str(path), '/test/..%252f../../../../etc/passwd', 'normalized path')
    is_ok(str(path.canonicalize()), '/../etc/passwd', 'canonicalized path')
    is_deeply_ok(path.parts, ['..', 'etc', 'passwd'], 'right structure')
    ok(path.leading_slash, 'has leading slash')
    ok(not path.trailing_slash, 'no trailing slash')

    # Contains
    path = Pyjo.Path.new('/foo/bar')
    ok(path.contains('/'), 'contains path')
    ok(path.contains('/foo'), 'contains path')
    ok(path.contains('/foo/bar'), 'contains path')
    ok(not path.contains('/foobar'), 'does not contain path')
    ok(not path.contains('/foo/b'), 'does not contain path')
    ok(not path.contains('/foo/bar/baz'), 'does not contain path')
    path = Pyjo.Path.new(u'/♥/bar')
    ok(path.contains(u'/♥'), 'contains path')
    ok(path.contains(u'/♥/bar'), 'contains path')
    ok(not path.contains(u'/♥foo'), 'does not contain path')
    ok(not path.contains(u'/foo♥'), 'does not contain path')
    path = Pyjo.Path.new('/')
    ok(path.contains('/'), 'contains path')
    ok(not path.contains('/foo'), 'does not contain path')
    path = Pyjo.Path.new('/0')
    ok(path.contains('/'), 'contains path')
    ok(path.contains('/0'), 'contains path')
    ok(not path.contains('/0/0'), 'does not contain path')
    path = Pyjo.Path.new(u'/0/♥.html')
    ok(path.contains('/'), 'contains path')
    ok(path.contains('/0'), 'contains path')
    ok(path.contains(u'/0/♥.html'), 'contains path')
    ok(not path.contains(u'/0/♥'), 'does not contain path')
    ok(not path.contains(u'/0/0.html'), 'does not contain path')
    ok(not path.contains('/0.html'), 'does not contain path')
    ok(not path.contains(u'/♥.html'), 'does not contain path')

    # Merge
    path = Pyjo.Path.new('/foo')
    path.merge('bar/baz')
    is_ok(str(path), '/bar/baz', 'right path')
    ok(path.leading_slash, 'has leading slash')
    ok(not path.trailing_slash, 'no trailing slash')
    path = Pyjo.Path.new('/foo/')
    path.merge('bar/baz')
    is_ok(str(path), '/foo/bar/baz', 'right path')
    ok(path.leading_slash, 'has leading slash')
    ok(not path.trailing_slash, 'no trailing slash')
    path = Pyjo.Path.new('/foo/')
    path.merge('bar/baz/')
    is_ok(str(path), '/foo/bar/baz/', 'right path')
    ok(path.leading_slash, 'has leading slash')
    ok(path.trailing_slash, 'has trailing slash')
    path = Pyjo.Path.new('/foo/')
    path.merge('/bar/baz')
    is_ok(str(path), '/bar/baz', 'right path')
    ok(path.leading_slash, 'has leading slash')
    ok(not path.trailing_slash, 'no trailing slash')
    is_ok(path.to_route(), '/bar/baz', 'right route')
    path = Pyjo.Path.new('/foo/bar')
    path.merge('/bar/baz/')
    is_ok(str(path), '/bar/baz/', 'right path')
    ok(path.leading_slash, 'has leading slash')
    ok(path.trailing_slash, 'has trailing slash')
    is_ok(path.to_route(), '/bar/baz/', 'right route')
    path = Pyjo.Path.new('foo/bar')
    path.merge('baz/yada')
    is_ok(str(path), 'foo/baz/yada', 'right path')
    ok(not path.leading_slash, 'no leading slash')
    ok(not path.trailing_slash, 'no trailing slash')
    is_ok(path.to_route(), '/foo/baz/yada', 'right route')

    # Empty path elements
    path = Pyjo.Path.new('//')
    is_ok(str(path), '//', 'right path')
    is_deeply_ok(path.parts, [], 'no parts')
    ok(path.leading_slash, 'has leading slash')
    ok(path.trailing_slash, 'has trailing slash')
    is_ok(str(path), '//', 'right normalized path')
    path = Pyjo.Path.new('%2F%2f')
    is_ok(str(path), '%2F%2f', 'right path')
    is_deeply_ok(path.parts, [], 'no parts')
    ok(path.leading_slash, 'has leading slash')
    ok(path.trailing_slash, 'has trailing slash')
    is_ok(str(path), '//', 'right normalized path')
    path = Pyjo.Path.new('/foo//bar/23/')
    is_ok(str(path), '/foo//bar/23/', 'right path')
    is_deeply_ok(path.parts, ['foo', '', 'bar', '23'], 'right structure')
    ok(path.leading_slash, 'has leading slash')
    ok(path.trailing_slash, 'has trailing slash')
    path = Pyjo.Path.new('//foo/bar/23/')
    is_ok(str(path), '//foo/bar/23/', 'right path')
    is_deeply_ok(path.parts, ['', 'foo', 'bar', '23'], 'right structure')
    ok(path.leading_slash, 'has leading slash')
    ok(path.trailing_slash, 'has trailing slash')
    path = Pyjo.Path.new('/foo///bar/23/')
    is_ok(str(path), '/foo///bar/23/', 'right path')
    is_deeply_ok(path.parts, ['foo', '', '', 'bar', '23'], 'right structure')
    ok(path.leading_slash, 'has leading slash')
    ok(path.trailing_slash, 'has trailing slash')
    path = Pyjo.Path.new('///foo/bar/23/')
    is_ok(str(path), '///foo/bar/23/', 'right path')
    is_deeply_ok(path.parts, ['', '', 'foo', 'bar', '23'], 'right structure')
    ok(path.leading_slash, 'has leading slash')
    ok(path.trailing_slash, 'has trailing slash')
    path = Pyjo.Path.new('///foo///bar/23///')
    is_ok(str(path), '///foo///bar/23///', 'right path')
    is_deeply_ok(path.parts, ['', '', 'foo', '', '', 'bar', '23', '', ''], 'right structure')
    ok(path.leading_slash, 'has leading slash')
    ok(path.trailing_slash, 'has trailing slash')

    # Escaped slash
    path = Pyjo.Path.new().set(parts=['foo/bar'])
    is_deeply_ok(path.parts, ['foo/bar'], 'right structure')
    is_ok(str(path), 'foo%2Fbar', 'right path')
    is_ok(str(path), 'foo%2Fbar', 'right path')
    is_ok(path.to_abs_str(), '/foo%2Fbar', 'right absolute path')
    is_ok(path.to_route(), '/foo/bar', 'right route')

    # Unchanged path
    path = Pyjo.Path.new('/foob%E4r/-._~!$&\'()*+,;=:@').set(charset='iso-8859-1')
    is_deeply_ok(path.clone().parts, [u"foob\xe4r", '-._~!$&\'()*+,;=:@'], 'right structure')
    ok(path.contains(u"/foob\xe4r"), 'contains path')
    ok(path.contains(u"/foob\xe4r/-._~!$&'()*+,;=:@"), 'contains path')
    ok(not path.contains(u"/foob\xe4r/-._~!\$&'()*+,;=:."), 'does not contain path')
    is_ok(str(path), '/foob%E4r/-._~!$&\'()*+,;=:@', 'right path')
    is_ok(path.to_abs_str(), '/foob%E4r/-._~!$&\'()*+,;=:@', 'right absolute path')
    is_ok(path.to_route(), u"/foob\xe4r/-._~!$&'()*+,;=:@", 'right route')
    is_ok(str(path.clone()), '/foob%E4r/-._~!$&\'()*+,;=:@', 'right path')
    is_ok(path.clone().to_abs_str(), '/foob%E4r/-._~!$&\'()*+,;=:@', 'right absolute path')
    is_ok(path.clone().to_route(), u"/foob\xe4r/-._~!$&'()*+,;=:@", 'right route')

    # Reuse path
    path = Pyjo.Path.new('/foob%E4r').set(charset='iso-8859-1')
    is_ok(str(path), '/foob%E4r', 'right path')
    is_deeply_ok(path.parts, [u"foob\xe4r"], 'right structure')
    path.parse('/foob%E4r')
    is_ok(str(path), '/foob%E4r', 'right path')
    is_deeply_ok(path.parts, [u"foob\xe4r"], 'right structure')

    # Latin-1
    path = Pyjo.Path.new().set(charset='iso-8859-1').parse('/foob%E4r')
    is_deeply_ok(path.parts, [u'foobär'], 'right structure')
    ok(path.leading_slash, 'has leading slash')
    ok(not path.trailing_slash, 'no trailing slash')
    is_ok(str(path), '/foob%E4r', 'right path')
    is_ok(str(path), '/foob%E4r', 'right path')
    is_ok(path.to_abs_str(), '/foob%E4r', 'right absolute path')
    is_ok(path.to_route(), u'/foobär', 'right route')
    is_ok(str(path.clone()), '/foob%E4r', 'right path')

    # No charset
    path = Pyjo.Path.new().set(charset=None).parse(b'/%E4')
    is_deeply_ok(path.parts, [b"\xe4"], 'right structure')
    ok(path.leading_slash, 'has leading slash')
    ok(not path.trailing_slash, 'no trailing slash')
    is_ok(str(path), '/%E4', 'right path')
    is_ok(path.to_route(), b"/\xe4", 'right route')
    is_ok(str(path.clone()), '/%E4', 'right path')

    done_testing()
