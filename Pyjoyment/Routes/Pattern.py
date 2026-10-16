"""
Pyjoyment.Routes.Pattern - Route pattern
========================================
::

    import Pyjoyment.Routes.Pattern

    # Create pattern
    pattern = Pyjoyment.Routes.Pattern.new('/test/:name')

    # Match routes
    captures = pattern.match('/test/sebastian')
    print(captures['name'])

:mod:`Pyjoyment.Routes.Pattern` is the core of :mod:`Pyjoyment.Routes`.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojolicious::Routes::Pattern
<https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojolicious/Routes/Pattern.pm>`_ of Mojolicious 9.49.
"""

import Pyjo.Base

import re

from typing import Any, Self


# A constraint is a regular expression, as a string or compiled, a list of alternatives, or for the format True to
# detect any and False to detect none
type Constraint = str | re.Pattern[str] | list[str] | bool

# A token of the tree is a list of its kind and its values, which the tokenizer changes as it reads the characters:
# ['text', '/foo'], ['slash'] or ['placeholder', [name, type], 'relaxed' | 'wildcard']
type Token = list[Any]


class Pyjoyment_Routes_Pattern(Pyjo.Base.object):
    """
    :mod:`Pyjoyment.Routes.Pattern` inherits all methods from :mod:`Pyjo.Base`
    and implements the following new ones.
    """

    def __init__(self, pattern: str | None = None, /, **constraints: Constraint) -> None:
        """::

            pattern = Pyjoyment.Routes.Pattern.new()
            pattern = Pyjoyment.Routes.Pattern.new('/users/:id')
            pattern = Pyjoyment.Routes.Pattern.new('/user/:id', id=re.compile(r'\\d+'))
            pattern = Pyjoyment.Routes.Pattern.new(format=['json', 'yaml'])

        Construct a new :mod:`Pyjoyment.Routes.Pattern` object and
        :meth:`parse` pattern if necessary.
        """
        self.constraints: dict[str, Constraint] = {}
        """::

            constraints = pattern.constraints
            pattern.constraints = {'foo': re.compile(r'\\w+')}

        Regular expression constraints.
        """

        self.defaults: dict[str, Any] = {}
        """::

            defaults = pattern.defaults
            pattern.defaults = {'foo': 'bar'}

        Default parameters.
        """

        self.placeholder_start = ':'
        """::

            start = pattern.placeholder_start
            pattern.placeholder_start = ':'

        Character indicating a placeholder, defaults to ``:``.
        """

        self.placeholders: list[str] = []
        """::

            placeholders = pattern.placeholders
            pattern.placeholders = ['foo', 'bar']

        Placeholder names.
        """

        self.quote_end = '>'
        """::

            end = pattern.quote_end
            pattern.quote_end = '}'

        Character indicating the end of a quoted placeholder, defaults to ``>``.
        """

        self.quote_start = '<'
        """::

            start = pattern.quote_start
            pattern.quote_start = '{'

        Character indicating the start of a quoted placeholder, defaults to
        ``<``.
        """

        self.regex: re.Pattern[str] | None = None
        """::

            regex = pattern.regex
            pattern.regex = regex

        Pattern in compiled regular expression form.
        """

        self.relaxed_start = '#'
        """::

            start = pattern.relaxed_start
            pattern.relaxed_start = '*'

        Character indicating a relaxed placeholder, defaults to ``#``.
        """

        self.tree: list[Token] = []
        """::

            tree = pattern.tree
            pattern.tree = [['text', '/foo']]

        Pattern in parsed form. Note that this structure should only be used
        very carefully since it is very dynamic.
        """

        self.type_start = ':'
        """::

            start = pattern.type_start
            pattern.type_start = '|'

        Character indicating the start of a placeholder type, defaults to ``:``.
        """

        self.types: dict[str, Constraint] = {}
        """::

            types = pattern.types
            pattern.types = {'int': re.compile(r'[0-9]+')}

        Placeholder types.
        """

        self.unparsed: str | None = None
        """::

            unparsed = pattern.unparsed
            pattern.unparsed = '/:foo/:bar'

        Raw unparsed pattern.
        """

        self.wildcard_start = '*'
        """::

            start = pattern.wildcard_start
            pattern.wildcard_start = '*'

        Character indicating the start of a wildcard placeholder, defaults to
        ``*``.
        """

        if pattern is not None or constraints:
            self.parse(pattern, **constraints)

    def match(self, path: str, detect: bool = False) -> dict[str, Any] | None:
        """::

            captures = pattern.match('/foo/bar')
            captures = pattern.match('/foo/bar', True)

        Match pattern against entire path, format detection is disabled by
        default.
        """
        if (result := self.match_partial(path, detect)) is None:
            return None
        captures, path = result
        # Unlike Mojolicious: a rest of "0" is no match, which Mojo's !$path takes for an empty one, as 0 is false
        return captures if not path or path == '/' else None

    def match_partial(self, path: str, detect: bool = False) -> tuple[dict[str, Any], str] | None:
        """::

            captures, path = pattern.match_partial(path)
            captures, path = pattern.match_partial(path, True)

        Match pattern against path and return the captures with the rest of the
        path, without the matching parts, format detection is disabled by
        default.
        """
        # Compile on demand
        if (regex := self.regex) is None:
            regex = self._compile(detect)

        if (m := regex.match(path)) is None:
            return None
        groups = list(m.groups())
        captures = {**self.defaults}
        for placeholder in [*self.placeholders, 'format']:
            if not groups:
                break
            if (capture := groups.pop(0)) is not None:
                captures[placeholder] = capture

        return captures, path[m.end() :]

    def parse(self, pattern: str | None = None, /, **constraints: Constraint) -> Self:
        """::

            pattern = pattern.parse('/user/:id')
            pattern = pattern.parse('/user/:id', id=re.compile(r'\\d+'))
            pattern = pattern.parse(format=['json', 'yaml'])

        Parse pattern.
        """
        pattern = re.sub(r'^/*|/+', '/', pattern if pattern is not None else '/')
        self.constraints = constraints
        if pattern == '/':
            return self

        return self._tokenize(re.sub(r'/$', '', pattern, count=1))

    def render(self, values: dict[str, Any] | None = None, endpoint: bool = False) -> str:
        """::

            path = pattern.render({'id': 24})
            path = pattern.render({'id': 24}, True)

        Render pattern into a path with parameters, format rendering is
        disabled by default.
        """
        values = values if values is not None else {}

        # Placeholders can only be optional without a format
        optional = not (format := values.get('format'))

        parts: list[str] = []
        for token in reversed(self.tree):
            op = token[0]
            part = ''

            # Text
            if op == 'text':
                part, optional = token[1], False

            # Slash
            elif op == 'slash':
                if not optional:
                    part = '/'

            # Placeholder
            else:
                name = token[1][0]
                default = self.defaults.get(name)
                value = values.get(name)
                part = str(value if value is not None else default if default is not None else '')
                if default is None or str(default) != part:
                    optional = False
                elif optional:
                    part = ''

            parts.append(part)

        # Format can be optional
        path = ''.join(reversed(parts))
        return f'{path}.{format}' if endpoint and format else path

    def _compile(self, detect: bool) -> re.Pattern[str]:
        constraints = self.constraints
        defaults = self.defaults
        types = self.types

        block = regex = ''
        optional = True
        for token in reversed(self.tree):
            op = token[0]
            part = ''

            # Text
            if op == 'text':
                part, optional = re.escape(token[1]), False

            # Slash
            elif op == 'slash':
                regex = (f'(?:/{block})?' if optional else f'/{block}') + regex
                block, optional = '', True
                continue

            # Placeholder
            else:
                value: list[str] = token[1]
                if len(value) > 1:
                    part = _compile_req(types.get(value[1], '?!'))
                else:
                    type = token[2] if len(token) > 2 else None
                    part = ('([^/]+)' if type == 'relaxed' else '(.+)') if type else '([^/.]+)'

                # Custom regex
                if c := constraints.get(value[0]):
                    part = _compile_req(c)

                # Optional placeholder
                if value[0] in defaults:
                    part += '?'
                else:
                    optional = False

            block = part + block

        # Not rooted with a slash
        if block:
            regex = block + regex

        # Format
        if detect:
            regex += _compile_format(constraints.get('format'), 'format' in defaults)

        self.regex = re.compile(f'^{regex}', re.DOTALL)
        return self.regex

    def _tokenize(self, pattern: str) -> Self:
        placeholders = self.placeholders
        type_start = self.type_start
        quote_end = self.quote_end
        quote_start = self.quote_start
        start = self.placeholder_start
        relaxed = self.relaxed_start
        wildcard = self.wildcard_start

        tree: list[Token] = []
        spec = more = 0
        for char in pattern:
            # Quoted
            if char == quote_start:
                spec += 1
                tree.append(['placeholder', ''])
            elif char == quote_end:
                spec = more = 0

            # Placeholder
            elif not more and char == start:
                if not spec:
                    tree.append(['placeholder', ''])
                spec += 1

            # Relaxed or wildcard (upgrade when quoted)
            elif not more and char in (relaxed, wildcard):
                if not spec:
                    tree.append(['placeholder', ''])
                spec += 1
                tree[-1][2:] = ['relaxed' if char == relaxed else 'wildcard']

            # Slash
            elif char == '/':
                tree.append(['slash'])
                spec = more = 0

            # Placeholder
            elif spec:
                more += 1
                tree[-1][1] += char

            # Text (optimize slash+text and *+text+slash+text)
            elif tree and tree[-1][0] == 'text':
                tree[-1][-1] += char
            elif len(tree) == 1 and tree[-1][0] == 'slash':
                tree = [['text', f'/{char}']]
            elif len(tree) > 1 and tree[-2][0] == 'text' and tree[-1][0] == 'slash':
                tree.pop()
                tree[-1][-1] += f'/{char}'
            else:
                tree.append(['text', char])

        # Placeholder types
        for token in reversed(tree):
            if token[0] != 'placeholder':
                continue
            m = re.match(rf'^(.+){re.escape(type_start)}(.+)$', token[1])
            token[1] = [m[1], m[2]] if m else [token[1]]
            placeholders.insert(0, token[1][0])

        self.unparsed = pattern
        self.tree = tree
        return self


def _compile_format(format: Constraint | None, has_default: bool) -> str:
    # No regex
    if not format:
        return ''

    # Default regex
    if format is True:
        return r'/?(?:\.([^/]+))?$'

    # Compile custom regex
    regex = r'\.' + _compile_req(format)
    return f'/?(?:{regex})?$' if has_default else f'/?{regex}$'


def _compile_req(req: Constraint) -> str:
    if isinstance(req, list):
        return '(' + '|'.join(re.escape(alternative) for alternative in sorted(req, reverse=True)) + ')'
    if isinstance(req, re.Pattern):
        return f'({_regex_source(req)})'
    return f'({req})'


# The source of a compiled regular expression with its flags, as Perl stringifies a qr// with (?^flags:...)
def _regex_source(regex: re.Pattern[str]) -> str:
    flags = ''.join(flag for flag, value in (('i', re.I), ('m', re.M), ('s', re.S), ('x', re.X)) if regex.flags & value)
    return f'(?{flags}:{regex.pattern})' if flags else regex.pattern


new = Pyjoyment_Routes_Pattern.new
object = Pyjoyment_Routes_Pattern
