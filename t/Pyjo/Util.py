from Pyjo.String.Unicode import u
from Pyjo.Test import *
from Pyjo.Util import (
    b64_decode,
    b64_encode,
    camelize,
    decamelize,
    decode,
    encode,
    gunzip,
    gzip,
    header_params,
    hmac_sha1_sum,
    html_attr_unescape,
    html_unescape,
    humanize_bytes,
    md5_bytes,
    md5_sum,
    network_contains,
    punycode_decode,
    punycode_encode,
    quote,
    secure_compare,
    sha1_bytes,
    sha1_sum,
    slugify,
    term_escape,
    trim,
    unindent,
    unquote,
    url_escape,
    url_unescape,
    xml_escape,
    xor_encode,
)

import re


# Pyjo.Util is brought to Mojolicious 9.49 one function at a time, so only the
# subtests of t/mojo/util.t for those functions are here

with subtest('camelize'):
    is_ok(camelize('foo_bar_baz'), 'FooBarBaz', 'right camelized result')
    is_ok(camelize('FooBarBaz'), 'FooBarBaz', 'right camelized result')
    is_ok(camelize('foo_b_b'), 'FooBB', 'right camelized result')
    is_ok(camelize('foo-b_b'), 'Foo::BB', 'right camelized result')
    is_ok(camelize('FooBar'), 'FooBar', 'already camelized')
    is_ok(camelize('Foo::Bar'), 'Foo::Bar', 'already camelized')

with subtest('decamelize'):
    is_ok(decamelize('FooBarBaz'), 'foo_bar_baz', 'right decamelized result')
    is_ok(decamelize('foo_bar_baz'), 'foo_bar_baz', 'right decamelized result')
    is_ok(decamelize('FooBB'), 'foo_b_b', 'right decamelized result')
    is_ok(decamelize('Foo::BB'), 'foo-b_b', 'right decamelized result')

with subtest('header_params'):
    is_deeply_ok(header_params(''), ({}, ''), 'right result')
    is_deeply_ok(header_params('foo=b=a=r'), ({'foo': 'b=a=r'}, ''), 'right result')
    is_deeply_ok(header_params('a=b; c, d=e'), ({'a': 'b'}, ', d=e'), 'right result')
    is_deeply_ok(header_params('a=b; a=c'), ({'a': 'b'}, ''), 'right result')
    is_deeply_ok(header_params('a=b; a="c"'), ({'a': 'b'}, ''), 'right result')
    is_deeply_ok(header_params('a=b; b="c=d"'), ({'a': 'b', 'b': 'c=d'}, ''), 'right result')
    is_deeply_ok(header_params('a=b, c=d'), ({'a': 'b'}, ', c=d'), 'right result')
    is_deeply_ok(
        header_params('rel="x"; t*=UTF-8\'de\'a%20b'), ({'rel': 'x', 't*': "UTF-8'de'a%20b"}, ''), 'right result'
    )

with subtest('unindent'):
    is_ok(unindent(' test\n  123\n 456\n'), 'test\n 123\n456\n', 'right unindented result')
    is_ok(unindent('\ttest\n\t\t123\n\t456\n'), 'test\n\t123\n456\n', 'right unindented result')
    is_ok(unindent('\t \ttest\n\t \t\t123\n\t \t456\n'), 'test\n\t123\n456\n', 'right unindented result')
    is_ok(unindent('\n\n\n test\n  123\n 456\n'), '\n\n\ntest\n 123\n456\n', 'right unindented result')
    is_ok(unindent('   test\n    123\n   456\n'), 'test\n 123\n456\n', 'right unindented result')
    is_ok(unindent('    test\n  123\n   456\n'), '  test\n123\n 456\n', 'right unindented result')
    is_ok(unindent('test\n123\n'), 'test\n123\n', 'right unindented result')
    is_ok(unindent(' test\n\n 123\n'), 'test\n\n123\n', 'right unindented result')
    is_ok(unindent('  test'), 'test', 'right unindented result')
    is_ok(unindent(' te st\r\n\r\n  1 2 3\r\n 456\r\n'), 'te st\r\n\r\n 1 2 3\r\n456\r\n', 'right unindented result')

