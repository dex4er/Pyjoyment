import Pyjoyment.Controller


class PyjoymentTest_SideEffects_Test(Pyjoyment.Controller.object):
    def index(self):
        self.render(text='pass')


object = PyjoymentTest_SideEffects_Test
