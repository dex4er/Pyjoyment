from Pyjo.Test import *

import math


with subtest('Synopsis'):
    import Pyjo.Base

    from Pyjo.String.Mixin import Mixin

    class SubClass(Pyjo.Base.object, Mixin):
        def to_bytes(self):
            return b'value'

        def to_str(self):
            return 'value'

    # Use it as a string
    obj = SubClass()
    is_ok(f'{obj:>10}', '     value', "f'{obj:>10}'")
    is_ok(obj + '!', 'value!', "obj + '!'")

    import Pyjo.Base
    import Pyjo.String.Mixin

    class SubClass(Pyjo.Base.object, Pyjo.String.Mixin.object):
        def to_bytes(self):
            return b'value'

        def to_str(self):
            return 'value'

    # Use it as a string
    obj = SubClass.new()
    is_ok(f'{obj:>10}', '     value', "f'{obj:>10}'")
    is_ok(obj + '!', 'value!', "obj + '!'")

with subtest('Description'):
    # 'value/value'
    is_ok('/'.join(str(obj) for obj in (SubClass.new(), SubClass.new())), 'value/value', 'join')


class Number(Pyjo.Base.object, Pyjo.String.Mixin.object):
    def to_str(self):
        return '2.5'


class Integer(Pyjo.Base.object, Pyjo.String.Mixin.object):
    def to_str(self):
        return '42'


class Other(Pyjo.Base.object, Pyjo.String.Mixin.object):
    def to_str(self):
        return 'other'


obj = SubClass.new()
number = Number.new()
other = Other.new()

with subtest('__add__'):
    string = obj + 'string'
    isa_ok(string, Pyjo.String.Unicode.object, 'string')
    is_ok(string, 'valuestring', 'string')

with subtest('__bool__'):
    boolean = bool(obj)
    is_ok(boolean, True, 'boolean')

with subtest('__bytes__'):
    bstring = bytes(obj)
    is_ok(bstring, b'value', 'bstring')

with subtest('__ceil__'):
    integer = math.ceil(number)
    is_ok(integer, 3, 'number')

with subtest('__complex__'):
    complexnumber = complex(number)
    is_ok(complexnumber, 2.5 + 0j, 'number')

with subtest('__eq__'):
    boolean = obj == other
    is_ok(boolean, False, 'boolean')

with subtest('__float__'):
    floatnumber = float(number)
    is_ok(floatnumber, 2.5, 'number')

with subtest('__floor__'):
    integer = math.floor(number)
    is_ok(integer, 2, 'number')

with subtest('__format__'):
    string = format(obj, '>10')
    is_ok(string, '     value', 'string')
    string = f'{obj:>10}'
    is_ok(string, '     value', 'string')

with subtest('__ge__'):
    boolean = obj >= other
    is_ok(boolean, True, 'boolean')

with subtest('__gt__'):
    boolean = obj > other
    is_ok(boolean, True, 'boolean')

with subtest('__hash__'):
    integer = hash(obj)
    is_ok(integer, hash('value'), 'number')

with subtest('__int__'):
    integer = int(Integer.new())
    is_ok(integer, 42, 'number')

with subtest('__le__'):
    boolean = obj <= other
    is_ok(boolean, False, 'boolean')

with subtest('__lt__'):
    boolean = obj < other
    is_ok(boolean, False, 'boolean')

with subtest('__ne__'):
    boolean = obj != other
    is_ok(boolean, True, 'boolean')

with subtest('__radd__'):
    string = 'string' + obj
    isa_ok(string, Pyjo.String.Unicode.object, 'string')
    is_ok(string, 'stringvalue', 'string')

with subtest('__repr__'):
    import Pyjo.URL

    string = repr(obj)
    is_ok(string, "SubClass('value')", 'string')
    is_ok(repr(Pyjo.URL.new('http://example.com')), "Pyjo.URL.new('http://example.com')", 'Pyjo.URL')

with subtest('__round__'):
    integer = round(number)
    is_ok(integer, 2, 'number')
    floatnumber = round(number, 2)
    is_ok(floatnumber, 2.5, 'number')

with subtest('__str__'):
    string = str(obj)
    is_ok(string, 'value', 'string')

with subtest('__trunc__'):
    integer = math.trunc(number)
    is_ok(integer, 2, 'number')

done_testing()
