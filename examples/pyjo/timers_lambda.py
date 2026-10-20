import Pyjo.IOLoop


writer_id = Pyjo.IOLoop.recurring(0, lambda loop: print('A'))
Pyjo.IOLoop.timer(1, lambda loop: loop.remove(writer_id))

Pyjo.IOLoop.start()
