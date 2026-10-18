import Pyjoyment.Command


class MyApp_Command_spy(Pyjoyment.Command.object):
    description = 'Spy on application'
    usage = 'Usage: APPLICATION spy [TARGET]\n'

    def run(self, *args):
        # Leak secret passphrases
        if args[0] == 'secrets':
            print(*self.app.secrets, sep='\n')

        # Leak mode
        elif args[0] == 'mode':
            print(self.app.mode)


object = MyApp_Command_spy
