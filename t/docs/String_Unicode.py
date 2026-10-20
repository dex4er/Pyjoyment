from Pyjo.Test import *

import contextlib
import io


with subtest('Synopsis'):
    from Pyjo.String.Unicode import Unicode

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        # Manipulate string
        string = Unicode('foo_bar_baz')
        print(string.camelize())
    is_ok(output.getvalue(), 'FooBarBaz\n', 'output')

    # Or import the module, as in Google Python Style Guide

    import Pyjo.String.Unicode

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        # Manipulate string
        string = Pyjo.String.Unicode.new('foo_bar_baz')
        print(string.camelize())

        # Chain methods
        string = Pyjo.String.Unicode.new('foo bar baz').quote()
        string = string.unquote().encode('UTF-8').b64_encode('')
        print(string)

        # Use the alternative constructor
        from Pyjo.String.Unicode import u

        string = u('foobarbaz').b64_encode('').say()
    is_ok(output.getvalue(), 'FooBarBaz\nZm9vIGJhciBiYXo=\nZm9vYmFyYmF6\n', 'output')

with subtest('Description'):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        # Use it as a str
        string = Pyjo.String.Unicode.new('foo')
        print(string.upper())
    is_ok(output.getvalue(), 'FOO\n', 'output')

with subtest('u'):
    string = u('test123')
    is_ok(string, 'test123', 'string')

with subtest('b64_encode'):
    # "Zm9vIGJhciBiYXo="
    is_ok(u('foo bar baz').b64_encode(''), 'Zm9vIGJhciBiYXo=', 'b64_encode')

with subtest('decode'):
    # "♥"
    is_ok(u('%E2%99%A5').url_unescape().decode(), '♥', 'decode')

with subtest('encode'):
    # b"%E2%99%A5"
    is_ok(u('♥').encode().url_escape(), b'%E2%99%A5', 'encode')

with subtest('hmac_sha1_sum'):
    # "7fbdc89263974a89210ea71f171c77d3f8c21471"
    is_ok(u('foo bar baz').hmac_sha1_sum('secr3t'), '7fbdc89263974a89210ea71f171c77d3f8c21471', 'hmac_sha1_sum')

with subtest('html_unescape'):
    # "%3Chtml%3E"
    is_ok(u('&lt;html&gt;').html_unescape().url_escape(), '%3Chtml%3E', 'html_unescape')

with subtest('new'):
    string = Pyjo.String.Unicode.new('test123')
    is_ok(string, 'test123', 'string')

with subtest('split'):
    # "One,Two,Three"
    is_ok(u('one,two,three').split(',').map('camelize').join(','), 'One,Two,Three', 'split')

    # "One,Two,Three,,,"
    is_ok(u('one,two,three,,,').split(',', -1).map('camelize').join(','), 'One,Two,Three,,,', 'split with limit')

with subtest('term_escape'):
    output = io.TextIOWrapper(io.BytesIO(), encoding='UTF-8')
    with contextlib.redirect_stdout(output):
        # Print binary checksum to terminal
        u('foo').sha1_bytes().term_escape().say()
    output.flush()
    is_ok(
        output.buffer.getvalue(),  # pyright: ignore[reportAttributeAccessIssue]
        b'\\x0b\xee\xc7\xb5\xea?\\x0f\xdb\xc9]\\x0d\xd4\\x7f<[\xc2u\xda\\x8a3\n',
        'output',
    )

with subtest('url_escape'):
    # b"%E2%98%83"
    is_ok(u('☃').encode().url_escape(), b'%E2%98%83', 'url_escape')

with subtest('url_unescape'):
    # "&lt;html&gt;"
    is_ok(u('%3Chtml%3E').url_unescape().xml_escape(), '&lt;html&gt;', 'url_unescape')

with subtest('xor_encode'):
    # b"%04%0E%15B%03%1B%10"
    is_ok(u('foo bar').xor_encode('baz').url_escape(), b'%04%0E%15B%03%1B%10', 'xor_encode')

done_testing()
