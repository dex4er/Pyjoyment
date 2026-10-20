import Pyjo.IOLoop


loop = Pyjo.IOLoop.singleton


@loop.recurring(0)
def writer(loop):
    print('A')


@loop.timer(1)
def timeouter(loop):
    loop.remove(writer)


loop.start()
