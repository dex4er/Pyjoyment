import Pyjo.Base
import Pyjo.String.Bytes
import Pyjo.String.Mixin
import Pyjo.String.Unicode

from Pyjo.Test import *

import math


class C(Pyjo.Base.object, Pyjo.String.Mixin.object):
    def __init__(self, **kwargs):
        self.value = kwargs.get('value')

    def to_str(self):
        return self.value


with subtest('to_str'):
    string = C(value='string')
    string2 = C(value='string')
    other = C(value='other')
    zero = C(value='0')
    empty = C(value='')

    isa_ok(string, C, 'string')
    isa_ok(string2, C, 'string2')
    isa_ok(other, C, 'other')
    isa_ok(zero, C, 'zero')
    isa_ok(empty, C, 'empty')

    # to_str
    isa_ok(string.to_str(), str, 'string.to_str()')
    is_ok(string.to_str(), 'string', "string.to_str() == 'string'")

    is_ok(string2.to_str(), 'string', "string2.to_str() == 'string'")
    is_ok(other.to_str(), 'other', "other.to_str() == 'other'")

    # __bool__
    ok(bool(string) is True, 'bool(string) is True')
    ok(bool(zero) is True, 'bool(zero) is True')
    ok(bool(empty) is False, 'bool(empty) is False')

    # __complex__
    is_ok(repr(complex(zero)), '0j', 'complex(zero)')

    # __eq__
    ok(string == 'string', "string == 'string'")
    ok(string == string, 'string == string')
    ok(string == string2, 'string == string2')

    # __float__
    is_ok(repr(float(zero)), '0.0', 'float(zero)')

    # __ge__
    ok(string >= 'string', "string >= 'string'")
    ok(string >= 'other', "string >= 'other'")
    ok(string >= string, 'string >= string')
    ok(string >= other, 'string >= other')

    # __gt__
    ok(not string > 'string', "not string > 'string'")
    ok(string > 'other', "string > 'other'")
    ok(not string > string, 'not string > string')
    ok(string > other, 'string > other')

    # __hash__
    ok(isinstance(hash(string), int), 'hash(string)')

    # __int__
    is_ok(repr(int(zero)), '0', 'int(zero)')

    # __le__
    ok(string <= 'string', "string <= 'string'")
    ok(not string <= 'other', "not string <= 'other'")
    ok(string <= string, 'string <= string')
    ok(not string <= other, 'not string <= other')

    # __lt__
    ok(not string < 'string', "not string < 'string'")
    ok(not string < 'other', "not string < 'other'")
    ok(not string < string, 'not string < string')
    ok(not string < other, 'string < other')

    # __ne__
    ok(not string != 'string', "not string != 'string'")
    ok(string != 'other', "string != 'other'")
    ok(string != other, 'string != other')
    ok(not other != other, 'not other != other')

    # __repr__
    is_ok(repr(string), "C('string')", 'repr(string) == "C(\'string\')"')

    # __str__
    isa_ok(str(string), str, 'string.to_str()')
    is_ok(str(string), 'string', "str(string) == 'string'")


class C2(Pyjo.Base.object, Pyjo.String.Mixin.object):
    def __init__(self, **kwargs):
        self.value = kwargs.get('value')

    def to_bytes(self):
        return self.value


