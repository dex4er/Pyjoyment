import Pyjoyment.Controller


# Controller
class MyApp_Controller_Foo(Pyjoyment.Controller.object):
    # Action
    def bye(self):
        # Render response
        self.render(text='Good bye.')


object = MyApp_Controller_Foo
