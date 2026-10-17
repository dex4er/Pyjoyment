import Pyjoyment.Command


class PyjoymentTest_Command__test2_command(Pyjoyment.Command.object):
    def run(self, *args):
        return 'works 2!'


object = PyjoymentTest_Command__test2_command