with subtest('to_bytes'):
    string = C2(value=b'string')
    string2 = C2(value=b'string')
    other = C2(value=b'other')
    zero = C2(value=b'0')
    empty = C2(value=b'')

    isa_ok(string, C2, 'string')
    isa_ok(string2, C2, 'string2')
    isa_ok(other, C2, 'other')
    isa_ok(zero, C2, 'zero')
    isa_ok(empty, C2, 'empty')

    # to_bytes
    isa_ok(string.to_bytes(), bytes, 'string.to_bytes()')
    is_ok(string.to_bytes(), b'string', "string.to_bytes() == b'string'")

    is_ok(string2.to_bytes(), b'string', "string2.to_bytes() == b'string'")
    is_ok(other.to_bytes(), b'other', "other.to_bytes() == b'other'")

    # __bool__
    ok(bool(string) is True, 'bool(string) is True')
    ok(bool(zero) is True, 'bool(zero) is True')
    ok(bool(empty) is False, 'bool(empty) is False')

    # __eq__
    ok(string == b'string', "string == b'string'")
    ok(string == string, 'string == string')
    ok(string == string2, 'string == string2')

    # __float__
    is_ok(repr(float(zero)), '0.0', 'float(zero)')

    # __ge__
    ok(string >= b'string', "string >= b'string'")
    ok(string >= b'other', "string >= b'other'")
    ok(string >= string, 'string >= string')
    ok(string >= other, 'string >= other')

    # __gt__
    ok(not string > b'string', "not string > b'string'")
    ok(string > b'other', "string > b'other'")
    ok(not string > string, 'not string > string')
    ok(string > other, 'string > other')

    # __hash__
    ok(isinstance(hash(string), int), 'hash(string)')

    # __int__
    is_ok(repr(int(zero)), '0', 'int(zero)')

    # __le__
    ok(string <= b'string', "string <= b'string'")
    ok(not string <= b'other', "not string <= b'other'")
    ok(string <= string, 'string <= string')
    ok(not string <= other, 'not string <= other')

    # __lt__
    ok(not string < b'string', "not string < b'string'")
    ok(not string < b'other', "not string < b'other'")
    ok(not string < string, 'not string < string')
    ok(not string < other, 'string < other')

    # __ne__
    ok(not string != b'string', "not string != b'string'")
    ok(string != b'other', "string != b'other'")
    ok(string != other, 'string != other')
    ok(not other != other, 'not other != other')

    # __repr__
    is_ok(repr(string), "C2(b'string')", 'repr(string) == "C(b\'string\')"')

    # __str__
    isa_ok(str(string), str, 'string.to_str()')
    is_ok(str(string), "b'string'", '''str(string) == "b'string'"''')


class C3(Pyjo.Base.object, Pyjo.String.Mixin.object):
    def __init__(self, **kwargs):
        self.value = kwargs.get('value')

    def to_bytes(self):
        return bytes(self.value, 'ascii')

    def to_str(self):
        return self.value


with subtest('to_bytes and to_str'):
    string = C3(value='string')
    string2 = C3(value='string')
    other = C3(value='other')
    zero = C3(value='0')
    empty = C3(value='')

    isa_ok(string, C3, 'string')
    isa_ok(string2, C3, 'string2')
    isa_ok(other, C3, 'other')
    isa_ok(zero, C3, 'zero')
    isa_ok(empty, C3, 'empty')

    # to_str
    isa_ok(string.to_str(), str, 'string.to_str()')
    is_ok(string.to_str(), 'string', "string.to_str() == 'string'")

    is_ok(string2.to_str(), 'string', "string2.to_str() == 'string'")
    is_ok(other.to_str(), 'other', "other.to_str() == 'other'")

    # __bool__
    ok(bool(string) is True, 'bool(string) is True')
    ok(bool(zero) is True, 'bool(zero) is True')
    ok(bool(empty) is False, 'bool(empty) is False')

    # __complex__
    is_ok(repr(complex(zero)), '0j', 'complex(zero)')

    # __eq__
    ok(string == 'string', "string == 'string'")
    ok(string == string, 'string == string')
    ok(string == string2, 'string == string2')

    # __float__
    is_ok(repr(float(zero)), '0.0', 'float(zero)')

    # __ge__
    ok(string >= 'string', "string >= 'string'")
    ok(string >= 'other', "string >= 'other'")
    ok(string >= string, 'string >= string')
    ok(string >= other, 'string >= other')

    # __gt__
    ok(not string > 'string', "not string > 'string'")
    ok(string > 'other', "string > 'other'")
    ok(not string > string, 'not string > string')
    ok(string > other, 'string > other')

    # __hash__
    ok(isinstance(hash(string), int), 'hash(string)')

    # __int__
    is_ok(repr(int(zero)), '0', 'int(zero)')

    # __le__
    ok(string <= 'string', "string <= 'string'")
    ok(not string <= 'other', "not string <= 'other'")
    ok(string <= string, 'string <= string')
    ok(not string <= other, 'not string <= other')

    # __lt__
    ok(not string < 'string', "not string < 'string'")
    ok(not string < 'other', "not string < 'other'")
    ok(not string < string, 'not string < string')
    ok(not string < other, 'string < other')

    # __ne__
    ok(not string != 'string', "not string != 'string'")
    ok(string != 'other', "string != 'other'")
    ok(string != other, 'string != other')
    ok(not other != other, 'not other != other')

    # __repr__
    is_ok(repr(string), "C3('string')", 'repr(string) == "C3(\'string\')"')

    # __str__
    isa_ok(str(string), str, 'string.to_str()')
    is_ok(str(string), 'string', "str(string) == 'string'")

