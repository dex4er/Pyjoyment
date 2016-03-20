# -*- coding: utf-8 -*-

"""
Pyjo.Util - Portable utility functions
======================================
::

    from Pyjo.Util import b, b64_encode, u, url_escape, url_unescape

    string = 'test=23'
    escaped = url_escape(b(string))
    print(u(url_unescape(escaped)))
    print(b64_encode(escaped, ''))

:mod:`Pyjo.Util` provides portable utility functions for :mod:`Pyjo`.

Functions
---------
"""

from __future__ import print_function

from Pyjo.Regexp import r

import base64
import binascii
import functools
import hashlib
import os
import random
import select
import sys
import time


class Error(Exception):
    pass


DEFAULT_CHARSET = 'utf-8'


if sys.version_info >= (3, 0):
    def b(unicodestring, charset=DEFAULT_CHARSET, errors='strict'):
        """::

            bytestring = b(unicodestring)
            bytestring = b(unicodestring, 'utf-8')
            bytestring = b(unicodestring, 'utf-8', 'strict')

        Encode unicodestring into bytestring.
        """
        if isbytes(unicodestring):
            return bytes(unicodestring)
        else:
            return bytes(str(unicodestring), charset, errors)
else:
    def b(unicodestring, charset=DEFAULT_CHARSET, errors='strict'):
        """::

            bytestring = b(unicodestring)
            bytestring = b(unicodestring, 'utf-8')
            bytestring = b(unicodestring, 'utf-8', 'strict')

        Encode unicodestring into bytestring.
        """
        if isinstance(unicodestring, unicode):
            return unicode(unicodestring).encode(charset, errors)
        else:
            return str(unicodestring)


def b64_decode(unicodestring):
    """::

        bytestring = b64_decode(unicodestring)

    Base64 decode bytes. Ignores errors.
    """
    for _ in range(6):
        try:
            return base64.b64decode(unicodestring)
        except binascii.Error:
            unicodestring = unicodestring[:-1]
    return b''


re_chars_76 = r('(.{76})')


def b64_encode(bstring, sep="\n"):
    r"""::

        asciistring = b64_encode(bytestring)
        asciistring = b64_encode(bytestring, "\n")

    Base64 encode bytes, the line ending defaults to a newline.
    """
    return re_chars_76.sub(lambda m: m.group(1) + sep, u(base64.b64encode(bstring), 'ascii'))


def convert(value, newtype, default=None):
    """::

        converted = convert(value, newtype)
        converted = convert(value, newtype, default)

    Convert value to new type, ignoring errors. Return default value (or None) if
    error occurred. ::

        port = convert(os.environ.get('HTTP_PORT', ''), int, 80)
    """
    try:
        return newtype(value)
    except (TypeError, ValueError):
        return default


def decorator(func):
    """::

        @decorator
        def function(cb, param):
            print("function cb='{0}' param='{1}'".format(cb(), param))

        function(lambda: 'callback 1', 'as function')

        @function('as decorator')
        def cb():
            return 'callback 2'

    Make decorator from function with callback as a first argument.
    """
    @functools.wraps(func)
    def wrap(*args):
        if not callable(args[0]):
            def wrap2(func2):
                return func(func2, *args)
            return wrap2
        return func(*args)
    return wrap


def decoratormethod(func):
    """::

        class MyClass(object):
            @decoratormethod
            def method(self, cb, param):
                print("method cb='{0}' param='{1}'".format(cb(), param))

        obj = MyClass()

        obj.method(lambda: 'callback 1', 'as method')

        @obj.method('as decorator')
        def cb():
            return 'callback 2'

    Make decorator from method with callback as a first argument.
    """
    @functools.wraps(func)
    def wrap(self, *args):
        if not callable(args[0]):
            def wrap2(func2):
                return func(self, func2, *args)
            return wrap2
        return func(self, *args)
    return wrap


def die(e):
    """::

        die(Exception('Something went wrong'))
        die('Exit immediately')

    Raise an exception. :class:`SystemExit` exception is raised
    if parameter is not an exception already. ::

        os.environ.get('HOME') or die('HOME is not defined')
    """
    if isinstance(e, BaseException):
        raise e
    else:
        raise SystemExit(e)


def getenv(name, default=None):
    """::

        envvar = getenv(name)
        envvar = getenv(name, default)

    Get the environment variable. Returns default value or ``None``
    if variable is not defined.
    """
    return os.environ.get(name, default)


re_entity = r(r'&(?:\#((?:\d{1,7}|x[0-9a-fA-F]{1,6}));|(\w+;?))')


def html_unescape(unicodestring):
    """::

        unicodestring = html_unescape(unicodestring)

    Unescape all HTML entities in string. ::

        # '<div>'
        html_unescape('&lt;div&gt;')
    """
    return re_entity.sub(lambda m: _decode(m.group(1), m.group(2)), unicodestring)


if sys.version_info >= (3, 0):
    def isbytes(obj):
        """::

            boolean = isbytes(obj)

        Check if object is ``bytearray`` or ``bytes`` (Python 3.x)
        or ``str`` (Python 2.x).
        """
        return isinstance(obj, (bytearray, bytes))
else:
    def isbytes(obj):
        """::

            boolean = isbytes(obj)

        Check if object is ``bytearray`` or ``bytes`` (Python 3.x)
        or ``str`` (Python 2.x).
        """
        return isinstance(obj, (bytearray, str))


def isiterable(obj):
    """::

        boolean = isiterable(obj)

    Check if object is iterable and not simple string.
    """
    return hasattr(obj, '__iter__') and not isstring(obj)


if sys.version_info >= (3, 0):
    def isstring(obj):
        """::

            boolean = isstring(obj)

        Check if object is string (``bytes``, ``str`` or ``unicode``).
        """
        return isinstance(obj, (bytes, str))
else:
    def isstring(obj):
        """::

            boolean = isstring(obj)

        Check if object is string (``bytes``, ``str`` or ``unicode``).
        """
        return isinstance(obj, (bytes, str, unicode))


if sys.version_info >= (3, 0):
    def isunicode(obj):
        """::

            boolean = isunicode(obj)

        Check if object is ``str`` (Python 3.x)
        or ``unicode`` (Python 2.x).
        """
        return isinstance(obj, str)
else:
    def isunicode(obj):
        """::

            boolean = isunicode(obj)

        Check if object is ``str`` (Python 3.x)
        or ``unicode`` (Python 2.x).
        """
        return isinstance(obj, unicode)


def md5_bytes(bytestring):
    r"""::

        md5 = md5_bytes(bytestring)

    Generate binary MD5 checksum for bytes. ::

        # b'\xac\xbd\x18\xdbL\xc2\xf8\\\xed\xefeO\xcc\xc4\xa4\xd8'
        md5_bytes(b'foo')
    """
    m = hashlib.md5()
    m.update(bytestring)
    return m.hexdigest()


def md5_sum(bytestring):
    """::

        md5 = md5_sum(bytestring)

    Generate MD5 checksum for bytes. ::

        # 'acbd18db4cc2f85cedef654fccc4a4d8'
        md5_sum(b'foo')
    """
    m = hashlib.md5()
    m.update(bytestring)
    return m.hexdigest()


def not_implemented(method):
    """::

        class BaseClass(object):
            @not_implemented
            def method(self):
                pass

    Raise the exception with "Method ``name`` not implemented by subclass"
    message.
    """
    @functools.wraps(method)
    def stub(*args, **kwargs):
        raise Error('Method "{0}" not implemented by subclass'.format(method.__name__))
    return stub


def notnone(*args):
    """::

        value = notnone(value, another_value, default_value)
        value = notnone(callable, callable_default)

    Return the first not ``None`` value from arguments list. If the argument
    is callable, then check the value which this callable returns (lazy
    evaluation). ::

        from Pyjo.Util import convert, getenv

        def print_log(msg, **kwargs):
            level = notnone(kwargs.get('log_level'),
                            lambda: convert(getenv('LOG_LEVEL'), int, 3))
            ...
    """
    for a in args:
        if a is not None:
            if callable(a):
                return a()
            else:
                return a


re_b_quote = r(br'(["\\])')
re_u_quote = r(r'(["\\])')


def quote(string):
    """::

        quoted = quote(string)

    Quote string.
    """
    if isbytes(string):
        string = re_b_quote.sub(br'\\\1', bytes(string))
        return b'"' + string + b'"'
    else:
        string = re_u_quote.sub(r'\\\1', string)
        return '"' + string + '"'


def rand(value=1):
    """::

        value = rand(range)

    Return random value from ``0`` to ``range``.
    """
    return random.random() * value


def setenv(name, value):
    """::

        setenv(name, value)

    Set the environment variable or remove it if value is ``None``.
    """
    if value is None:
        if name in os.environ:
            del os.environ[name]
    else:
        os.environ.update({name: value})


def slurp(path, charset=DEFAULT_CHARSET):
    """::

        string = slurp('/etc/passwd')
        string = slurp('/etc/passwd', 'utf-8')

    Read all data at once from file as unicode string.
    """
    with open(path, 'rb') as f:
        return u(f.read(), charset)


def slurpb(path):
    """::

        bytestring = slurpb('/etc/passwd')

    Read all data at once from file as binary string.
    """
    with open(path, 'rb') as f:
        return b(f.read())


def split_cookie_header(string):
    """::

        tree = split_cookie_header('a=b; expires=Thu, 07 Aug 2008 07:07:59 GMT')

    Same as :func:`split_header`, but handles ``expires`` values from
    :rfc:`6265`.
    """
    return _header(string, True)


def split_header(string):
    """::

        tree = split_header('foo="bar baz"; test=123, yada')

    Split HTTP header value into key/value pairs, each comma separated part gets
    its own list, and keys without a value get ``None`` assigned. ::

        # 'one'
        split_header('one; two="three four", five=six')[0][0][0]

        # 'two'
        split_header('one; two="three four", five=six')[0][1][0]

        # 'three four'
        split_header('one; two="three four", five=six')[0][1][1]

        # 'five'
        split_header('one; two="three four", five=six')[1][0][0]

        # 'six'
        split_header('one; two="three four", five=six')[1][0][1]
    """
    return _header(string, False)


def spurt(content, path, charset=DEFAULT_CHARSET):
    """::

        written = spurt(string, '/etc/passwd')
        written = spurt(string, '/etc/passwd', 'utf-8')

    Write all data from unicode string at once to file.
    """
    with open(path, 'wb') as f:
        return f.write(b(content, charset))


def spurtb(content, path):
    """::

        written = spurt(bytestring, '/etc/passwd')

    Write all data from binary string at once to file.
    """
    with open(path, 'wb') as f:
        return f.write(content)


re_whitespaces = r(r'\s+')


def squish(string):
    """::

        squished = squish(string)

    Trim whitespace characters from both ends of string and then change all
    consecutive groups of whitespace into one space each. ::

        # 'foo bar'
        squish('  foo  bar  ')
    """
    return re_whitespaces.sub(' ', trim(string))


steady_time = time.time


re_whitespaces_starts = r(r'^\s+')
re_whitespaces_ends = r(r'\s+$')


def trim(string):
    """::

        trimmed = trim(string)

    Trim whitespace characters from both ends of string. ::

        # 'foo bar'
        trim('  foo bar  ')
    """
    return re_whitespaces_starts.sub('', re_whitespaces_ends.sub('', string, 1), 1)


if sys.version_info >= (3, 0):
    def u(string, charset=DEFAULT_CHARSET):
        """::

            unicodestring = u(bytestring)
            unicodestring = u(bytestring, 'utf-8')

        Decode bytestring into unicodestring.
        """
        if isbytes(string):
            return bytes(string).decode(charset)
        else:
            return str(string)
else:
    def u(string, charset=DEFAULT_CHARSET):
        """::

            unicodestring = u(bytestring)
            unicodestring = u(bytestring, 'utf-8')

        Decode bytestring into unicodestring.
        """
        if isinstance(string, unicode) or hasattr(string, '__unicode__'):
            return unicode(string)
        else:
            if charset.lower() in ['ascii', '646', 'us-ascii']:
                return str(str(string).decode(charset))
            else:
                return str(string).decode(charset)


if sys.version_info >= (3, 0):
    uchr = chr
else:
    uchr = unichr


re_b_unquote = r(br'^"(.*)"$')
re_b_unquote2 = r(br'\\\\')
re_b_unquote3 = r(br'\\"')
re_u_unquote = r(r'^"(.*)"$')
re_u_unquote2 = r(r'\\\\')
re_u_unquote3 = r(r'\\"')


def unquote(string):
    """::

        string = unquote(quoted)

    Unquote string.
    """
    if isbytes(string):
        string, n = re_b_unquote.subn(lambda m: m.group(1), bytes(string))
        if n:
            string = re_b_unquote2.sub(br'\\', string)
            string = re_b_unquote3.sub(br'"', string)
    else:
        string, n = re_u_unquote.subn(lambda m: m.group(1), string)
        if n:
            string = re_u_unquote2.sub(r'\\', string)
            string = re_u_unquote3.sub(r'"', string)
    return string


re_url_allow_chars = r(br'([^A-Za-z0-9\-._~])')


def url_escape(bstring, pattern=None):
    """::

        escaped = url_escape(string)
        escaped = url_escape(string, r'^A-Za-z0-9\-._~')

    Percent encode unsafe characters in string as described in
    :rfc:`3986`, the pattern used defaults to
    ``^A-Za-z0-9\-._~``. ::

        # 'foo%3Bbar'
        url_escape('foo;bar')
    """
    if pattern is not None:
        pattern = b'([' + pattern + b'])'
        re_pattern = r(pattern)
    else:
        re_pattern = re_url_allow_chars

    return re_pattern.sub(lambda m: b'%' + format(ord(m.group(1)), 'X').encode('ascii'), bstring)