with subtest('b64_encode'):
    is_ok(b64_encode(b'foobar$%^&3217'), 'Zm9vYmFyJCVeJjMyMTc=\n', 'right Base64 encoded result')

with subtest('b64_decode'):
    is_ok(b64_decode('Zm9vYmFyJCVeJjMyMTc=\n'), b'foobar$%^&3217', 'right Base64 decoded result')

with subtest('b64_encode (UTF-8)'):
    is_ok(
        b64_encode(encode('UTF-8', 'foo\xdfĀbar%23☺')),
        'Zm9vw5/EgGJhciUyM+KYug==\n',
        'right Base64 encoded result',
    )

with subtest('b64_decode (UTF-8)'):
    is_ok(
        decode('UTF-8', b64_decode('Zm9vw5/EgGJhciUyM+KYug==\n')),
        'foo\xdfĀbar%23☺',
        'right Base64 decoded result',
    )

with subtest('b64_encode (custom line ending)'):
    is_ok(b64_encode(b'foobar$%^&3217', ''), 'Zm9vYmFyJCVeJjMyMTc=', 'right Base64 encoded result')

with subtest('decode (invalid UTF-8)'):
    is_ok(decode('UTF-8', 'က'), None, 'decoding invalid UTF-8 worked')

with subtest('decode (invalid encoding)'):
    is_ok(decode('does_not_exist', ''), None, 'decoding with invalid encoding worked')

with subtest('encode (invalid encoding)'):
    throws_ok(lambda: encode('does_not_exist', ''), re.compile(r"Unknown encoding 'does_not_exist'"), 'right error')

with subtest('url_escape'):
    is_ok(url_escape('business;23'), 'business%3B23', 'right URL escaped result')

with subtest('url_escape (custom pattern)'):
    is_ok(url_escape('&business;23', 's&'), '%26bu%73ine%73%73;23', 'right URL escaped result')

with subtest('url_escape (nothing to escape)'):
    is_ok(url_escape('foobar123-._~'), 'foobar123-._~', 'no changes')

with subtest('url_unescape'):
    is_ok(url_unescape('business%3B23'), 'business;23', 'right URL unescaped result')

with subtest('UTF-8 url_escape'):
    is_ok(
        url_escape(encode('UTF-8', 'foo\xdfĀbar☺')),
        b'foo%C3%9F%C4%80bar%E2%98%BA',
        'right URL escaped result',
    )

with subtest('UTF-8 url_unescape'):
    is_ok(
        decode('UTF-8', url_unescape('foo%C3%9F%C4%80bar%E2%98%BA')),
        'foo\xdfĀbar☺',
        'right URL unescaped result',
    )

with subtest('html_unescape'):
    is_ok(html_unescape('&#x3c;foo&#x3E;bar&lt;baz&gt;&#x0026;&#34;'), '<foo>bar<baz>&"', 'right HTML unescaped result')
    is_ok(html_unescape('foo&lt;baz&gt;&#x26;&#34;&OElig;&Foo;'), 'foo<baz>&"Œ&Foo;', 'right HTML unescaped result')

with subtest('html_unescape (special entities)'):
    is_ok(
        html_unescape('foo &#x2603; &CounterClockwiseContourIntegral; bar &sup1baz'),
        'foo ☃ ∳ bar ¹baz',
        'right HTML unescaped result',
    )

with subtest('html_unescape (multi-character entity)'):
    is_ok(html_unescape('&acE;'), '∾̳', 'right HTML unescaped result')

with subtest('html_unescape (apos)'):
    is_ok(html_unescape('foobar&apos;&lt;baz&gt;&#x26;&#34;'), 'foobar\'<baz>&"', 'right HTML unescaped result')

with subtest('html_unescape (nothing to unescape)'):
    is_ok(html_unescape('foobar'), 'foobar', 'no changes')

with subtest('html_unescape (relaxed)'):
    is_ok(html_unescape('&0&Ltf&amp&0oo&nbspba;&ltr'), '&0&Ltf&&0oo\xa0ba;<r', 'right HTML unescaped result')

