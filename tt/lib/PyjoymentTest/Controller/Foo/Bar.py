import Pyjoyment.Controller


class PyjoymentTest_Controller_Foo_Bar(Pyjoyment.Controller.object):
    def index(self):
        return 1

    def test(self):
        self.stash(msg='works')


object = PyjoymentTest_Controller_Foo_Bar
