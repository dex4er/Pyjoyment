import Pyjo.EventEmitter


class Cat(Pyjo.EventEmitter.object):
    def poke(self, times):
        self.emit('roar', times)

    def kill(self):
        self.emit('dead')


def roar_cb(cat, times):
    for _ in range(0, times):
        print('RAWR!')


def dead_cb(cat):
    print('(x.x)')


tiger = Cat()

tiger.on(roar_cb, 'roar')
tiger.once(dead_cb, 'dead')

tiger.poke(2)
tiger.poke(2)
tiger.kill()
tiger.kill()