re_percent_chars = r(br'%([0-9a-fA-F]{2})')


def url_unescape(bstring):
    """::

        str = url_unescape $escaped;

    Decode percent encoded characters in string as described in
    :rfc:`3986`. ::

        # 'foo;bar'
        url_unescape('foo%3Bbar')
    """
    return re_percent_chars.sub(lambda m: b(chr(int(m.group(1), 16)), 'iso-8859-1'), bstring)


def warn(msg, *args):
    """::

        warn(string)

    Output message to ``sys.stderr``.
    """
    if not msg.endswith("\n"):
        msg += "\n"
    print(msg, end='', file=sys.stderr)


# Characters that should be escaped in XML
XML = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    '\'': '&#39;'
}


re_xml_allow_chars = r(r'([&<>"\'])')


def xml_escape(string):
    """::

        escaped = xml_escape(string)

    Escape unsafe characters ``&``, ``<``, ``>``, ``"`` and ``'`` in string, but
    do not escape :class:`Pyjo.ByteStream` objects. ::

        # '&lt;div&gt;'
        xml_escape('<div>')

        # '<div>'
        from Pyjo.Util import b
        xml_escape(b('<div>'))
    """
    return re_xml_allow_chars.sub(lambda m: XML[m.group(1)], string)


def xor_encode(data, mask):
    """::

        encoded = xor_encode(string, key)

    XOR encode string with variable length key.
    """
    return bytearray(a ^ b for a, b in zip(*map(bytearray, [data, mask])))


