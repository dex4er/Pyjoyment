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

:mod:`Pyjo.YAML` loads the YAML that configuration files and workflows use, a
subset of `YAML 1.2 <https://yaml.org>`_, which :mod:`Pyjoyment.Plugin.YAMLConfig`
reads, as Python has no YAML in its standard library:

* mappings and sequences in the block style, nested by their indentation, and
  a mapping that starts in an item of a sequence (``- name: value``);
* flow sequences and mappings, ``[a, b]`` and ``{a: 1}``, nested, and over
  several lines;
* scalars, plain, in single quotes (with ``''`` for a quote) and in double
  quotes (with the escapes ``\\n``, ``\\t``, ``\\xHH`` and the others of C),
  over several lines too, and the literal ``|`` and folded ``>`` block
  scalars, with their empty lines, and the indicators ``-`` and ``+`` that
  strip and keep the final line breaks;
* comments, documents that ``---`` starts and ``...`` ends, a scalar after
  ``---`` and the directive ``%YAML``.

A plain scalar has the type of the core schema of YAML 1.2: ``null`` and ``~``
are ``None``, ``true`` and ``false`` are booleans, and numbers, with ``0o`` and
``0x`` too, ``.inf`` and ``.nan``, are :class:`int` and :class:`float`, as
``404:`` is a key of :class:`int`. The words and the forms of YAML 1.1, as
``yes``, ``off``, ``0755`` for an octal number and an implicit date, are not of
the core schema, and stay strings or decimal numbers. A quoted scalar and a
block scalar are strings. ::

    # {'foo': [1, True, 'yes', '2']}
    load("foo:\\n  - 1\\n  - true\\n  - yes\\n  - '2'\\n")

A standard tag gives a scalar its type: ``!!str``, ``!!int``, ``!!float``,
``!!bool`` and ``!!null`` of YAML 1.2, and ``!!binary``, Base64 for
:class:`bytes`, and ``!!timestamp``, ISO 8601 for :class:`datetime.date` and
:class:`datetime.datetime`, of YAML 1.1. ::

    # {'port': '8080', 'key': b'hello', 'day': datetime.date(2001, 12, 14)}
    load('port: !!str 8080\\nkey: !!binary aGVsbG8=\\nday: !!timestamp 2001-12-14\\n')

An anchor ``&name`` names a node, a value or a key, in a block or a flow
collection, and an alias ``*name`` after it in the same document is the same
object; an anchor defined again names the node of the aliases after it. The
merge key ``<<`` of YAML 1.1 puts the keys of the mapping that it names, or of
a sequence of mappings, the earlier ones first, into the mapping, under the
keys of the mapping itself. ::

    # {'base': {'a': 1, 'b': 1}, 'copy': {'a': 1, 'b': 2}}
    load('base: &base\\n  a: 1\\n  b: 1\\ncopy:\\n  <<: *base\\n  b: 2\\n')

Other tags, complex keys and the indicator of the indentation of a block
scalar are not supported, and raise an error, as do lines that the subset
does not know.

See also
--------

:mod:`Pyjoyment.Plugin.YAMLConfig`, https://mojolicious.org.

