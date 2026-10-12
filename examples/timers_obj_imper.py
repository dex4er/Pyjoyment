import Pyjo.IOLoop


loop = Pyjo.IOLoop.singleton


def writer_cb(loop):
    print('A')


writer_id = loop.recurring(writer_cb, 0)


def timeouter_cb(loop):
    loop.remove(writer_id)


loop.timer(timeouter_cb, 1)


loop.start()
