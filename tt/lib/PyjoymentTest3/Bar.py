import Pyjoyment.Controller


class PyjoymentTest3_Bar(Pyjoyment.Controller.object):
    def index(self):
        self.render(text='Development namespace works!')


object = PyjoymentTest3_Bar
