import Pyjoyment.Command

from Pyjo.Util import getopt


class PyjoymentTest_Command_test_command(Pyjoyment.Command.object):
    def run(self, *args):
        # Left out from Mojolicious: the configuration "default" of Getopt::Long, which Pyjo.GetOpt has as it is
        opts = getopt(list(args), {'too': None})
        return 'works too!' if opts.too else 'works!'


object = PyjoymentTest_Command_test_command
