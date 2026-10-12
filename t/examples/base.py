import Pyjo.Test


class NoseTest(Pyjo.Test.NoseTest):
    script = __file__
    srcdir = '../..'


class UnitTest(Pyjo.Test.UnitTest):
    script = __file__


if __name__ == '__main__':
    from Pyjo.Test import *  # noqa

    import Pyjo.Base

    from Pyjo.Util import notnone

    class Point(Pyjo.Base.object):
        def __init__(self, **kwargs):
            self.x = kwargs.get('x', 0)
            self.y = kwargs.get('y', 0)

    class Line(Pyjo.Base.object):
        def __init__(self, **kwargs):
            self.p1 = notnone(kwargs.get('p1'), lambda: Point())
            self.p2 = notnone(kwargs.get('p2'), lambda: Point())

    p = Point(x=1, y=2)

    line = Line(p1=p)

    is_ok(f'[{line.p1.x},{line.p1.y}]', '[1,2]', 'line.p1')
    is_ok(f'[{line.p2.x},{line.p2.y}]', '[0,0]', 'line.p2')

    done_testing()
