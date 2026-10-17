import Pyjoyment.Controller


class PyjoymentTest_Baz(Pyjoyment.Controller.object):
    def index(self):
        self.render(text='Production namespace has low precedence!')


object = PyjoymentTest_Baz
