from Pyjo.Test import *
from Pyjo.Util import (
    b64_decode,
    b64_encode,
    deprecated,
    dumper,
    generate_secret,
    gunzip,
    gzip,
    header_params,
    hmac_sha1_sum,
    html_unescape,
    md5_sum,
    monkey_patch,
    network_contains,
    punycode_decode,
    punycode_encode,
    random_bytes,
    scope_guard,
    secure_compare,
    sha1_sum,
    slurp,
    split_header,
    spurt,
    steady_time,
    tablify,
    url_escape,
    url_unescape,
    xml_escape,
)

import ast
import base64
import contextlib
import csv
import email.message
import gzip as gzip_module
import hashlib
import hmac
import html
import io
import ipaddress
import pathlib
import pickle
import sys
import tempfile
import time
import types
import urllib.parse
import warnings
import zlib


with subtest('base64'):
    data = bytes(range(256)) * 2
    is_ok(b64_encode(data), base64.encodebytes(data).decode(), 'lines of 76 characters, as encodebytes')
    is_ok(b64_encode(data, ''), base64.b64encode(data).decode(), 'one line, as b64encode')
    is_ok(b64_decode(base64.encodebytes(data)), data, 'decodes encodebytes')

with subtest('urllib.parse'):
    string = 'foo bar;baz/€~'
    is_ok(url_escape(string.encode()).decode(), urllib.parse.quote(string, safe='-._~'), 'same as quote of UTF-8')
    is_ok(url_unescape(urllib.parse.quote(string).encode()).decode(), string, 'decodes quote')
    is_ok(urllib.parse.unquote(url_escape(string.encode()).decode()), string, 'unquote decodes it')

with subtest('html'):
    string = '<a href="x">Tom & Jerry\'s</a>'
    is_ok(html.unescape(xml_escape(string)), string, 'unescape of html decodes it')
    is_ok(html_unescape(html.escape(string)), string, 'decodes escape of html')
    is_ok(html_unescape('&eacute;&#233;&#xe9;'), html.unescape('&eacute;&#233;&#xe9;'), 'same as unescape of html')

with subtest('Markup joined to a string'):
    from Pyjo.String.HTML import html as markup

    escaped = xml_escape(markup('&lt;'))
    is_ok(type(escaped), str, 'plain string')
    is_ok('<a title="' + escaped + '">', '<a title="&lt;">', 'joined as it is')

with subtest('hashlib and hmac'):
    is_ok(md5_sum(b'foo'), hashlib.md5(b'foo').hexdigest(), 'md5')
    is_ok(sha1_sum(b'foo'), hashlib.sha1(b'foo').hexdigest(), 'sha1')
    is_ok(hmac_sha1_sum(b'foo', b'passw0rd'), hmac.new(b'passw0rd', b'foo', 'sha1').hexdigest(), 'hmac')
    ok(secure_compare('foo', 'foo') == hmac.compare_digest(b'foo', b'foo'), 'same as compare_digest')

with subtest('gzip and zlib'):
    data = b'a' * 1000
    is_ok(gzip_module.decompress(gzip(data)), data, 'gzip module decompresses it')
    is_ok(gunzip(gzip_module.compress(data)), data, 'decompresses the gzip module')
    is_ok(zlib.decompress(gzip(data), wbits=31), data, 'zlib decompresses it')

with subtest('punycode codec'):
    is_ok(punycode_encode('bücher'), 'bücher'.encode('punycode').decode(), 'same as the codec')
    is_ok(punycode_decode('bcher-kva'), b'bcher-kva'.decode('punycode'), 'same as the codec')

with subtest('ipaddress'):
    ok(network_contains('10.0.0.0/8', '10.10.10.10'), 'contained')
    ok(ipaddress.ip_address('10.10.10.10') in ipaddress.ip_network('10.0.0.0/8'), 'contained for ipaddress too')
    ok(not network_contains('fc00::/7', '::1'), 'not contained')
    ok(ipaddress.ip_address('::1') not in ipaddress.ip_network('fc00::/7'), 'not contained for ipaddress either')

with subtest('email.message'):
    header = 'attachment; filename="a b.txt"; size=3'
    msg = email.message.Message()
    msg['Content-Disposition'] = header
    params, _ = header_params(header.split(';', 1)[1])
    is_ok(params['filename'], msg.get_param('filename', header='Content-Disposition'), 'quoted parameter')
    is_ok(params['size'], msg.get_param('size', header='Content-Disposition'), 'unquoted parameter')

with subtest('dict of a part of a header'):
    is_deeply_ok(dict(split_header('a=1; b="2 3"; c')[0]), {'a': '1', 'b': '2 3', 'c': None}, 'dict')

with subtest('pathlib and tempfile'):
    with tempfile.TemporaryDirectory() as tmp:
        path = pathlib.Path(tmp) / 'test.txt'
        spurt('zażółć\n', path)
        is_ok(path.read_bytes(), 'zażółć\n'.encode(), 'read_bytes of pathlib')
        path.write_text('gęślą\r\n', encoding='utf-8', newline='')
        is_ok(slurp(path), 'gęślą\r\n', 'write_text of pathlib')

with subtest('time.monotonic'):
    before = time.monotonic()
    now = steady_time()
    ok(before <= now <= time.monotonic(), 'same clock as monotonic')

with subtest('ast.literal_eval'):
    data = {'b': [1, (2, 3)], 'a': {'c': None, 'd': 'e'}}
    is_deeply_ok(ast.literal_eval(dumper(data)), data, 'dumped structure evaluates to the same')

with subtest('secrets'):
    is_ok(len(base64.urlsafe_b64decode(generate_secret() + '==')), 128, '128 random bytes, as token_urlsafe')
    is_ok(len(random_bytes(32)), 32, 'token_bytes')

with subtest('warnings'):
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        throws_ok(lambda: deprecated('foo is DEPRECATED'), DeprecationWarning, 'error filter raises it')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        is_ok(deprecated('foo is DEPRECATED'), None, 'ignore filter hides it')

with subtest('contextlib.ExitStack'):
    calls = []
    with contextlib.ExitStack() as stack:
        stack.enter_context(scope_guard(lambda: calls.append('first')))
        stack.enter_context(scope_guard(lambda: calls.append('second')))
    is_deeply_ok(calls, ['second', 'first'], 'in reverse order')

with subtest('csv'):
    rows = list(csv.reader(io.StringIO('name,size\nfoo,1\nyada,23\n')))
    is_ok(tablify(rows), 'name  size\nfoo   1\nyada  23\n', 'rows of a reader')

with subtest('repr and pickle of a patched function'):

    class MojoMonkeyTest:
        pass

    monkey_patch(MojoMonkeyTest, foo=lambda: 'foo')
    like_ok(repr(MojoMonkeyTest.foo), r'^<function MojoMonkeyTest\.foo at ', 'qualified name in repr')
    module = types.ModuleType('MojoMonkeyModule')
    sys.modules['MojoMonkeyModule'] = module
    monkey_patch(module, foo=lambda: 'foo')
    is_ok(pickle.loads(pickle.dumps(module.foo))(), 'foo', 'pickled by its name')
    del sys.modules['MojoMonkeyModule']

done_testing()