with subtest('html_attr_unescape'):
    is_ok(html_attr_unescape('/?foo&lt=bar'), '/?foo&lt=bar', 'right HTML unescaped result')
    is_ok(html_attr_unescape('/?f&ltoo=bar'), '/?f&ltoo=bar', 'right HTML unescaped result')
    is_ok(html_attr_unescape('/?f&lt-oo=bar'), '/?f<-oo=bar', 'right HTML unescaped result')
    is_ok(html_attr_unescape('/?foo=&lt'), '/?foo=<', 'right HTML unescaped result')
    is_ok(html_attr_unescape('/?f&lt;oo=bar'), '/?f<oo=bar', 'right HTML unescaped result')

with subtest('url_unescape (bengal numbers with nothing to unescape)'):
    is_ok(html_unescape('&#০৩৯;&#x০৩৯;'), '&#০৩৯;&#x০৩৯;', 'no changes')

with subtest('xml_escape'):
    is_ok(
        xml_escape('la<f>\nbar"baz"\'yada\n\'&lt;la'),
        'la&lt;f&gt;\nbar&quot;baz&quot;&#39;yada\n&#39;&amp;lt;la',
        'right XML escaped result',
    )
    is_ok(xml_escape('привет<foo>'), 'привет&lt;foo&gt;', 'right XML escaped result')

with subtest('xml_escape (nothing to escape)'):
    is_ok(xml_escape('привет'), 'привет', 'no changes')

with subtest('xml_escape (XSS)'):
    is_ok(xml_escape('<p>'), '&lt;p&gt;', 'right XSS escaped result')
    is_ok(xml_escape(u('<p>')), '<p>', 'right XSS escaped result')

with subtest('punycode_encode'):
    is_ok(punycode_encode('bücher'), 'bcher-kva', 'right punycode encoded result')

with subtest('punycode_decode'):
    is_ok(punycode_decode('bcher-kva'), 'bücher', 'right punycode decoded result')

with subtest('punycode_decode/punycode_encode roundtrip'):
    is_ok(punycode_decode(punycode_encode('☃⭐️ ')), '☃⭐️ ', 'right punycode roundtrip result')
    is_ok(punycode_decode(punycode_encode('🐳')), '🐳', 'right punycode roundtrip result')

with subtest('RFC 3492'):
    tests = [
        '(A) Arabic (Egyptian):',
        'ليهمابتكلموشعربي؟',
        'egbpdaj6bu4bxfgehfvwxn',
        '(B) Chinese (simplified):',
        '他们为什么不说中文',
        'ihqwcrb4cv8a8dqg056pqjye',
        '(C) Chinese (traditional):',
        '他們爲什麽不說中文',
        'ihqwctvzc91f659drss3x8bo0yb',
        '(D) Czech: Pro<ccaron>prost<ecaron>nemluv<iacute><ccaron>esky',
        'Pročprostěnemluvíčesky',
        'Proprostnemluvesky-uyb24dma41a',
        '(E) Hebrew:',
        'למההםפשוטלאמדבריםעברית',
        '4dbcagdahymbxekheh6e0a7fei0b',
        '(F) Hindi (Devanagari):',
        'यहलोगहिन्दीक्योंनहींबोलसकतेहैं',
        'i1baa7eci9glrd9b2ae1bj0hfcgg6iyaf8o0a1dig0cd',
        '(G) Japanese (kanji and hiragana):',
        'なぜみんな日本語を話してくれないのか',
        'n8jok5ay5dzabd5bym9f0cm5685rrjetr6pdxa',
        '(H) Korean (Hangul syllables):',
        '세계의모든사람들이한국어를이해한다면얼마나좋을까',
        '989aomsvi5e83db1d2a355cv1e0vak1dwrv93d5xbh15a0dt30a5jpsd879ccm6fea98c',
        '(I) Russian (Cyrillic):',
        'почемужеонинеговорятпорусски',
        'b1abfaaepdrnnbgefbadotcwatmq2g4l',
        '(J) Spanish: Porqu<eacute>nopuedensimplementehablarenEspa<ntilde>ol',
        'PorquénopuedensimplementehablarenEspañol',
        'PorqunopuedensimplementehablarenEspaol-fmd56a',
        '(K) Vietnamese: T<adotbelow>isaoh<odotbelow>kh<ocirc>ngth'
        '<ecirchookabove>ch<ihookabove>n<oacute>iti<ecircacute>ngVi'
        '<ecircdotbelow>t',
        'TạisaohọkhôngthểchỉnóitiếngViệt',
        'TisaohkhngthchnitingVit-kjcr8268qyxafd2f1b9g',
        '(L) 3<nen>B<gumi><kinpachi><sensei>',
        '3年B組金八先生',
        '3B-ww4c5e180e575a65lsy2b',
        '(M) <amuro><namie>-with-SUPER-MONKEYS',
        '安室奈美恵-with-SUPER-MONKEYS',
        '-with-SUPER-MONKEYS-pc58ag80a8qai00g7n9n',
        '(N) Hello-Another-Way-<sorezore><no><basho>',
        'Hello-Another-Way-それぞれの場所',
        'Hello-Another-Way--fc4qua05auwb3674vfr0b',
        '(O) <hitotsu><yane><no><shita>2',
        'ひとつ屋根の下2',
        '2-u9tlzr9756bt3uc0v',
        '(P) Maji<de>Koi<suru>5<byou><mae>',
        'MajiでKoiする5秒前',
        'MajiKoi5-783gue6qz075azm5e',
        '(Q) <pafii>de<runba>',
        'パフィーdeルンバ',
        'de-jg4avhby1noc0d',
        '(R) <sono><supiido><de>',
        'そのスピードで',
        'd9juau41awczczp',
        '(S) -> $1.00 <-',
        '-> $1.00 <-',
        '-> $1.00 <--',
    ]

    for i in range(0, len(tests), 3):
        d, o, p = tests[i], tests[i + 1], tests[i + 2]
        is_ok(punycode_encode(o), p, f'punycode_encode {d}')
        is_ok(punycode_decode(p), o, f'punycode_decode {d}')

