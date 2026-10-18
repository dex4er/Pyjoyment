import Pyjoyment.Controller


# Controller
class MyApp_Controller_Foo(Pyjoyment.Controller.object):
    # Action
    def echo(self):
        @self.on('message')
        def message(self, msg):
            self.send(f'echo: {msg}')


object = MyApp_Controller_Foo