with subtest('Concatenation'):
    string = C(value='string')
    concat = string + '!'
    isa_ok(concat, Pyjo.String.Unicode.object, 'string + str')
    is_ok(concat, 'string!', 'right string')
    concat = '!' + string
    isa_ok(concat, Pyjo.String.Unicode.object, 'str + string')
    is_ok(concat, '!string', 'right string')
    is_ok(string + string, 'stringstring', 'string + string')
    throws_ok(lambda: string + C2(value=b'bytes'), TypeError, 'string + object of bytes')
    throws_ok(lambda: string + 1, TypeError, 'string + int')
    throws_ok(lambda: 1 + string, TypeError, 'int + string')
    throws_ok(lambda: string + b'!', TypeError, 'string + bytes')

    bstring = C2(value=b'bytes')
    concat = bstring + b'!'
    isa_ok(concat, Pyjo.String.Bytes.object, 'bytes + bytes')
    is_ok(concat, b'bytes!', 'right bytes')
    concat = b'!' + bstring
    isa_ok(concat, Pyjo.String.Bytes.object, 'bytes + bytes')
    is_ok(concat, b'!bytes', 'right bytes')
    is_ok(bstring + bytearray(b'!'), b'bytes!', 'bytes + bytearray')
    throws_ok(lambda: bstring + '!', TypeError, 'bytes + str')
    throws_ok(lambda: '!' + bstring, TypeError, 'str + bytes')

    is_ok(C3(value='both') + '!', 'both!', 'str of an object with both')

with subtest('Bytes'):
    is_ok(bytes(C(value='żółw')), 'żółw'.encode(), 'to_str encoded with UTF-8')
    is_ok(bytes(C2(value=b'bytes')), b'bytes', 'to_bytes')
    is_ok(bytes(C3(value='both')), b'both', 'to_bytes of an object with both')

with subtest('Format'):
    string = C(value='string')
    is_ok(f'{string}', 'string', 'f-string')
    is_ok(f'{string:>8}|', '  string|', 'f-string with a format')
    is_ok(format(string, '*^10'), '**string**', 'format')
    is_ok(f'{C2(value=b"bytes")}', "b'bytes'", 'f-string of bytes')

with subtest('Numbers'):
    number = C(value='2.5')
    is_ok(float(number), 2.5, 'float')
    is_ok(round(number), 2, 'round')
    is_ok(round(number, 1), 2.5, 'round with digits')
    is_ok(math.floor(number), 2, 'math.floor')
    is_ok(math.ceil(number), 3, 'math.ceil')
    is_ok(math.trunc(number), 2, 'math.trunc')
    number = C(value='-2.5')
    is_ok(math.floor(number), -3, 'math.floor of a negative number')
    is_ok(math.ceil(number), -2, 'math.ceil of a negative number')
    is_ok(math.trunc(number), -2, 'math.trunc of a negative number')
    is_ok(int(C(value='42')), 42, 'int')
    throws_ok(lambda: int(C(value='2.5')), ValueError, 'int of a float number')
    is_ok(complex(C(value='1+2j')), 1 + 2j, 'complex')
    is_ok(complex(C2(value=b'1+2j')), 1 + 2j, 'complex of bytes')
    is_ok(float(C2(value=b'2.5')), 2.5, 'float of bytes')
    is_ok(math.floor(C2(value=b'2.5')), 2, 'math.floor of bytes')


class Epoch(C):
    def __float__(self):
        return 1.5


with subtest('Overridden conversion'):
    epoch = Epoch(value='Thu, 01 Jan 1970 00:00:01 GMT')
    is_ok(round(epoch), 2, 'round')
    is_ok(math.floor(epoch), 1, 'math.floor')
    is_ok(math.ceil(epoch), 2, 'math.ceil')
    is_ok(math.trunc(epoch), 1, 'math.trunc')
    is_ok(f'{epoch:.3}', 'Thu', 'format of the string form')


class Nothing(Pyjo.Base.object, Pyjo.String.Mixin.object):
    pass


with subtest('Neither to_bytes nor to_str'):
    nothing = Nothing()
    error = 'Method "to_bytes" or "to_str" not implemented by subclass'
    throws_ok(lambda: str(nothing), error, 'str')
    throws_ok(lambda: bytes(nothing), error, 'bytes')
    throws_ok(lambda: bool(nothing), error, 'bool')
    throws_ok(lambda: nothing == 'string', error, '==')
    throws_ok(lambda: nothing + 'string', NotImplementedError, '+')

done_testing()
