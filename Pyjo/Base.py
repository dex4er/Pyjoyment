"""
Pyjo.Base - Minimal base class
==============================
::

    import Pyjo.Base
    from Pyjo.Util import notnone

    class Cat(Pyjo.Base.object):
        def __init__(self, **kwargs):
            self.name = kwargs.get('name', 'Nyan')
            self.birds = kwargs.get('birds', 2)
            self.mice = kwargs.get('mice', 2)

    class Tiger(Cat):
        def __init__(self, **kwargs):
            super(Tiger, self).__init__(**kwargs)
            self.friend = notnone(kwargs.get('friend'), lambda: Cat())
            self.stripes = kwargs.get('stripes', 42)

    mew = Cat.new(name='Longcat')
    print(mew.mice)
    print(mew.set(mice=3, birds=4).mice)

    rawr = Tiger.new(stripes=23, mice=0)
    print(rawr.tap(lambda self: self.friend.set(name='Tacgnol').mice))

:mod:`Pyjo.Base` is a simple base class for :mod:`Pyjo` projects.
"""


class Pyjo_Base:
    """::

        obj = SubClass.new()
        obj = SubClass.new(name='value')

    This base class provides a standard constructor for :mod:`Pyjo` objects. You can
    pass it a dict with attribute values.
    """

    @classmethod
    def new(cls, *args, **kwargs):
        """
        Factory method for :mod:`Pyjo.Base` class.
        """
        return cls(*args, **kwargs)

    def set(self, **kwargs):
        """::

            obj = obj.set(name='value')

        Sets each attribute from a dict.
        """
        for k, v in sorted(kwargs.items()):
            setattr(self, k, v)
        return self

    def tap(self, *args, **kwargs):
        """::

            obj = obj.tap(lambda obj: expression)
            obj = obj.tap(method)
            obj = obj.tap(method, *args, **kwargs)

        K combinator, tap into a method chain to perform operations on an object
        within the chain. The object will be the first argument passed to the callback. ::

            # Longer version
            obj = obj.tap(lambda obj: obj.method(args))

            # Inject side effects into a method chain
            obj.foo('A').tap(lambda obj: print(obj.foo)).set(foo='B')
        """
        method = args[0]
        if callable(method):
            method(self, *args[1:], **kwargs)
        else:
            getattr(self, method)(*args[1:], **kwargs)
        return self


new = Pyjo_Base.new
object = Pyjo_Base