Inspired by `CPAN::Meta::YAML <https://metacpan.org/pod/CPAN::Meta::YAML>`_
of Adam Kennedy and David Golden, which Mojolicious uses, whose regular
expressions of scalars and keys it borrows, with thanks.
"""

import Pyjo.Exception

import base64
import binascii
import datetime
import re

from collections.abc import Callable
from typing import Any, cast


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
_RE_BLANK = re.compile(r'^\s*(?:#.*)?\Z')

# Not in CPAN::Meta::YAML: the name of an anchor or an alias, an anchor of a key and an alias as a key
_ANCHOR = r'[^\s,\[\]{}]+'
_RE_KEY_ALIAS = re.compile(rf'^\s*\*({_ANCHOR}){_KEY_VALUE_SEPARATOR}')
_RE_KEY_ANCHOR = re.compile(rf'^(\s*)&({_ANCHOR})\s+')

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
    if re.fullmatch(r'~|null|Null|NULL', string):
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
        self.anchors: dict[str, Any] = {}
        self.lines = re.split(r'\r\r?\n|\r|\n', string.removeprefix('\ufeff'))

        # The line break at the end ends the last line, it does not start an empty one
        if self.lines[-1] == '':
            self.lines.pop()

    def alias(self, name: str) -> Any:
        if name not in self.anchors:
            raise _error(f"found an unknown alias '*{name}'")
        return self.anchors[name]

    def block(self, string: str, indent: int | None) -> str:
        if not (m := re.search(r'^([|>])([+-]?)\s*(?:#.*)?\Z', string)):
            raise _error(f"does not support a feature in line '{string}'")

        # The lines more indented than the key, with the empty ones among them
        lines = self.lines
        block: list[str] = []
        depth: int | None = None
        while lines:
            if not lines[0].strip():
                block.append('')
                lines.pop(0)
                continue
            if depth is None:
                if indent is not None and _indent(lines[0]) <= indent:
                    break
                depth = _indent(lines[0])
            if _indent(lines[0]) < depth:
                break
            block.append(lines.pop(0)[depth:])

        # The empty lines at the end, which the chomping indicator keeps, strips or clips to one line break
        trailing = len(block) - len(content := _rstrip_empty(block))
        text = '\n'.join(content) if m[1] == '|' else _fold(content)
        if m[2] == '-' or not content:
            return text
        return text + '\n' * (1 + trailing if m[2] == '+' else 1)

    def documents(self) -> list[Any]:
        documents: list[Any] = []
        explicit = False
        lines = self.lines

        # The directive of the version
        if self.skip() and re.search(r'^%YAML[: ][\d.]+', lines[0]):
            lines.pop(0)

        while self.skip():
            # The anchors of a document are its own
            self.anchors = {}

            # The start of a document, with a scalar after it
            if m := re.search(r'^---\s*(?:(.+?)\s*)?\Z', lines[0]):
                lines.pop(0)
                if m[1] is not None and not re.search(r'^(?:#.+|%YAML[: ][\d.]+)\Z', m[1]):
                    documents.append(self.scalar(m[1], None))
                    continue
                explicit = True

            # An empty document
            if not self.skip() or re.search(r'^(?:---|\.\.\.)', lines[0]):
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

            # A flow collection
            elif re.search(r'^\s*[\[{]', lines[0]):
                documents.append(self.scalar(lines.pop(0).strip(), None))

            # A mapping
            else:
                documents.append(self.mapping(_indent(lines[0])))

        return documents

    def end_of_document(self) -> bool:
        lines = self.lines
        if not self.skip():
            return True
        if not re.search(r'^(?:---|\.\.\.)', lines[0]):
            return False
        while lines and not lines[0].startswith('---'):
            lines.pop(0)
        return True

    def flow(self, string: str) -> Any:
        # The lines of the collection, until its brackets are closed
        text = string
        while (end := _flow_end(text)) is None:
            if not self.lines:
                raise _error(f"failed to find the end of the flow collection '{string}'")
            if not _RE_BLANK.search(line := self.lines.pop(0)):
                text += ' ' + line.strip()
        if (rest := text[end:].strip()) and not rest.startswith('#'):
            raise _error(f"found illegal characters after the flow collection '{text}'")
        return _Flow(text[:end], self).value()

    def mapping(self, indent: int, outer: int | None = None) -> dict[Any, Any]:
        mapping: dict[Any, Any] = {}
        merges: list[Any] = []
        lines = self.lines
        while not self.end_of_document():
            if (depth := _indent(lines[0])) < indent:
                break
            if depth > indent:
                raise _error(f"found bad indenting in line '{lines[0]}'")

            # Not in CPAN::Meta::YAML: the anchor of the key
            line = lines[0]
            anchor = None
            if m := _RE_KEY_ANCHOR.search(line):
                anchor = m[2]
                line = m[1] + line[m.end() :]

            # The key, quoted or not, or an alias, and the rest of the line
            if m := _RE_KEY_ALIAS.search(line):
                quote = '*'
                key = self.alias(m[1])
            elif re.search(r'^\s*[!&*]', line):
                raise _error(f"does not support a feature in line '{line}'")
            elif m := _key(line):
                quote = line.lstrip()[:1]
                if quote == "'":
                    key = _unquote_single(m[1])
                elif quote == '"':
                    key = _unquote_double(m[1])
                else:
                    key = _resolve(m[1].rstrip())
            elif re.search(r'^\s*\?', line):
                raise _error(f"does not support a feature in line '{line}'")
            else:
                raise _error(f"failed to classify line '{line}'")
            rest = line[m.end() :]
            lines.pop(0)
            try:
                hash(key)
            except TypeError:
                raise _error(f"found a key that is not hashable in line '{line}'") from None
            if anchor is not None:
                self.anchors[anchor] = key

            # A value on the line, or below it, or none
            value = self.scalar(rest, indent) if rest else self.value(indent)
            if key == '<<' and quote not in ("'", '"', '*'):
                merges.append(value)
            else:
                mapping[key] = value

        return _merge(mapping, merges)

    def plain(self, string: str, indent: int | None) -> str:
        if re.search(r'^(?:-(?:\s|$)|[@%`])', string) or re.search(r':(?:\s|$)', string):
            raise _error(f"found illegal characters in plain scalar: '{string}'")
        plain = re.sub(r'\s+#.*\Z', '', string)
        if plain != string or indent is None:
            return plain

        # The lines more indented than the key, folded, which a comment ends
        lines = self.lines
        empty = 0
        while lines and (indent < _indent(lines[0]) or not lines[0].strip()):
            line = lines[0].strip()
            if line.startswith('#'):
                break
            lines.pop(0)
            if not line:
                empty += 1
                continue
            if re.search(r':(?:\s|$)', line):
                raise _error(f"found illegal characters in plain scalar: '{line}'")
            continued = re.sub(r'\s+#.*\Z', '', line)
            plain += ('\n' * empty if empty else ' ') + continued
            empty = 0
            if continued != line:
                break
        return plain

    def quoted(self, string: str) -> str:
        double = string.startswith('"')
        pattern = _RE_DOUBLE if double else _RE_SINGLE

        # The lines of the scalar, until its quote is closed, folded
        text = string
        empty = 0
        while not (m := pattern.search(text)):
            if not self.lines:
                raise _error(f"failed to find the end of the quoted scalar '{string}'")
            line = self.lines.pop(0).strip()
            if not line:
                empty += 1
                continue
            text = text.rstrip(' \t')
            if double and re.search(r'(?<!\\)(?:\\\\)*\\\Z', text) and not empty:
                text = text[:-1] + line
            else:
                text += ('\n' * empty if empty else ' ') + line
            empty = 0
        return _unquote_double(m[1]) if double else _unquote_single(m[1])

    def scalar(self, string: str, indent: int | None, item: bool = False) -> Any:
        string = string.rstrip()

        # Not in CPAN::Meta::YAML: an alias, the node of its anchor
        if string.startswith('*'):
            if not (m := re.search(rf'^\*({_ANCHOR})(?:\s+#.*)?\Z', string)):
                raise _error(f"found illegal characters after the alias '{string}'")
            return self.alias(m[1])

        # Not in CPAN::Meta::YAML: the properties of a node, an anchor and a standard tag, in either order
        anchor = tag = None
        while m := re.search(rf'^(?:&({_ANCHOR})|!!(\w+))(?:\s+|\Z)', string):
            if m[1] is not None and anchor is None:
                anchor = m[1]
            elif m[2] is not None and tag is None:
                tag = m[2]
            else:
                raise _error(f"found a property twice in line '{string}'")
            string = string[m.end() :]

        # A node below the anchor
        if anchor is not None and tag is None and (not string or string.startswith('#')):
            value = self.value(-1 if indent is None else indent, item)

        # The tag, which gives a scalar its type
        elif tag is not None:
            if (convert := _TAGS.get(tag)) is None or string.startswith(('[', '{')):
                raise _error(f"does not support a feature in line '!!{tag} {string}'")
            text = self.text(string, indent, False)
            try:
                value = convert(text)
            except ValueError:
                raise _error(f"found an invalid value of the tag !!{tag}: '{text}'") from None

        else:
            value = self.text(string, indent, True)

        # Unlike PyYAML: an anchor can be defined again, as in YAML 1.2, and an alias is the node of the last one
        if anchor is not None:
            self.anchors[anchor] = value
        return value

    def sequence(self, indent: int, outer: int | None = None) -> list[Any]:
        sequence: list[Any] = []
        lines = self.lines
        while not self.end_of_document():
            if (depth := _indent(lines[0])) < indent:
                break
            if depth > indent:
                raise _error(f"found bad indenting in line '{lines[0]}'")

            # A mapping that starts on the line of the item
            if (m := re.search(r'^(\s*-\s+)(?![\[{!|>])', lines[0])) and _is_key(lines[0][m.end() :]):
                lines[0] = lines[0].replace('-', ' ', 1)
                sequence.append(self.mapping(len(m[1]), indent))

            # An item whose value is below it, or none
            elif re.search(r'^\s*-\s*(?:#.*)?\Z', lines[0]):
                lines.pop(0)
                sequence.append(self.value(indent, True))

            # An item with a value
            elif m := re.search(r'^\s*-\s+(.+?)\s*\Z', lines[0]):
                lines.pop(0)
                sequence.append(self.scalar(m[1], indent, True))

            # The key of a mapping after a sequence at its indentation
            elif outer is not None and indent == outer:
                break

            else:
                raise _error(f"failed to classify line '{lines[0]}'")

        return sequence

    def skip(self) -> bool:
        # The empty lines and the lines of comments, before the next line of the structure
        lines = self.lines
        while lines and _RE_BLANK.search(lines[0]):
            lines.pop(0)
        return bool(lines)

    def text(self, string: str, indent: int | None, resolve: bool) -> Any:
        if string.startswith(('[', '{')):
            return self.flow(string)
        if string.startswith(("'", '"')):
            return self.quoted(string)
        if re.search(r'^[!&*]', string):
            raise _error(f"does not support a feature in line '{string}'")
        if string.startswith(('|', '>')):
            return self.block(string, indent)
        plain = self.plain(string, indent)
        return _resolve(plain) if resolve else plain

    def value(self, indent: int, item: bool = False) -> Any:
        # A sequence, a mapping or a scalar below its key or its item, or nothing
        lines = self.lines
        if not self.skip() or re.search(r'^(?:---|\.\.\.)', lines[0]):
            return None
        depth = _indent(lines[0])
        if m := re.search(r'^(\s*)-(?:\s|\Z)', lines[0]):
            if item and len(m[1]) == indent:
                return None
            if len(m[1]) < indent or item and len(m[1]) <= indent:
                return None
            return self.sequence(len(m[1]), indent)
        if depth <= indent:
            return None
        if _is_key(lines[0]):
            return self.mapping(depth, indent)
        if re.search(r'^\s*\?', lines[0]):
            raise _error(f"does not support a feature in line '{lines[0]}'")
        return self.scalar(lines.pop(0).strip(), indent)


class _Flow:
    # A flow collection, in one string, with the anchors of its document
    def __init__(self, text: str, loader: _Loader) -> None:
        self.loader = loader
        self.text = text
        self.pos = 0

    def entry(self, end: str) -> tuple[Any, bool]:
        # A node, or a pair of a key and a value, as a mapping is an entry of a sequence
        if (c := self.peek()) in ('"', "'"):
            key: Any = self.quoted()
        elif c in ('[', '{', '*', '&'):
            return self.node(), False
        else:
            key = self.plain(end)
        if self.peek() == ':':
            self.pos += 1
            value = None if self.peek() in (',', end) else self.node()
            return {key if c in ('"', "'") else _resolve(key): value}, True
        return (key if c in ('"', "'") else _resolve(key)), False

    def error(self) -> Pyjo.Exception.object:
        return _error(f"failed to parse the flow collection '{self.text}' at offset {self.pos}")

    def mapping(self) -> dict[Any, Any]:
        mapping: dict[Any, Any] = {}
        merges: list[Any] = []
        self.pos += 1
        while (c := self.peek()) != '}':
            key = self.quoted() if c in ('"', "'") else _resolve(self.plain('}'))
            value = None
            if self.peek() == ':':
                self.pos += 1
                value = None if self.peek() in (',', '}') else self.node()
            if key == '<<' and c not in ('"', "'"):
                merges.append(value)
            else:
                mapping[key] = value
            if self.peek() == ',':
                self.pos += 1
            elif self.peek() != '}':
                raise self.error()
        self.pos += 1
        return _merge(mapping, merges)

    def name(self) -> str:
        # The name of an anchor or an alias, after its indicator
        if not (m := re.compile(_ANCHOR).match(self.text, self.pos + 1)):
            raise self.error()
        self.pos = m.end()
        return m[0]

    def node(self) -> Any:
        c = self.peek()
        if c == '*':
            return self.loader.alias(self.name())
        if c == '&':
            anchor = self.name()
            self.loader.anchors[anchor] = value = self.node()
            return value
        if c == '[':
            return self.sequence()
        if c == '{':
            return self.mapping()
        if c in ('"', "'"):
            return self.quoted()
        return _resolve(self.plain(None))

    def peek(self) -> str:
        text = self.text
        while self.pos < len(text) and text[self.pos] in ' \t':
            self.pos += 1
        if self.pos >= len(text):
            raise self.error()
        return text[self.pos]

    def plain(self, end: str | None) -> str:
        text = self.text
        start = self.pos
        while self.pos < len(text):
            c = text[self.pos]
            if c in ',[]{}' or c == ':' and (self.pos + 1 == len(text) or text[self.pos + 1] in ' ,[]{}'):
                break
            self.pos += 1
        plain = text[start : self.pos].strip()
        if not plain or re.search(r'^[!&*@`|>%#]|^-(?:\s|$)', plain):
            raise self.error()
        return plain

    def quoted(self) -> str:
        text = self.text
        quote = text[self.pos]
        pattern = _DOUBLE_QUOTED if quote == '"' else _SINGLE_QUOTED
        if not (m := re.compile(pattern).match(text, self.pos)):
            raise self.error()
        self.pos = m.end()
        return _unquote_double(m[1]) if quote == '"' else _unquote_single(m[1])

    def sequence(self) -> list[Any]:
        sequence: list[Any] = []
        self.pos += 1
        while self.peek() != ']':
            sequence.append(self.entry(']')[0])
            if self.peek() == ',':
                self.pos += 1
            elif self.peek() != ']':
                raise self.error()
        self.pos += 1
        return sequence

    def value(self) -> Any:
        value = self.node()
        if self.text[self.pos :].strip():
            raise self.error()
        return value


# Not in CPAN::Meta::YAML: the merge keys of a mapping, << of YAML 1.1, which PyYAML reads too: the keys of the
# mappings that they name, of the earlier ones first, with the keys of the mapping itself over them
def _merge(mapping: dict[Any, Any], merges: list[Any]) -> dict[Any, Any]:
    if not merges:
        return mapping
    merged: dict[Any, Any] = {}
    for merge in merges:
        sources: list[Any] = cast(list[Any], merge) if isinstance(merge, list) else [merge]
        for source in reversed(sources):
            if not isinstance(source, dict):
                raise _error('found a merge key with a value that is not a mapping or a sequence of mappings')
            merged.update(cast(dict[Any, Any], source))
    merged.update(mapping)
    return merged


# The key at the start of a line, quoted, which only the pattern of its quotes reads, or not
def _key(line: str) -> re.Match[str] | None:
    if (stripped := line.lstrip()).startswith("'"):
        return _RE_KEY_SINGLE.search(line)
    if stripped.startswith('"'):
        return _RE_KEY_DOUBLE.search(line)
    return _RE_KEY_UNQUOTED.search(line)


def _is_key(line: str) -> bool:
    line = _RE_KEY_ANCHOR.sub(r'\1', line, count=1)
    return _key(line) is not None or _RE_KEY_ALIAS.search(line) is not None


# The end of the flow collection at the start of a string, after its closing bracket, or None while it is open
def _flow_end(text: str) -> int | None:
    depth = 0
    quote = ''
    i = 0
    while i < len(text):
        c = text[i]
        if quote == '"':
            if c == '\\':
                i += 1
            elif c == '"':
                quote = ''
        elif quote == "'":
            if c == "'" and text[i + 1 : i + 2] == "'":
                i += 1
            elif c == "'":
                quote = ''
        elif c in ('"', "'"):
            quote = c
        elif c in '[{':
            depth += 1
        elif c in ']}':
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return None


# The lines of a folded block scalar: a line break between two lines is a space, an empty line a line break, and the
# lines more indented keep their line breaks
def _fold(lines: list[str]) -> str:
    folded = ''
    previous: str | None = None
    empty = 0
    for line in lines:
        if not line:
            empty += 1
            continue
        if previous is None:
            folded = '\n' * empty + line
        elif not empty and not previous[:1].isspace() and not line[:1].isspace():
            folded += ' ' + line
        elif previous[:1].isspace() or line[:1].isspace():
            folded += '\n' * (1 + empty) + line
        else:
            folded += '\n' * empty + line
        previous = line
        empty = 0
    return folded


def _rstrip_empty(lines: list[str]) -> list[str]:
    end = len(lines)
    while end and not lines[end - 1]:
        end -= 1
    return lines[:end]
