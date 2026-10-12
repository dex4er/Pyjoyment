import Pyjo.IOLoop


@Pyjo.IOLoop.recurring(0)
def writer(loop):
    print('A')


@Pyjo.IOLoop.timer(1)
def timeouter(loop):
    loop.remove(writer)


Pyjo.IOLoop.start()
