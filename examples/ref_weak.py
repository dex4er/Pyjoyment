import weakref


class C:
    _ref = None

    def __del__(self):
        print('__del__ ' + str(self))

    def ref(self, value=None):
        if value is None:
            return self._ref
        self._ref = value
        self._ref = weakref.proxy(self._ref)
        return self


def test():
    a = C()
    b = C()

    a.ref(b)
    b.ref(a)

    print(f'{a}.ref = {a.ref()}')
    print(f'{b}.ref = {b.ref()}')


test()
print('END')