with subtest('quote'):
    is_ok(quote('foo; 23 "bar'), '"foo; 23 \\"bar"', 'right quoted result')
    is_ok(quote('"foo; 23 "bar"'), '"\\"foo; 23 \\"bar\\""', 'right quoted result')

with subtest('unquote'):
    is_ok(unquote('"foo 23 \\"bar"'), 'foo 23 "bar', 'right unquoted result')
    is_ok(unquote('"\\"foo 23 \\"bar\\""'), '"foo 23 "bar"', 'right unquoted result')

with subtest('trim'):
    is_ok(trim(' la la  la '), 'la la  la', 'right trimmed result')
    is_ok(trim(' \n la la la \n '), 'la la la', 'right trimmed result')
    is_ok(trim('\n la\nla la \n'), 'la\nla la', 'right trimmed result')
    is_ok(trim(' \nla \n  \t\nla\nla\n '), 'la \n  \t\nla\nla', 'right trimmed result')

with subtest('md5_bytes'):
    is_ok(
        md5_bytes(encode('UTF-8', 'foo bar baz ♥')).hex(),
        'a740aeb6e066f158cbf19fd92e890d2d',
        'right binary md5 checksum',
    )

with subtest('md5_sum'):
    is_ok(md5_sum(b'foo bar baz'), 'ab07acbb1e496801937adfa772424bf7', 'right md5 checksum')

with subtest('sha1_bytes'):
    is_ok(sha1_bytes(b'foo bar baz').hex(), 'c7567e8b39e2428e38bf9c9226ac68de4c67dc39', 'right binary sha1 checksum')

with subtest('sha1_sum'):
    is_ok(sha1_sum(b'foo bar baz'), 'c7567e8b39e2428e38bf9c9226ac68de4c67dc39', 'right sha1 checksum')

with subtest('hmac_sha1_sum'):
    is_ok(
        hmac_sha1_sum(b'Hi there', b'abc1234567890'),
        '5344f37e1948dd3ffb07243a4d9201a227abd6e1',
        'right hmac sha1 checksum',
    )

