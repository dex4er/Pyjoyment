import Pyjo.IOLoop


loop = Pyjo.IOLoop.singleton


def writer_cb(loop):
    print('A')


writer_id = loop.recurring(0, writer_cb)


def timeouter_cb(loop):
    loop.remove(writer_id)


loop.timer(1, timeouter_cb)


loop.start()
