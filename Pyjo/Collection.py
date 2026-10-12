
r"""
Pyjo.Collection - Collection
============================
::

    import Pyjo.Collection

    # Manipulate collection
    collection = Pyjo.Collection.new(['just', 'works'])
    collection.insert(0, 'it')
    print(collection.join("\n"))

    # Chain methods
    collection.map(lambda word: word.capitalize()).shuffle() \
        .each(lambda word, num: print('{0}: {1}'.format(word, num)))

    # Use the alternative constructor
    from Pyjo.Collection import c
    c(['a', 'b', 'c']).join('/').encode().url_escape().decode().say()

:mod:`Pyjo.Collection` is a container for list-based collections which
inherits all methods from :class:`list` and provides own methods.

Classes
-------
"""

import Pyjo.String.Unicode


DEFAULT_CHARSET = 'utf-8'


class Pyjo_Collection(list):
    """
    :mod:`Pyjo.Collection` inherits all methods from
    :class:`list` and implements the following new ones.
    """

    def __new__(cls, value=[]):
        return super().__new__(cls, value)

    def __repr__(self):
        return "{0}.new({1})".format(self.__module__, super().__repr__())

    def compact(self):
        """::

            new = collection.compact()

        Create a new collection with all elements that are defined and not an empty
        string or list. ::

            # "0, 1, 2, 3"
            Pyjo.Collection.new([0, 1, None, 2, '', 3]).compact().join(', ')
        """
        return self.new(filter(lambda i: i is not None and not (hasattr(i, '__len__') and not len(i)), self))

    def get(self, index, default=None):
        """::

            value = collection.get(index)
            value = collection.get(index, default)

        Return the value for index if index is in the collection, else default.
        If default is not given, it defaults to None, so that this method never
        raises a KeyError. ::

            import sys
            from Pyjo.Util import die
            address = c(sys.argv).get(1) or die('address missing')
            port = int(c(sys.argv).get(2, '80'))
        """
        if len(self) > index:
            return self[index]
        else:
            return default

    def each(self, cb=None):
        """::

            iterator = collection.each()
            collection = collection.each(lambda e, num: ...)

        Evaluate callback for each element in collection or return all elements as an
        iterator if none has been provided. The element will be the first argument passed
        to the callback. ::

            # Make a numbered list
            @collection.each
            def cb(e, num):
                print("{0}: {1}".format(e, num))
        """
        if cb is None:
            return self.to_iter()
        else:
            num = 1
            for i in self:
                cb(i, num)
                num += 1
            return self

    def first(self, matched=None):
        """::

            first = collection.first()
            first = collection.first('string')
            first = collection.first(m(r'pattern', 'flags'))
            first = collection.first(lambda i: ...)

        Evaluate string or regular expression or callback for each element in collection and
        return the first one that matched the string or regular expression, or for which the
        callback returned true. The element will be the first argument passed to the
        callback. ::

            # Find first value that contains the word "mojo"
            interesting = collection.first(m('pyjo', 'i'))

            # Find first value that is greater than 5
            greater = collection.first(lambda i: i > 5)

        Return the first element in collection or :class:`None` if collection is empty.
        """
        if matched is None:
            if len(self) > 0:
                return self[0]
        elif callable(matched):
            for i in self:
                if matched(i):
                    return i
        else:
            for i in self:
                if i == matched:
                    return i
        return

    def flatten(self):
        """::

            new = collection.flatten()

        Flatten nested collections/lists/tuples recursively and create a new collection with
        all elements. ::

            # "1, 2, 3, 4, 5, 6, 7"
            Pyjo.Collection.new([1, [2, [3, 4], 5, [6]], 7]).flatten().join(', ').say()
        """
        return self.new(_flatten(self))

    def grep(self, matched):
        """::

            new = collection.grep('string')
            new = collection.grep(m(r'pattern', 'flags'))
            new = collection.grep(lambda i: ...)

        Evaluate string or regular expression or callback for each element in collection and
        create a new collection with all elements that matched the regular expression,
        or for which the callback returned true. The element will be the first
        argument passed to the callback.

            # Find all values that contain the word "mojo"
            interesting = collection.grep(m('mojo', 'i'))

            # Find all values that are greater than 5
            greater = collection.grep(lambda i: i > 5)
        """
        if callable(matched):
            return self.new(filter(lambda i: matched(i), self))
        else:
            return self.new(filter(lambda i: i == matched, self))

    def item(self, offset):
        """::

            item = collection.item(0)

        Return element from collection. ::

            # the same as
            item = collection[0]
        """
        return self[offset]

    def join(self, string=''):
        r"""::

            stream = collection.join()
            stream = collection.join("\n")

        Turn collection into :mod:`Pyjo.String.Bytes`. ::

            # Join all values with commas
            collection.join(', ').say()
        """
        return Pyjo.String.Unicode.new(string.join(map(lambda s: Pyjo.Util.u(s), self)))

    def last(self):
        """::

            last = collection.last()

        Return the last element in collection or :class:`None` if collection is empty.
        """
        if len(self) > 0:
            return self[-1]
        else:
            return

    def map(self, *args, **kwargs):
        """::

            new = collection.map(lambda a: ...)
            new = collection.map(attribute)
            new = collection.map(attribute, value)
            new = collection.map(method)
            new = collection.map(method, *args, **kwargs)

        Evaluate callback for, or get/set attribute from,
        or call method on, each element in collection and
        create a new collection from the results. The element will be the first
        argument passed to the callback. ::

            # Longer version for attribute
            new = collection.map(lambda a: getattr(a, attribute))
            new = collection.map(lambda a: setattr(a, attribute, value))

            # Longer version for method
            new = collection.map(lambda a: getattr(a, method)(*args))

            # Append the word "pyjo" to all values
            pyjoified = collection.map(lambda a: a + 'pyjo')
        """
        assert(args)
        attribute = args[0]
        args = args[1:]
        if callable(attribute):
            return self.new(map(attribute, self))
        else:
            return self.new(
                map(lambda a:
                    getattr(a, attribute)(*args, **kwargs) if callable(getattr(a, attribute))
                    else getattr(a, attribute, setattr(a, attribute, args[0])) if args
                    else getattr(a, attribute),
                    self))

    @classmethod
    def new(cls, value=[]):
        """::

            collection = Pyjo.Collection.new([1, 2, 3])

        Construct a new :mod:`Pyjo.Collection` object.
        """
        return Pyjo_Collection(value)

    def reverse(self):
        """::

            new = collection.reverse()

        Create a new collection with all elements in reverse order.
        """
        new = self.new(self)
        super(Pyjo_Collection, new).reverse()
        return new

    @property
    def size(self):
        """::

            size = collection.size()

        Number of elements in collection.
        """
        return len(self)

    def to_dict(self):
        """::

            d = params.to_dict()

        Turn collection of pairs of key and value into a :class:`dict`. ::

            # {'b': 2, 'a': 1, 'c': 3}
            Pyjo.Collection.new([('a', 1), ('b', 2), ('c', 3)]).to_dict()
        """
        return list(self)

    def to_iter(self):
        """::

            i = params.to_iter()

        Turn collection into a :class:`iter` iterator. ::

            for i in Pyjo.Collection.new([1, 2, 3]).to_iter():
                print(i)
        """
        return iter(self)

    def to_list(self):
        """::

            l = params.to_list()

        Turn collection into a :class:`list`. ::

            # [1, 2, 3]
            Pyjo.Collection.new([1, 2, 3]).to_list()
        """
        return list(self)

    def to_set(self):
        """::

            s = params.to_set()

        Turn collection into a :class:`set`. ::

            # {1, 2, 3}
            Pyjo.Collection.new([1, 2, 3]).to_set()
        """
        return set(self)

    def to_tuple(self):
        """::

            t = params.to_tuple()

        Turn collection into a :class:`tuple`. ::

            # (1, 2, 3)
            Pyjo.Collection.new([1, 2, 3]).to_tuple()
        """
        return tuple(self)

    def zip(self, list2):
        """::

            new = collection.zip([1, 2, 3])

        Agregates elements from collection and iterable and returns new
        collection of pairs. ::

            # [('a', 1), ('b', 2), ('c', 3)]
            Pyjo.Collection.new(['a', 'b', 'c']).zip([1, 2, 3])

        """
        return Pyjo.Collection.new(zip(self, list2))


def c(value=[]):
    """::

        collection = c([1, 2, 3])

    Construct a new :mod:`Pyjo.Collection` object.
    """
    return Pyjo_Collection(value)


def _flatten(array):
    for item in array:
        if isinstance(item, (list, tuple)):
            yield from _flatten(item)
        else:
            yield item


new = Pyjo_Collection.new
object = Pyjo_Collection
