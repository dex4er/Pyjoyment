import Pyjoyment


class PyjoymentConfigTest(Pyjoyment.object):
    def startup(self):
        self.plugin('Config')


new = PyjoymentConfigTest.new
object = PyjoymentConfigTest
