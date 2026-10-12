
r"""
Pyjo.JSON - Minimalistic JSON
=============================
::

    from Pyjo.JSON import decode_json, encode_json

    bstring = encode_json({'foo': [1, 2], 'bar': 'hello!', 'baz': True})
    dictionary = decode_json(bstring)

:mod:`Pyjo.JSON` is an implementation of :rfc:`7159` based on :mod:`json` module.

It supports normal Python data types like numbers, strings, booleans, lists, tuples and dicts
and will try to call the :meth:`to_json` method or :func:`dict` or :func:`list` function on objects, or
stringify them if it doesn't exist.

The two Unicode whitespace characters ``u2028`` and ``u2029`` will always be
escaped to make JSONP easier, and the character ``/`` to prevent XSS attacks. ::

    u"\u2028\u2029</script>" -> b'"\\u2028\\u2029<\\/script>"'

Other charaters will be encoded with ``utf-8`` encoding without escaping. ::

    {'i': u"♥ pyjo"} -> b'{"i":"\xe2\x99\xa5 pyjo"}'

Classes
-------
"""

from Pyjo.Util import b, isbytes, isiterable, isunicode, u

import json


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'to_json'):
            return obj.to_json()

        elif hasattr(obj, 'to_dict'):
            return obj.to_dict()

        elif isiterable(obj):
            try:
                return dict(obj)
            except TypeError:
                pass
            except ValueError:
                pass

            try:
                return list(obj)
            except TypeError:
                pass

        elif isbytes(obj):
            return u(obj)

        return str(obj)


def decode_json(bstring):
    """::

        value = decode_json(bstring)

    Decode JSON to Python value and die if decoding fails.
    """
    return from_json(u(bstring))


def encode_json(value):
    """::

        bstring = encode_json({'i': u'♥ pyjo'})

    Encode Python value to JSON.
    """
    return b(to_json(value))


def from_json(string):
    """::

        value = from_json(string)

    Decode JSON text that is not ``utf-8`` encoded to Python value and die if
    decoding fails.
    """
    return json.loads(string)


def j(obj):
    """::

        bstring = j([1, 2, 3])
        bstring = j({'i': u'♥ pyjo'})
        value = j(bstring)

    Encode Python data structure (which may only be :class:`dict` or :class:`list`
    or :class:`tuple`) or decode JSON, an :class:`None` return value indicates a bare ``null``
    or that decoding failed.
    """
    if isinstance(obj, (dict, list, tuple)):
        return encode_json(obj)
    else:
        try:
            return decode_json(obj)
        except ValueError:
            return


def to_json(value):
    """::

        string = to_json({'i': u'♥ pyjo'}

    Encode Python value to JSON text without ``utf-8`` encoding it.
    """
    string = json.dumps(value,
                        ensure_ascii=False,
                        allow_nan=False,
                        cls=JSONEncoder,
                        separators=(',', ':'),
                        sort_keys=True) \
                 .replace('/', r'\/')

    if isunicode(string):
        return string.replace('\u2028', r'\u2028') \
                     .replace('\u2029', r'\u2029')
    else:
        return string
