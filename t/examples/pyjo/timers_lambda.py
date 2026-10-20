if __name__ == '__main__':
    from Pyjo.Test import *  # noqa

    import Pyjo.IOLoop

    plan_tests(3)

    writer_id = Pyjo.IOLoop.recurring(0.4, lambda loop: pass_ok('A'))
    Pyjo.IOLoop.timer(1, lambda loop: loop.remove(writer_id))

    Pyjo.IOLoop.start()

    pass_ok('Event loop ended')

    done_testing()
