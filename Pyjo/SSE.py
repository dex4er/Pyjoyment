r"""
Pyjo.SSE - Server-Sent Events
=============================
::

    from Pyjo.SSE import build_event, parse_event

:mod:`Pyjo.SSE` implements the Server-Sent Events protocol. Note that this
module is **EXPERIMENTAL** and may change without warning!

An event is a :class:`dict` with the keys ``type``, ``text``, ``id`` and,
when it is built, ``comment``.

Functions
---------

:mod:`Pyjo.SSE` implements the following functions, which can be imported
individually.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::SSE <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/SSE.pm>`_
of Mojolicious 9.49.
"""

import Pyjo.String.Unicode

from Pyjo.Util import decode, encode

import re

from collections.abc import Mapping
from typing import Any, TypedDict


__all__ = ['Event', 'build_event', 'parse_event']


class Event(TypedDict):
    """A parsed Server-Sent Event."""

    id: str | None
    type: str
    text: str


SPLIT_RE = re.compile(r'(?:\x0d\x0a|(?<!\x0d)\x0a|\x0d(?!\x0a))')
EVENT_RE = re.compile(rb'(.*?)(?:(?:\x0d\x0a|(?<!\x0d)\x0a|\x0d(?!\x0a)){2})', re.S)


def build_event(event: Mapping[str, Any]) -> bytes:
    r"""::

        data = build_event({'type': 'foo', 'text': 'bar', 'id': 23})

    Build Server-Sent Event.
    """
    data = _split(event.get('text'))
    comment = _split(event.get('comment'))

    parts: list[str] = []
    if len(comment):
        parts.extend(f': {line}' for line in comment)
    else:
        if event.get('type') is not None:
            parts.append(f'event: {event["type"]}')
        parts.extend(f'data: {line}' for line in data)
        if event.get('id') is not None:
            parts.append(f'id: {event["id"]}')

    return encode('UTF-8', '\x0d\x0a'.join([*parts, '', '']))


# Unlike Mojolicious: the buffer is a bytearray, which parse_event changes, where Mojo takes a reference to a string
def parse_event(buffer: bytearray) -> Event | None:
    r"""::

        event = parse_event(bytearray(b'data: bar\r\n\r\n'))

    Parse Server-Sent Event from a :class:`bytearray`, which loses the parsed
    event. Returns ``None`` if no complete event was found.
    """
    event: Event = {'id': None, 'type': 'message', 'text': ''}

    # A copy is matched, as the bytearray cannot be resized while a regular expression scans it
    while m := EVENT_RE.match(bytes(buffer)):
        del buffer[: m.end()]

        # Skip lines with encoding errors
        if (lines := decode('UTF-8', m[1])) is None:
            continue

        # Skip comments
        if re.match(r'\s*:', lines):
            continue

        first = 0
        for line in _split(lines):
            if m := re.fullmatch(r'event(?::\s*(\S.*))?', line):
                event['type'] = m[1] if m[1] is not None else 'message'
            elif m := re.fullmatch(r'data(?::\s*(.*))?', line):
                event['text'] += ('\n' if first else '') + (m[1] if m[1] is not None else '')
                first += 1
            elif m := re.fullmatch(r'id(?::\s*(.*))?', line):
                event['id'] = m[1]

        return event

    return None


# Perl's split of the lines, which leaves out the empty ones at the end
def _split(text: Any) -> list[str]:
    if text is None:
        return []
    return [str(line) for line in Pyjo.String.Unicode.u(str(text)).split(SPLIT_RE) if line is not None]
