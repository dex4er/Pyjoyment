import Pyjoyment


class PyjoymentTest(Pyjoyment.object):
    def startup(self):
        # TODO: the rest of the startup of MojoliciousTest, with app.t, when it is ported

        # Application specific commands
        self.commands.namespaces.append('PyjoymentTest.Command')


new = PyjoymentTest.new
object = PyjoymentTest