ENTITIES = {
    "Aacute;": u"\xc1",
    "Aacute": u"\xc1",
    "aacute;": u"\xe1",
    "aacute": u"\xe1",
    "Abreve;": u"\u0102",
    "abreve;": u"\u0103",
    "ac;": u"\u223e",
    "acd;": u"\u223f",
    "acE;": u"\u223e"u"\u0333",
    "Acirc;": u"\xc2",
    "Acirc": u"\xc2",
    "acirc;": u"\xe2",
    "acirc": u"\xe2",
    "acute;": u"\xb4",
    "acute": u"\xb4",
    "Acy;": u"\u0410",
    "acy;": u"\u0430",
    "AElig;": u"\xc6",
    "AElig": u"\xc6",
    "aelig;": u"\xe6",
    "aelig": u"\xe6",
    "af;": u"\u2061",
    "Afr;": u"\U0001d504",
    "afr;": u"\U0001d51e",
    "Agrave;": u"\xc0",
    "Agrave": u"\xc0",
    "agrave;": u"\xe0",
    "agrave": u"\xe0",
    "alefsym;": u"\u2135",
    "aleph;": u"\u2135",
    "Alpha;": u"\u0391",
    "alpha;": u"\u03b1",
    "Amacr;": u"\u0100",
    "amacr;": u"\u0101",
    "amalg;": u"\u2a3f",
    "AMP;": "\x26",
    "AMP": "\x26",
    "amp;": "\x26",
    "amp": "\x26",
    "And;": u"\u2a53",
    "and;": u"\u2227",
    "andand;": u"\u2a55",
    "andd;": u"\u2a5c",
    "andslope;": u"\u2a58",
    "andv;": u"\u2a5a",
    "ang;": u"\u2220",
    "ange;": u"\u29a4",
    "angle;": u"\u2220",
    "angmsd;": u"\u2221",
    "angmsdaa;": u"\u29a8",
    "angmsdab;": u"\u29a9",
    "angmsdac;": u"\u29aa",
    "angmsdad;": u"\u29ab",
    "angmsdae;": u"\u29ac",
    "angmsdaf;": u"\u29ad",
    "angmsdag;": u"\u29ae",
    "angmsdah;": u"\u29af",
    "angrt;": u"\u221f",
    "angrtvb;": u"\u22be",
    "angrtvbd;": u"\u299d",
    "angsph;": u"\u2222",
    "angst;": u"\xc5",
    "angzarr;": u"\u237c",
    "Aogon;": u"\u0104",
    "aogon;": u"\u0105",
    "Aopf;": u"\U0001d538",
    "aopf;": u"\U0001d552",
    "ap;": u"\u2248",
    "apacir;": u"\u2a6f",
    "apE;": u"\u2a70",
    "ape;": u"\u224a",
    "apid;": u"\u224b",
    "apos;": "\x27",
    "ApplyFunction;": u"\u2061",
    "approx;": u"\u2248",
    "approxeq;": u"\u224a",
    "Aring;": u"\xc5",
    "Aring": u"\xc5",
    "aring;": u"\xe5",
    "aring": u"\xe5",
    "Ascr;": u"\U0001d49c",
    "ascr;": u"\U0001d4b6",
    "Assign;": u"\u2254",
    "ast;": "\x2a",
    "asymp;": u"\u2248",
    "asympeq;": u"\u224d",
    "Atilde;": u"\xc3",
    "Atilde": u"\xc3",
    "atilde;": u"\xe3",
    "atilde": u"\xe3",
    "Auml;": u"\xc4",
    "Auml": u"\xc4",
    "auml;": u"\xe4",
    "auml": u"\xe4",
    "awconint;": u"\u2233",
    "awint;": u"\u2a11",
    "backcong;": u"\u224c",
    "backepsilon;": u"\u03f6",
    "backprime;": u"\u2035",
    "backsim;": u"\u223d",
    "backsimeq;": u"\u22cd",
    "Backslash;": u"\u2216",
    "Barv;": u"\u2ae7",
    "barvee;": u"\u22bd",
    "Barwed;": u"\u2306",
    "barwed;": u"\u2305",
    "barwedge;": u"\u2305",
    "bbrk;": u"\u23b5",
    "bbrktbrk;": u"\u23b6",
    "bcong;": u"\u224c",
    "Bcy;": u"\u0411",
    "bcy;": u"\u0431",
    "bdquo;": u"\u201e",
    "becaus;": u"\u2235",
    "Because;": u"\u2235",
    "because;": u"\u2235",
    "bemptyv;": u"\u29b0",
    "bepsi;": u"\u03f6",
    "bernou;": u"\u212c",
    "Bernoullis;": u"\u212c",
    "Beta;": u"\u0392",
    "beta;": u"\u03b2",
    "beth;": u"\u2136",
    "between;": u"\u226c",
    "Bfr;": u"\U0001d505",
    "bfr;": u"\U0001d51f",
    "bigcap;": u"\u22c2",
    "bigcirc;": u"\u25ef",
    "bigcup;": u"\u22c3",
    "bigodot;": u"\u2a00",
    "bigoplus;": u"\u2a01",
    "bigotimes;": u"\u2a02",
    "bigsqcup;": u"\u2a06",
    "bigstar;": u"\u2605",
    "bigtriangledown;": u"\u25bd",
    "bigtriangleup;": u"\u25b3",
    "biguplus;": u"\u2a04",
    "bigvee;": u"\u22c1",
    "bigwedge;": u"\u22c0",
    "bkarow;": u"\u290d",
    "blacklozenge;": u"\u29eb",
    "blacksquare;": u"\u25aa",
    "blacktriangle;": u"\u25b4",
    "blacktriangledown;": u"\u25be",
    "blacktriangleleft;": u"\u25c2",
    "blacktriangleright;": u"\u25b8",
    "blank;": u"\u2423",
    "blk12;": u"\u2592",
    "blk14;": u"\u2591",
    "blk34;": u"\u2593",
    "block;": u"\u2588",
    "bne;": "\x3d"u"\u20e5",
    "bnequiv;": u"\u2261"u"\u20e5",
    "bNot;": u"\u2aed",
    "bnot;": u"\u2310",
    "Bopf;": u"\U0001d539",
    "bopf;": u"\U0001d553",
    "bot;": u"\u22a5",
    "bottom;": u"\u22a5",
    "bowtie;": u"\u22c8",
    "boxbox;": u"\u29c9",
    "boxDL;": u"\u2557",
    "boxDl;": u"\u2556",
    "boxdL;": u"\u2555",
    "boxdl;": u"\u2510",
    "boxDR;": u"\u2554",
    "boxDr;": u"\u2553",
    "boxdR;": u"\u2552",
    "boxdr;": u"\u250c",
    "boxH;": u"\u2550",
    "boxh;": u"\u2500",
    "boxHD;": u"\u2566",
    "boxHd;": u"\u2564",
    "boxhD;": u"\u2565",
    "boxhd;": u"\u252c",
    "boxHU;": u"\u2569",
    "boxHu;": u"\u2567",
    "boxhU;": u"\u2568",
    "boxhu;": u"\u2534",
    "boxminus;": u"\u229f",
    "boxplus;": u"\u229e",
    "boxtimes;": u"\u22a0",
    "boxUL;": u"\u255d",
    "boxUl;": u"\u255c",
    "boxuL;": u"\u255b",
    "boxul;": u"\u2518",
    "boxUR;": u"\u255a",
    "boxUr;": u"\u2559",
    "boxuR;": u"\u2558",
    "boxur;": u"\u2514",
    "boxV;": u"\u2551",
    "boxv;": u"\u2502",
    "boxVH;": u"\u256c",
    "boxVh;": u"\u256b",
    "boxvH;": u"\u256a",
    "boxvh;": u"\u253c",
    "boxVL;": u"\u2563",
    "boxVl;": u"\u2562",
    "boxvL;": u"\u2561",
    "boxvl;": u"\u2524",
    "boxVR;": u"\u2560",
    "boxVr;": u"\u255f",
    "boxvR;": u"\u255e",
    "boxvr;": u"\u251c",
    "bprime;": u"\u2035",
    "Breve;": u"\u02d8",
    "breve;": u"\u02d8",
    "brvbar;": u"\xa6",
    "brvbar": u"\xa6",
    "Bscr;": u"\u212c",
    "bscr;": u"\U0001d4b7",
    "bsemi;": u"\u204f",
    "bsim;": u"\u223d",
    "bsime;": u"\u22cd",
    "bsol;": "\x5c",
    "bsolb;": u"\u29c5",
    "bsolhsub;": u"\u27c8",
    "bull;": u"\u2022",
    "bullet;": u"\u2022",
    "bump;": u"\u224e",
    "bumpE;": u"\u2aae",
    "bumpe;": u"\u224f",
    "Bumpeq;": u"\u224e",
    "bumpeq;": u"\u224f",
    "Cacute;": u"\u0106",
    "cacute;": u"\u0107",
    "Cap;": u"\u22d2",
    "cap;": u"\u2229",
    "capand;": u"\u2a44",
    "capbrcup;": u"\u2a49",
    "capcap;": u"\u2a4b",
    "capcup;": u"\u2a47",
    "capdot;": u"\u2a40",
    "CapitalDifferentialD;": u"\u2145",
    "caps;": u"\u2229"u"\ufe00",
    "caret;": u"\u2041",
    "caron;": u"\u02c7",
    "Cayleys;": u"\u212d",
    "ccaps;": u"\u2a4d",
    "Ccaron;": u"\u010c",
    "ccaron;": u"\u010d",
    "Ccedil;": u"\xc7",
    "Ccedil": u"\xc7",
    "ccedil;": u"\xe7",
    "ccedil": u"\xe7",
    "Ccirc;": u"\u0108",
    "ccirc;": u"\u0109",
    "Cconint;": u"\u2230",
    "ccups;": u"\u2a4c",
    "ccupssm;": u"\u2a50",
    "Cdot;": u"\u010a",
    "cdot;": u"\u010b",
    "cedil;": u"\xb8",
    "cedil": u"\xb8",
    "Cedilla;": u"\xb8",
    "cemptyv;": u"\u29b2",
    "cent;": u"\xa2",
    "cent": u"\xa2",
    "CenterDot;": u"\xb7",
    "centerdot;": u"\xb7",
    "Cfr;": u"\u212d",
    "cfr;": u"\U0001d520",
    "CHcy;": u"\u0427",
    "chcy;": u"\u0447",
    "check;": u"\u2713",
    "checkmark;": u"\u2713",
    "Chi;": u"\u03a7",
    "chi;": u"\u03c7",
    "cir;": u"\u25cb",
    "circ;": u"\u02c6",
    "circeq;": u"\u2257",
    "circlearrowleft;": u"\u21ba",
    "circlearrowright;": u"\u21bb",
    "circledast;": u"\u229b",
    "circledcirc;": u"\u229a",
    "circleddash;": u"\u229d",
    "CircleDot;": u"\u2299",
    "circledR;": u"\xae",
    "circledS;": u"\u24c8",
    "CircleMinus;": u"\u2296",
    "CirclePlus;": u"\u2295",
    "CircleTimes;": u"\u2297",
    "cirE;": u"\u29c3",
    "cire;": u"\u2257",
    "cirfnint;": u"\u2a10",
    "cirmid;": u"\u2aef",
    "cirscir;": u"\u29c2",
    "ClockwiseContourIntegral;": u"\u2232",
    "CloseCurlyDoubleQuote;": u"\u201d",
    "CloseCurlyQuote;": u"\u2019",
    "clubs;": u"\u2663",
    "clubsuit;": u"\u2663",
    "Colon;": u"\u2237",
    "colon;": "\x3a",
    "Colone;": u"\u2a74",
    "colone;": u"\u2254",
    "coloneq;": u"\u2254",
    "comma;": "\x2c",
    "commat;": "\x40",
    "comp;": u"\u2201",
    "compfn;": u"\u2218",
    "complement;": u"\u2201",
    "complexes;": u"\u2102",
    "cong;": u"\u2245",
    "congdot;": u"\u2a6d",
    "Congruent;": u"\u2261",
    "Conint;": u"\u222f",
    "conint;": u"\u222e",
    "ContourIntegral;": u"\u222e",
    "Copf;": u"\u2102",
    "copf;": u"\U0001d554",
    "coprod;": u"\u2210",
    "Coproduct;": u"\u2210",
    "COPY;": u"\xa9",
    "COPY": u"\xa9",
    "copy;": u"\xa9",
    "copy": u"\xa9",
    "copysr;": u"\u2117",
    "CounterClockwiseContourIntegral;": u"\u2233",
    "crarr;": u"\u21b5",
    "Cross;": u"\u2a2f",
    "cross;": u"\u2717",
    "Cscr;": u"\U0001d49e",
    "cscr;": u"\U0001d4b8",
    "csub;": u"\u2acf",
    "csube;": u"\u2ad1",
    "csup;": u"\u2ad0",
    "csupe;": u"\u2ad2",
    "ctdot;": u"\u22ef",
    "cudarrl;": u"\u2938",
    "cudarrr;": u"\u2935",
    "cuepr;": u"\u22de",
    "cuesc;": u"\u22df",
    "cularr;": u"\u21b6",
    "cularrp;": u"\u293d",
    "Cup;": u"\u22d3",
    "cup;": u"\u222a",
    "cupbrcap;": u"\u2a48",
    "CupCap;": u"\u224d",
    "cupcap;": u"\u2a46",
    "cupcup;": u"\u2a4a",
    "cupdot;": u"\u228d",
    "cupor;": u"\u2a45",
    "cups;": u"\u222a"u"\ufe00",
    "curarr;": u"\u21b7",
    "curarrm;": u"\u293c",
    "curlyeqprec;": u"\u22de",
    "curlyeqsucc;": u"\u22df",
    "curlyvee;": u"\u22ce",
    "curlywedge;": u"\u22cf",
    "curren;": u"\xa4",
    "curren": u"\xa4",
    "curvearrowleft;": u"\u21b6",
    "curvearrowright;": u"\u21b7",
    "cuvee;": u"\u22ce",
    "cuwed;": u"\u22cf",
    "cwconint;": u"\u2232",
    "cwint;": u"\u2231",
    "cylcty;": u"\u232d",
    "Dagger;": u"\u2021",
    "dagger;": u"\u2020",
    "daleth;": u"\u2138",
    "Darr;": u"\u21a1",
    "dArr;": u"\u21d3",
    "darr;": u"\u2193",
    "dash;": u"\u2010",
    "Dashv;": u"\u2ae4",
    "dashv;": u"\u22a3",
    "dbkarow;": u"\u290f",
    "dblac;": u"\u02dd",
    "Dcaron;": u"\u010e",
    "dcaron;": u"\u010f",
    "Dcy;": u"\u0414",
    "dcy;": u"\u0434",
    "DD;": u"\u2145",
    "dd;": u"\u2146",
    "ddagger;": u"\u2021",
    "ddarr;": u"\u21ca",
    "DDotrahd;": u"\u2911",
    "ddotseq;": u"\u2a77",
    "deg;": u"\xb0",
    "deg": u"\xb0",
    "Del;": u"\u2207",
    "Delta;": u"\u0394",
    "delta;": u"\u03b4",
    "demptyv;": u"\u29b1",
    "dfisht;": u"\u297f",
    "Dfr;": u"\U0001d507",
    "dfr;": u"\U0001d521",
    "dHar;": u"\u2965",
    "dharl;": u"\u21c3",
    "dharr;": u"\u21c2",
    "DiacriticalAcute;": u"\xb4",
    "DiacriticalDot;": u"\u02d9",
    "DiacriticalDoubleAcute;": u"\u02dd",
    "DiacriticalGrave;": "\x60",
    "DiacriticalTilde;": u"\u02dc",
    "diam;": u"\u22c4",
    "Diamond;": u"\u22c4",
    "diamond;": u"\u22c4",
    "diamondsuit;": u"\u2666",
    "diams;": u"\u2666",
    "die;": u"\xa8",
    "DifferentialD;": u"\u2146",
    "digamma;": u"\u03dd",
    "disin;": u"\u22f2",
    "div;": u"\xf7",
    "divide;": u"\xf7",
    "divide": u"\xf7",
    "divideontimes;": u"\u22c7",
    "divonx;": u"\u22c7",
    "DJcy;": u"\u0402",
    "djcy;": u"\u0452",
    "dlcorn;": u"\u231e",
    "dlcrop;": u"\u230d",
    "dollar;": "\x24",
    "Dopf;": u"\U0001d53b",
    "dopf;": u"\U0001d555",
    "Dot;": u"\xa8",
    "dot;": u"\u02d9",
    "DotDot;": u"\u20dc",
    "doteq;": u"\u2250",
    "doteqdot;": u"\u2251",
    "DotEqual;": u"\u2250",
    "dotminus;": u"\u2238",
    "dotplus;": u"\u2214",
    "dotsquare;": u"\u22a1",
    "doublebarwedge;": u"\u2306",
    "DoubleContourIntegral;": u"\u222f",
    "DoubleDot;": u"\xa8",
    "DoubleDownArrow;": u"\u21d3",
    "DoubleLeftArrow;": u"\u21d0",
    "DoubleLeftRightArrow;": u"\u21d4",
    "DoubleLeftTee;": u"\u2ae4",
    "DoubleLongLeftArrow;": u"\u27f8",
    "DoubleLongLeftRightArrow;": u"\u27fa",
    "DoubleLongRightArrow;": u"\u27f9",
    "DoubleRightArrow;": u"\u21d2",
    "DoubleRightTee;": u"\u22a8",
    "DoubleUpArrow;": u"\u21d1",
    "DoubleUpDownArrow;": u"\u21d5",
    "DoubleVerticalBar;": u"\u2225",
    "DownArrow;": u"\u2193",
    "Downarrow;": u"\u21d3",
    "downarrow;": u"\u2193",
    "DownArrowBar;": u"\u2913",
    "DownArrowUpArrow;": u"\u21f5",
    "DownBreve;": u"\u0311",
    "downdownarrows;": u"\u21ca",
    "downharpoonleft;": u"\u21c3",
    "downharpoonright;": u"\u21c2",
    "DownLeftRightVector;": u"\u2950",
    "DownLeftTeeVector;": u"\u295e",
    "DownLeftVector;": u"\u21bd",
    "DownLeftVectorBar;": u"\u2956",
    "DownRightTeeVector;": u"\u295f",
    "DownRightVector;": u"\u21c1",
    "DownRightVectorBar;": u"\u2957",
    "DownTee;": u"\u22a4",
    "DownTeeArrow;": u"\u21a7",
    "drbkarow;": u"\u2910",
    "drcorn;": u"\u231f",
    "drcrop;": u"\u230c",
    "Dscr;": u"\U0001d49f",
    "dscr;": u"\U0001d4b9",
    "DScy;": u"\u0405",
    "dscy;": u"\u0455",
    "dsol;": u"\u29f6",
    "Dstrok;": u"\u0110",
    "dstrok;": u"\u0111",
    "dtdot;": u"\u22f1",
    "dtri;": u"\u25bf",
    "dtrif;": u"\u25be",
    "duarr;": u"\u21f5",
    "duhar;": u"\u296f",
    "dwangle;": u"\u29a6",
    "DZcy;": u"\u040f",
    "dzcy;": u"\u045f",
    "dzigrarr;": u"\u27ff",
    "Eacute;": u"\xc9",
    "Eacute": u"\xc9",
    "eacute;": u"\xe9",
    "eacute": u"\xe9",
    "easter;": u"\u2a6e",
    "Ecaron;": u"\u011a",
    "ecaron;": u"\u011b",
    "ecir;": u"\u2256",
    "Ecirc;": u"\xca",
    "Ecirc": u"\xca",
    "ecirc;": u"\xea",
    "ecirc": u"\xea",
    "ecolon;": u"\u2255",
    "Ecy;": u"\u042d",
    "ecy;": u"\u044d",
    "eDDot;": u"\u2a77",
    "Edot;": u"\u0116",
    "eDot;": u"\u2251",
    "edot;": u"\u0117",
    "ee;": u"\u2147",
    "efDot;": u"\u2252",
    "Efr;": u"\U0001d508",
    "efr;": u"\U0001d522",
    "eg;": u"\u2a9a",
    "Egrave;": u"\xc8",
    "Egrave": u"\xc8",
    "egrave;": u"\xe8",
    "egrave": u"\xe8",
    "egs;": u"\u2a96",
    "egsdot;": u"\u2a98",
    "el;": u"\u2a99",
    "Element;": u"\u2208",
    "elinters;": u"\u23e7",
    "ell;": u"\u2113",
    "els;": u"\u2a95",
    "elsdot;": u"\u2a97",
    "Emacr;": u"\u0112",
    "emacr;": u"\u0113",
    "empty;": u"\u2205",
    "emptyset;": u"\u2205",
    "EmptySmallSquare;": u"\u25fb",
    "emptyv;": u"\u2205",
    "EmptyVerySmallSquare;": u"\u25ab",
    "emsp;": u"\u2003",
    "emsp13;": u"\u2004",
    "emsp14;": u"\u2005",
    "ENG;": u"\u014a",
    "eng;": u"\u014b",
    "ensp;": u"\u2002",
    "Eogon;": u"\u0118",
    "eogon;": u"\u0119",
    "Eopf;": u"\U0001d53c",
    "eopf;": u"\U0001d556",
    "epar;": u"\u22d5",
    "eparsl;": u"\u29e3",
    "eplus;": u"\u2a71",
    "epsi;": u"\u03b5",
    "Epsilon;": u"\u0395",
    "epsilon;": u"\u03b5",
    "epsiv;": u"\u03f5",
    "eqcirc;": u"\u2256",
    "eqcolon;": u"\u2255",
    "eqsim;": u"\u2242",
    "eqslantgtr;": u"\u2a96",
    "eqslantless;": u"\u2a95",
    "Equal;": u"\u2a75",
    "equals;": "\x3d",
    "EqualTilde;": u"\u2242",
    "equest;": u"\u225f",
    "Equilibrium;": u"\u21cc",
    "equiv;": u"\u2261",
    "equivDD;": u"\u2a78",
    "eqvparsl;": u"\u29e5",
    "erarr;": u"\u2971",
    "erDot;": u"\u2253",
    "Escr;": u"\u2130",
    "escr;": u"\u212f",
    "esdot;": u"\u2250",
    "Esim;": u"\u2a73",
    "esim;": u"\u2242",
    "Eta;": u"\u0397",
    "eta;": u"\u03b7",
    "ETH;": u"\xd0",
    "ETH": u"\xd0",
    "eth;": u"\xf0",
    "eth": u"\xf0",
    "Euml;": u"\xcb",
    "Euml": u"\xcb",
    "euml;": u"\xeb",
    "euml": u"\xeb",
    "euro;": u"\u20ac",
    "excl;": "\x21",
    "exist;": u"\u2203",
    "Exists;": u"\u2203",
    "expectation;": u"\u2130",
    "ExponentialE;": u"\u2147",
    "exponentiale;": u"\u2147",
    "fallingdotseq;": u"\u2252",
    "Fcy;": u"\u0424",
    "fcy;": u"\u0444",
    "female;": u"\u2640",
    "ffilig;": u"\ufb03",
    "fflig;": u"\ufb00",
    "ffllig;": u"\ufb04",
    "Ffr;": u"\U0001d509",
    "ffr;": u"\U0001d523",
    "filig;": u"\ufb01",
    "FilledSmallSquare;": u"\u25fc",
    "FilledVerySmallSquare;": u"\u25aa",
    "fjlig;": "\x66""\x6a",
    "flat;": u"\u266d",
    "fllig;": u"\ufb02",
    "fltns;": u"\u25b1",
    "fnof;": u"\u0192",
    "Fopf;": u"\U0001d53d",
    "fopf;": u"\U0001d557",
    "ForAll;": u"\u2200",
    "forall;": u"\u2200",
    "fork;": u"\u22d4",
    "forkv;": u"\u2ad9",
    "Fouriertrf;": u"\u2131",
    "fpartint;": u"\u2a0d",
    "frac12;": u"\xbd",
    "frac12": u"\xbd",
    "frac13;": u"\u2153",
    "frac14;": u"\xbc",
    "frac14": u"\xbc",
    "frac15;": u"\u2155",
    "frac16;": u"\u2159",
    "frac18;": u"\u215b",
    "frac23;": u"\u2154",
    "frac25;": u"\u2156",
    "frac34;": u"\xbe",
    "frac34": u"\xbe",
    "frac35;": u"\u2157",
    "frac38;": u"\u215c",
    "frac45;": u"\u2158",
    "frac56;": u"\u215a",
    "frac58;": u"\u215d",
    "frac78;": u"\u215e",
    "frasl;": u"\u2044",
    "frown;": u"\u2322",
    "Fscr;": u"\u2131",
    "fscr;": u"\U0001d4bb",
    "gacute;": u"\u01f5",
    "Gamma;": u"\u0393",
    "gamma;": u"\u03b3",
    "Gammad;": u"\u03dc",
    "gammad;": u"\u03dd",
    "gap;": u"\u2a86",
    "Gbreve;": u"\u011e",
    "gbreve;": u"\u011f",
    "Gcedil;": u"\u0122",
    "Gcirc;": u"\u011c",
    "gcirc;": u"\u011d",
    "Gcy;": u"\u0413",
    "gcy;": u"\u0433",
    "Gdot;": u"\u0120",
    "gdot;": u"\u0121",
    "gE;": u"\u2267",
    "ge;": u"\u2265",
    "gEl;": u"\u2a8c",
    "gel;": u"\u22db",
    "geq;": u"\u2265",
    "geqq;": u"\u2267",
    "geqslant;": u"\u2a7e",
    "ges;": u"\u2a7e",
    "gescc;": u"\u2aa9",
    "gesdot;": u"\u2a80",
    "gesdoto;": u"\u2a82",
    "gesdotol;": u"\u2a84",
    "gesl;": u"\u22db"u"\ufe00",
    "gesles;": u"\u2a94",
    "Gfr;": u"\U0001d50a",
    "gfr;": u"\U0001d524",
    "Gg;": u"\u22d9",
    "gg;": u"\u226b",
    "ggg;": u"\u22d9",
    "gimel;": u"\u2137",
    "GJcy;": u"\u0403",
    "gjcy;": u"\u0453",
    "gl;": u"\u2277",
    "gla;": u"\u2aa5",
    "glE;": u"\u2a92",
    "glj;": u"\u2aa4",
    "gnap;": u"\u2a8a",
    "gnapprox;": u"\u2a8a",
    "gnE;": u"\u2269",
    "gne;": u"\u2a88",
    "gneq;": u"\u2a88",
    "gneqq;": u"\u2269",
    "gnsim;": u"\u22e7",
    "Gopf;": u"\U0001d53e",
    "gopf;": u"\U0001d558",
    "grave;": "\x60",
    "GreaterEqual;": u"\u2265",
    "GreaterEqualLess;": u"\u22db",
    "GreaterFullEqual;": u"\u2267",
    "GreaterGreater;": u"\u2aa2",
    "GreaterLess;": u"\u2277",
    "GreaterSlantEqual;": u"\u2a7e",
    "GreaterTilde;": u"\u2273",
    "Gscr;": u"\U0001d4a2",
    "gscr;": u"\u210a",
    "gsim;": u"\u2273",
    "gsime;": u"\u2a8e",
    "gsiml;": u"\u2a90",
    "GT;": "\x3e",
    "GT": "\x3e",
    "Gt;": u"\u226b",
    "gt;": "\x3e",
    "gt": "\x3e",
    "gtcc;": u"\u2aa7",
    "gtcir;": u"\u2a7a",
    "gtdot;": u"\u22d7",
    "gtlPar;": u"\u2995",
    "gtquest;": u"\u2a7c",
    "gtrapprox;": u"\u2a86",
    "gtrarr;": u"\u2978",
    "gtrdot;": u"\u22d7",
    "gtreqless;": u"\u22db",
    "gtreqqless;": u"\u2a8c",
    "gtrless;": u"\u2277",
    "gtrsim;": u"\u2273",
    "gvertneqq;": u"\u2269"u"\ufe00",
    "gvnE;": u"\u2269"u"\ufe00",
    "Hacek;": u"\u02c7",
    "hairsp;": u"\u200a",
    "half;": u"\xbd",
    "hamilt;": u"\u210b",
    "HARDcy;": u"\u042a",
    "hardcy;": u"\u044a",
    "hArr;": u"\u21d4",
    "harr;": u"\u2194",
    "harrcir;": u"\u2948",
    "harrw;": u"\u21ad",
    "Hat;": "\x5e",
    "hbar;": u"\u210f",
    "Hcirc;": u"\u0124",
    "hcirc;": u"\u0125",
    "hearts;": u"\u2665",
    "heartsuit;": u"\u2665",
    "hellip;": u"\u2026",
    "hercon;": u"\u22b9",
    "Hfr;": u"\u210c",
    "hfr;": u"\U0001d525",
    "HilbertSpace;": u"\u210b",
    "hksearow;": u"\u2925",
    "hkswarow;": u"\u2926",
    "hoarr;": u"\u21ff",
    "homtht;": u"\u223b",
    "hookleftarrow;": u"\u21a9",
    "hookrightarrow;": u"\u21aa",
    "Hopf;": u"\u210d",
    "hopf;": u"\U0001d559",
    "horbar;": u"\u2015",
    "HorizontalLine;": u"\u2500",
    "Hscr;": u"\u210b",
    "hscr;": u"\U0001d4bd",
    "hslash;": u"\u210f",
    "Hstrok;": u"\u0126",
    "hstrok;": u"\u0127",
    "HumpDownHump;": u"\u224e",
    "HumpEqual;": u"\u224f",
    "hybull;": u"\u2043",
    "hyphen;": u"\u2010",
    "Iacute;": u"\xcd",
    "Iacute": u"\xcd",
    "iacute;": u"\xed",
    "iacute": u"\xed",
    "ic;": u"\u2063",
    "Icirc;": u"\xce",
    "Icirc": u"\xce",
    "icirc;": u"\xee",
    "icirc": u"\xee",
    "Icy;": u"\u0418",
    "icy;": u"\u0438",
    "Idot;": u"\u0130",
    "IEcy;": u"\u0415",
    "iecy;": u"\u0435",
    "iexcl;": u"\xa1",
    "iexcl": u"\xa1",
    "iff;": u"\u21d4",
    "Ifr;": u"\u2111",
    "ifr;": u"\U0001d526",
    "Igrave;": u"\xcc",
    "Igrave": u"\xcc",
    "igrave;": u"\xec",
    "igrave": u"\xec",
    "ii;": u"\u2148",
    "iiiint;": u"\u2a0c",
    "iiint;": u"\u222d",
    "iinfin;": u"\u29dc",
    "iiota;": u"\u2129",
    "IJlig;": u"\u0132",
    "ijlig;": u"\u0133",
    "Im;": u"\u2111",
    "Imacr;": u"\u012a",
    "imacr;": u"\u012b",
    "image;": u"\u2111",
    "ImaginaryI;": u"\u2148",
    "imagline;": u"\u2110",
    "imagpart;": u"\u2111",
    "imath;": u"\u0131",
    "imof;": u"\u22b7",
    "imped;": u"\u01b5",
    "Implies;": u"\u21d2",
    "in;": u"\u2208",
    "incare;": u"\u2105",
    "infin;": u"\u221e",
    "infintie;": u"\u29dd",
    "inodot;": u"\u0131",
    "Int;": u"\u222c",
    "int;": u"\u222b",
    "intcal;": u"\u22ba",
    "integers;": u"\u2124",
    "Integral;": u"\u222b",
    "intercal;": u"\u22ba",
    "Intersection;": u"\u22c2",
    "intlarhk;": u"\u2a17",
    "intprod;": u"\u2a3c",
    "InvisibleComma;": u"\u2063",
    "InvisibleTimes;": u"\u2062",
    "IOcy;": u"\u0401",
    "iocy;": u"\u0451",
    "Iogon;": u"\u012e",
    "iogon;": u"\u012f",
    "Iopf;": u"\U0001d540",
    "iopf;": u"\U0001d55a",
    "Iota;": u"\u0399",
    "iota;": u"\u03b9",
    "iprod;": u"\u2a3c",
    "iquest;": u"\xbf",
    "iquest": u"\xbf",
    "Iscr;": u"\u2110",
    "iscr;": u"\U0001d4be",
    "isin;": u"\u2208",
    "isindot;": u"\u22f5",
    "isinE;": u"\u22f9",
    "isins;": u"\u22f4",
    "isinsv;": u"\u22f3",
    "isinv;": u"\u2208",
    "it;": u"\u2062",
    "Itilde;": u"\u0128",
    "itilde;": u"\u0129",
    "Iukcy;": u"\u0406",
    "iukcy;": u"\u0456",
    "Iuml;": u"\xcf",
    "Iuml": u"\xcf",
    "iuml;": u"\xef",
    "iuml": u"\xef",
    "Jcirc;": u"\u0134",
    "jcirc;": u"\u0135",
    "Jcy;": u"\u0419",
    "jcy;": u"\u0439",
    "Jfr;": u"\U0001d50d",
    "jfr;": u"\U0001d527",
    "jmath;": u"\u0237",
    "Jopf;": u"\U0001d541",
    "jopf;": u"\U0001d55b",
    "Jscr;": u"\U0001d4a5",
    "jscr;": u"\U0001d4bf",
    "Jsercy;": u"\u0408",
    "jsercy;": u"\u0458",
    "Jukcy;": u"\u0404",
    "jukcy;": u"\u0454",
    "Kappa;": u"\u039a",
    "kappa;": u"\u03ba",
    "kappav;": u"\u03f0",
    "Kcedil;": u"\u0136",
    "kcedil;": u"\u0137",
    "Kcy;": u"\u041a",
    "kcy;": u"\u043a",
    "Kfr;": u"\U0001d50e",
    "kfr;": u"\U0001d528",
    "kgreen;": u"\u0138",
    "KHcy;": u"\u0425",
    "khcy;": u"\u0445",
    "KJcy;": u"\u040c",
    "kjcy;": u"\u045c",
    "Kopf;": u"\U0001d542",
    "kopf;": u"\U0001d55c",
    "Kscr;": u"\U0001d4a6",
    "kscr;": u"\U0001d4c0",
    "lAarr;": u"\u21da",
    "Lacute;": u"\u0139",
    "lacute;": u"\u013a",
    "laemptyv;": u"\u29b4",
    "lagran;": u"\u2112",
    "Lambda;": u"\u039b",
    "lambda;": u"\u03bb",
    "Lang;": u"\u27ea",
    "lang;": u"\u27e8",
    "langd;": u"\u2991",
    "langle;": u"\u27e8",
    "lap;": u"\u2a85",
    "Laplacetrf;": u"\u2112",
    "laquo;": u"\xab",
    "laquo": u"\xab",
    "Larr;": u"\u219e",
    "lArr;": u"\u21d0",
    "larr;": u"\u2190",
    "larrb;": u"\u21e4",
    "larrbfs;": u"\u291f",
    "larrfs;": u"\u291d",
    "larrhk;": u"\u21a9",
    "larrlp;": u"\u21ab",
    "larrpl;": u"\u2939",
    "larrsim;": u"\u2973",
    "larrtl;": u"\u21a2",
    "lat;": u"\u2aab",
    "lAtail;": u"\u291b",
    "latail;": u"\u2919",
    "late;": u"\u2aad",
    "lates;": u"\u2aad"u"\ufe00",
    "lBarr;": u"\u290e",
    "lbarr;": u"\u290c",
    "lbbrk;": u"\u2772",
    "lbrace;": "\x7b",
    "lbrack;": "\x5b",
    "lbrke;": u"\u298b",
    "lbrksld;": u"\u298f",
    "lbrkslu;": u"\u298d",
    "Lcaron;": u"\u013d",
    "lcaron;": u"\u013e",
    "Lcedil;": u"\u013b",
    "lcedil;": u"\u013c",
    "lceil;": u"\u2308",
    "lcub;": "\x7b",
    "Lcy;": u"\u041b",
    "lcy;": u"\u043b",
    "ldca;": u"\u2936",
    "ldquo;": u"\u201c",
    "ldquor;": u"\u201e",
    "ldrdhar;": u"\u2967",
    "ldrushar;": u"\u294b",
    "ldsh;": u"\u21b2",
    "lE;": u"\u2266",
    "le;": u"\u2264",
    "LeftAngleBracket;": u"\u27e8",
    "LeftArrow;": u"\u2190",
    "Leftarrow;": u"\u21d0",
    "leftarrow;": u"\u2190",
    "LeftArrowBar;": u"\u21e4",
    "LeftArrowRightArrow;": u"\u21c6",
    "leftarrowtail;": u"\u21a2",
    "LeftCeiling;": u"\u2308",
    "LeftDoubleBracket;": u"\u27e6",
    "LeftDownTeeVector;": u"\u2961",
    "LeftDownVector;": u"\u21c3",
    "LeftDownVectorBar;": u"\u2959",
    "LeftFloor;": u"\u230a",
    "leftharpoondown;": u"\u21bd",
    "leftharpoonup;": u"\u21bc",
    "leftleftarrows;": u"\u21c7",
    "LeftRightArrow;": u"\u2194",
    "Leftrightarrow;": u"\u21d4",
    "leftrightarrow;": u"\u2194",
    "leftrightarrows;": u"\u21c6",
    "leftrightharpoons;": u"\u21cb",
    "leftrightsquigarrow;": u"\u21ad",
    "LeftRightVector;": u"\u294e",
    "LeftTee;": u"\u22a3",
    "LeftTeeArrow;": u"\u21a4",
    "LeftTeeVector;": u"\u295a",
    "leftthreetimes;": u"\u22cb",
    "LeftTriangle;": u"\u22b2",
    "LeftTriangleBar;": u"\u29cf",
    "LeftTriangleEqual;": u"\u22b4",
    "LeftUpDownVector;": u"\u2951",
    "LeftUpTeeVector;": u"\u2960",
    "LeftUpVector;": u"\u21bf",
    "LeftUpVectorBar;": u"\u2958",
    "LeftVector;": u"\u21bc",
    "LeftVectorBar;": u"\u2952",
    "lEg;": u"\u2a8b",
    "leg;": u"\u22da",
    "leq;": u"\u2264",
    "leqq;": u"\u2266",
    "leqslant;": u"\u2a7d",
    "les;": u"\u2a7d",
    "lescc;": u"\u2aa8",
    "lesdot;": u"\u2a7f",
    "lesdoto;": u"\u2a81",
    "lesdotor;": u"\u2a83",
    "lesg;": u"\u22da"u"\ufe00",
    "lesges;": u"\u2a93",
    "lessapprox;": u"\u2a85",
    "lessdot;": u"\u22d6",
    "lesseqgtr;": u"\u22da",
    "lesseqqgtr;": u"\u2a8b",
    "LessEqualGreater;": u"\u22da",
    "LessFullEqual;": u"\u2266",
    "LessGreater;": u"\u2276",
    "lessgtr;": u"\u2276",
    "LessLess;": u"\u2aa1",
    "lesssim;": u"\u2272",
    "LessSlantEqual;": u"\u2a7d",
    "LessTilde;": u"\u2272",
    "lfisht;": u"\u297c",
    "lfloor;": u"\u230a",
    "Lfr;": u"\U0001d50f",
    "lfr;": u"\U0001d529",
    "lg;": u"\u2276",
    "lgE;": u"\u2a91",
    "lHar;": u"\u2962",
    "lhard;": u"\u21bd",
    "lharu;": u"\u21bc",
    "lharul;": u"\u296a",
    "lhblk;": u"\u2584",
    "LJcy;": u"\u0409",
    "ljcy;": u"\u0459",
    "Ll;": u"\u22d8",
    "ll;": u"\u226a",
    "llarr;": u"\u21c7",
    "llcorner;": u"\u231e",
    "Lleftarrow;": u"\u21da",
    "llhard;": u"\u296b",
    "lltri;": u"\u25fa",
    "Lmidot;": u"\u013f",
    "lmidot;": u"\u0140",
    "lmoust;": u"\u23b0",
    "lmoustache;": u"\u23b0",
    "lnap;": u"\u2a89",
    "lnapprox;": u"\u2a89",
    "lnE;": u"\u2268",
    "lne;": u"\u2a87",
    "lneq;": u"\u2a87",
    "lneqq;": u"\u2268",
    "lnsim;": u"\u22e6",
    "loang;": u"\u27ec",
    "loarr;": u"\u21fd",
    "lobrk;": u"\u27e6",
    "LongLeftArrow;": u"\u27f5",
    "Longleftarrow;": u"\u27f8",
    "longleftarrow;": u"\u27f5",
    "LongLeftRightArrow;": u"\u27f7",
    "Longleftrightarrow;": u"\u27fa",
    "longleftrightarrow;": u"\u27f7",
    "longmapsto;": u"\u27fc",
    "LongRightArrow;": u"\u27f6",
    "Longrightarrow;": u"\u27f9",
    "longrightarrow;": u"\u27f6",
    "looparrowleft;": u"\u21ab",
    "looparrowright;": u"\u21ac",
    "lopar;": u"\u2985",
    "Lopf;": u"\U0001d543",
    "lopf;": u"\U0001d55d",
    "loplus;": u"\u2a2d",
    "lotimes;": u"\u2a34",
    "lowast;": u"\u2217",
    "lowbar;": "\x5f",
    "LowerLeftArrow;": u"\u2199",
    "LowerRightArrow;": u"\u2198",
    "loz;": u"\u25ca",
    "lozenge;": u"\u25ca",
    "lozf;": u"\u29eb",
    "lpar;": "\x28",
    "lparlt;": u"\u2993",
    "lrarr;": u"\u21c6",
    "lrcorner;": u"\u231f",
    "lrhar;": u"\u21cb",
    "lrhard;": u"\u296d",
    "lrm;": u"\u200e",
    "lrtri;": u"\u22bf",
    "lsaquo;": u"\u2039",
    "Lscr;": u"\u2112",
    "lscr;": u"\U0001d4c1",
    "Lsh;": u"\u21b0",
    "lsh;": u"\u21b0",
    "lsim;": u"\u2272",
    "lsime;": u"\u2a8d",
    "lsimg;": u"\u2a8f",
    "lsqb;": "\x5b",
    "lsquo;": u"\u2018",
    "lsquor;": u"\u201a",
    "Lstrok;": u"\u0141",
    "lstrok;": u"\u0142",
    "LT;": "\x3c",
    "LT": "\x3c",
    "Lt;": u"\u226a",
    "lt;": "\x3c",
    "lt": "\x3c",
    "ltcc;": u"\u2aa6",
    "ltcir;": u"\u2a79",
    "ltdot;": u"\u22d6",
    "lthree;": u"\u22cb",
    "ltimes;": u"\u22c9",
    "ltlarr;": u"\u2976",
    "ltquest;": u"\u2a7b",
    "ltri;": u"\u25c3",
    "ltrie;": u"\u22b4",
    "ltrif;": u"\u25c2",
    "ltrPar;": u"\u2996",
    "lurdshar;": u"\u294a",
    "luruhar;": u"\u2966",
    "lvertneqq;": u"\u2268"u"\ufe00",
    "lvnE;": u"\u2268"u"\ufe00",
    "macr;": u"\xaf",
    "macr": u"\xaf",
    "male;": u"\u2642",
    "malt;": u"\u2720",
    "maltese;": u"\u2720",
    "Map;": u"\u2905",
    "map;": u"\u21a6",
    "mapsto;": u"\u21a6",
    "mapstodown;": u"\u21a7",
    "mapstoleft;": u"\u21a4",
    "mapstoup;": u"\u21a5",
    "marker;": u"\u25ae",
    "mcomma;": u"\u2a29",
    "Mcy;": u"\u041c",
    "mcy;": u"\u043c",
    "mdash;": u"\u2014",
    "mDDot;": u"\u223a",
    "measuredangle;": u"\u2221",
    "MediumSpace;": u"\u205f",
    "Mellintrf;": u"\u2133",
    "Mfr;": u"\U0001d510",
    "mfr;": u"\U0001d52a",
    "mho;": u"\u2127",
    "micro;": u"\xb5",
    "micro": u"\xb5",
    "mid;": u"\u2223",
    "midast;": "\x2a",
    "midcir;": u"\u2af0",
    "middot;": u"\xb7",
    "middot": u"\xb7",
    "minus;": u"\u2212",
    "minusb;": u"\u229f",
    "minusd;": u"\u2238",
    "minusdu;": u"\u2a2a",
    "MinusPlus;": u"\u2213",
    "mlcp;": u"\u2adb",
    "mldr;": u"\u2026",
    "mnplus;": u"\u2213",
    "models;": u"\u22a7",
    "Mopf;": u"\U0001d544",
    "mopf;": u"\U0001d55e",
    "mp;": u"\u2213",
    "Mscr;": u"\u2133",
    "mscr;": u"\U0001d4c2",
    "mstpos;": u"\u223e",
    "Mu;": u"\u039c",
    "mu;": u"\u03bc",
    "multimap;": u"\u22b8",
    "mumap;": u"\u22b8",
    "nabla;": u"\u2207",
    "Nacute;": u"\u0143",
    "nacute;": u"\u0144",
    "nang;": u"\u2220"u"\u20d2",
    "nap;": u"\u2249",
    "napE;": u"\u2a70"u"\u0338",
    "napid;": u"\u224b"u"\u0338",
    "napos;": u"\u0149",
    "napprox;": u"\u2249",
    "natur;": u"\u266e",
    "natural;": u"\u266e",
    "naturals;": u"\u2115",
    "nbsp;": u"\xa0",
    "nbsp": u"\xa0",
    "nbump;": u"\u224e"u"\u0338",
    "nbumpe;": u"\u224f"u"\u0338",
    "ncap;": u"\u2a43",
    "Ncaron;": u"\u0147",
    "ncaron;": u"\u0148",
    "Ncedil;": u"\u0145",
    "ncedil;": u"\u0146",
    "ncong;": u"\u2247",
    "ncongdot;": u"\u2a6d"u"\u0338",
    "ncup;": u"\u2a42",
    "Ncy;": u"\u041d",
    "ncy;": u"\u043d",
    "ndash;": u"\u2013",
    "ne;": u"\u2260",
    "nearhk;": u"\u2924",
    "neArr;": u"\u21d7",
    "nearr;": u"\u2197",
    "nearrow;": u"\u2197",
    "nedot;": u"\u2250"u"\u0338",
    "NegativeMediumSpace;": u"\u200b",
    "NegativeThickSpace;": u"\u200b",
    "NegativeThinSpace;": u"\u200b",
    "NegativeVeryThinSpace;": u"\u200b",
    "nequiv;": u"\u2262",
    "nesear;": u"\u2928",
    "nesim;": u"\u2242"u"\u0338",
    "NestedGreaterGreater;": u"\u226b",
    "NestedLessLess;": u"\u226a",
    "NewLine;": "\x0a",
    "nexist;": u"\u2204",
    "nexists;": u"\u2204",
    "Nfr;": u"\U0001d511",
    "nfr;": u"\U0001d52b",
    "ngE;": u"\u2267"u"\u0338",
    "nge;": u"\u2271",
    "ngeq;": u"\u2271",
    "ngeqq;": u"\u2267"u"\u0338",
    "ngeqslant;": u"\u2a7e"u"\u0338",
    "nges;": u"\u2a7e"u"\u0338",
    "nGg;": u"\u22d9"u"\u0338",
    "ngsim;": u"\u2275",
    "nGt;": u"\u226b"u"\u20d2",
    "ngt;": u"\u226f",
    "ngtr;": u"\u226f",
    "nGtv;": u"\u226b"u"\u0338",
    "nhArr;": u"\u21ce",
    "nharr;": u"\u21ae",
    "nhpar;": u"\u2af2",
    "ni;": u"\u220b",
    "nis;": u"\u22fc",
    "nisd;": u"\u22fa",
    "niv;": u"\u220b",
    "NJcy;": u"\u040a",
    "njcy;": u"\u045a",
    "nlArr;": u"\u21cd",
    "nlarr;": u"\u219a",
    "nldr;": u"\u2025",
    "nlE;": u"\u2266"u"\u0338",
    "nle;": u"\u2270",
    "nLeftarrow;": u"\u21cd",
    "nleftarrow;": u"\u219a",
    "nLeftrightarrow;": u"\u21ce",
    "nleftrightarrow;": u"\u21ae",
    "nleq;": u"\u2270",
    "nleqq;": u"\u2266"u"\u0338",
    "nleqslant;": u"\u2a7d"u"\u0338",
    "nles;": u"\u2a7d"u"\u0338",
    "nless;": u"\u226e",
    "nLl;": u"\u22d8"u"\u0338",
    "nlsim;": u"\u2274",
    "nLt;": u"\u226a"u"\u20d2",
    "nlt;": u"\u226e",
    "nltri;": u"\u22ea",
    "nltrie;": u"\u22ec",
    "nLtv;": u"\u226a"u"\u0338",
    "nmid;": u"\u2224",
    "NoBreak;": u"\u2060",
    "NonBreakingSpace;": u"\xa0",
    "Nopf;": u"\u2115",
    "nopf;": u"\U0001d55f",
    "Not;": u"\u2aec",
    "not;": u"\xac",
    "not": u"\xac",
    "NotCongruent;": u"\u2262",
    "NotCupCap;": u"\u226d",
    "NotDoubleVerticalBar;": u"\u2226",
    "NotElement;": u"\u2209",
    "NotEqual;": u"\u2260",
    "NotEqualTilde;": u"\u2242"u"\u0338",
    "NotExists;": u"\u2204",
    "NotGreater;": u"\u226f",
    "NotGreaterEqual;": u"\u2271",
    "NotGreaterFullEqual;": u"\u2267"u"\u0338",
    "NotGreaterGreater;": u"\u226b"u"\u0338",
    "NotGreaterLess;": u"\u2279",
    "NotGreaterSlantEqual;": u"\u2a7e"u"\u0338",
    "NotGreaterTilde;": u"\u2275",
    "NotHumpDownHump;": u"\u224e"u"\u0338",
    "NotHumpEqual;": u"\u224f"u"\u0338",
    "notin;": u"\u2209",
    "notindot;": u"\u22f5"u"\u0338",
    "notinE;": u"\u22f9"u"\u0338",
    "notinva;": u"\u2209",
    "notinvb;": u"\u22f7",
    "notinvc;": u"\u22f6",
    "NotLeftTriangle;": u"\u22ea",
    "NotLeftTriangleBar;": u"\u29cf"u"\u0338",
    "NotLeftTriangleEqual;": u"\u22ec",
    "NotLess;": u"\u226e",
    "NotLessEqual;": u"\u2270",
    "NotLessGreater;": u"\u2278",
    "NotLessLess;": u"\u226a"u"\u0338",
    "NotLessSlantEqual;": u"\u2a7d"u"\u0338",
    "NotLessTilde;": u"\u2274",
    "NotNestedGreaterGreater;": u"\u2aa2"u"\u0338",
    "NotNestedLessLess;": u"\u2aa1"u"\u0338",
    "notni;": u"\u220c",
    "notniva;": u"\u220c",
    "notnivb;": u"\u22fe",
    "notnivc;": u"\u22fd",
    "NotPrecedes;": u"\u2280",
    "NotPrecedesEqual;": u"\u2aaf"u"\u0338",
    "NotPrecedesSlantEqual;": u"\u22e0",
    "NotReverseElement;": u"\u220c",
    "NotRightTriangle;": u"\u22eb",
    "NotRightTriangleBar;": u"\u29d0"u"\u0338",
    "NotRightTriangleEqual;": u"\u22ed",
    "NotSquareSubset;": u"\u228f"u"\u0338",
    "NotSquareSubsetEqual;": u"\u22e2",
    "NotSquareSuperset;": u"\u2290"u"\u0338",
    "NotSquareSupersetEqual;": u"\u22e3",
    "NotSubset;": u"\u2282"u"\u20d2",
    "NotSubsetEqual;": u"\u2288",
    "NotSucceeds;": u"\u2281",
    "NotSucceedsEqual;": u"\u2ab0"u"\u0338",
    "NotSucceedsSlantEqual;": u"\u22e1",
    "NotSucceedsTilde;": u"\u227f"u"\u0338",
    "NotSuperset;": u"\u2283"u"\u20d2",
    "NotSupersetEqual;": u"\u2289",
    "NotTilde;": u"\u2241",
    "NotTildeEqual;": u"\u2244",
    "NotTildeFullEqual;": u"\u2247",
    "NotTildeTilde;": u"\u2249",
    "NotVerticalBar;": u"\u2224",
    "npar;": u"\u2226",
    "nparallel;": u"\u2226",
    "nparsl;": u"\u2afd"u"\u20e5",
    "npart;": u"\u2202"u"\u0338",
    "npolint;": u"\u2a14",
    "npr;": u"\u2280",
    "nprcue;": u"\u22e0",
    "npre;": u"\u2aaf"u"\u0338",
    "nprec;": u"\u2280",
    "npreceq;": u"\u2aaf"u"\u0338",
    "nrArr;": u"\u21cf",
    "nrarr;": u"\u219b",
    "nrarrc;": u"\u2933"u"\u0338",
    "nrarrw;": u"\u219d"u"\u0338",
    "nRightarrow;": u"\u21cf",
    "nrightarrow;": u"\u219b",
    "nrtri;": u"\u22eb",
    "nrtrie;": u"\u22ed",
    "nsc;": u"\u2281",
    "nsccue;": u"\u22e1",
    "nsce;": u"\u2ab0"u"\u0338",
    "Nscr;": u"\U0001d4a9",
    "nscr;": u"\U0001d4c3",
    "nshortmid;": u"\u2224",
    "nshortparallel;": u"\u2226",
    "nsim;": u"\u2241",
    "nsime;": u"\u2244",
    "nsimeq;": u"\u2244",
    "nsmid;": u"\u2224",
    "nspar;": u"\u2226",
    "nsqsube;": u"\u22e2",
    "nsqsupe;": u"\u22e3",
    "nsub;": u"\u2284",
    "nsubE;": u"\u2ac5"u"\u0338",
    "nsube;": u"\u2288",
    "nsubset;": u"\u2282"u"\u20d2",
    "nsubseteq;": u"\u2288",
    "nsubseteqq;": u"\u2ac5"u"\u0338",
    "nsucc;": u"\u2281",
    "nsucceq;": u"\u2ab0"u"\u0338",
    "nsup;": u"\u2285",
    "nsupE;": u"\u2ac6"u"\u0338",
    "nsupe;": u"\u2289",
    "nsupset;": u"\u2283"u"\u20d2",
    "nsupseteq;": u"\u2289",
    "nsupseteqq;": u"\u2ac6"u"\u0338",
    "ntgl;": u"\u2279",
    "Ntilde;": u"\xd1",
    "Ntilde": u"\xd1",
    "ntilde;": u"\xf1",
    "ntilde": u"\xf1",
    "ntlg;": u"\u2278",
    "ntriangleleft;": u"\u22ea",
    "ntrianglelefteq;": u"\u22ec",
    "ntriangleright;": u"\u22eb",
    "ntrianglerighteq;": u"\u22ed",
    "Nu;": u"\u039d",
    "nu;": u"\u03bd",
    "num;": "\x23",
    "numero;": u"\u2116",
    "numsp;": u"\u2007",
    "nvap;": u"\u224d"u"\u20d2",
    "nVDash;": u"\u22af",
    "nVdash;": u"\u22ae",
    "nvDash;": u"\u22ad",
    "nvdash;": u"\u22ac",
    "nvge;": u"\u2265"u"\u20d2",
    "nvgt;": "\x3e"u"\u20d2",
    "nvHarr;": u"\u2904",
    "nvinfin;": u"\u29de",
    "nvlArr;": u"\u2902",
    "nvle;": u"\u2264"u"\u20d2",
    "nvlt;": "\x3c"u"\u20d2",
    "nvltrie;": u"\u22b4"u"\u20d2",
    "nvrArr;": u"\u2903",
    "nvrtrie;": u"\u22b5"u"\u20d2",
    "nvsim;": u"\u223c"u"\u20d2",
    "nwarhk;": u"\u2923",
    "nwArr;": u"\u21d6",
    "nwarr;": u"\u2196",
    "nwarrow;": u"\u2196",
    "nwnear;": u"\u2927",
    "Oacute;": u"\xd3",
    "Oacute": u"\xd3",
    "oacute;": u"\xf3",
    "oacute": u"\xf3",
    "oast;": u"\u229b",
    "ocir;": u"\u229a",
    "Ocirc;": u"\xd4",
    "Ocirc": u"\xd4",
    "ocirc;": u"\xf4",
    "ocirc": u"\xf4",
    "Ocy;": u"\u041e",
    "ocy;": u"\u043e",
    "odash;": u"\u229d",
    "Odblac;": u"\u0150",
    "odblac;": u"\u0151",
    "odiv;": u"\u2a38",
    "odot;": u"\u2299",
    "odsold;": u"\u29bc",
    "OElig;": u"\u0152",
    "oelig;": u"\u0153",
    "ofcir;": u"\u29bf",
    "Ofr;": u"\U0001d512",
    "ofr;": u"\U0001d52c",
    "ogon;": u"\u02db",
    "Ograve;": u"\xd2",
    "Ograve": u"\xd2",
    "ograve;": u"\xf2",
    "ograve": u"\xf2",
    "ogt;": u"\u29c1",
    "ohbar;": u"\u29b5",
    "ohm;": u"\u03a9",
    "oint;": u"\u222e",
    "olarr;": u"\u21ba",
    "olcir;": u"\u29be",
    "olcross;": u"\u29bb",
    "oline;": u"\u203e",
    "olt;": u"\u29c0",
    "Omacr;": u"\u014c",
    "omacr;": u"\u014d",
    "Omega;": u"\u03a9",
    "omega;": u"\u03c9",
    "Omicron;": u"\u039f",
    "omicron;": u"\u03bf",
    "omid;": u"\u29b6",
    "ominus;": u"\u2296",
    "Oopf;": u"\U0001d546",
    "oopf;": u"\U0001d560",
    "opar;": u"\u29b7",
    "OpenCurlyDoubleQuote;": u"\u201c",
    "OpenCurlyQuote;": u"\u2018",
    "operp;": u"\u29b9",
    "oplus;": u"\u2295",
    "Or;": u"\u2a54",
    "or;": u"\u2228",
    "orarr;": u"\u21bb",
    "ord;": u"\u2a5d",
    "order;": u"\u2134",
    "orderof;": u"\u2134",
    "ordf;": u"\xaa",
    "ordf": u"\xaa",
    "ordm;": u"\xba",
    "ordm": u"\xba",
    "origof;": u"\u22b6",
    "oror;": u"\u2a56",
    "orslope;": u"\u2a57",
    "orv;": u"\u2a5b",
    "oS;": u"\u24c8",
    "Oscr;": u"\U0001d4aa",
    "oscr;": u"\u2134",
    "Oslash;": u"\xd8",
    "Oslash": u"\xd8",
    "oslash;": u"\xf8",
    "oslash": u"\xf8",
    "osol;": u"\u2298",
    "Otilde;": u"\xd5",
    "Otilde": u"\xd5",
    "otilde;": u"\xf5",
    "otilde": u"\xf5",
    "Otimes;": u"\u2a37",
    "otimes;": u"\u2297",
    "otimesas;": u"\u2a36",
    "Ouml;": u"\xd6",
    "Ouml": u"\xd6",
    "ouml;": u"\xf6",
    "ouml": u"\xf6",
    "ovbar;": u"\u233d",
    "OverBar;": u"\u203e",
    "OverBrace;": u"\u23de",
    "OverBracket;": u"\u23b4",
    "OverParenthesis;": u"\u23dc",
    "par;": u"\u2225",
    "para;": u"\xb6",
    "para": u"\xb6",
    "parallel;": u"\u2225",
    "parsim;": u"\u2af3",
    "parsl;": u"\u2afd",
    "part;": u"\u2202",
    "PartialD;": u"\u2202",
    "Pcy;": u"\u041f",
    "pcy;": u"\u043f",
    "percnt;": "\x25",
    "period;": "\x2e",
    "permil;": u"\u2030",
    "perp;": u"\u22a5",
    "pertenk;": u"\u2031",
    "Pfr;": u"\U0001d513",
    "pfr;": u"\U0001d52d",
    "Phi;": u"\u03a6",
    "phi;": u"\u03c6",
    "phiv;": u"\u03d5",
    "phmmat;": u"\u2133",
    "phone;": u"\u260e",
    "Pi;": u"\u03a0",
    "pi;": u"\u03c0",
    "pitchfork;": u"\u22d4",
    "piv;": u"\u03d6",
    "planck;": u"\u210f",
    "planckh;": u"\u210e",
    "plankv;": u"\u210f",
    "plus;": "\x2b",
    "plusacir;": u"\u2a23",
    "plusb;": u"\u229e",
    "pluscir;": u"\u2a22",
    "plusdo;": u"\u2214",
    "plusdu;": u"\u2a25",
    "pluse;": u"\u2a72",
    "PlusMinus;": u"\xb1",
    "plusmn;": u"\xb1",
    "plusmn": u"\xb1",
    "plussim;": u"\u2a26",
    "plustwo;": u"\u2a27",
    "pm;": u"\xb1",
    "Poincareplane;": u"\u210c",
    "pointint;": u"\u2a15",
    "Popf;": u"\u2119",
    "popf;": u"\U0001d561",
    "pound;": u"\xa3",
    "pound": u"\xa3",
    "Pr;": u"\u2abb",
    "pr;": u"\u227a",
    "prap;": u"\u2ab7",
    "prcue;": u"\u227c",
    "prE;": u"\u2ab3",
    "pre;": u"\u2aaf",
    "prec;": u"\u227a",
    "precapprox;": u"\u2ab7",
    "preccurlyeq;": u"\u227c",
    "Precedes;": u"\u227a",
    "PrecedesEqual;": u"\u2aaf",
    "PrecedesSlantEqual;": u"\u227c",
    "PrecedesTilde;": u"\u227e",
    "preceq;": u"\u2aaf",
    "precnapprox;": u"\u2ab9",
    "precneqq;": u"\u2ab5",
    "precnsim;": u"\u22e8",
    "precsim;": u"\u227e",
    "Prime;": u"\u2033",
    "prime;": u"\u2032",
    "primes;": u"\u2119",
    "prnap;": u"\u2ab9",
    "prnE;": u"\u2ab5",
    "prnsim;": u"\u22e8",
    "prod;": u"\u220f",
    "Product;": u"\u220f",
    "profalar;": u"\u232e",
    "profline;": u"\u2312",
    "profsurf;": u"\u2313",
    "prop;": u"\u221d",
    "Proportion;": u"\u2237",
    "Proportional;": u"\u221d",
    "propto;": u"\u221d",
    "prsim;": u"\u227e",
    "prurel;": u"\u22b0",
    "Pscr;": u"\U0001d4ab",
    "pscr;": u"\U0001d4c5",
    "Psi;": u"\u03a8",
    "psi;": u"\u03c8",
    "puncsp;": u"\u2008",
    "Qfr;": u"\U0001d514",
    "qfr;": u"\U0001d52e",
    "qint;": u"\u2a0c",
    "Qopf;": u"\u211a",
    "qopf;": u"\U0001d562",
    "qprime;": u"\u2057",
    "Qscr;": u"\U0001d4ac",
    "qscr;": u"\U0001d4c6",
    "quaternions;": u"\u210d",
    "quatint;": u"\u2a16",
    "quest;": "\x3f",
    "questeq;": u"\u225f",
    "QUOT;": "\x22",
    "QUOT": "\x22",
    "quot;": "\x22",
    "quot": "\x22",
    "rAarr;": u"\u21db",
    "race;": u"\u223d"u"\u0331",
    "Racute;": u"\u0154",
    "racute;": u"\u0155",
    "radic;": u"\u221a",
    "raemptyv;": u"\u29b3",
    "Rang;": u"\u27eb",
    "rang;": u"\u27e9",
    "rangd;": u"\u2992",
    "range;": u"\u29a5",
    "rangle;": u"\u27e9",
    "raquo;": u"\xbb",
    "raquo": u"\xbb",
    "Rarr;": u"\u21a0",
    "rArr;": u"\u21d2",
    "rarr;": u"\u2192",
    "rarrap;": u"\u2975",
    "rarrb;": u"\u21e5",
    "rarrbfs;": u"\u2920",
    "rarrc;": u"\u2933",
    "rarrfs;": u"\u291e",
    "rarrhk;": u"\u21aa",
    "rarrlp;": u"\u21ac",
    "rarrpl;": u"\u2945",
    "rarrsim;": u"\u2974",
    "Rarrtl;": u"\u2916",
    "rarrtl;": u"\u21a3",
    "rarrw;": u"\u219d",
    "rAtail;": u"\u291c",
    "ratail;": u"\u291a",
    "ratio;": u"\u2236",
    "rationals;": u"\u211a",
    "RBarr;": u"\u2910",
    "rBarr;": u"\u290f",
    "rbarr;": u"\u290d",
    "rbbrk;": u"\u2773",
    "rbrace;": "\x7d",
    "rbrack;": "\x5d",
    "rbrke;": u"\u298c",
    "rbrksld;": u"\u298e",
    "rbrkslu;": u"\u2990",
    "Rcaron;": u"\u0158",
    "rcaron;": u"\u0159",
    "Rcedil;": u"\u0156",
    "rcedil;": u"\u0157",
    "rceil;": u"\u2309",
    "rcub;": "\x7d",
    "Rcy;": u"\u0420",
    "rcy;": u"\u0440",
    "rdca;": u"\u2937",
    "rdldhar;": u"\u2969",
    "rdquo;": u"\u201d",
    "rdquor;": u"\u201d",
    "rdsh;": u"\u21b3",
    "Re;": u"\u211c",
    "real;": u"\u211c",
    "realine;": u"\u211b",
    "realpart;": u"\u211c",
    "reals;": u"\u211d",
    "rect;": u"\u25ad",
    "REG;": u"\xae",
    "REG": u"\xae",
    "reg;": u"\xae",
    "reg": u"\xae",
    "ReverseElement;": u"\u220b",
    "ReverseEquilibrium;": u"\u21cb",
    "ReverseUpEquilibrium;": u"\u296f",
    "rfisht;": u"\u297d",
    "rfloor;": u"\u230b",
    "Rfr;": u"\u211c",
    "rfr;": u"\U0001d52f",
    "rHar;": u"\u2964",
    "rhard;": u"\u21c1",
    "rharu;": u"\u21c0",
    "rharul;": u"\u296c",
    "Rho;": u"\u03a1",
    "rho;": u"\u03c1",
    "rhov;": u"\u03f1",
    "RightAngleBracket;": u"\u27e9",
    "RightArrow;": u"\u2192",
    "Rightarrow;": u"\u21d2",
    "rightarrow;": u"\u2192",
    "RightArrowBar;": u"\u21e5",
    "RightArrowLeftArrow;": u"\u21c4",
    "rightarrowtail;": u"\u21a3",
    "RightCeiling;": u"\u2309",
    "RightDoubleBracket;": u"\u27e7",
    "RightDownTeeVector;": u"\u295d",
    "RightDownVector;": u"\u21c2",
    "RightDownVectorBar;": u"\u2955",
    "RightFloor;": u"\u230b",
    "rightharpoondown;": u"\u21c1",
    "rightharpoonup;": u"\u21c0",
    "rightleftarrows;": u"\u21c4",
    "rightleftharpoons;": u"\u21cc",
    "rightrightarrows;": u"\u21c9",
    "rightsquigarrow;": u"\u219d",
    "RightTee;": u"\u22a2",
    "RightTeeArrow;": u"\u21a6",
    "RightTeeVector;": u"\u295b",
    "rightthreetimes;": u"\u22cc",
    "RightTriangle;": u"\u22b3",
    "RightTriangleBar;": u"\u29d0",
    "RightTriangleEqual;": u"\u22b5",
    "RightUpDownVector;": u"\u294f",
    "RightUpTeeVector;": u"\u295c",
    "RightUpVector;": u"\u21be",
    "RightUpVectorBar;": u"\u2954",
    "RightVector;": u"\u21c0",
    "RightVectorBar;": u"\u2953",
    "ring;": u"\u02da",
    "risingdotseq;": u"\u2253",
    "rlarr;": u"\u21c4",
    "rlhar;": u"\u21cc",
    "rlm;": u"\u200f",
    "rmoust;": u"\u23b1",
    "rmoustache;": u"\u23b1",
    "rnmid;": u"\u2aee",
    "roang;": u"\u27ed",
    "roarr;": u"\u21fe",
    "robrk;": u"\u27e7",
    "ropar;": u"\u2986",
    "Ropf;": u"\u211d",
    "ropf;": u"\U0001d563",
    "roplus;": u"\u2a2e",
    "rotimes;": u"\u2a35",
    "RoundImplies;": u"\u2970",
    "rpar;": "\x29",
    "rpargt;": u"\u2994",
    "rppolint;": u"\u2a12",
    "rrarr;": u"\u21c9",
    "Rrightarrow;": u"\u21db",
    "rsaquo;": u"\u203a",
    "Rscr;": u"\u211b",
    "rscr;": u"\U0001d4c7",
    "Rsh;": u"\u21b1",
    "rsh;": u"\u21b1",
    "rsqb;": "\x5d",
    "rsquo;": u"\u2019",
    "rsquor;": u"\u2019",
    "rthree;": u"\u22cc",
    "rtimes;": u"\u22ca",
    "rtri;": u"\u25b9",
    "rtrie;": u"\u22b5",
    "rtrif;": u"\u25b8",
    "rtriltri;": u"\u29ce",
    "RuleDelayed;": u"\u29f4",
    "ruluhar;": u"\u2968",
    "rx;": u"\u211e",
    "Sacute;": u"\u015a",
    "sacute;": u"\u015b",
    "sbquo;": u"\u201a",
    "Sc;": u"\u2abc",
    "sc;": u"\u227b",
    "scap;": u"\u2ab8",
    "Scaron;": u"\u0160",
    "scaron;": u"\u0161",
    "sccue;": u"\u227d",
    "scE;": u"\u2ab4",
    "sce;": u"\u2ab0",
    "Scedil;": u"\u015e",
    "scedil;": u"\u015f",
    "Scirc;": u"\u015c",
    "scirc;": u"\u015d",
    "scnap;": u"\u2aba",
    "scnE;": u"\u2ab6",
    "scnsim;": u"\u22e9",
    "scpolint;": u"\u2a13",
    "scsim;": u"\u227f",
    "Scy;": u"\u0421",
    "scy;": u"\u0441",
    "sdot;": u"\u22c5",
    "sdotb;": u"\u22a1",
    "sdote;": u"\u2a66",
    "searhk;": u"\u2925",
    "seArr;": u"\u21d8",
    "searr;": u"\u2198",
    "searrow;": u"\u2198",
    "sect;": u"\xa7",
    "sect": u"\xa7",
    "semi;": "\x3b",
    "seswar;": u"\u2929",
    "setminus;": u"\u2216",
    "setmn;": u"\u2216",
    "sext;": u"\u2736",
    "Sfr;": u"\U0001d516",
    "sfr;": u"\U0001d530",
    "sfrown;": u"\u2322",
    "sharp;": u"\u266f",
    "SHCHcy;": u"\u0429",
    "shchcy;": u"\u0449",
    "SHcy;": u"\u0428",
    "shcy;": u"\u0448",
    "ShortDownArrow;": u"\u2193",
    "ShortLeftArrow;": u"\u2190",
    "shortmid;": u"\u2223",
    "shortparallel;": u"\u2225",
    "ShortRightArrow;": u"\u2192",
    "ShortUpArrow;": u"\u2191",
    "shy;": u"\xad",
    "shy": u"\xad",
    "Sigma;": u"\u03a3",
    "sigma;": u"\u03c3",
    "sigmaf;": u"\u03c2",
    "sigmav;": u"\u03c2",
    "sim;": u"\u223c",
    "simdot;": u"\u2a6a",
    "sime;": u"\u2243",
    "simeq;": u"\u2243",
    "simg;": u"\u2a9e",
    "simgE;": u"\u2aa0",
    "siml;": u"\u2a9d",
    "simlE;": u"\u2a9f",
    "simne;": u"\u2246",
    "simplus;": u"\u2a24",
    "simrarr;": u"\u2972",
    "slarr;": u"\u2190",
    "SmallCircle;": u"\u2218",
    "smallsetminus;": u"\u2216",
    "smashp;": u"\u2a33",
    "smeparsl;": u"\u29e4",
    "smid;": u"\u2223",
    "smile;": u"\u2323",
    "smt;": u"\u2aaa",
    "smte;": u"\u2aac",
    "smtes;": u"\u2aac"u"\ufe00",
    "SOFTcy;": u"\u042c",
    "softcy;": u"\u044c",
    "sol;": "\x2f",
    "solb;": u"\u29c4",
    "solbar;": u"\u233f",
    "Sopf;": u"\U0001d54a",
    "sopf;": u"\U0001d564",
    "spades;": u"\u2660",
    "spadesuit;": u"\u2660",
    "spar;": u"\u2225",
    "sqcap;": u"\u2293",
    "sqcaps;": u"\u2293"u"\ufe00",
    "sqcup;": u"\u2294",
    "sqcups;": u"\u2294"u"\ufe00",
    "Sqrt;": u"\u221a",
    "sqsub;": u"\u228f",
    "sqsube;": u"\u2291",
    "sqsubset;": u"\u228f",
    "sqsubseteq;": u"\u2291",
    "sqsup;": u"\u2290",
    "sqsupe;": u"\u2292",
    "sqsupset;": u"\u2290",
    "sqsupseteq;": u"\u2292",
    "squ;": u"\u25a1",
    "Square;": u"\u25a1",
    "square;": u"\u25a1",
    "SquareIntersection;": u"\u2293",
    "SquareSubset;": u"\u228f",
    "SquareSubsetEqual;": u"\u2291",
    "SquareSuperset;": u"\u2290",
    "SquareSupersetEqual;": u"\u2292",
    "SquareUnion;": u"\u2294",
    "squarf;": u"\u25aa",
    "squf;": u"\u25aa",
    "srarr;": u"\u2192",
    "Sscr;": u"\U0001d4ae",
    "sscr;": u"\U0001d4c8",
    "ssetmn;": u"\u2216",
    "ssmile;": u"\u2323",
    "sstarf;": u"\u22c6",
    "Star;": u"\u22c6",
    "star;": u"\u2606",
    "starf;": u"\u2605",
    "straightepsilon;": u"\u03f5",
    "straightphi;": u"\u03d5",
    "strns;": u"\xaf",
    "Sub;": u"\u22d0",
    "sub;": u"\u2282",
    "subdot;": u"\u2abd",
    "subE;": u"\u2ac5",
    "sube;": u"\u2286",
    "subedot;": u"\u2ac3",
    "submult;": u"\u2ac1",
    "subnE;": u"\u2acb",
    "subne;": u"\u228a",
    "subplus;": u"\u2abf",
    "subrarr;": u"\u2979",
    "Subset;": u"\u22d0",
    "subset;": u"\u2282",
    "subseteq;": u"\u2286",
    "subseteqq;": u"\u2ac5",
    "SubsetEqual;": u"\u2286",
    "subsetneq;": u"\u228a",
    "subsetneqq;": u"\u2acb",
    "subsim;": u"\u2ac7",
    "subsub;": u"\u2ad5",
    "subsup;": u"\u2ad3",
    "succ;": u"\u227b",
    "succapprox;": u"\u2ab8",
    "succcurlyeq;": u"\u227d",
    "Succeeds;": u"\u227b",
    "SucceedsEqual;": u"\u2ab0",
    "SucceedsSlantEqual;": u"\u227d",
    "SucceedsTilde;": u"\u227f",
    "succeq;": u"\u2ab0",
    "succnapprox;": u"\u2aba",
    "succneqq;": u"\u2ab6",
    "succnsim;": u"\u22e9",
    "succsim;": u"\u227f",
    "SuchThat;": u"\u220b",
    "Sum;": u"\u2211",
    "sum;": u"\u2211",
    "sung;": u"\u266a",
    "Sup;": u"\u22d1",
    "sup;": u"\u2283",
    "sup1;": u"\xb9",
    "sup1": u"\xb9",
    "sup2;": u"\xb2",
    "sup2": u"\xb2",
    "sup3;": u"\xb3",
    "sup3": u"\xb3",
    "supdot;": u"\u2abe",
    "supdsub;": u"\u2ad8",
    "supE;": u"\u2ac6",
    "supe;": u"\u2287",
    "supedot;": u"\u2ac4",
    "Superset;": u"\u2283",
    "SupersetEqual;": u"\u2287",
    "suphsol;": u"\u27c9",
    "suphsub;": u"\u2ad7",
    "suplarr;": u"\u297b",
    "supmult;": u"\u2ac2",
    "supnE;": u"\u2acc",
    "supne;": u"\u228b",
    "supplus;": u"\u2ac0",
    "Supset;": u"\u22d1",
    "supset;": u"\u2283",
    "supseteq;": u"\u2287",
    "supseteqq;": u"\u2ac6",
    "supsetneq;": u"\u228b",
    "supsetneqq;": u"\u2acc",
    "supsim;": u"\u2ac8",
    "supsub;": u"\u2ad4",
    "supsup;": u"\u2ad6",
    "swarhk;": u"\u2926",
    "swArr;": u"\u21d9",
    "swarr;": u"\u2199",
    "swarrow;": u"\u2199",
    "swnwar;": u"\u292a",
    "szlig;": u"\xdf",
    "szlig": u"\xdf",
    "Tab;": "\x09",
    "target;": u"\u2316",
    "Tau;": u"\u03a4",
    "tau;": u"\u03c4",
    "tbrk;": u"\u23b4",
    "Tcaron;": u"\u0164",
    "tcaron;": u"\u0165",
    "Tcedil;": u"\u0162",
    "tcedil;": u"\u0163",
    "Tcy;": u"\u0422",
    "tcy;": u"\u0442",
    "tdot;": u"\u20db",
    "telrec;": u"\u2315",
    "Tfr;": u"\U0001d517",
    "tfr;": u"\U0001d531",
    "there4;": u"\u2234",
    "Therefore;": u"\u2234",
    "therefore;": u"\u2234",
    "Theta;": u"\u0398",
    "theta;": u"\u03b8",
    "thetasym;": u"\u03d1",
    "thetav;": u"\u03d1",
    "thickapprox;": u"\u2248",
    "thicksim;": u"\u223c",
    "ThickSpace;": u"\u205f"u"\u200a",
    "thinsp;": u"\u2009",
    "ThinSpace;": u"\u2009",
    "thkap;": u"\u2248",
    "thksim;": u"\u223c",
    "THORN;": u"\xde",
    "THORN": u"\xde",
    "thorn;": u"\xfe",
    "thorn": u"\xfe",
    "Tilde;": u"\u223c",
    "tilde;": u"\u02dc",
    "TildeEqual;": u"\u2243",
    "TildeFullEqual;": u"\u2245",
    "TildeTilde;": u"\u2248",
    "times;": u"\xd7",
    "times": u"\xd7",
    "timesb;": u"\u22a0",
    "timesbar;": u"\u2a31",
    "timesd;": u"\u2a30",
    "tint;": u"\u222d",
    "toea;": u"\u2928",
    "top;": u"\u22a4",
    "topbot;": u"\u2336",
    "topcir;": u"\u2af1",
    "Topf;": u"\U0001d54b",
    "topf;": u"\U0001d565",
    "topfork;": u"\u2ada",
    "tosa;": u"\u2929",
    "tprime;": u"\u2034",
    "TRADE;": u"\u2122",
    "trade;": u"\u2122",
    "triangle;": u"\u25b5",
    "triangledown;": u"\u25bf",
    "triangleleft;": u"\u25c3",
    "trianglelefteq;": u"\u22b4",
    "triangleq;": u"\u225c",
    "triangleright;": u"\u25b9",
    "trianglerighteq;": u"\u22b5",
    "tridot;": u"\u25ec",
    "trie;": u"\u225c",
    "triminus;": u"\u2a3a",
    "TripleDot;": u"\u20db",
    "triplus;": u"\u2a39",
    "trisb;": u"\u29cd",
    "tritime;": u"\u2a3b",
    "trpezium;": u"\u23e2",
    "Tscr;": u"\U0001d4af",
    "tscr;": u"\U0001d4c9",
    "TScy;": u"\u0426",
    "tscy;": u"\u0446",
    "TSHcy;": u"\u040b",
    "tshcy;": u"\u045b",
    "Tstrok;": u"\u0166",
    "tstrok;": u"\u0167",
    "twixt;": u"\u226c",
    "twoheadleftarrow;": u"\u219e",
    "twoheadrightarrow;": u"\u21a0",
    "Uacute;": u"\xda",
    "Uacute": u"\xda",
    "uacute;": u"\xfa",
    "uacute": u"\xfa",
    "Uarr;": u"\u219f",
    "uArr;": u"\u21d1",
    "uarr;": u"\u2191",
    "Uarrocir;": u"\u2949",
    "Ubrcy;": u"\u040e",
    "ubrcy;": u"\u045e",
    "Ubreve;": u"\u016c",
    "ubreve;": u"\u016d",
    "Ucirc;": u"\xdb",
    "Ucirc": u"\xdb",
    "ucirc;": u"\xfb",
    "ucirc": u"\xfb",
    "Ucy;": u"\u0423",
    "ucy;": u"\u0443",
    "udarr;": u"\u21c5",
    "Udblac;": u"\u0170",
    "udblac;": u"\u0171",
    "udhar;": u"\u296e",
    "ufisht;": u"\u297e",
    "Ufr;": u"\U0001d518",
    "ufr;": u"\U0001d532",
    "Ugrave;": u"\xd9",
    "Ugrave": u"\xd9",
    "ugrave;": u"\xf9",
    "ugrave": u"\xf9",
    "uHar;": u"\u2963",
    "uharl;": u"\u21bf",
    "uharr;": u"\u21be",
    "uhblk;": u"\u2580",
    "ulcorn;": u"\u231c",
    "ulcorner;": u"\u231c",
    "ulcrop;": u"\u230f",
    "ultri;": u"\u25f8",
    "Umacr;": u"\u016a",
    "umacr;": u"\u016b",
    "uml;": u"\xa8",
    "uml": u"\xa8",
    "UnderBar;": "\x5f",
    "UnderBrace;": u"\u23df",
    "UnderBracket;": u"\u23b5",
    "UnderParenthesis;": u"\u23dd",
    "Union;": u"\u22c3",
    "UnionPlus;": u"\u228e",
    "Uogon;": u"\u0172",
    "uogon;": u"\u0173",
    "Uopf;": u"\U0001d54c",
    "uopf;": u"\U0001d566",
    "UpArrow;": u"\u2191",
    "Uparrow;": u"\u21d1",
    "uparrow;": u"\u2191",
    "UpArrowBar;": u"\u2912",
    "UpArrowDownArrow;": u"\u21c5",
    "UpDownArrow;": u"\u2195",
    "Updownarrow;": u"\u21d5",
    "updownarrow;": u"\u2195",
    "UpEquilibrium;": u"\u296e",
    "upharpoonleft;": u"\u21bf",
    "upharpoonright;": u"\u21be",
    "uplus;": u"\u228e",
    "UpperLeftArrow;": u"\u2196",
    "UpperRightArrow;": u"\u2197",
    "Upsi;": u"\u03d2",
    "upsi;": u"\u03c5",
    "upsih;": u"\u03d2",
    "Upsilon;": u"\u03a5",
    "upsilon;": u"\u03c5",
    "UpTee;": u"\u22a5",
    "UpTeeArrow;": u"\u21a5",
    "upuparrows;": u"\u21c8",
    "urcorn;": u"\u231d",
    "urcorner;": u"\u231d",
    "urcrop;": u"\u230e",
    "Uring;": u"\u016e",
    "uring;": u"\u016f",
    "urtri;": u"\u25f9",
    "Uscr;": u"\U0001d4b0",
    "uscr;": u"\U0001d4ca",
    "utdot;": u"\u22f0",
    "Utilde;": u"\u0168",
    "utilde;": u"\u0169",
    "utri;": u"\u25b5",
    "utrif;": u"\u25b4",
    "uuarr;": u"\u21c8",
    "Uuml;": u"\xdc",
    "Uuml": u"\xdc",
    "uuml;": u"\xfc",
    "uuml": u"\xfc",
    "uwangle;": u"\u29a7",
    "vangrt;": u"\u299c",
    "varepsilon;": u"\u03f5",
    "varkappa;": u"\u03f0",
    "varnothing;": u"\u2205",
    "varphi;": u"\u03d5",
    "varpi;": u"\u03d6",
    "varpropto;": u"\u221d",
    "vArr;": u"\u21d5",
    "varr;": u"\u2195",
    "varrho;": u"\u03f1",
    "varsigma;": u"\u03c2",
    "varsubsetneq;": u"\u228a"u"\ufe00",
    "varsubsetneqq;": u"\u2acb"u"\ufe00",
    "varsupsetneq;": u"\u228b"u"\ufe00",
    "varsupsetneqq;": u"\u2acc"u"\ufe00",
    "vartheta;": u"\u03d1",
    "vartriangleleft;": u"\u22b2",
    "vartriangleright;": u"\u22b3",
    "Vbar;": u"\u2aeb",
    "vBar;": u"\u2ae8",
    "vBarv;": u"\u2ae9",
    "Vcy;": u"\u0412",
    "vcy;": u"\u0432",
    "VDash;": u"\u22ab",
    "Vdash;": u"\u22a9",
    "vDash;": u"\u22a8",
    "vdash;": u"\u22a2",
    "Vdashl;": u"\u2ae6",
    "Vee;": u"\u22c1",
    "vee;": u"\u2228",
    "veebar;": u"\u22bb",
    "veeeq;": u"\u225a",
    "vellip;": u"\u22ee",
    "Verbar;": u"\u2016",
    "verbar;": "\x7c",
    "Vert;": u"\u2016",
    "vert;": "\x7c",
    "VerticalBar;": u"\u2223",
    "VerticalLine;": "\x7c",
    "VerticalSeparator;": u"\u2758",
    "VerticalTilde;": u"\u2240",
    "VeryThinSpace;": u"\u200a",
    "Vfr;": u"\U0001d519",
    "vfr;": u"\U0001d533",
    "vltri;": u"\u22b2",
    "vnsub;": u"\u2282"u"\u20d2",
    "vnsup;": u"\u2283"u"\u20d2",
    "Vopf;": u"\U0001d54d",
    "vopf;": u"\U0001d567",
    "vprop;": u"\u221d",
    "vrtri;": u"\u22b3",
    "Vscr;": u"\U0001d4b1",
    "vscr;": u"\U0001d4cb",
    "vsubnE;": u"\u2acb"u"\ufe00",
    "vsubne;": u"\u228a"u"\ufe00",
    "vsupnE;": u"\u2acc"u"\ufe00",
    "vsupne;": u"\u228b"u"\ufe00",
    "Vvdash;": u"\u22aa",
    "vzigzag;": u"\u299a",
    "Wcirc;": u"\u0174",
    "wcirc;": u"\u0175",
    "wedbar;": u"\u2a5f",
    "Wedge;": u"\u22c0",
    "wedge;": u"\u2227",
    "wedgeq;": u"\u2259",
    "weierp;": u"\u2118",
    "Wfr;": u"\U0001d51a",
    "wfr;": u"\U0001d534",
    "Wopf;": u"\U0001d54e",
    "wopf;": u"\U0001d568",
    "wp;": u"\u2118",
    "wr;": u"\u2240",
    "wreath;": u"\u2240",
    "Wscr;": u"\U0001d4b2",
    "wscr;": u"\U0001d4cc",
    "xcap;": u"\u22c2",
    "xcirc;": u"\u25ef",
    "xcup;": u"\u22c3",
    "xdtri;": u"\u25bd",
    "Xfr;": u"\U0001d51b",
    "xfr;": u"\U0001d535",
    "xhArr;": u"\u27fa",
    "xharr;": u"\u27f7",
    "Xi;": u"\u039e",
    "xi;": u"\u03be",
    "xlArr;": u"\u27f8",
    "xlarr;": u"\u27f5",
    "xmap;": u"\u27fc",
    "xnis;": u"\u22fb",
    "xodot;": u"\u2a00",
    "Xopf;": u"\U0001d54f",
    "xopf;": u"\U0001d569",
    "xoplus;": u"\u2a01",
    "xotime;": u"\u2a02",
    "xrArr;": u"\u27f9",
    "xrarr;": u"\u27f6",
    "Xscr;": u"\U0001d4b3",
    "xscr;": u"\U0001d4cd",
    "xsqcup;": u"\u2a06",
    "xuplus;": u"\u2a04",
    "xutri;": u"\u25b3",
    "xvee;": u"\u22c1",
    "xwedge;": u"\u22c0",
    "Yacute;": u"\xdd",
    "Yacute": u"\xdd",
    "yacute;": u"\xfd",
    "yacute": u"\xfd",
    "YAcy;": u"\u042f",
    "yacy;": u"\u044f",
    "Ycirc;": u"\u0176",
    "ycirc;": u"\u0177",
    "Ycy;": u"\u042b",
    "ycy;": u"\u044b",
    "yen;": u"\xa5",
    "yen": u"\xa5",
    "Yfr;": u"\U0001d51c",
    "yfr;": u"\U0001d536",
    "YIcy;": u"\u0407",
    "yicy;": u"\u0457",
    "Yopf;": u"\U0001d550",
    "yopf;": u"\U0001d56a",
    "Yscr;": u"\U0001d4b4",
    "yscr;": u"\U0001d4ce",
    "YUcy;": u"\u042e",
    "yucy;": u"\u044e",
    "Yuml;": u"\u0178",
    "yuml;": u"\xff",
    "yuml": u"\xff",
    "Zacute;": u"\u0179",
    "zacute;": u"\u017a",
    "Zcaron;": u"\u017d",
    "zcaron;": u"\u017e",
    "Zcy;": u"\u0417",
    "zcy;": u"\u0437",
    "Zdot;": u"\u017b",
    "zdot;": u"\u017c",
    "zeetrf;": u"\u2128",
    "ZeroWidthSpace;": u"\u200b",
    "Zeta;": u"\u0396",
    "zeta;": u"\u03b6",
    "Zfr;": u"\u2128",
    "zfr;": u"\U0001d537",
    "ZHcy;": u"\u0416",
    "zhcy;": u"\u0436",
    "zigrarr;": u"\u21dd",
    "Zopf;": u"\u2124",
    "zopf;": u"\U0001d56b",
    "Zscr;": u"\U0001d4b5",
    "zscr;": u"\U0001d4cf",
    "zwj;": u"\u200d",
    "zwnj;": u"\u200c",
}


