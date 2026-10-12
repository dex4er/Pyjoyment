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

    loop = Pyjo.IOLoop.singleton

    def writer_cb(loop):
        pass_ok('A')

    writer_id = loop.recurring(writer_cb, 0.4)

    def timeouter_cb(loop):
        loop.remove(writer_id)

    loop.timer(timeouter_cb, 1)

    loop.start()

    pass_ok('Event loop ended')

    done_testing()
