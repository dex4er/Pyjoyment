import Pyjo.IOLoop


# Synchronize multiple events
delay = Pyjo.IOLoop.delay()


@delay.step
def step(delay):
    print('BOOM!')


for i in range(10):
    end = delay.begin()

    def timer_wrap(i):
        def timer_cb(loop):
            print(10 - i)
            end()

        return timer_cb

    Pyjo.IOLoop.timer(timer_wrap(i), i)

delay.wait()
