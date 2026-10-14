from Pyjo.SSE import build_event, parse_event
from Pyjo.Test import *


with subtest('Simple event roundtrip'):
    data = build_event({'type': 'foo', 'text': 'bar', 'id': 23})
    is_ok(data, b'event: foo\x0d\x0adata: bar\x0d\x0aid: 23\x0d\x0a\x0d\x0a', 'right event')
    event = parse_event(bytearray(data))
    is_ok(event['type'], 'foo', 'right event type')
    is_ok(event['text'], 'bar', 'right event text')
    is_ok(event['id'], '23', 'right event id')

with subtest('No id and type'):
    data = build_event({'text': 'bar'})
    is_ok(data, b'data: bar\x0d\x0a\x0d\x0a', 'right event')
    event = parse_event(bytearray(data))
    is_ok(event['type'], 'message', 'default event type')
    is_ok(event['text'], 'bar', 'right event text')
    is_ok(event['id'], None, 'no event id')

with subtest('Unicode roundtrip'):
    data = build_event({'type': 'fo♥o', 'text': 'I ♥ Mojolicious', 'id': '1♥3'})
    event = parse_event(bytearray(data))
    is_ok(event['type'], 'fo♥o', 'right event type')
    is_ok(event['text'], 'I ♥ Mojolicious', 'right event text')
    is_ok(event['id'], '1♥3', 'right event id')

with subtest('Event with multiple data sections'):
    event = parse_event(bytearray(b'data: YHOO\x0d\x0adata: +2\x0d\x0adata: 10\x0d\x0a\x0d\x0a'))
    is_ok(event['type'], 'message', 'right event type')
    is_ok(event['text'], 'YHOO\n+2\n10', 'right event text')
    is_ok(event['id'], None, 'no event id')

with subtest('Multiple lines'):
    buffer = bytearray(
        b'data: This is the first message.\x0a\x0adata: This is the second message, it\x0a'
        b'data: has two lines.\x0a\x0adata: This is the third message.\x0a\x0a'
    )
    event1 = parse_event(buffer)
    is_ok(event1['type'], 'message', 'right event type')
    is_ok(event1['text'], 'This is the first message.', 'right event text')
    is_ok(event1['id'], None, 'no event id')
    event2 = parse_event(buffer)
    is_ok(event2['type'], 'message', 'right event type')
    is_ok(event2['text'], 'This is the second message, it\nhas two lines.', 'right event text')
    is_ok(event2['id'], None, 'no event id')
    event3 = parse_event(buffer)
    is_ok(event3['type'], 'message', 'right event type')
    is_ok(event3['text'], 'This is the third message.', 'right event text')
    is_ok(event3['id'], None, 'no event id')
    is_ok(parse_event(buffer), None, 'no more events')

with subtest('Event types'):
    buffer = bytearray(
        b'event: add\x0ddata: 73857293\x0d\x0devent: remove\x0ddata: 2153\x0d\x0devent: add\x0ddata: 113411\x0d\x0d'
    )
    event1 = parse_event(buffer)
    is_ok(event1['type'], 'add', 'right event type')
    is_ok(event1['text'], '73857293', 'right event text')
    is_ok(event1['id'], None, 'no event id')
    event2 = parse_event(buffer)
    is_ok(event2['type'], 'remove', 'right event type')
    is_ok(event2['text'], '2153', 'right event text')
    is_ok(event2['id'], None, 'no event id')
    event3 = parse_event(buffer)
    is_ok(event3['type'], 'add', 'right event type')
    is_ok(event3['text'], '113411', 'right event text')
    is_ok(event3['id'], None, 'no event id')
    is_ok(parse_event(buffer), None, 'no more events')

with subtest('Insignificant whitespace'):
    buffer = bytearray(b'data:test\x0d\x0a\x0d\x0adata: test\x0d\x0a\x0d\x0a')
    event1 = parse_event(buffer)
    is_ok(event1['type'], 'message', 'right event type')
    is_ok(event1['text'], 'test', 'right event text')
    is_ok(event1['id'], None, 'no event id')
    event2 = parse_event(buffer)
    is_ok(event2['type'], 'message', 'right event type')
    is_ok(event2['text'], 'test', 'right event text')
    is_ok(event2['id'], None, 'no event id')
    is_ok(parse_event(buffer), None, 'no more events')

