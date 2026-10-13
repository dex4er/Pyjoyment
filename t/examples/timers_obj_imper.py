if __name__ == '__main__':
    from Pyjo.Test import *  # noqa

    import Pyjo.IOLoop

    plan_tests(3)

    loop = Pyjo.IOLoop.singleton

    def writer_cb(loop):
        pass_ok('A')

    writer_id = loop.recurring(0.4, writer_cb)

    def timeouter_cb(loop):
        loop.remove(writer_id)

    loop.timer(1, timeouter_cb)

    loop.start()

    pass_ok('Event loop ended')

    done_testing()
