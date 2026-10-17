"""
Pyjo.YAML - Minimal YAML loader
===============================
::

    from Pyjo.YAML import load, load_all

    config = load(\"\"\"\\
    foo: bar
    list:
      - one
      - two
    \"\"\")

    documents = load_all('--- first\\n--- second\\n')

:mod:`Pyjo.YAML` loads the subset of `YAML <https://yaml.org>`_ that
configuration files need, the subset of ``CPAN::Meta::YAML`` and
``YAML::Tiny`` of Perl, which :mod:`Pyjoyment.Plugin.YAMLConfig` reads, as
Python has no YAML in its standard library:

* mappings and sequences in the block style, nested by their indentation, and
  a mapping that starts in an item of a sequence (``- name: value``);
* scalars, plain, in single quotes (with ``''`` for a quote) and in double
  quotes (with the escapes ``\\n``, ``\\t``, ``\\xHH`` and the others of
  C), the literal ``|`` and folded ``>`` block scalars, with the indicator
  ``-`` that chomps the final line break, ``~`` for ``None``, and ``{}`` and
  ``[]`` for an empty mapping and sequence;
* comments, documents that ``---`` starts and ``...`` ends, a scalar after
  ``---`` and the directive ``%YAML``.

A plain scalar of a value has the type of the core schema of YAML 1.2:
``null`` and ``~`` are ``None``, ``true`` and ``false`` are booleans, and
numbers, with ``0o`` and ``0x`` too, ``.inf`` and ``.nan``, are :class:`int`
and :class:`float`, where the words of YAML 1.1, as ``yes`` and ``off``, stay
strings. A quoted scalar, a block scalar and a key are strings.

A standard tag gives a scalar its type: ``!!str``, ``!!int``, ``!!float``,
``!!bool`` and ``!!null`` of YAML 1.2, and ``!!binary``, Base64 for
:class:`bytes`, and ``!!timestamp``, ISO 8601 for :class:`datetime.date` and
:class:`datetime.datetime`, of YAML 1.1. ::

    # {'port': '8080', 'key': b'hello', 'day': datetime.date(2001, 12, 14)}
    load('port: !!str 8080\\nkey: !!binary aGVsbG8=\\nday: !!timestamp 2001-12-14\\n')

Flow collections other than ``{}`` and ``[]``, anchors, aliases, other tags
and complex keys are not supported, and raise an error, as do lines that the
subset does not know. ::

    # {'foo': [1, True, 'yes', '2']}
    load('foo: [1, true]')    # raises an exception
    load("foo:\\n  - 1\\n  - true\\n  - yes\\n  - '2'\\n")

See also
--------

:mod:`Pyjoyment.Plugin.YAMLConfig`, https://mojolicious.org.

Inspired by `CPAN::Meta::YAML <https://metacpan.org/pod/CPAN::Meta::YAML>`_
of Adam Kennedy and David Golden, whose regular expressions of scalars and keys
it borrows, with thanks.
"""

import Pyjo.Exception

import base64
import binascii
import datetime
import re

from collections.abc import Callable
from typing import Any


# The regular expressions of CPAN::Meta::YAML
_DOUBLE_QUOTED = r'"([^\\"]*(?:\\.[^\\"]*)*)"'
_SINGLE_QUOTED = r"'([^']*(?:''[^']*)*)'"
_UNQUOTED_KEY = r'([^:]+(?::+\S(?:[^:]*|.*?(?=:)))*)(?=\s*:(?:\s+|$))'
_TRAILING_COMMENT = r'(?:\s+#.*)?'
_KEY_VALUE_SEPARATOR = r'\s*:(?:\s+(?:#.*)?|$)'

_RE_DOUBLE = re.compile(rf'^{_DOUBLE_QUOTED}{_TRAILING_COMMENT}\Z')
_RE_SINGLE = re.compile(rf'^{_SINGLE_QUOTED}{_TRAILING_COMMENT}\Z')
_RE_KEY_DOUBLE = re.compile(rf'^\s*{_DOUBLE_QUOTED}{_KEY_VALUE_SEPARATOR}')
_RE_KEY_SINGLE = re.compile(rf'^\s*{_SINGLE_QUOTED}{_KEY_VALUE_SEPARATOR}')
_RE_KEY_UNQUOTED = re.compile(rf'^\s*{_UNQUOTED_KEY}{_KEY_VALUE_SEPARATOR}')

_ESCAPES = {
    '0': '\x00',
    'N': '\x85',
    'a': '\x07',
    'b': '\x08',
    'e': '\x1b',
    'f': '\x0c',
    'n': '\x0a',
    'r': '\x0d',
    't': '\x09',
    'v': '\x0b',
    'z': '\x00',
    '\\': '\\',
}


def load(string: str) -> Any:
    """::

        value = load(string)

    Load a YAML string and return its document, or its last one when there
    are several, as the ``Load`` of ``YAML`` of Perl does, or ``None`` for an
    empty string. ::

        # {'foo': 'bar'}
        load('foo: bar')
    """
    documents = load_all(string)
    return documents[-1] if documents else None