with subtest('secure_compare'):
    ok(secure_compare('hello', 'hello'), 'values are equal')
    ok(not secure_compare('hell', 'hello'), 'values are not equal')
    ok(not secure_compare('hallo', 'hello'), 'values are not equal')
    ok(secure_compare('0', '0'), 'values are equal')
    ok(secure_compare('1', '1'), 'values are equal')
    ok(not secure_compare('1', '0'), 'values are not equal')
    ok(not secure_compare('0', '1'), 'values are not equal')
    ok(secure_compare('00', '00'), 'values are equal')
    ok(secure_compare('11', '11'), 'values are equal')
    ok(not secure_compare('11', '00'), 'values are not equal')
    ok(not secure_compare('00', '11'), 'values are not equal')
    ok(secure_compare('♥', '♥'), 'values are equal')
    ok(secure_compare('0♥', '0♥'), 'values are equal')
    ok(secure_compare('♥1', '♥1'), 'values are equal')
    ok(not secure_compare('♥', '♥0'), 'values are not equal')
    ok(not secure_compare('0♥', '♥'), 'values are not equal')
    ok(not secure_compare('0♥1', '1♥0'), 'values are not equal')
    ok(not secure_compare('', '♥'), 'values are not equal')
    ok(not secure_compare('♥', ''), 'values are not equal')

with subtest('xor_encode'):
    is_ok(xor_encode(b'hello', b'foo'), b'\x0e\x0a\x03\x0a\x00', 'right result')
    is_ok(xor_encode(b'\x0e\x0a\x03\x0a\x00', b'foo'), b'hello', 'right result')
    is_ok(xor_encode(b'hello world', b'x'), b'\x10\x1d\x14\x14\x17\x58\x0f\x17\x0a\x14\x1c', 'right result')
    is_ok(xor_encode(b'\x10\x1d\x14\x14\x17\x58\x0f\x17\x0a\x14\x1c', b'x'), b'hello world', 'right result')
    is_ok(xor_encode(b'hello', b'123456789'), b'\x59\x57\x5f\x58\x5a', 'right result')
    is_ok(xor_encode(b'\x59\x57\x5f\x58\x5a', b'123456789'), b'hello', 'right result')

