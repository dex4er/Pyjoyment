r"""
Pyjo.Regexp - Compile regexp pattern into object
================================================
::

    from Pyjo.Regexp import r

    re_words = r('(\w+) AND (\w+)', 'i')

    m = re_words.search('This and that')
    if m:
        print('{0} + {1}'.format(*m.groups()))

:mod:`Pyjo.Regexp` provides factory function which compiles regexp pattern
into object.

:mod:`Pyjo.Regexp` uses internally cache and compiles pattern only once. Setting
flag ``o`` means that cache is not used.

Functions
---------
"""

import importlib
import os


try:
    re = importlib.import_module(os.environ.get('PYJO_REGEXP', 'regex'))
except ImportError:
    import re


re_EXTRA = 0

FLAGS = {
    'd': re.DEBUG,
    'i': re.IGNORECASE,
    'l': re.LOCALE,
    'm': re.MULTILINE,
    'o': re_EXTRA,
    's': re.DOTALL,
    'u': re.UNICODE,
    'x': re.VERBOSE,
}


CACHE = {}


RE_TYPE = type(re.compile(''))


def r(pattern, flags=''):
    """::

        re_obj = r(pattern, flags='')

    Compile pattern with flags into regexp object.
    """
    if isinstance(pattern, RE_TYPE):
        re_flags = pattern.flags
        re_pattern = pattern.pattern
    else:
        re_flags = 0
        re_pattern = pattern
        idx = ':'.join((str(hash(pattern)), str(hash(flags)), str(hash(type(re_pattern)))))
        if idx in CACHE:
            return CACHE[idx]

    for f in flags:
        if f in FLAGS:
            re_flags |= FLAGS[f]
        else:
            raise ValueError(f'Bad flag: {f}')

    new_obj = re.compile(re_pattern, flags=re_flags)

    if not isinstance(pattern, RE_TYPE) and 'o' not in flags:
        CACHE[idx] = new_obj

    return new_obj
