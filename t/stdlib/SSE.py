from Pyjo.SSE import build_event, parse_event
from Pyjo.Test import *

import json


with subtest('JSON data'):
    data = {'temperature': 21.5, 'unit': 'C'}
    buffer = bytearray(build_event({'type': 'reading', 'text': json.dumps(data), 'id': 1}))
    event = parse_event(buffer)
    is_ok(json.loads(event['text']), data, 'JSON roundtrip')
    is_ok(event['type'], 'reading', 'right type')

with subtest('A buffer that grows'):
    buffer = bytearray()
    events = []
    for chunk in (b'data: fo', b'o\x0d\x0a', b'\x0d\x0adata: bar\x0d\x0a\x0d', b'\x0a'):
        buffer += chunk
        while event := parse_event(buffer):
            events.append(event['text'])
    is_ok(events, ['foo', 'bar'], 'events from chunks')
    # A carriage return at the end of the buffer ends a line, as in Mojo, so a line feed that follows is left
    is_ok(bytes(buffer), b'\x0a', 'the line feed of a split CRLF is left')

done_testing()
