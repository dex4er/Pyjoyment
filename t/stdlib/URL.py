import Pyjo.URL

from Pyjo.Test import *

from urllib.parse import SplitResult, urlparse, urlsplit, urlunsplit


with subtest('From urllib'):
    url = Pyjo.URL.new(urlsplit('http://sri:foo@example.com:3000/foo?f=b#x'))
    is_ok(url.to_unsafe_str(), 'http://sri:foo@example.com:3000/foo?f=b#x', 'from urlsplit')
    is_ok(url.port, 3000, 'right port')
    url = Pyjo.URL.new(urlparse('http://example.com/a;p?q#f'))
    is_ok(str(url), 'http://example.com/a;p?q#f', 'from urlparse')
    url = Pyjo.URL.new(urlsplit(b'http://example.com/%E2%99%A5'))
    is_deeply_ok(url.path.parts, ['♥'], 'from urlsplit of bytes')
    url = Pyjo.URL.new().parse(urlsplit('/relative?x=1'))
    is_ok(str(url), '/relative?x=1', 'parse urlsplit')

with subtest('To urllib'):
    url = Pyjo.URL.new('http://isabel:s3cret@Bücher.ch:8080/a b?c=d#e')
    split = url.to_urllib()
    isa_ok(split, SplitResult, 'split')
    is_ok(split.scheme, 'http', 'right scheme')
    is_ok(split.netloc, 'isabel:s3cret@xn--Bcher-kva.ch:8080', 'right netloc')
    is_ok(split.path, '/a%20b', 'right path')
    is_ok(split.query, 'c=d', 'right query')
    is_ok(split.fragment, 'e', 'right fragment')
    is_ok(split.username, 'isabel', 'right username')
    is_ok(split.password, 's3cret', 'right password')
    is_ok(split.hostname, 'xn--bcher-kva.ch', 'hostname lowercased by urllib')
    is_ok(split.port, 8080, 'right port')

with subtest('Roundtrip'):
    url = Pyjo.URL.new('https://sri:☃@☃.net:3000/♥?♥=☃#☃')
    is_ok(Pyjo.URL.new(url.to_urllib()).to_unsafe_str(), url.to_unsafe_str(), 'Pyjo.URL -> urllib -> Pyjo.URL')
    is_ok(urlunsplit(url.to_urllib()), url.to_unsafe_str(), 'urlunsplit')

with subtest('Strings for urllib'):
    url = Pyjo.URL.new('http://sri:foo@example.com/foo?bar=baz')
    is_ok(urlsplit(str(url)).username, None, 'str leaves out the userinfo')
    is_ok(urlsplit(url.to_unsafe_str()).username, 'sri', 'to_unsafe_str keeps it')
    throws_ok(lambda: urlsplit(url), AttributeError, 'urllib takes only str and bytes')

done_testing()
