from Pyjo.Test import *


# Pyjo.Util is brought to Mojolicious 9.49 one function at a time, so only the
# documented code of those functions is here

with subtest('Synopsis'):
    from Pyjo.Util import b64_encode, url_escape, url_unescape

    string = 'test=23'
    escaped = url_escape(string)
    is_ok(url_unescape(escaped), 'test=23', 'url_unescape')
    is_ok(b64_encode(escaped.encode(), ''), 'dGVzdCUzRDIz', 'b64_encode')

with subtest('camelize'):
    from Pyjo.Util import camelize

    # "FooBar"
    is_ok(camelize('foo_bar'), 'FooBar', 'foo_bar')

    # "FooBar::Baz"
    is_ok(camelize('foo_bar-baz'), 'FooBar::Baz', 'foo_bar-baz')

    # "FooBar::Baz"
    is_ok(camelize('FooBar::Baz'), 'FooBar::Baz', 'FooBar::Baz')

with subtest('decamelize'):
    from Pyjo.Util import decamelize

    # "foo_bar"
    is_ok(decamelize('FooBar'), 'foo_bar', 'FooBar')

    # "foo_bar-baz"
    is_ok(decamelize('FooBar::Baz'), 'foo_bar-baz', 'FooBar::Baz')

    # "foo_bar-baz"
    is_ok(decamelize('foo_bar-baz'), 'foo_bar-baz', 'foo_bar-baz')

with subtest('hmac_sha1_sum'):
    from Pyjo.Util import hmac_sha1_sum

    # "11cedfd5ec11adc0ec234466d8a0f2a83736aa68"
    is_ok(hmac_sha1_sum(b'foo', b'passw0rd'), '11cedfd5ec11adc0ec234466d8a0f2a83736aa68', 'foo')

with subtest('html_attr_unescape'):
    from Pyjo.Util import html_attr_unescape

    # "foo=bar&ltest=baz"
    is_ok(html_attr_unescape('foo=bar&ltest=baz'), 'foo=bar&ltest=baz', 'not an entity in an attribute')

    # "foo=bar<est=baz"
    is_ok(html_attr_unescape('foo=bar&lt;est=baz'), 'foo=bar<est=baz', 'an entity')

with subtest('html_unescape'):
    from Pyjo.Util import html_unescape

    # "<div>"
    is_ok(html_unescape('&lt;div&gt;'), '<div>', '&lt;div&gt;')

with subtest('humanize_bytes'):
    from Pyjo.Util import humanize_bytes

    # "1B"
    is_ok(humanize_bytes(1), '1B', 'one Byte')

    # "7.5GiB"
    is_ok(humanize_bytes(8007188480), '7.5GiB', 'smaller GiB')

    # "13GiB"
    is_ok(humanize_bytes(13443399680), '13GiB', 'two digits GiB')

    # "-685MiB"
    is_ok(humanize_bytes(-717946880), '-685MiB', 'large negative MiB')

with subtest('md5_sum'):
    from Pyjo.Util import md5_sum

    # "acbd18db4cc2f85cedef654fccc4a4d8"
    is_ok(md5_sum(b'foo'), 'acbd18db4cc2f85cedef654fccc4a4d8', 'foo')

with subtest('network_contains'):
    from Pyjo.Util import network_contains

    # True
    ok(network_contains('10.0.0.0/8', '10.10.10.10'), 'network')
    ok(network_contains('10.10.10.10', '10.10.10.10'), 'single address')
    ok(network_contains('fc00::/7', 'fc00::c0:ff:ee'), 'IPv6 network')

    # False
    ok(not network_contains('10.0.0.0/29', '10.10.10.10'), 'outside the network')
    ok(not network_contains('10.10.10.12', '10.10.10.10'), 'other address')
    ok(not network_contains('fc00::/7', '::1'), 'outside the IPv6 network')

with subtest('punycode_decode'):
    from Pyjo.Util import punycode_decode

    # "bücher"
    is_ok(punycode_decode('bcher-kva'), 'bücher', 'bcher-kva')

with subtest('punycode_encode'):
    from Pyjo.Util import punycode_encode

    # "bcher-kva"
    is_ok(punycode_encode('bücher'), 'bcher-kva', 'bücher')

with subtest('sha1_sum'):
    from Pyjo.Util import sha1_sum

    # "0beec7b5ea3f0fdbc95d0dd47f3c5bc275da8a33"
    is_ok(sha1_sum(b'foo'), '0beec7b5ea3f0fdbc95d0dd47f3c5bc275da8a33', 'foo')

with subtest('slugify'):
    from Pyjo.Util import slugify

    # "joel-is-a-slug"
    is_ok(slugify('Joel is a slug'), 'joel-is-a-slug', 'Joel is a slug')

    # "this-is-my-resume"
    is_ok(slugify('This is: my - résumé! ☃ '), 'this-is-my-resume', 'ASCII')

    # "this-is-my-résumé"
    is_ok(slugify('This is: my - résumé! ☃ ', True), 'this-is-my-résumé', 'unicode')

with subtest('term_escape'):
    from Pyjo.Util import term_escape

    # "foo\\x09bar\\x0d\n"
    is_ok(term_escape('foo\tbar\r\n'), 'foo\\x09bar\\x0d\n', 'foo\\tbar\\r\\n')

with subtest('trim'):
    from Pyjo.Util import trim

    # "foo bar"
    is_ok(trim('  foo bar  '), 'foo bar', '  foo bar  ')

with subtest('unindent'):
    from Pyjo.Util import unindent

    # "foo\nbar\nbaz\n"
    is_ok(unindent('  foo\n  bar\n  baz\n'), 'foo\nbar\nbaz\n', 'unindent')

with subtest('url_escape'):
    from Pyjo.Util import url_escape

    # "foo%3Bbar"
    is_ok(url_escape('foo;bar'), 'foo%3Bbar', 'foo;bar')

with subtest('url_unescape'):
    from Pyjo.Util import url_unescape

    # "foo;bar"
    is_ok(url_unescape('foo%3Bbar'), 'foo;bar', 'foo%3Bbar')

with subtest('xml_escape'):
    from Pyjo.Util import xml_escape

    # "&lt;div&gt;"
    is_ok(xml_escape('<div>'), '&lt;div&gt;', '<div>')

    # "<div>"
    from Pyjo.String.HTML import html

    is_ok(xml_escape(html('<div>')), '<div>', "html('<div>')")

done_testing()
