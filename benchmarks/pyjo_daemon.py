import Pyjo.Server.Daemon

import sys


Pyjo.Server.Daemon.new(listen=[f'http://127.0.0.1:{sys.argv[1]}'], silent=True).run()
