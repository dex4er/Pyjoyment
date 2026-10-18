import Pyjoyment.Controller


# Controller
class MyApp_Controller_Foo(Pyjoyment.Controller.object):
    # Action
    def welcome(self):
        # Render response
        self.render(text='Hello there.')


object = MyApp_Controller_Foo
