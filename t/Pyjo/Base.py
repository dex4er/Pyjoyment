import Pyjo.Test


class NoseTest(Pyjo.Test.NoseTest):
    script = __file__
    srcdir = '../..'


class UnitTest(Pyjo.Test.UnitTest):
    script = __file__


if __name__ == '__main__':
    from Pyjo.Test import *  # noqa

    import Pyjo.Base

    class A(Pyjo.Base.object):
        def __init__(self, **kwargs):
            self.a = kwargs.get('a')
            self.b = kwargs.get('b')

    obj = A()
    isa_ok(obj, A, 'obj')

    obj.set(a=1, b=2)
    is_ok(obj.a, 1, 'obj.a')
    is_ok(obj.b, 2, 'obj.b')

    obj = A.new(c=1, d=2)
    isa_ok(obj, A, 'obj')
    none_ok(obj.a, 'obj.c')
    none_ok(obj.b, 'obj.d')

    class B(Pyjo.Base.object):
        def __init__(self, **kwargs):
            self.a = kwargs.get('a', 1)
            self.b = kwargs.get('b', 2)
            self.c = kwargs.get('c', 3)
            self.d = kwargs.get('d', 45)
            self.e = kwargs.get('e', 45)

    obj = B.new()

    isa_ok(obj, B, 'obj')

    is_ok(obj.a, 1, 'obj.a')
    is_ok(obj.b, 2, 'obj.b')
    is_ok(obj.c, 3, 'obj.c')
    is_ok(obj.d, 45, 'obj.d')
    is_ok(obj.e, 45, 'obj.e')

    class C(Pyjo.Base.object):
        def __init__(self, **kwargs):
            self.a = kwargs.get('a', 1)

    obj1 = C.new()

    isa_ok(obj1, C, 'obj1')

    obj2 = C.new()

    isa_ok(obj2, C, 'obj2')

    is_ok(obj1.a, 1, 'obj1.a')

    obj1.a = 11

    is_ok(obj1.a, 11, 'obj1.a')
    is_ok(obj2.a, 1, 'obj2.a')

    obj3 = C.new()

    isa_ok(obj3, C, 'obj3')

    is_ok(obj3.a, 1, 'obj3.a')
    is_ok(obj2.a, 1, 'obj2.a')
    is_ok(obj1.a, 11, 'obj1.a')

    obj2.a = 2

    is_ok(obj3.a, 1, 'obj3.a')
    is_ok(obj2.a, 2, 'obj2.a')
    is_ok(obj1.a, 11, 'obj1.a')

    obj4 = C.new(a=4)

    is_ok(obj4.a, 4, 'obj4.a')
    is_ok(obj3.a, 1, 'obj3.a')
    is_ok(obj2.a, 2, 'obj2.a')
    is_ok(obj1.a, 11, 'obj1.a')

    obj5 = C.new()

    isa_ok(obj5, C, 'obj5')

    is_ok(obj5.a, 1, 'obj5.a')

    done_testing()
