class C:
    def m(self):
        v = 42

        def s():
            v = 666  # noqa

        s()

        return v

o = C()
print(o.m())
