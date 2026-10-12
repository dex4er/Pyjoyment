import Pyjo.IOLoop


# Sequentialize multiple events
delay = Pyjo.IOLoop.delay()


@delay.step
def step1(delay):
    # First step (simple timer)
    Pyjo.IOLoop.timer(delay.begin(), 2)
    print('Second step in 2 seconds.')


@delay.step
def step2(delay):
    # Second step (concurrent timers)
    Pyjo.IOLoop.timer(delay.begin(), 1)
    Pyjo.IOLoop.timer(delay.begin(), 3)
    print('Third step in 3 seconds.')


@delay.step
def step3(delay):
    print('And done after 5 seconds total.')


delay.wait()

print('END')
