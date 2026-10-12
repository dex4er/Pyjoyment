import Pyjo.Test


class NoseTest(Pyjo.Test.NoseTest):
    script = __file__
    srcdir = '../..'


class UnitTest(Pyjo.Test.UnitTest):
    script = __file__


if __name__ == '__main__':
    from Pyjo.Test import *  # noqa

    import Pyjo.IOLoop

    plan_tests(3)

    @Pyjo.IOLoop.recurring(0.4)
    def writer(loop):
        pass_ok('A')

    @Pyjo.IOLoop.timer(1)
    def timeouter(loop):
        loop.remove(writer)

    Pyjo.IOLoop.start()

    pass_ok('Event loop ended')

    done_testing()
