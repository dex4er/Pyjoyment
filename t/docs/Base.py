if __name__ == '__main__':
    from Pyjo.Test import *  # noqa

    import Pyjo.Base

    from Pyjo.Util import notnone

    class Cat(Pyjo.Base.object):
        def __init__(self, **kwargs):
            self.name = kwargs.get('name', 'Nyan')
            self.birds = kwargs.get('birds', 2)
            self.mice = kwargs.get('mice', 2)

    class Tiger(Cat):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.friend = notnone(kwargs.get('friend'), lambda: Cat())
            self.stripes = kwargs.get('stripes', 42)

    mew = Cat.new(name='Longcat')
    is_ok(mew.mice, 2, 'mew.mice')
    is_ok(mew.set(mice=3, birds=4).mice, 3, 'mew.set(...).mice')

    rawr = Tiger.new(stripes=23, mice=0)
    is_ok(rawr.tap(lambda rawr: rawr.friend.set(name='Tacgnol')).mice, 0, 'rawr.tap(...).mice')

    class SubClass(Pyjo.Base.object):
        def __init__(self, **kwargs):
            self.name = kwargs.get('name')

    # new
    obj = SubClass.new()
    isa_ok(obj, SubClass, 'obj')
    none_ok(obj.name, 'obj.name')

    obj = SubClass.new(name='value')
    is_ok(obj.name, 'value', 'obj.name')

    # set
    obj = SubClass.new()
    obj = obj.set(name='value')
    isa_ok(obj, SubClass, 'obj')
    is_ok(obj.name, 'value', 'obj.name')

    # tap
    obj = SubClass.new()
    obj = obj.tap(lambda obj: obj.set(name='value'))
    isa_ok(obj, SubClass, 'obj')
    is_ok(obj.name, 'value', 'obj.name')

    obj = SubClass.new()
    obj = obj.tap('set', name='value')
    isa_ok(obj, SubClass, 'obj')
    is_ok(obj.name, 'value', 'obj.name')

    done_testing()