def _decode(point, name):
    rest = u''

    # Code point
    if name is None:
        if point.startswith('x'):
            return uchr(int(point[1:], 16))
        else:
            return uchr(int(point))

    while len(name):
        if name in ENTITIES:
            return u'' + ENTITIES[name] + rest

        rest = name[-1] + rest
        name = name[:-1]

    return u'&' + rest


re_header = r(br'^[,;\s]*([^=;, ]+)\s*')
re_expires = r(br'^=\s*(\w+\W+\d+\W+\w+\W+\d+\W+\d+:\d+:\d+\W*\w+)')
re_quoted = r(br'^=\s*("(?:\\\\|\\"|[^"])*")')
re_unquoted = r(br'^=\s*([^;, ]*)')
re_separator = r(br'^[;\s]*,\s*')


def _header(string, cookie):
    decode = not isbytes(string)
    buf = bytearray(b(string, 'ascii'))
    tree = []
    tokens = []

    while buf:
        m = re_header.search(buf)
        if not m:
            break

        token = bytes(m.group(1))
        if decode:
            token = token.decode('ascii')
        tokens.append([token, None])
        del buf[:m.end()]

        while True:
            if cookie and len(tokens) and token.lower() == 'expires':
                m = re_expires.search(buf)
                if m:
                    tokens[-1][1] = bytes(m.group(1))
                    if decode:
                        tokens[-1][1] = tokens[-1][1].decode('ascii')
                    del buf[:m.end()]
                    break

            m = re_quoted.search(buf)
            if m:
                tokens[-1][1] = unquote(bytes(m.group(1)))
                if decode:
                    tokens[-1][1] = tokens[-1][1].decode('ascii')
                del buf[:m.end()]
                break

            m = re_unquoted.search(buf)
            if m:
                tokens[-1][1] = bytes(m.group(1))
                if decode:
                    tokens[-1][1] = tokens[-1][1].decode('ascii')
                del buf[:m.end()]
                break

            break

        m = re_separator.search(buf)
        if m:
            del buf[:m.end()]
            tree.append(tokens)
            tokens = []

    # Take care of final token
    if len(tokens):
        tree.append(tokens)

    return tree


def _readable(fd):
    readable, _, _ = select.select([fd], [], [], 0)
    return fd in readable


def _stash(obj, stash, *args, **kwargs):
    if kwargs:
        stash.update(kwargs)
        return obj
    elif len(args) == 1:
        return stash[args[0]]
    elif len(args) > 1:
        return tuple(map(lambda k: stash[k], args))
    else:
        return stash
