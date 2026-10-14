from Pyjo.Test import *


with subtest('Synopsis'):
    from Pyjo.SSE import build_event, parse_event

    ok(callable(build_event) and callable(parse_event), 'imported')

with subtest('build_event'):
    event = {'type': 'foo', 'text': 'bar', 'id': 23}
    data = build_event(event)
    is_ok(data, b'event: foo\x0d\x0adata: bar\x0d\x0aid: 23\x0d\x0a\x0d\x0a', 'event')
    data = build_event({'type': 'foo', 'text': 'bar', 'id': 23})
    is_ok(data, b'event: foo\x0d\x0adata: bar\x0d\x0aid: 23\x0d\x0a\x0d\x0a', 'event')

with subtest('parse_event'):
    buffer = bytearray(b'data: bar\r\n\r\n')
    event = parse_event(buffer)
    is_ok(event, {'id': None, 'type': 'message', 'text': 'bar'}, 'event')
    is_ok(bytes(buffer), b'', 'parsed event removed')
    event = parse_event(bytearray(b'data: bar\r\n\r\n'))
    is_ok(event['text'], 'bar', 'event')

done_testing()
