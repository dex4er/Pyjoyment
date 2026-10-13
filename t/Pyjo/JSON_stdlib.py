import Pyjo.Base
import Pyjo.JSON
import Pyjo.String.Bytes

from Pyjo.JSON import decode_json, encode_json, false, from_json, j, to_json, true
from Pyjo.Test import *
from Pyjo.Util import encode

import re


if not Pyjo.JSON.JSON_STDLIB:
    plan(skip_all='json module of the standard library required for this test!')


class JSONTest(Pyjo.Base.object):
    def __init__(self, **kwargs):
        self.something = {}
        self.set(**kwargs)

    def __json__(self):
        return self.something


class JSONTest2(Pyjo.Base.object):
    def __and__(self, other):
        raise RuntimeError

    def __str__(self):
        return 'works!'


class JSONTest3(Pyjo.Base.object):
    pass


with subtest('Basics'):
    array = decode_json('[]')
    is_deeply_ok(array, [], 'decode_json')
    data = encode_json([])
    is_ok(data, b'[]', 'encode_json')
    array = from_json('[]')
    is_deeply_ok(array, [], 'from_json')
    chars = to_json([])
    is_ok(chars, '[]', 'to_json')
    array = j('[]')
    is_deeply_ok(array, [], 'j() decode')
    data = j([])
    is_ok(data, b'[]', 'j() encode')
    is_ok(encode_json([true]), b'[true]', 'true')
    is_ok(encode_json([false]), b'[false]', 'false')

with subtest('"utf8"'):
    is_deeply_ok(decode_json(encode('UTF-8', '["♥"]')), ['♥'], 'bytes decoded')
    is_ok(encode_json(['♥']), encode('UTF-8', '["♥"]'), 'bytes encoded')
    is_deeply_ok(from_json('["♥"]'), ['♥'], 'characters decoded')
    is_ok(to_json(['♥']), '["♥"]', 'characters encoded')

with subtest('"canonical"'):
    is_deeply_ok(encode_json({'a': 1, 'b': 2, 'c': 3}), b'{"a":1,"b":2,"c":3}', 'canonical object')

with subtest('"allow_nonref"'):
    is_deeply_ok(encode_json(true), b'true', 'bare true')

with subtest('"allow_unknown"'):
    is_deeply_ok(encode_json(lambda: None), b'null', 'unknown reference')

with subtest('"allow_blessed"'):
    is_deeply_ok(encode_json(Pyjo.String.Bytes.new('test')), b'"test"', 'blessed reference')

with subtest('"convert_blessed"'):
    data = encode_json(JSONTest.new())
    is_deeply_ok(decode_json(data), {}, 'successful roundtrip')
    data = encode_json(JSONTest.new(something={'just': 'works'}, **{'else': {'not': 'working'}}))
    is_deeply_ok(decode_json(data), {'just': 'works'}, 'successful roundtrip')
    is_ok(encode_json([JSONTest2.new()]), b'["works!"]', 'object stringified')
    is_ok(encode_json([JSONTest3.new()]), b'[null]', 'object with no stringification overload')

with subtest('"stringify_infnan"'):
    like_ok(encode_json({'test': float('inf')}), re.compile(rb'^{"test":".*"}$'), 'encode "inf" as string')
    like_ok(encode_json({'test': float('nan')}), re.compile(rb'^{"test":".*"}$'), 'encode "nan" as string')

with subtest('"escape_slash"'):
    is_deeply_ok(encode_json('/test/123'), rb'"\/test\/123"', 'escaped slash')

with subtest('"allow_dupkeys"'):
    is_deeply_ok(decode_json('{"test":1,"test":2}'), {'test': 2}, 'no duplicate keys error')

done_testing()
