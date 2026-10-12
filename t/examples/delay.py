import Pyjo.Test


class NoseTest(Pyjo.Test.NoseTest):
    script = __file__
    srcdir = '../..'


class UnitTest(Pyjo.Test.UnitTest):
    script = __file__


if __name__ == '__main__':

    from Pyjo.Test import *  # noqa

    import Pyjo.IOLoop

    plan_tests(9)

    def step1(delay):
        pass_ok("Step 1")
        Pyjo.IOLoop.timer(delay.begin(), 0.2)
        Pyjo.IOLoop.timer(delay.begin(), 0.1)
        pass_ok('Wait 2 seconds for step 2.')

    def step2(delay):
        pass_ok("Step 2")

        def step2_1(delay2):
            pass_ok("Step 2.1")
            end = delay2.begin()
            Pyjo.IOLoop.timer(lambda loop: end('', 'OK'), 0.1)
            pass_ok('Wait 1 second for step 2.2.')

        def step2_2(delay2, *args):
            pass_ok(f"Step 2.2 got {args}")
            Pyjo.IOLoop.timer(delay2.begin(), 0.3)
            pass_ok('Wait 3 seconds for step 3.')

        Pyjo.IOLoop.delay().steps(
            step2_1,
            step2_2,
            delay.begin()
        ).wait()

    def step3(delay):
        pass_ok("Step 3")
        pass_ok('And done.')

    Pyjo.IOLoop.delay().steps(
        step1,
        step2,
        step3
    ).wait()

    done_testing()
