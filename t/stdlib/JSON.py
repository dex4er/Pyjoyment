import Pyjo.Collection
import Pyjo.Date
import Pyjo.JSON
import Pyjo.Path
import Pyjo.String.Unicode
import Pyjo.URL

from Pyjo.JSON import decode_json, encode_json, from_json, to_json
from Pyjo.Test import *

import json


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __json__(self):
        return {'x': self.x, 'y': self.y}


with subtest('json.dumps with Pyjo.JSON.default'):
    data = {'url': Pyjo.URL.new('http://example.com/foo'), 'path': Pyjo.Path.new('/a/b'), 'point': Point(1, 2)}
    is_ok(
        json.dumps(data, default=Pyjo.JSON.default, sort_keys=True),
        '{"path": "/a/b", "point": {"x": 1, "y": 2}, "url": "http://example.com/foo"}',
        'objects of Pyjoyment and __json__',
    )
    is_ok(json.dumps(Pyjo.Date.new(0), default=Pyjo.JSON.default), '"Thu, 01 Jan 1970 00:00:00 GMT"', 'Pyjo.Date')
    is_ok(json.dumps([b'caf\xe9'], default=Pyjo.JSON.default), '["caf\\u00e9"]', 'bytes as characters 0-255')
    is_ok(json.dumps([object()], default=Pyjo.JSON.default), '[null]', 'unknown object')

with subtest('Same result as json.dumps'):
    data = {'foo': [1, 2.5, 'bar', None, True, False], 'baz': {'a': 'b'}}
    is_ok(
        to_json(data),
        json.dumps(data, separators=(',', ':'), ensure_ascii=False),
        'to_json is json.dumps, compact and in the order of the dict',
    )
    is_ok(
        to_json(data, sort_keys=True),
        json.dumps(data, separators=(',', ':'), sort_keys=True, ensure_ascii=False),
        'to_json with sort_keys is json.dumps, compact and sorted',
    )
    is_ok(to_json('a/b'), json.dumps('a/b').replace('/', '\\/'), 'with "/" escaped')

with subtest('Same result as json.loads'):
    text = '{"foo": [1, 2.5, "bar", null, true, false], "baz": {"a": "\\u2603"}}'
    is_ok(from_json(text), json.loads(text), 'from_json')
    is_ok(decode_json(text.encode()), json.loads(text), 'decode_json')
    is_ok(json.loads(encode_json(json.loads(text))), json.loads(text), 'json.loads reads encode_json')

with subtest('Subclasses of standard types'):
    is_ok(encode_json(Pyjo.Collection.new(1, 2, 3)), b'[1,2,3]', 'Pyjo.Collection is a list')
    is_ok(encode_json(Pyjo.String.Unicode.new('test')), b'"test"', 'Pyjo.String.Unicode is a str')
    is_ok(json.dumps(Pyjo.Collection.new(1, 2, 3)), '[1, 2, 3]', 'json.dumps of Pyjo.Collection')

done_testing()
