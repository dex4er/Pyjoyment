import PyjoymentTest.Baz


class PyjoymentTest3_Baz(PyjoymentTest.Baz.object):
    def index(self):
        self.render(text='Development namespace has high precedence!')


object = PyjoymentTest3_Baz
