import Pyjo.IOLoop


def step1(delay):
    # First step (simple timer)
    Pyjo.IOLoop.timer(delay.begin(), 2)
    print('Second step in 2 seconds.')


def step2(delay):
    # Second step (concurrent timers)
    Pyjo.IOLoop.timer(delay.begin(), 1)
    Pyjo.IOLoop.timer(delay.begin(), 3)
    print('Third step in 3 seconds.')


def step3(delay):
    print('And done after 5 seconds total.')


# Sequentialize multiple events
Pyjo.IOLoop.delay().steps(step1, step2, step3).wait()

print('END')
