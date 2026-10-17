import Pyjoyment.Controller


class PyjoymentTest2_Foo(Pyjoyment.Controller.object):
    def test(self):
        self.res.headers.header('X-Bender', 'Bite my shiny metal ass!')
        self.render(text=self.url_for())


object = PyjoymentTest2_Foo
