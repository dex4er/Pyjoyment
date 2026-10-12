# -*- coding: utf-8 -*-

r"""
Pyjo.DOM.CSS - CSS selector engine
==================================
::

    import Pyjo.DOM.CSS

    # Select elements from DOM tree
    css = Pyjo.DOM.CSS.new(tree=tree)
    elements = css.select('head > title')

:mod:`Pyjo.DOM.CSS` is the CSS selector engine used by :mod:`Pyjo.DOM` and based on
`Selectors Level 3 <http://www.w3.org/TR/css3-selectors/>`_.

Selectors
---------

All CSS selectors that make sense for a standalone parser are supported.

\*
^^

Any element. ::

    all = css.select('*')

E
^

An element of type ``E``. ::

    title = css.select('title')

E[foo]
^^^^^^

An ``E`` element with a ``foo`` attribute. ::

    links = css.select('a[href]')

E[foo="bar"]
^^^^^^^^^^^^

An ``E`` element whose ``foo`` attribute value is exactly equal to ``bar``. ::

    case_sensitive = css.select('input[type="hidden"]')
    case_sensitive = css.select('input[type=hidden]')

E[foo="bar" i]
^^^^^^^^^^^^^^

An ``E`` element whose ``foo`` attribute value is exactly equal to any
(ASCII-range) case-permutation of ``bar``. Note that this selector is
EXPERIMENTAL and might change without warning! ::

    case_insensitive = css.select('input[type="hidden" i]')
    case_insensitive = css.select('input[type=hidden i]')
    case_insensitive = css.select('input[class~="foo" i]')

This selector is part of
`Selectors Level 4 <http://dev.w3.org/csswg/selectors-4>`_, which is still a
work in progress.

E[foo~="bar"]
^^^^^^^^^^^^^

An ``E`` element whose ``foo`` attribute value is a list of
whitespace-separated values, one of which is exactly equal to ``bar``. ::

    foo = css.select('input[class~="foo"]')
    foo = css.select('input[class~=foo]')

E[foo^="bar"]
^^^^^^^^^^^^^

An ``E`` element whose ``foo`` attribute value begins exactly with the string
``bar``. ::

    begins_with = css.select('input[name^="f"]')
    begins_with = css.select('input[name^=f]')

E[foo$="bar"]
^^^^^^^^^^^^^

An ``E`` element whose ``foo`` attribute value ends exactly with the string
``bar``. ::

    ends_with = css.select('input[name$="o"]')
    ends_with = css.select('input[name$=o]')

E[foo*="bar"]
^^^^^^^^^^^^^

An ``E`` element whose ``foo`` attribute value contains the substring ``bar``. ::

    contains = css.select('input[name*="fo"]')
    contains = css.select('input[name*=fo]')

E:root
^^^^^^

An ``E`` element, root of the document. ::

    root = css.select(':root')

E:checked
^^^^^^^^^

A user interface element ``E`` which is checked (for instance a radio-button or
checkbox). ::

    input = css.select(':checked')

E:empty
^^^^^^^

An ``E`` element that has no children (including text nodes). ::

    empty = css.select(':empty')

E:nth-child(n)
^^^^^^^^^^^^^^

An ``E`` element, the ``n-th`` child of its parent. ::

    third = css.select('div:nth-child(3)')
    odd   = css.select('div:nth-child(odd)')
    even  = css.select('div:nth-child(even)')
    top3  = css.select('div:nth-child(-n+3)')

E:nth-last-child(n)
^^^^^^^^^^^^^^^^^^^

An ``E`` element, the ``n-th`` child of its parent, counting from the last one. ::

    third    = css.select('div:nth-last-child(3)')
    odd      = css.select('div:nth-last-child(odd)')
    even     = css.select('div:nth-last-child(even)')
    bottom3  = css.select('div:nth-last-child(-n+3)')

E:nth-of-type(n)
^^^^^^^^^^^^^^^^

An ``E`` element, the ``n-th`` sibling of its type. ::

    third = css.select('div:nth-of-type(3)')
    odd   = css.select('div:nth-of-type(odd)')
    even  = css.select('div:nth-of-type(even)')
    top3  = css.select('div:nth-of-type(-n+3)')

E:nth-last-of-type(n)
^^^^^^^^^^^^^^^^^^^^^

An ``E`` element, the ``n-th`` sibling of its type, counting from the last one. ::

    third    = css.select('div:nth-last-of-type(3)')
    odd      = css.select('div:nth-last-of-type(odd)')
    even     = css.select('div:nth-last-of-type(even)')
    bottom3  = css.select('div:nth-last-of-type(-n+3)')

E:first-child
^^^^^^^^^^^^^

An ``E`` element, first child of its parent. ::

    first = css.select('div p:first-child')

E:last-child
^^^^^^^^^^^^

An ``E`` element, last child of its parent. ::

    last = css.select('div p:last-child')

E:first-of-type
^^^^^^^^^^^^^^^

An ``E`` element, first sibling of its type. ::

    first = css.select('div p:first-of-type')

E:last-of-type
^^^^^^^^^^^^^^

An ``E`` element, last sibling of its type. ::

    last = css.select('div p:last-of-type')

E:only-child
^^^^^^^^^^^^

An ``E`` element, only child of its parent. ::

    lonely = css.select('div p:only-child')

E:only-of-type
^^^^^^^^^^^^^^

An ``E`` element, only sibling of its type. ::

    lonely = css.select('div p:only-of-type')

E.warning
^^^^^^^^^

An ``E`` element whose class is "warning". ::

    warning = css.select('div.warning')

E#myid
^^^^^^

An ``E`` element with ``ID`` equal to "myid". ::

    foo = css.select('div#foo')

E:not(s)
^^^^^^^^

An ``E`` element that does not match simple selector ``s``. ::

    others = css.select('div p:not(:first-child)')

E F
^^^

An ``F`` element descendant of an ``E`` element. ::

    headlines = css.select('div h1')

E > F
^^^^^

An ``F`` element child of an ``E`` element. ::

    headlines = css.select('html > body > div > h1')

E + F
^^^^^

An ``F`` element immediately preceded by an ``E`` element. ::

    second = css.select('h1 + h2')

E ~ F
^^^^^

An ``F`` element preceded by an ``E`` element. ::

    second = css.select('h1 ~ h2')

E, F, G
^^^^^^^

Elements of type ``E``, ``F`` and ``G``. ::

    headlines = css.select('h1, h2, h3')

E[foo=bar][bar=baz]
^^^^^^^^^^^^^^^^^^^

An ``E`` element whose attributes match all following attribute selectors. ::

    links = css.select('a[foo^=b][foo$=ar]')

Classes
-------
"""


