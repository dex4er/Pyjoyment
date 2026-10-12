
import Pyjo.Test


class NoseTest(Pyjo.Test.NoseTest):
    script = __file__
    srcdir = '../..'


class UnitTest(Pyjo.Test.UnitTest):
    script = __file__


if __name__ == '__main__':

    from Pyjo.Test import *  # noqa

    import platform

    import Pyjo.Base
    import Pyjo.String.Mixin

    class C(Pyjo.Base.object, Pyjo.String.Mixin.object):
        def __init__(self, **kwargs):
            self.value = kwargs.get('value')

        def to_str(self):
            return self.value

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
    isa_ok(string.to_str(), str, "string.to_str()")
    is_ok(string.to_str(), 'string', "string.to_str() == 'string'")

    is_ok(string2.to_str(), 'string', "string2.to_str() == 'string'")
    is_ok(other.to_str(), 'other', "other.to_str() == 'other'")

    # __bool__
    ok(bool(string) is True, "bool(string) is True")
    ok(bool(zero) is True, "bool(zero) is True")
    ok(bool(empty) is False, "bool(empty) is False")

    # __complex__
    is_ok(repr(complex(zero)), '0j', "complex(zero)")

    # __eq__
    ok(string == 'string', "string == 'string'")
    ok(string == string, "string == string")
    ok(string == string2, "string == string2")

    # __float__
    is_ok(repr(float(zero)), '0.0', "float(zero)")

    # __ge__
    ok(string >= 'string', "string >= 'string'")
    ok(string >= 'other', "string >= 'other'")
    ok(string >= string, "string >= string")
    ok(string >= other, "string >= other")

    # __gt__
    ok(not string > 'string', "not string > 'string'")
    ok(string > 'other', "string > 'other'")
    ok(not string > string, "not string > string")
    ok(string > other, "string > other")

    # __hash__
    ok(isinstance(hash(string), int), "hash(string)")

    # __int__
    if platform.python_implementation() != 'PyPy':
        is_ok(repr(int(zero)), '0', "int(zero)")
    else:
        skip('PyPy3 error')

    # __le__
    ok(string <= 'string', "string <= 'string'")
    ok(not string <= 'other', "not string <= 'other'")
    ok(string <= string, "string <= string")
    ok(not string <= other, "not string <= other")

    # __lt__
    ok(not string < 'string', "not string < 'string'")
    ok(not string < 'other', "not string < 'other'")
    ok(not string < string, "not string < string")
    ok(not string < other, "string < other")

    # __ne__
    ok(not string != 'string', "not string != 'string'")
    ok(string != 'other', "string != 'other'")
    ok(string != other, "string != other")
    ok(not other != other, "not other != other")

    # __repr__
    is_ok(repr(string), "C('string')", "repr(string) == \"C('string')\"")

    # __str__
    isa_ok(str(string), str, "string.to_str()")
    is_ok(str(string), 'string', "str(string) == 'string'")

    class C2(Pyjo.Base.object, Pyjo.String.Mixin.object):
        def __init__(self, **kwargs):
            self.value = kwargs.get('value')

        def to_bytes(self):
            return self.value

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
    isa_ok(string.to_bytes(), bytes, "string.to_bytes()")
    is_ok(string.to_bytes(), b'string', "string.to_bytes() == b'string'")

    is_ok(string2.to_bytes(), b'string', "string2.to_bytes() == b'string'")
    is_ok(other.to_bytes(), b'other', "other.to_bytes() == b'other'")

    # __bool__
    ok(bool(string) is True, "bool(string) is True")
    ok(bool(zero) is True, "bool(zero) is True")
    ok(bool(empty) is False, "bool(empty) is False")

    # __eq__
    ok(string == b'string', "string == b'string'")
    ok(string == string, "string == string")
    ok(string == string2, "string == string2")

    # __float__
    is_ok(repr(float(zero)), '0.0', "float(zero)")

    # __ge__
    ok(string >= b'string', "string >= b'string'")
    ok(string >= b'other', "string >= b'other'")
    ok(string >= string, "string >= string")
    ok(string >= other, "string >= other")

    # __gt__
    ok(not string > b'string', "not string > b'string'")
    ok(string > b'other', "string > b'other'")
    ok(not string > string, "not string > string")
    ok(string > other, "string > other")

    # __hash__
    ok(isinstance(hash(string), int), "hash(string)")

    # __int__
    if platform.python_implementation() != 'PyPy':
        is_ok(repr(int(zero)), '0', "int(zero)")
    else:
        skip('PyPy3 error')

    # __le__
    ok(string <= b'string', "string <= b'string'")
    ok(not string <= b'other', "not string <= b'other'")
    ok(string <= string, "string <= string")
    ok(not string <= other, "not string <= other")

    # __lt__
    ok(not string < b'string', "not string < b'string'")
    ok(not string < b'other', "not string < b'other'")
    ok(not string < string, "not string < string")
    ok(not string < other, "string < other")

    # __ne__
    ok(not string != b'string', "not string != b'string'")
    ok(string != b'other', "string != b'other'")
    ok(string != other, "string != other")
    ok(not other != other, "not other != other")

    # __repr__
    is_ok(repr(string), "C2(b'string')", "repr(string) == \"C(b'string')\"")

    # __str__
    isa_ok(str(string), str, "string.to_str()")
    is_ok(str(string), "b'string'", '''str(string) == "b'string'"''')

    class C3(Pyjo.Base.object, Pyjo.String.Mixin.object):
        def __init__(self, **kwargs):
            self.value = kwargs.get('value')

        def to_bytes(self):
            return bytes(self.value, 'ascii')

        def to_str(self):
            return self.value

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
    isa_ok(string.to_str(), str, "string.to_str()")
    is_ok(string.to_str(), 'string', "string.to_str() == 'string'")

    is_ok(string2.to_str(), 'string', "string2.to_str() == 'string'")
    is_ok(other.to_str(), 'other', "other.to_str() == 'other'")

    # __bool__
    ok(bool(string) is True, "bool(string) is True")
    ok(bool(zero) is True, "bool(zero) is True")
    ok(bool(empty) is False, "bool(empty) is False")

    # __complex__
    is_ok(repr(complex(zero)), '0j', "complex(zero)")

    # __eq__
    ok(string == 'string', "string == 'string'")
    ok(string == string, "string == string")
    ok(string == string2, "string == string2")

    # __float__
    is_ok(repr(float(zero)), '0.0', "float(zero)")

    # __ge__
    ok(string >= 'string', "string >= 'string'")
    ok(string >= 'other', "string >= 'other'")
    ok(string >= string, "string >= string")
    ok(string >= other, "string >= other")

    # __gt__
    ok(not string > 'string', "not string > 'string'")
    ok(string > 'other', "string > 'other'")
    ok(not string > string, "not string > string")
    ok(string > other, "string > other")

    # __hash__
    ok(isinstance(hash(string), int), "hash(string)")

    # __int__
    if platform.python_implementation() != 'PyPy':
        is_ok(repr(int(zero)), '0', "int(zero)")
    else:
        skip('PyPy3 error')

    # __le__
    ok(string <= 'string', "string <= 'string'")
    ok(not string <= 'other', "not string <= 'other'")
    ok(string <= string, "string <= string")
    ok(not string <= other, "not string <= other")

    # __lt__
    ok(not string < 'string', "not string < 'string'")
    ok(not string < 'other', "not string < 'other'")
    ok(not string < string, "not string < string")
    ok(not string < other, "string < other")

    # __ne__
    ok(not string != 'string', "not string != 'string'")
    ok(string != 'other', "string != 'other'")
    ok(string != other, "string != other")
    ok(not other != other, "not other != other")

    # __repr__
    is_ok(repr(string), "C3('string')", "repr(string) == \"C3('string')\"")

    # __str__
    isa_ok(str(string), str, "string.to_str()")
    is_ok(str(string), 'string', "str(string) == 'string'")

    done_testing()