def load_all(string: str) -> list[Any]:
    """::

        values = load_all(string)

    Load a YAML string and return a list of all its documents. ::

        # ['first', 'second']
        load_all('--- first\\n--- second\\n')
    """
    return _Loader(string).documents()


def _error(message: str) -> Pyjo.Exception.object:
    return Pyjo.Exception.new(f'YAML {message}')


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def _unquote_double(string: str) -> str:
    def unescape(m: re.Match[str]) -> str:
        return chr(int(m[1], 16)) if m[1] is not None else _ESCAPES.get(m[2], m[2])

    return re.sub(r'\\(?:x([0-9a-fA-F]{2})|(["\\0Nabefnrtvz]))', unescape, string)


# Not in CPAN::Meta::YAML: the type of a plain scalar of the core schema of YAML 1.2, where CPAN::Meta::YAML keeps a
# string, as Perl takes "8080" for 8080, and Python does not
def _resolve(string: str) -> Any:
    if re.fullmatch(r'null|Null|NULL', string):
        return None
    if re.fullmatch(r'true|True|TRUE', string):
        return True
    if re.fullmatch(r'false|False|FALSE', string):
        return False
    if re.fullmatch(r'[-+]?[0-9]+', string):
        return int(string)
    if re.fullmatch(r'0o[0-7]+', string):
        return int(string[2:], 8)
    if re.fullmatch(r'0x[0-9a-fA-F]+', string):
        return int(string[2:], 16)
    if re.fullmatch(r'[-+]?(?:\.[0-9]+|[0-9]+(?:\.[0-9]*)?)(?:[eE][-+]?[0-9]+)?', string):
        return float(string)
    if m := re.fullmatch(r'([-+]?)\.(?:inf|Inf|INF)', string):
        return float(f'{m[1]}inf')
    if re.fullmatch(r'\.(?:nan|NaN|NAN)', string):
        return float('nan')
    return string


# The standard tags of the scalars, of the core schema of YAML 1.2 and, for the types of Python they have, of YAML 1.1
def _tag_binary(value: str) -> bytes:
    try:
        return base64.b64decode(re.sub(r'\s+', '', value), validate=True)
    except binascii.Error as e:
        raise ValueError(str(e)) from None


def _tag_bool(value: str) -> bool:
    if (resolved := _resolve(value)) is True or resolved is False:
        return resolved
    raise ValueError(value)


def _tag_float(value: str) -> float:
    if isinstance(resolved := _resolve(value), (int, float)) and not isinstance(resolved, bool):
        return float(resolved)
    raise ValueError(value)


def _tag_int(value: str) -> int:
    if isinstance(resolved := _resolve(value), int) and not isinstance(resolved, bool):
        return resolved
    raise ValueError(value)


def _tag_null(value: str) -> None:
    if value not in ('', '~') and _resolve(value) is not None:
        raise ValueError(value)


def _tag_timestamp(value: str) -> datetime.date | datetime.datetime:
    if re.fullmatch(r'\d{4}-\d\d-\d\d', value):
        return datetime.date.fromisoformat(value)
    return datetime.datetime.fromisoformat(re.sub(r'(?<=\d)[tT](?=\d)', 'T', value))


_TAGS: dict[str, Callable[[str], Any]] = {
    'binary': _tag_binary,
    'bool': _tag_bool,
    'float': _tag_float,
    'int': _tag_int,
    'null': _tag_null,
    'str': str,
    'timestamp': _tag_timestamp,
}


def _unquote_single(string: str) -> str:
    return string.replace("''", "'")


