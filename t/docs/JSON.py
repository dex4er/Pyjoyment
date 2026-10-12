import Pyjo.Test


class NoseTest(Pyjo.Test.NoseTest):
    script = __file__
    srcdir = '../..'


class UnitTest(Pyjo.Test.UnitTest):
    script = __file__


if __name__ == '__main__':
    from Pyjo.Test import *  # noqa

    from Pyjo.JSON import decode_json, encode_json, from_json, j, to_json

    bstring = encode_json({'foo': [1, 2], 'bar': 'hello!', 'baz': True})
    is_ok(bstring, b'{"bar":"hello!","baz":true,"foo":[1,2]}', 'bstring')

    dictionary = decode_json(bstring)
    is_deeply_ok(dictionary, {'bar': 'hello!', 'baz': True, 'foo': [1, 2]}, 'dictionary')

    bstring = encode_json('\u2028\u2029</script>')
    is_ok(bstring, b'"\\u2028\\u2029<\\/script>"', 'bstring')

    bstring = encode_json({'i': '♥ pyjo'})
    is_ok(bstring, b'{"i":"\xe2\x99\xa5 pyjo"}')

    # decode_json
    value = decode_json(bstring)
    is_deeply_ok(value, {'i': '♥ pyjo'}, 'value')

    # encode_json
    bstring = encode_json({'i': '♥ pyjo'})
    is_ok(bstring, b'{"i":"\xe2\x99\xa5 pyjo"}')

    # from_json
    string = '{"i":"♥ pyjo"}'
    value = from_json(string)
    is_deeply_ok(value, {'i': '♥ pyjo'}, 'value')

    # j
    bstring = j([1, 2, 3])
    is_ok(bstring, b'[1,2,3]')
    bstring = j({'i': '♥ pyjo'})
    is_ok(bstring, b'{"i":"\xe2\x99\xa5 pyjo"}')
    value = j(bstring)
    is_deeply_ok(value, {'i': '♥ pyjo'}, 'value')

    # to_json
    string = to_json({'i': '♥ pyjo'})
    is_ok(string, '{"i":"♥ pyjo"}', 'string')

    done_testing()
