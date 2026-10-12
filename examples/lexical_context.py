class C:
    def m(self):
        class context:
            v = 42

        def s():
            context.v = 666

        s()

        return context.v


o = C()
print(o.m())
