from Pyjo.Test import *

import contextlib
import io


with subtest('Synopsis'):
    from Pyjo.String.Bytes import Bytes

    output = io.TextIOWrapper(io.BytesIO(), encoding='UTF-8', newline='\n')
    with contextlib.redirect_stdout(output):
        # Manipulate bytes
        data = Bytes(b'foo bar baz')
        print(data.md5_sum())
    output.flush()
    is_ok(
        output.buffer.getvalue(),  # pyright: ignore[reportAttributeAccessIssue]
        b'ab07acbb1e496801937adfa772424bf7\n',
        'output',
    )

    # Or import the module, as in Google Python Style Guide
    import Pyjo.String.Bytes

    output = io.TextIOWrapper(io.BytesIO(), encoding='UTF-8', newline='\n')
    with contextlib.redirect_stdout(output):
        # Manipulate bytes
        data = Pyjo.String.Bytes.new(b'foo bar baz')
        print(data.md5_sum())

        # Chain methods
        data = Pyjo.String.Bytes.new(b'foo bar baz').quote()
        string = data.unquote().b64_encode('')
        print(string)

        # Use the alternative constructor
        from Pyjo.String.Bytes import b

        string = b(b'foobarbaz').b64_encode('').say()
    output.flush()
    is_ok(
        output.buffer.getvalue(),  # pyright: ignore[reportAttributeAccessIssue]
        b'ab07acbb1e496801937adfa772424bf7\nZm9vIGJhciBiYXo=\nZm9vYmFyYmF6\n',
        'output',
    )

with subtest('Description'):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        # Use it as bytes
        data = Pyjo.String.Bytes.new(b'foo')
        print(data.upper())
    is_ok(output.getvalue(), "b'FOO'\n", 'output')

with subtest('b'):
    data = b(b'test123')
    is_ok(data, b'test123', 'data')

with subtest('b64_encode'):
    # "Zm9vIGJhciBiYXo="
    is_ok(b(b'foo bar baz').b64_encode(''), 'Zm9vIGJhciBiYXo=', 'b64_encode')

with subtest('decode'):
    # "♥"
    is_ok(b(b'%E2%99%A5').url_unescape().decode(), '♥', 'decode')

with subtest('hmac_sha1_sum'):
    # "7fbdc89263974a89210ea71f171c77d3f8c21471"
    is_ok(b(b'foo bar baz').hmac_sha1_sum(b'secr3t'), '7fbdc89263974a89210ea71f171c77d3f8c21471', 'hmac_sha1_sum')

with subtest('html_unescape'):
    # b"%3Chtml%3E"
    is_ok(b(b'&lt;html&gt;').html_unescape().url_escape(), b'%3Chtml%3E', 'html_unescape')

with subtest('new'):
    data = Pyjo.String.Bytes.new(b'test123')
    is_ok(data, b'test123', 'data')

with subtest('split'):
    # b"One,Two,Three"
    is_ok(b(b'one,two,three').split(b',').map('camelize').join(',').encode(), b'One,Two,Three', 'split')

with subtest('term_escape'):
    output = io.TextIOWrapper(io.BytesIO(), encoding='UTF-8', newline='\n')
    with contextlib.redirect_stdout(output):
        # Print binary checksum to terminal
        b(b'foo').sha1_bytes().term_escape().say()
    output.flush()
    is_ok(
        output.buffer.getvalue(),  # pyright: ignore[reportAttributeAccessIssue]
        b'\\x0b\xee\xc7\xb5\xea?\\x0f\xdb\xc9]\\x0d\xd4\\x7f<[\xc2u\xda\\x8a3\n',
        'output',
    )

with subtest('url_escape'):
    # b"%E2%98%83"
    is_ok(b('☃').url_escape(), b'%E2%98%83', 'url_escape')

with subtest('url_unescape'):
    # b"&lt;html&gt;"
    is_ok(b(b'%3Chtml%3E').url_unescape().xml_escape(), b'&lt;html&gt;', 'url_unescape')

with subtest('xor_encode'):
    # b"%04%0E%15B%03%1B%10"
    is_ok(b(b'foo bar').xor_encode(b'baz').url_escape(), b'%04%0E%15B%03%1B%10', 'xor_encode')

done_testing()
