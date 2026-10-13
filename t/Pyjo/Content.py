if __name__ == '__main__':
    from Pyjo.Test import *  # noqa

    import Pyjo.Asset.Memory
    import Pyjo.Content.MultiPart
    import Pyjo.Content.Single

    # Single
    content = Pyjo.Content.Single.new()
    content.asset.add_chunk(b'foo')
    ok(not content.body_contains(b'a'), 'content does not contain "a"')
    ok(content.body_contains(b'f'), 'content contains "f"')
    ok(content.body_contains(b'o'), 'content contains "o"')
    ok(content.body_contains(b'foo'), 'content contains "foo"')
    content = Pyjo.Content.Single.new(asset=Pyjo.Asset.Memory.new().add_chunk(b'bar'))
    ok(not content.body_contains(b'foo'), 'content does not contain "foo"')
    ok(content.body_contains(b'bar'), 'content contains "bar"')
    content = Pyjo.Content.Single.new(asset=Pyjo.Asset.Memory.new().add_chunk(b'foo'))
    ok(not content.body_contains(b'bar'), 'content does not contain "bar"')
    ok(content.body_contains(b'foo'), 'content contains "foo"')

    # Multipart
    content = Pyjo.Content.MultiPart.new(parts=[content])
    ok(not content.body_contains(b'a'), 'content does not contain "a"')
    ok(content.body_contains(b'f'), 'content contains "f"')
    ok(content.body_contains(b'o'), 'content contains "o"')
    ok(content.body_contains(b'foo'), 'content contains "foo"')
    content = Pyjo.Content.MultiPart.new(parts=[content])
    ok(content.body_contains(b'foo'), 'content contains "foo"')
    content.parts.append(Pyjo.Content.Single.new())
    content.parts[1].asset.add_chunk(b'.*?foo+')
    content.parts[1].headers.header('X-Bender', 'bar+')
    ok(not content.body_contains(b'z'), 'content does not contain "z"')
    ok(content.body_contains(b'f'), 'content contains "f"')
    ok(content.body_contains(b'o'), 'content contains "o"')
    ok(content.body_contains(b'foo'), 'content contains "foo"')
    ok(content.body_contains(b'bar+'), 'content contains "bar+"')
    ok(content.body_contains(b'.'), 'content contains "."')
    ok(content.body_contains(b'.*?foo+'), 'content contains ".*?foo+"')
    ok(not content.headers.content_type, 'no "Content-Type" header')
    boundary = content.build_boundary()
    ok(boundary, 'boundary has been generated')
    is_ok(boundary, content.boundary, 'same boundary')
    is_ok(content.headers.content_type, f'multipart/mixed; boundary={boundary}', 'right "Content-Type" header')

    # Dynamic content
    content = Pyjo.Content.Single.new()
    content.write(b'Hello ').write(b'World!')
    ok(content.is_dynamic, 'dynamic content')
    ok(not content.is_chunked, 'no chunked content')
    content.write(b'')
    ok(content.is_dynamic, 'dynamic content')
    is_ok(content.build_body(), b'Hello World!', 'right content')

    # Chunked content
    content = Pyjo.Content.Single.new()
    content.write_chunk(b'Hello ').write_chunk(b'World!')
    ok(content.is_dynamic, 'dynamic content')
    ok(content.is_chunked, 'chunked content')
    content.write_chunk(b'')
    ok(content.is_dynamic, 'dynamic content')
    is_ok(content.build_body(), b'6\x0d\x0aHello \x0d\x0a6\x0d\x0aWorld!\x0d\x0a0\x0d\x0a\x0d\x0a', 'right content')

    # Multipart boundary detection
    content = Pyjo.Content.MultiPart.new()
    none_ok(content.boundary, 'no boundary')
    content.headers.content_type = 'multipart/form-data; boundary  =  "azAZ09\'(),.:?-_+/"'
    is_ok(content.boundary, "azAZ09'(),.:?-_+/", 'right boundary')
    is_ok(content.boundary, content.build_boundary(), 'same boundary')
    content.headers.content_type = 'multipart/form-data'
    none_ok(content.boundary, 'no boundary')
    content.headers.content_type = 'multipart/form-data; boundary="foo bar baz"'
    is_ok(content.boundary, 'foo bar baz', 'right boundary')
    is_ok(content.boundary, content.build_boundary(), 'same boundary')
    content.headers.content_type = 'MultiPart/Form-Data; BounDaRy="foo 123"'
    is_ok(content.boundary, 'foo 123', 'right boundary')
    is_ok(content.boundary, content.build_boundary(), 'same boundary')

    # Charset detection
    content = Pyjo.Content.Single.new()
    none_ok(content.charset, 'no charset')
    content.headers.content_type = 'text/plain; charset=UTF-8'
    is_ok(content.charset, 'UTF-8', 'right charset')
    content.headers.content_type = 'text/plain; charset="UTF-8"'
    is_ok(content.charset, 'UTF-8', 'right charset')
    content.headers.content_type = 'text/plain; charset  =  UTF-8'
    is_ok(content.charset, 'UTF-8', 'right charset')
    content.headers.content_type = 'text/plain; charset  =  "UTF-8"'
    is_ok(content.charset, 'UTF-8', 'right charset')

    # Partial content with 128-bit content length
    content = Pyjo.Content.Single.new()
    content.parse(b'Content-Length: 18446744073709551616\x0d\x0a\x0d\x0aHello World!')
    is_ok(content.asset.size, 12, 'right size')

    # Abstract methods
    throws_ok(
        lambda: Pyjo.Content.new().body_contains(), 'Method "body_contains" not implemented by subclass', 'right error'
    )
    throws_ok(lambda: Pyjo.Content.new().body_size(), 'Method "body_size" not implemented by subclass', 'right error')
    throws_ok(
        lambda: Pyjo.Content.new().get_body_chunk(),
        'Method "get_body_chunk" not implemented by subclass',
        'right error',
    )

    done_testing()