with subtest('network_contains'):
    ok(not network_contains('10.0.0.0/8', ''), 'empty address')
    ok(not network_contains('', '10.10.10.10'), 'empty network')
    ok(not network_contains('foo', '10.10.10.10'), 'invalid v4 network')
    ok(not network_contains('10.10.10.10', 'foo'), 'invalid v4 address')
    ok(not network_contains('foo:', '::'), 'invalid v6 network')
    ok(not network_contains('::', 'foo:'), 'invalid v6 address')
    ok(not network_contains('::/96', '192.168.0.1'), 'v6 network, v4 address')
    ok(not network_contains('10.10.10.10/32', '::'), 'v4 network, v6 address')

    ok(network_contains('192.168.0.1/33', '192.168.0.1'), 'oversize v4 mask')
    ok(network_contains('::/130', '::'), 'oversize v6 mask')

    ok(network_contains('0.0.0.0/0', '0.0.0.0'), 'v4 network contains addresss')
    ok(network_contains('0.0.0.0/0', '255.255.255.255'), 'v4 network contains addresss')
    ok(network_contains('192.168.0.0/24', '192.168.0.1'), 'v4 network contains addresss')
    ok(network_contains('10.10.10.8/30', '10.10.10.11'), 'v4 network contains addresss')
    ok(network_contains('10.10.10.8/30', '10.10.10.8'), 'v4 network contains addresss')
    ok(network_contains('10.10.10.8/31', '10.10.10.9'), 'v4 network contains addresss')
    ok(network_contains('10.0.0.0/8', '10.255.255.255'), 'v4 network contains addresss')
    ok(network_contains('255.255.255.255/32', '255.255.255.255'), 'v4 network contains addresss')
    ok(network_contains('10.10.10.8/29', '10.10.10.10'), 'v4 network contains addresss')
    ok(network_contains('127.0.0.1', '127.0.0.1'), 'v4 network contains addresss')

    ok(not network_contains('0.0.0.0/32', '0.0.0.1'), 'v4 network does not contain address')
    ok(not network_contains('192.168.1.0/24', '192.168.0.1'), 'v4 network does not contain address')
    ok(not network_contains('10.10.0.8/29', '10.10.10.8'), 'v4 network does not contain address')
    ok(not network_contains('10.10.10.8/29', '10.10.10.7'), 'v4 network does not contain address')
    ok(not network_contains('10.10.10.8/29', '10.10.10.16'), 'v4 network does not contain address')
    ok(not network_contains('10.0.0.0/9', '10.255.255.255'), 'v4 network does not contain address')
    ok(not network_contains('10.10.10.8/29', '10.10.10.19'), 'v4 network does not contain address')
    ok(not network_contains('127.0.0.1', '127.0.0.2'), 'v4 network does not contain address')
    ok(not network_contains('10.0.0.1/8', '10.0.0.2'), 'v4 network does not contain address')

    ok(network_contains('::/128', '::'), 'v6 network contains addresss')
    ok(network_contains('::/0', '::'), 'v6 network contains addresss')
    ok(network_contains('::1', '::1'), 'v6 network contains addresss')
    ok(network_contains('::/0', 'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff'), 'v6 network contains addresss')
    ok(network_contains('1:2:3:4:5:6:0::/96', '1:2:3:4:5:6:8000:8'), 'v6 network contains addresss')
    ok(network_contains('1:2:3:4:5:6:8000::/112', '1:2:3:4:5:6:8000:F1'), 'v6 network contains addresss')
    ok(network_contains('1:2:3:4:5:6:8000:20/123', '1:2:3:4:5:6:8000:3F'), 'v6 network contains addresss')
    ok(network_contains('ff:ff:ff:ff:ff:ff:8000::/127', 'ff:ff:ff:ff:ff:ff:8000:0'), 'v6 network contains addresss')
    ok(network_contains('ff:ff:ff:ff:ff:ff:8000::/127', 'ff:ff:ff:ff:ff:ff:8000:1'), 'v6 network contains addresss')
    ok(network_contains('::1', '::1'), 'v6 network contains addresss')
    ok(network_contains('::1/128', '::1'), 'v6 network contains addresss')
    ok(network_contains('a0:a0:a0:a0::/64', 'a0:a0:a0:a0:1::1'), 'v6 network contains addresss')
    ok(network_contains('a0::/16', 'a0:b0:a0:a0:1::1'), 'v6 network contains addresss')
    ok(network_contains('a000::/8', 'a0ff:dd0:1234:a0:1::1'), 'v6 network contains addresss')
    ok(network_contains('::ffff:0:0/96', '::ffff:10.10.10.10'), 'v6 network contains addresss')
    ok(network_contains('::ffff:127.0.0.0/120', '::ffff:127.0.0.255'), 'v6 network contains addresss')
    ok(network_contains('::ffff:10.10.10.8/127', '::ffff:10.10.10.9'), 'v6 network contains addresss')

    ok(not network_contains('::1/0', '::'), 'v6 network does not contain address')
    ok(not network_contains('::1', '::2'), 'v6 network does not contain address')
    ok(not network_contains('1::/0', 'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff'), 'v6 network does not contain address')
    ok(not network_contains('1:2:3:4:5:6:0::/96', '1:2:3:4:5:7:8000:8'), 'v6 network does not contain address')
    ok(not network_contains('1:2:3:4:5:6:8000::/112', '1:2:3:4:5:6:8001:F1'), 'v6 network does not contain address')
    ok(not network_contains('1:2:3:4:5:6:8000:20/123', '1:2:3:4:5:6:8000:40'), 'v6 network does not contain address')
    ok(
        not network_contains('ff:ff:ff:ff:ff:ff:8000::/127', 'ff:ff:ff:ff:ff:ff:8000:4'),
        'v6 network does not contain address',
    )
    ok(
        not network_contains('ff:ff:ff:ff:ff:ff:8000::/127', 'ff:ff:ff:ff:ff:ff:7FFF:0'),
        'v6 network does not contain address',
    )
    ok(not network_contains('::1', '1::1'), 'v6 network does not contain address')
    ok(not network_contains('::1/128', '::11'), 'v6 network does not contain address')
    ok(not network_contains('a0:a0:a0:a0::/64', 'a0:a0:a0:a1:1::1'), 'v6 network does not contain address')
    ok(not network_contains('a0::/16', 'a1:b0:a0:a0:1::1'), 'v6 network does not contain address')
    ok(not network_contains('a000::/8', 'b0ff:dd0:1234:a0:1::1'), 'v6 network does not contain address')
    ok(not network_contains('::ffff:0:0/96', '::fffe:0a0a:0a0a'), 'v6 network does not contain address')
    ok(not network_contains('::ffff:127.0.0.0/120', '::ffff:127.0.1.255'), 'v6 network does not contain address')
    ok(not network_contains('::ffff:10.10.10.8/127', '::ffff:10.10.10.12'), 'v6 network does not contain address')

