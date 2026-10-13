from Pyjo.Test import *


with subtest('Synopsis'):
    from Pyjo.JSON import decode_json, encode_json

    data = encode_json({'foo': [1, 2], 'bar': 'hello!', 'baz': True})
    is_ok(data, b'{"bar":"hello!","baz":true,"foo":[1,2]}', 'data')
    value = decode_json(data)
    is_ok(value, {'foo': [1, 2], 'bar': 'hello!', 'baz': True}, 'value')

with subtest('Description'):
    # [1, -2, 3]     -> [1, -2, 3]
    # {"foo": "bar"} -> {'foo': 'bar'}
    is_ok(decode_json('[1, -2, 3]'), [1, -2, 3], '[1, -2, 3]')
    is_ok(decode_json('{"foo": "bar"}'), {'foo': 'bar'}, '{"foo": "bar"}')

    # true  -> True
    # false -> False
    # null  -> None
    is_ok(decode_json('true'), True, 'true')
    is_ok(decode_json('false'), False, 'false')
    is_ok(decode_json('null'), None, 'null')

    # "</script>" -> "<\/script>"
    is_ok(encode_json('</script>'), rb'"<\/script>"', '"</script>"')

with subtest('decode_json'):
    value = decode_json(data)
    is_ok(value, {'foo': [1, 2], 'bar': 'hello!', 'baz': True}, 'value')

with subtest('default'):
    import Pyjo.JSON
    import Pyjo.URL

    import json

    value = Pyjo.URL.new('http://example.com')
    data = json.dumps(value, default=Pyjo.JSON.default)
    is_ok(data, '"http://example.com"', 'data')

    # '{"url": "http://example.com"}'
    is_ok(
        json.dumps({'url': Pyjo.URL.new('http://example.com')}, default=Pyjo.JSON.default),
        '{"url": "http://example.com"}',
        'json.dumps',
    )

with subtest('encode_json'):
    data = encode_json({'i': '♥ pyjoyment'})
    is_ok(data, '{"i":"♥ pyjoyment"}'.encode(), 'data')

with subtest('false'):
    from Pyjo.JSON import false

    is_ok(false, False, 'false')

with subtest('from_json'):
    from Pyjo.JSON import from_json

    chars = '{"i":"♥ pyjoyment"}'
    value = from_json(chars)
    is_ok(value, {'i': '♥ pyjoyment'}, 'value')

with subtest('j'):
    from Pyjo.JSON import j

    data = j([1, 2, 3])
    is_ok(data, b'[1,2,3]', 'list')
    data = j({'i': '♥ pyjoyment'})
    is_ok(data, '{"i":"♥ pyjoyment"}'.encode(), 'dict')
    value = j(data)
    is_ok(value, {'i': '♥ pyjoyment'}, 'value')

with subtest('to_json'):
    from Pyjo.JSON import to_json

    chars = to_json({'i': '♥ pyjoyment'})
    is_ok(chars, '{"i":"♥ pyjoyment"}', 'chars')

with subtest('true'):
    from Pyjo.JSON import true

    is_ok(true, True, 'true')

done_testing()