with subtest('Events with comment'):
    buffer = bytearray(
        b': test stream\x0a\x0ddata: first event\x0did: 1\x0d\x0ddata:second event\x0did\x0d\x0ddata:  third event\x0a\x0a'
    )
    event1 = parse_event(buffer)
    is_ok(event1['type'], 'message', 'right event type')
    is_ok(event1['text'], 'first event', 'right event text')
    is_ok(event1['id'], '1', 'right event id')
    event2 = parse_event(buffer)
    is_ok(event2['type'], 'message', 'right event type')
    is_ok(event2['text'], 'second event', 'right event text')
    is_ok(event2['id'], None, 'no event id')
    event3 = parse_event(buffer)
    is_ok(event3['type'], 'message', 'right event type')
    is_ok(event3['text'], 'third event', 'right event text')
    is_ok(event3['id'], None, 'no event id')
    is_ok(parse_event(buffer), None, 'no more events')

with subtest('Lots of data'):
    buffer = bytearray(b'data\x0a\x0adata\x0adata\x0a\x0adata:\x0a\x0a')
    event1 = parse_event(buffer)
    is_ok(event1['type'], 'message', 'right event type')
    is_ok(event1['text'], '', 'right event text')
    is_ok(event1['id'], None, 'no event id')
    event2 = parse_event(buffer)
    is_ok(event2['type'], 'message', 'right event type')
    is_ok(event2['text'], '\n', 'right event text')
    is_ok(event2['id'], None, 'no event id')
    event3 = parse_event(buffer)
    is_ok(event3['type'], 'message', 'right event type')
    is_ok(event3['text'], '', 'right event text')
    is_ok(event3['id'], None, 'no event id')
    is_ok(parse_event(buffer), None, 'no more events')

with subtest('Comments'):
    buffer = bytearray(build_event({'comment': 'This is a comment'}))
    is_ok(bytes(buffer), b': This is a comment\x0d\x0a\x0d\x0a', 'right event')
    is_ok(parse_event(buffer), None, 'no event')
    is_ok(bytes(buffer), b'', 'buffer is empty')

    buffer = bytearray(build_event({'comment': 'This will be\x0atwo comments'}))
    is_ok(bytes(buffer), b': This will be\x0d\x0a: two comments\x0d\x0a\x0d\x0a', 'right event')
    is_ok(parse_event(buffer), None, 'no event')
    is_ok(bytes(buffer), b'', 'buffer is empty')

with subtest('Unallowed characters'):
    buffer = bytearray(build_event({'type': 'foo', 'text': 'bar\x0abaz'}))
    is_ok(bytes(buffer), b'event: foo\x0d\x0adata: bar\x0d\x0adata: baz\x0d\x0a\x0d\x0a', 'right event')
    event = parse_event(buffer)
    is_ok(event['type'], 'foo', 'right event type')
    is_ok(event['text'], 'bar\nbaz', 'right event text')
    is_ok(event['id'], None, 'no event id')
    is_ok(bytes(buffer), b'', 'buffer is empty')

    buffer = bytearray(build_event({'type': 'foo', 'text': 'bar\x0dbaz'}))
    is_ok(bytes(buffer), b'event: foo\x0d\x0adata: bar\x0d\x0adata: baz\x0d\x0a\x0d\x0a', 'right event')
    event = parse_event(buffer)
    is_ok(event['type'], 'foo', 'right event type')
    is_ok(event['text'], 'bar\nbaz', 'right event text')
    is_ok(event['id'], None, 'no event id')
    is_ok(bytes(buffer), b'', 'buffer is empty')

    buffer = bytearray(build_event({'type': 'foo', 'text': 'bar\x0d\x0abaz'}))
    is_ok(bytes(buffer), b'event: foo\x0d\x0adata: bar\x0d\x0adata: baz\x0d\x0a\x0d\x0a', 'right event')
    event = parse_event(buffer)
    is_ok(event['type'], 'foo', 'right event type')
    is_ok(event['text'], 'bar\nbaz', 'right event text')
    is_ok(event['id'], None, 'no event id')
    is_ok(bytes(buffer), b'', 'buffer is empty')

done_testing()
