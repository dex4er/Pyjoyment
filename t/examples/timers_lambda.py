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

    writer_id = Pyjo.IOLoop.recurring(lambda loop: pass_ok('A'), 0.4)
    Pyjo.IOLoop.timer(lambda loop: loop.remove(writer_id), 1)

    Pyjo.IOLoop.start()

    pass_ok('Event loop ended')

    done_testing()