import Pyjo.Base

from Pyjo.Regexp import r
from Pyjo.Util import uchr


ESCAPE_PAT = r'(?:\\[^0-9a-fA-F]|\\[0-9a-fA-F]{1,6})'
ATTR_PAT = r'''
    \[
    ((?:''' + ESCAPE_PAT + r'''|[\w\-])+)         # Key
    (?:
        (\W)?=                                    # Operator
        (?:"((?:\\"|[^"])*?)"|([^\]]+?))          # Value
        (?:\s+(i))?                               # Case-sensitivity
    )?
    \]
'''
PSEUDO_CLASS_PAT = r'(?::([\w\-]+)(?:\(((?:\([^)]+\)|[^)])+)\))?)'
TOKEN_PAT = r'''
    (\s*,\s*)?                                        # Separator
    ((?:[^[\\:\s,>+~]|''' + ESCAPE_PAT + r'''\s?)+)?  # Element  #]
    (''' + PSEUDO_CLASS_PAT + r'''*)?                 # Pseudoclass
    ((?:''' + ATTR_PAT + r''')*)?                     # Attributes
    (?:\s*([>+~]))?                                   # Combinator
'''


re_token = r(TOKEN_PAT, 'x')
re_tag = r(r'^((?:\\\.|\\\#|[^.#])+)')
re_class_or_id = r(r'(?:([.#])((?:\\[.\#]|[^\#.])+))')
re_pseudo_class = r(PSEUDO_CLASS_PAT)
re_attr = r(ATTR_PAT, 'x')
re_even = r(r'^\s*even\s*$', 'i')
re_odd = r(r'^\s*odd\s*$', 'i')
re_equation = r(r'(?:(-?(?:\d+)?)?(n))?\s*\+?\s*(-?\s*\d+)?\s*$', 'i')
re_whitespace = r(r'\s+')
re_first_last = r(r'^(first|last)-')
re_only_child_of_type = r(r'^only-(?:child|(of-type))$')
re_escaped_unicode = r(r'\\([0-9a-fA-F]{1,6})\s?')


