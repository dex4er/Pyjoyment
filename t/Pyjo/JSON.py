# coding: utf-8

import Pyjo.Test


class NoseTest(Pyjo.Test.NoseTest):
    script = __file__
    srcdir = '../..'


class UnitTest(Pyjo.Test.UnitTest):
    script = __file__


class JSONTest(object):
    def __init__(self, something={}):
        self.something = something

    def to_json(self):
        return self.something


if __name__ == '__main__':

    from Pyjo.Test import *  # noqa

    from Pyjo.JSON import decode_json, encode_json, from_json, j, to_json
    from Pyjo.String.Bytes import b
    from Pyjo.String.Unicode import u

    # Decode array
    array = decode_json('[]')
    is_deeply_ok(array, [], 'decode []')
    array = decode_json('[ [ ]]')
    is_deeply_ok(array, [[]], 'decode [ [ ]]')

    # Decode number
    array = decode_json('[0]')
    is_deeply_ok(array, [0], 'decode [0]')
    array = decode_json('[1]')
    is_deeply_ok(array, [1], 'decode [1]')
    array = decode_json('[ "-122.026020" ]')
    is_deeply_ok(array, ['-122.026020'], 'decode [ -122.026020 ]')
    array = decode_json('[ -122.026020 ]')
    is_deeply_ok(array, [-122.02602], 'decode [ -122.026020 ]')
    array = decode_json('[0.0]')
    cmp_ok(array[0], '==', 0, 'value is 0')
    array = decode_json('[0e0]')
    cmp_ok(array[0], '==', 0, 'value is 0')
    array = decode_json('[1,-2]')
    is_deeply_ok(array, [1, -2], 'decode [1,-2]')
    array = decode_json('["10e12" , [2 ]]')
    is_deeply_ok(array, ['10e12', [2]], 'decode ["10e12" , [2 ]]')
    array = decode_json('[10e12 , [2 ]]')
    is_deeply_ok(array, [10000000000000, [2]], 'decode [10e12 , [2 ]]')
    array = decode_json('[37.7668 , [ 20 ]] ')
    is_deeply_ok(array, [37.7668, [20]], 'decode [37.7668 , [ 20 ]] ')
    array = decode_json('[1e3]')
    cmp_ok(array[0], '==', 1e3, 'value is 1e3')
    value = decode_json('0')
    cmp_ok(value, '==', 0, 'decode 0')
    value = decode_json('23.3')
    cmp_ok(value, '==', 23.3, 'decode 23.3')

    # Decode name
    array = decode_json('[true]')
    is_deeply_ok(array, [True], 'decode [true]')
    array = decode_json('[null]')
    is_deeply_ok(array, [None], 'decode [null]')
    array = decode_json('[true, false]')
    is_deeply_ok(array, [True, False], 'decode [true, false]')
    value = decode_json('true')
    is_ok(value, True, 'decode true')
    value = decode_json('false')
    is_ok(value, False, 'decode false')
    value = decode_json('null')
    is_ok(value, None, 'decode null')

    # Decode string
    array = decode_json('[" "]')
    is_deeply_ok(array, [' '], 'decode [" "]')
    array = decode_json('["hello world!"]')
    is_deeply_ok(array, ['hello world!'], 'decode ["hello world!"]')
    array = decode_json(r'["hello\nworld!"]')
    is_deeply_ok(array, ["hello\nworld!"], r'decode ["hello\nworld!"]')
    array = decode_json(r'["hello\t\"world!"]')
    is_deeply_ok(array, ["hello\t\"world!"], r'decode ["hello\t\"world!"]')
    array = decode_json(r'["hello\u0152world\u0152!"]')
    is_deeply_ok(array, [u"hello\u0152world\u0152!"], r'decode ["hello\u0152world\u0152!"]')
    array = decode_json('["0."]')
    is_deeply_ok(array, ['0.'], 'decode ["0."]')
    array = decode_json('[" 0"]')
    is_deeply_ok(array, [' 0'], 'decode [" 0"]')
    array = decode_json('["1"]')
    is_deeply_ok(array, ['1'], 'decode ["1"]')
    array = decode_json(r'["\u0007\b\/\f\r"]')
    is_deeply_ok(array, ["\a\b/\f\r"], r'decode ["\u0007\b\/\f\r"]')
    value = decode_json('""')
    is_ok(value, '', 'decode ""')
    value = decode_json(r'"hell\no"')
    is_ok(value, "hell\no", r'decode "hell\no"')

    # Decode object
    dictionary = decode_json('{}')
    is_deeply_ok(dictionary, {}, 'decode {}')
    dictionary = decode_json('{"foo": "bar"}')
    is_deeply_ok(dictionary, {'foo': 'bar'}, 'decode {"foo": "bar"}')
    dictionary = decode_json('{"foo": [23, "bar"]}')
    is_deeply_ok(dictionary, {'foo': [23, 'bar']}, 'decode {"foo": [23, "bar"]}')

    # Decode full spec example
    dictionary = decode_json('''
    {
       "Image": {
           "Width":  800,
           "Height": 600,
           "Title":  "View from 15th Floor",
           "Thumbnail": {
               "Url":    "http://www.example.com/image/481989943",
               "Height": 125,
               "Width":  "100"
           },
           "IDs": [116, 943, 234, 38793]
        }
    }
    ''')
    is_ok(dictionary['Image']['Width'], 800, 'right value')
    is_ok(dictionary['Image']['Height'], 600, 'right value')
    is_ok(dictionary['Image']['Title'], 'View from 15th Floor', 'right value')
    is_ok(dictionary['Image']['Thumbnail']['Url'], 'http://www.example.com/image/481989943', 'right value')
    is_ok(dictionary['Image']['Thumbnail']['Height'], 125, 'right value')
    is_ok(dictionary['Image']['Thumbnail']['Width'], '100', 'right value')
    is_ok(dictionary['Image']['IDs'][0], 116, 'right value')
    is_ok(dictionary['Image']['IDs'][1], 943, 'right value')
    is_ok(dictionary['Image']['IDs'][2], 234, 'right value')
    is_ok(dictionary['Image']['IDs'][3], 38793, 'right value')

    # Encode array
    bstring = encode_json([])
    is_ok(bstring, b'[]', 'encode []')
    bstring = encode_json([[]])
    is_ok(bstring, b'[[]]', 'encode [[]]')
    bstring = encode_json([[], []])
    is_ok(bstring, b'[[],[]]', 'encode [[], []]')
    bstring = encode_json([[], [[]], []])
    is_ok(bstring, b'[[],[[]],[]]', 'encode [[], [[]], []]')

    # Encode string
    bstring = encode_json(['foo'])
    is_ok(bstring, b'["foo"]', 'encode [\'foo\']')
    bstring = encode_json(["hello\nworld!"])
    is_ok(bstring, br'["hello\nworld!"]', r'encode ["hello\nworld!"]')
    bstring = encode_json(["hello\t\"world!"])
    is_ok(bstring, br'["hello\t\"world!"]', r'encode ["hello\t\"world!"]')
    bstring = encode_json([u"hello\x03\u0152world\u0152!"])
    is_ok(b(bstring).decode('utf-8'), u"[\"hello\\u0003\u0152world\u0152!\"]", r'encode ["hello\x03\u0152world\u0152!"]')
    bstring = encode_json(["123abc"])
    is_ok(bstring, b'["123abc"]', 'encode ["123abc"]')
    bstring = encode_json(["\x00\x1f \a\b/\f\r"])
    is_ok(bstring, b'["\\u0000\\u001f \\u0007\\b\\/\\f\\r"]', r'encode ["\x00\x1f \a\b/\f\r"]')
    bstring = encode_json('')
    is_ok(bstring, b'""', 'encode ""')
    bstring = encode_json("hell\no")
    is_ok(bstring, b'"hell\\no"', r'encode "hell\no"')

    # Encode object
    bstring = encode_json({})
    is_ok(bstring, b'{}', 'encode {}')
    bstring = encode_json({'foo': {}})
    is_ok(bstring, b'{"foo":{}}', 'encode {foo: {}}')
    bstring = encode_json({'foo': 'bar'})
    is_ok(bstring, b'{"foo":"bar"}', 'encode {foo: \'bar\'}')
    bstring = encode_json({'foo': []})
    is_ok(bstring, b'{"foo":[]}', 'encode {foo: []}')
    bstring = encode_json({'foo': ['bar']})
    is_ok(bstring, b'{"foo":["bar"]}', 'encode {foo: [\'bar\']}')

    # Encode name
    bstring = encode_json([True])
    is_ok(bstring, b'[true]', 'encode [True]')
    bstring = encode_json([None])
    is_ok(bstring, b'[null]', 'encode [None]')
    bstring = encode_json([True, False])
    is_ok(bstring, b'[true,false]', 'encode [True, False]')
    bstring = encode_json(True)
    is_ok(bstring, b'true', 'encode True')
    bstring = encode_json(False)
    is_ok(bstring, b'false', 'encode False')
    bstring = encode_json(None)
    is_ok(bstring, b'null', 'encode None')

    # Encode number
    bstring = encode_json([1])
    is_ok(bstring, b'[1]', 'encode [1]')
    bstring = encode_json(["1"])
    is_ok(bstring, b'["1"]', 'encode ["1"]')
    bstring = encode_json(['-122.026020'])
    is_ok(bstring, b'["-122.026020"]', 'encode [\'-122.026020\']')
    bstring = encode_json([-122.026020])
    is_ok(bstring, b'[-122.02602]', 'encode [-122.026020]')
    bstring = encode_json([1, -2])
    is_ok(bstring, b'[1,-2]', 'encode [1, -2]')
    bstring = encode_json(['10e12', [2]])
    is_ok(bstring, b'["10e12",[2]]', 'encode [\'10e12\', [2]]')
    bstring = encode_json([int(10e12), [2]])
    is_ok(bstring, b'[10000000000000,[2]]', 'encode [10e12, [2]]')
    bstring = encode_json([37.7668, [20]])
    is_ok(bstring, b'[37.7668,[20]]', 'encode [37.7668, [20]]')
    bstring = encode_json(0)
    is_ok(bstring, b'0', 'encode 0')
    bstring = encode_json(23.3)
    is_ok(bstring, b'23.3', 'encode 23.3')

    # Faihu roundtrip
    bstring = j([u"\U00010346"])
    is_ok(b(bstring).decode('utf-8'), u"[\"\U00010346\"]", r'encode ["\U00010346"]')
    array = j(bstring)
    is_deeply_ok(array, [u"\U00010346"], 'successful roundtrip')

    # Decode faihu surrogate pair
    array = decode_json(b'["\\ud800\\udf46"]')
    is_deeply_ok(array, [u"\U00010346"], 'decode [\"\\ud800\\udf46\"]')

    # Decode object with duplicate keys
    dictionary = decode_json(b'{"foo": 1, "foo": 2}')
    is_deeply_ok(dictionary, {'foo': 2}, 'decode {"foo": 1, "foo": 2}')

    # Complicated roudtrips
    bstring = b'{"":""}'
    dictionary = decode_json(bstring)
    is_deeply_ok(dictionary, {'': ''}, 'decode {"":""}')
    is_ok(encode_json(dictionary), bstring, 're-encode')
    bstring = b'[null,false,true,"",0,1]'
    array = decode_json(bstring)
    is_deeply_ok(array, [None, False, True, '', 0, 1], 'decode [null,false,true,"",0,1]')
    is_ok(encode_json(array), bstring, 're-encode')
    array = [None, 0, 1, '', True, False]
    bstring = encode_json(array)
    ok(bstring, 'defined value')
    is_deeply_ok(decode_json(bstring), array, 'successful roundtrip')

    # Real world roundtrip
    bstring = encode_json({'foo': r'c:\progra~1\mozill~1\firefox.exe'})
    is_ok(bstring, b'{"foo":"c:\\\\progra~1\\\\mozill~1\\\\firefox.exe"}', r'encode {foo: \'c:\progra~1\mozill~1\firefox.exe\'}')
    dictionary = decode_json(bstring)
    is_deeply_ok(dictionary, {'foo': r'c:\progra~1\mozill~1\firefox.exe'}, 'successful roundtrip')

    # Huge string
    bstring = encode_json(['a' * 32768])
    is_deeply_ok(decode_json(bstring), ['a' * 32768], 'successful roundtrip')

    # u2028, u2029 and slash
    bstring = encode_json([u"\u2028test\u2029123</script>"])
    is_ok(bstring, br'["\u2028test\u2029123<\/script>"]', 'escaped u2028, u2029 and slash')
    is_deeply_ok(decode_json(bstring), [u"\u2028test\u2029123</script>"], 'successful roundtrip')

    # JSON without utf-8 encoding
    is_deeply_ok(from_json(u'["♥"]'), [u'♥'], 'characters decoded')
    is_ok(to_json([u'♥']), u'["♥"]', 'characters encoded')
    is_deeply_ok(from_json(to_json([u"\xe9"])), [u"\xe9"], 'successful roundtrip')

    # Object
    bstring = encode_json([b('test')])
    is_deeply_ok(decode_json(bstring), ['test'], 'successful roundtrip')
    bstring = encode_json([u('test')])
    is_deeply_ok(decode_json(bstring), ['test'], 'successful roundtrip')

    # Object with to_json method
    bstring = encode_json(JSONTest())
    is_deeply_ok(decode_json(bstring), {}, 'successful roundtrip')
    bstring = encode_json(JSONTest({'just': 'works'}))
    is_deeply_ok(decode_json(bstring), {'just': 'works'}, 'successful roundtrip')

    # Converted numbers
    num = 3
    string = str(num)
    is_ok(encode_json({'test': [num, string]}), b'{"test":[3,"3"]}', 'upgraded number detected')
    num = 3.21
    string = str(num)
    is_ok(encode_json({'test': [num, string]}), b'{"test":[3.21,"3.21"]}', 'upgraded number detected')

    # "inf" and "nan"
    throws_ok(lambda: encode_json({'test': float('Inf')}), ValueError, 'encode "Inf"')
    throws_ok(lambda: encode_json({'test': float('NaN')}), ValueError, 'encode "NaN"')

    # "null"
    is_ok(j('null'), None, 'decode null')

    # Errors
    throws_ok(lambda: decode_json('test'), ValueError, 'right error')
    throws_ok(lambda: decode_json('{'), ValueError, 'right error')

    done_testing()
