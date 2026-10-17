from Pyjoyment.Lite import get

import sys


@get('/yada')
def yada(c):
    name = c.stash('name')
    c.render(text=f'yada {name} works!')


@get('/bye')
def bye(c):
    name = c.stash('name')
    nb = ''
    c.ua().server.app = sys.modules['__main__'].app

    def cb(ua, tx):
        c.render(text=f'{tx.res.text}{name}! {nb}')

    c.ua().get('/hello/hello', cb)
    nb += 'success!'
