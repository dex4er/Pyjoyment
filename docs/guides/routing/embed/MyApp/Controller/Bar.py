import Pyjoyment


class MyApp_Controller_Bar(Pyjoyment.object):
    def handler(self, c):
        c.res.code = 200
        name = c.param('name')
        c.res.body = f'Hello {name}.'.encode()
        c.rendered()


object = MyApp_Controller_Bar