class Pyjo_DOM_CSS(Pyjo.Base.object):
    """
    :mod:`Pyjo.DOM.CSS` inherits all attributes and methods from
    :mod:`Pyjo.Base` and implements the following new ones.
    """

    def __init__(self, **kwargs):
        self.tree = kwargs.get('tree')
        """::

            tree = html.tree
            html.tree = ['root']

        Document Object Model. Note that this structure should only be used very
        carefully since it is very dynamic.
        """

    def matches(self, pattern):
        """::

            bool = css.matches('head > title')

        Check if first node in :attr:`tree` matches the CSS selector.
        """
        tree = self.tree
        if tree[0] == 'tag':
            return self._match(self._compile(pattern), tree, tree)
        else:
            return

    def select(self, pattern):
        """::

            results = css.select('head > title')

        Run CSS selector against :attr:`tree`.
        """
        return self._select(False, self.tree, self._compile(pattern))

    def select_one(self, pattern):
        """::

            results = css.select_one('head > title')

        Run CSS selector against :attr:`tree` and stop as soon as the first node
        matched.
        """
        return self._select(True, self.tree, self._compile(pattern))

    def _ancestor(self, selectors, current, tree, pos):
        while len(current) > 3 and current[3]:
            current = current[3]
            if current[0] == 'root' or current == tree:
                return False
            if self._combinator(selectors, current, tree, pos):
                return True
        return False

    def _attr(self, name_pat, value_pat, current):
        attrs = current[2]
        re_name = r(name_pat)
        if value_pat is not None:
            re_value = r(value_pat)
        for name, value in attrs.items():
            if re_name.search(name):
                if value is not None and value_pat is not None:
                    if re_value.search(value):
                        return True
                else:
                    return True
        return False

    def _combinator(self, selectors, current, tree, pos):
        if len(selectors) > pos:
            c = selectors[pos]
        else:
            return False

        if isinstance(c, list):
            if not self._selector(c, current):
                return False
            pos += 1
            if len(selectors) > pos and selectors[pos]:
                c = selectors[pos]
            else:
                return True

        pos += 1

        # ">" (parent only)
        if c == '>':
            return self._parent(selectors, current, tree, pos)

        # "~" (preceding siblings)
        if c == '~':
            return self._sibling(selectors, current, tree, False, pos)

        # "+" (immediately preceding siblings)
        if c == '+':
            return self._sibling(selectors, current, tree, True, pos)

        # " " (ancestor)
        return self._ancestor(selectors, current, tree, pos)

    def _compile(self, css):
        pattern = [[]]
        for m in re_token.finditer(css):
            separator, element, pc, attrs, combinator = m.group(1, 2, 3, 6, 12)
            if element is None:
                element = ''

            if separator or element or pc or attrs or combinator:
                # New selector
                if separator:
                    pattern.append([])
                part = pattern[-1]

                # Empty combinator
                if part and part[-1] and isinstance(part[-1], list):
                    part.append(' ')

                # Tag
                selector = []
                part.append(selector)
                m = re_tag.search(element)
                if m:
                    element = re_tag.sub('', element, 1)
                    g = ('',) + m.groups()
                    if g[1] != '*':
                        selector.append(['tag', self._name(g[1])])

                # Class or ID
                for m in re_class_or_id.finditer(element):
                    g = ('',) + m.groups()
                    if g[1] == '.':
                        name, op = 'class', '~'
                    else:
                        name, op = 'id', ''
                    selector.append(['attr', self._name(name), self._value(op, g[2])])

                # Pseudo classes (":not" contains more selectors)
                for m in re_pseudo_class.finditer(pc):
                    g = ('',) + m.groups()
                    if g[1] == 'not':
                        value = self._compile(g[2])
                    else:
                        value = self._equation(g[2])
                    selector.append(['pc', g[1].lower(), value])

                # Attributes
                for m in re_attr.finditer(attrs):
                    g = ('',) + m.groups()
                    if g[2] is not None:
                        op = g[2]
                    else:
                        op = ''
                    if g[3] is not None:
                        value = g[3]
                    else:
                        value = g[4]
                    insensitive = bool(g[5])
                    selector.append(['attr', self._name(g[1]), self._value(op, value, insensitive)])

                # Combinator
                if combinator:
                    part.append(combinator)

        return pattern

    def _empty(self, node):
        return node[0] == 'comment' or node[0] == 'pi'

    def _equation(self, equation):
        if not equation:
            return []

        # "even"
        if re_even.search(equation):
            return [2, 2]

        # "odd"
        if re_odd.search(equation):
            return [2, 1]

        # Equation
        num = [1, 1]
        m = re_equation.search(equation)
        if m:
            g = ('',) + m.groups()
            if g[1] is not None and len(m.group(1)):
                num[0] = m.group(1)
            elif g[2]:
                num[0] = 1
            else:
                num[0] = 0
            if num[0] == '-':
                num[0] = -1
            num[0] = int(num[0])
            if g[3] is not None:
                num[1] = g[3]
            else:
                num[1] = '0'
            num[1] = re_whitespace.sub('', num[1])
            num[1] = int(num[1])

        return num

    def _match(self, pattern, current, tree):
        for p in pattern:
            selectors = list(p)
            selectors.reverse()
            if self._combinator(selectors, current, tree, 0):
                return True
        return False

    def _name(self, value):
        return r'(?:^|:)' + Pyjo.Regexp.re.escape(self._unescape(value)) + r'$'

    def _parent(self, selectors, current, tree, pos):
        if len(current) <= 3 or not current[3]:
            return False

        parent = current[3]

        if parent[0] == 'root' or parent == tree:
            return False

        return self._combinator(selectors, parent, tree, pos)

    def _pc(self, pclass, args, current):
        # ":empty"
        if pclass == 'empty':
            return not list(filter(lambda i: not self._empty(i), current[4:]))

        # ":root"
        if pclass == 'root':
            return current[3] and current[3][0] == 'root'

        # ":not"
        if pclass == 'not':
            return not self._match(args, current, current)

        # ":checked"
        if pclass == 'checked':
            return 'checked' in current[2] or 'selected' in current[2]

        # ":first-*" or ":last-*" (rewrite with equation)
        m = re_first_last.search(pclass)
        if m:
            pclass = re_first_last.sub('', pclass)
            if m.group(1) == 'first':
                pclass = 'nth-' + pclass
                args = [0, 1]
            else:
                pclass = 'nth-last-' + pclass
                args = [-1, 1]

        # ":nth-*"
        if pclass.startswith('nth-'):
            if pclass.endswith('of-type'):
                ptype = current[1]
            else:
                ptype = None
            siblings = list(self._siblings(current, ptype))

            # ":nth-last-*"
            if pclass.startswith('nth-last'):
                siblings.reverse()

            for i in range(len(siblings)):
                result = args[0] * i + args[1]
                if result < 1:
                    continue
                if not len(siblings) > result - 1:
                    break
                sibling = siblings[result - 1]
                if not sibling:
                    break
                if sibling == current:
                    return True

        # ":only-*"
        else:
            m = re_only_child_of_type.search(pclass)
            if m:
                for i in self._siblings(current, current[1] if m.group(1) else None):
                    if i != current:
                        return False
                return True

        return False

    def _select(self, one, tree, pattern):
        results = []
        if tree[0] == 'root':
            pos = 1
        else:
            pos = 4
        queue = tree[pos:]
        while queue:
            current = queue.pop(0)
            if current[0] == 'tag':
                queue = current[4:] + queue
                if self._match(pattern, current, tree):
                    if one:
                        return current
                    else:
                        results.append(current)
        if one:
            return
        else:
            return results

    def _selector(self, selector, current):
        for s in selector:
            if s:
                nodetype = s[0]

                # Tag
                if nodetype == 'tag':
                    if not r(s[1]).search(current[1]):
                        return False

                # Attribute
                elif nodetype == 'attr':
                    if not self._attr(s[1], s[2], current):
                        return False

                # Pseudo class
                elif nodetype == 'pc':
                    if not self._pc(s[1], s[2], current):
                        return False

        return True

    def _sibling(self, selectors, current, tree, immediate, pos):
        found = False

        for sibling in self._siblings(current):
            if sibling == current:
                return found

            # "+" (immediately preceding sibling)
            if immediate:
                found = self._combinator(selectors, sibling, tree, pos)

            # "~" (preceding sibling)
            elif self._combinator(selectors, sibling, tree, pos):
                return True

        return False

    def _siblings(self, current, nodetype=None):
        parent = current[3]

        siblings = filter(lambda n: n[0] == 'tag',
                          parent[(1 if parent[0] == 'root' else 4):])

        if nodetype is not None:
            siblings = filter(lambda n: nodetype == n[1], siblings)

        return siblings

    def _unescape(self, value):
        # Remove escaped newlines
        value = value.replace('\\\n', '')

        # Unescape Unicode characters
        value = re_escaped_unicode.sub(lambda m: uchr(int(m.group(1), 16)), value)

        # Remove backslash
        value = value.replace('\\', '')

        return value

    def _value(self, op, value, insensitive=False):
        if value is None:
            return

        value = Pyjo.Regexp.re.escape(self._unescape(value))
        if insensitive:
            value = '(?i:' + value + ')'

        # "~=" (word)
        if op == '~':
            return r'(?:^|\s+)' + value + r'(?:\s+|$)'

        # "*=" (contains)
        if op == '*':
            return value

        # "^=" (begins with)
        if op == '^':
            return r'^' + value

        # "$=" (ends with)
        if op == '$':
            return value + r'$'

        # Everything else
        return r'^' + value + r'$'


new = Pyjo_DOM_CSS.new
object = Pyjo_DOM_CSS
