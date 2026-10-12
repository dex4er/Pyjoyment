
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

print(f"[{line.p1.x},{line.p1.y}]")
print(f"[{line.p2.x},{line.p2.y}]")