class _Loader:
    def __init__(self, string: str) -> None:
        string = string.removeprefix('﻿')

        # The lines that are not empty or only a comment
        lines = [line for line in re.split(r'\r\r?\n|\r|\n', string) if not re.search(r'^\s*(?:#.*)?\Z', line)]

        # The directive of the version
        if lines and re.search(r'^%YAML[: ][\d.]+', lines[0]):
            lines.pop(0)

        self.lines = lines

    def documents(self) -> list[Any]:
        documents: list[Any] = []
        explicit = False
        lines = self.lines
        while lines:
            # The start of a document, with a scalar after it
            if m := re.search(r'^---\s*(?:(.+?)\s*)?\Z', lines[0]):
                lines.pop(0)
                if m[1] is not None and not re.search(r'^(?:#.+|%YAML[: ][\d.]+)\Z', m[1]):
                    documents.append(self.scalar(m[1], None))
                    continue
                explicit = True

            # An empty document
            if not lines or re.search(r'^(?:---|\.\.\.)', lines[0]):
                documents.append(None)
                while lines and not lines[0].startswith('---'):
                    lines.pop(0)
                explicit = False

            # Only the first document can do without its start
            elif not explicit and documents:
                raise _error(f"failed to classify the line '{lines[0]}'")

            # A sequence
            elif re.search(r'^\s*-(?:\s|$|-+$)', lines[0]):
                documents.append(self.sequence(0))

            # A mapping
            else:
                documents.append(self.mapping(_indent(lines[0])))

        return documents

    def end_of_document(self) -> bool:
        lines = self.lines
        if not re.search(r'^(?:---|\.\.\.)', lines[0]):
            return False
        while lines and not lines[0].startswith('---'):
            lines.pop(0)
        return True

    def mapping(self, indent: int, outer: int | None = None) -> dict[str, Any]:
        mapping: dict[str, Any] = {}
        lines = self.lines
        while lines and not self.end_of_document():
            if (depth := _indent(lines[0])) < indent:
                break
            if depth > indent:
                raise _error(f"found bad indenting in line '{lines[0]}'")

            # The key, quoted or not, and the rest of the line
            line = lines[0]
            if m := _RE_KEY_SINGLE.search(line):
                key = _unquote_single(m[1])
            elif m := _RE_KEY_DOUBLE.search(line):
                key = _unquote_double(m[1])
            elif m := _RE_KEY_UNQUOTED.search(line):
                key = m[1].rstrip()
            elif re.search(r'^\s*\?', line):
                raise _error(f"does not support a feature in line '{line}'")
            else:
                raise _error(f"failed to classify line '{line}'")
            rest = line[m.end() :]

            # A value on the line
            if rest:
                lines.pop(0)
                mapping[key] = self.scalar(rest, indent)
                continue

            # A value on the lines below, or none
            lines.pop(0)
            if not lines:
                mapping[key] = None
            elif m := re.search(r'^(\s*)-', lines[0]):
                mapping[key] = self.sequence(len(m[1]), indent)
            elif (depth := _indent(lines[0])) <= indent:
                mapping[key] = None
            else:
                mapping[key] = self.mapping(depth, indent)

        return mapping

    def scalar(self, string: str, indent: int | None) -> Any:
        string = string.rstrip()

        # Not in CPAN::Meta::YAML: a standard tag of a scalar, which gives it its type
        if m := re.search(r'^!!(\w+)(?:\s+|\Z)', string):
            if (tag := _TAGS.get(m[1])) is None:
                raise _error(f"does not support a feature in line '{string}'")
            value = self.text(string[m.end() :], indent, False)
            try:
                return tag(value)
            except ValueError:
                raise _error(f"found an invalid value of the tag !!{m[1]}: '{value}'") from None

        return self.text(string, indent, True)

    def text(self, string: str, indent: int | None, resolve: bool) -> Any:
        if string == '~' and resolve:
            return None
        if m := _RE_SINGLE.search(string):
            return _unquote_single(m[1])
        if m := _RE_DOUBLE.search(string):
            return _unquote_double(m[1])
        if re.search(r'^[\'"!&*]', string):
            raise _error(f"does not support a feature in line '{string}'")
        if re.search(r'^\{\}(?:\s+#.*)?\Z', string) and resolve:
            return {}
        if re.search(r'^\[\](?:\s+#.*)?\Z', string) and resolve:
            return []

        # A plain scalar
        if not string.startswith(('|', '>')):
            if re.search(r'^(?:-(?:\s|$)|[@%`{\[])', string) or re.search(r':(?:\s|$)', string):
                raise _error(f"found illegal characters in plain scalar: '{string}'")
            plain = re.sub(r'\s+#.*\Z', '', string)
            return _resolve(plain) if resolve else plain

        # A block scalar, more indented than its key
        lines = self.lines
        if not lines:
            raise _error('failed to find multi-line scalar content')
        depth = _indent(lines[0])
        if indent is not None and depth <= indent:
            raise _error(f"found bad indenting in line '{lines[0]}'")
        block: list[str] = []
        while lines and _indent(lines[0]) >= depth:
            block.append(lines.pop(0)[depth:])
        join = ' ' if string.startswith('>') else '\n'
        end = '' if string[1:2] == '-' else '\n'
        return join.join(block) + end

    def sequence(self, indent: int, outer: int | None = None) -> list[Any]:
        sequence: list[Any] = []
        lines = self.lines
        while lines and not self.end_of_document():
            if (depth := _indent(lines[0])) < indent:
                break
            if depth > indent:
                raise _error(f"found bad indenting in line '{lines[0]}'")

            # A mapping that starts on the line of the item
            if m := re.search(r'^(\s*-\s+)[^\'"]\S*\s*:(?:\s+|$)', lines[0]):
                lines[0] = lines[0].replace('-', ' ', 1)
                sequence.append(self.mapping(len(m[1]), indent))

            # An item whose value is on the lines below
            elif re.search(r'^\s*-\s*\Z', lines[0]):
                lines.pop(0)
                if not lines:
                    sequence.append(None)
                elif m := re.search(r'^(\s*)-', lines[0]):
                    sequence.append(None if len(m[1]) == indent else self.sequence(len(m[1]), indent))
                else:
                    sequence.append(self.mapping(_indent(lines[0]), indent))

            # An item with a value
            elif m := re.search(r'^\s*-\s*(.+?)\s*\Z', lines[0]):
                lines.pop(0)
                sequence.append(self.scalar(m[1], indent))

            # The key of a mapping after a sequence at its indentation
            elif outer is not None and indent == outer:
                break

            else:
                raise _error(f"failed to classify line '{lines[0]}'")

        return sequence
