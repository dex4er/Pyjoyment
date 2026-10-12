import Pyjo.IOLoop


writer_id = Pyjo.IOLoop.recurring(lambda loop: print('A'), 0)
Pyjo.IOLoop.timer(lambda loop: loop.remove(writer_id), 1)

Pyjo.IOLoop.start()
