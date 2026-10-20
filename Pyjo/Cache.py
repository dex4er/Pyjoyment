"""
Pyjo.Cache - Naive in-memory cache
==================================
::

    import Pyjo.Cache

    cache = Pyjo.Cache.new(max_keys=50)
    cache.set('foo', 'bar')
    foo = cache.get('foo')

:mod:`Pyjo.Cache` is a naive in-memory cache with size limits.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojo::Cache <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojo/Cache.pm>`_
of Mojolicious 9.49.
"""

import Pyjo.Base

import builtins

from collections.abc import Hashable
from typing import Self


type Anything = builtins.object


class Pyjo_Cache[K: Hashable, V](Pyjo.Base.object):
    """
    :mod:`Pyjo.Cache` inherits all methods from :mod:`Pyjo.Base` and
    implements the following new ones.
    """

    def __init__(self, max_keys: int = 100) -> None:
        """::

            cache = Pyjo.Cache.new()
            cache = Pyjo.Cache.new(max_keys=50)

        Construct a new :mod:`Pyjo.Cache` object.
        """
        self.max_keys = max_keys
        """::

            max = cache.max_keys
            cache.max_keys = 50

        Maximum number of cache keys, defaults to ``100``. Setting the value to
        ``0`` will disable caching.
        """

        # The order of the keys of a dict is the queue of Mojo
        self._cache: dict[K, V] = {}

    # Not in Mojolicious: the protocol of a container
    def __contains__(self, key: Anything) -> bool:
        """::

            boolean = 'foo' in cache

        Check if a value is cached.
        """
        return key in self._cache

    # Not in Mojolicious: the protocol of a container
    def __len__(self) -> int:
        """::

            count = len(cache)

        Number of cached values.
        """
        return len(self._cache)

    def get(self, key: K) -> V | None:
        """::

            value = cache.get('foo')

        Get cached value.
        """
        return self._cache.get(key)

    # The set() of Pyjo.Base sets attributes, the set() of Mojo caches a value
    def set(self, key: K, value: V) -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        """::

            cache = cache.set('foo', 'bar')

        Set cached value.
        """
        if (max := self.max_keys) <= 0:
            return self

        cache = self._cache
        while len(cache) >= max:
            del cache[next(iter(cache))]
        cache[key] = value

        return self


new = Pyjo_Cache.new
object = Pyjo_Cache
Cache = Pyjo_Cache