with subtest('term_escape'):
    is_ok(term_escape('Accept: */*\x0d\x0a'), 'Accept: */*\\x0d\x0a', 'right result')
    is_ok(term_escape('\t\b\r\n\f'), '\\x09\\x08\\x0d\n\\x0c', 'right result')
    is_ok(term_escape('\x00\x09\x0b\x1f\x7f\x80\x9f'), r'\x00\x09\x0b\x1f\x7f\x80\x9f', 'right result')

with subtest('slugify'):
    is_ok(slugify('a & b'), 'a-b', 'right result')
    is_ok(slugify('a &amp; b'), 'a-amp-b', 'right result')
    is_ok(slugify(123), '123', 'right result')
    is_ok(
        slugify(' Jack & Jill like numbers 1,2,3 and 4 and silly characters ?%.$!/'),
        'jack-jill-like-numbers-123-and-4-and-silly-characters',
        'right result',
    )
    is_ok(slugify("Un \xe9l\xe9phant \xe0 l'or\xe9e du bois"), 'un-elephant-a-loree-du-bois', 'right result')
    is_ok(
        slugify("Un \xe9l\xe9phant \xe0 l'or\xe9e du bois", True),
        'un-\xe9l\xe9phant-\xe0-lor\xe9e-du-bois',
        'right result',
    )
    is_ok(slugify('Hello, World!'), 'hello-world', 'right result')
    is_ok(slugify('spam & eggs'), 'spam-eggs', 'right result')
    is_ok(slugify('spam & ıçüş', True), 'spam-ıçüş', 'right result')
    is_ok(slugify('foo ıç bar', True), 'foo-ıç-bar', 'right result')
    is_ok(slugify('    foo ıç bar', True), 'foo-ıç-bar', 'right result')
    is_ok(slugify('你好', True), '你好', 'right result')

with subtest('gzip/gunzip'):
    uncompressed = b'a' * 1000
    compressed = gzip(uncompressed)
    isnt_ok(compressed, uncompressed, 'string changed')
    ok(len(compressed) < len(uncompressed), 'string is shorter')
    result = gunzip(compressed)
    is_ok(result, uncompressed, 'same string')

with subtest('humanize_bytes'):
    is_ok(humanize_bytes(0), '0B', 'zero Bytes')
    is_ok(humanize_bytes(1), '1B', 'one Byte')
    is_ok(humanize_bytes(-1023), '-1023B', 'negative Bytes')
    is_ok(humanize_bytes(1024), '1KiB', 'one KiB')
    is_ok(humanize_bytes(1025), '1KiB', 'one KiB')
    is_ok(humanize_bytes(1024 * 1024), '1MiB', 'one MiB')
    is_ok(humanize_bytes(1024 * 1024 * 1024), '1GiB', 'one GiB')
    is_ok(humanize_bytes(1024 * 1024 * 1024 * 1024), '1TiB', 'one TiB')
    is_ok(humanize_bytes(3000), '2.9KiB', 'almost 3KiB')
    is_ok(humanize_bytes(-3000), '-2.9KiB', 'almost -3KiB')
    is_ok(humanize_bytes(13443399680), '13GiB', 'two digits GiB')
    is_ok(humanize_bytes(8007188480), '7.5GiB', 'smaller GiB')
    is_ok(humanize_bytes(-8007188480), '-7.5GiB', 'negative smaller GiB')
    is_ok(humanize_bytes(-1099511627776), '-1TiB', 'negative smaller TiB')
    is_ok(humanize_bytes(717946880), '685MiB', 'large MiB')
    is_ok(humanize_bytes(-717946880), '-685MiB', 'large negative MiB')
    is_ok(humanize_bytes(245760), '240KiB', 'less than a MiB')

done_testing()
